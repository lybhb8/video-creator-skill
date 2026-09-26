"""
MoviePy-based compositor: stitches Manim-rendered videos with TTS audio and subtitles.
"""
from moviepy import *
from moviepy.video.tools.subtitles import SubtitlesClip
import os
import time
from pathlib import Path
from typing import Tuple, List, Dict, Optional
import json
import logging
import subprocess
import asyncio
import edge_tts
import numpy as np

# Use manim_env ffmpeg (system ffmpeg is broken: missing libSvtAv1Enc)
_FFMPEG = "/Users/mac/micromamba/envs/manim_env/bin/ffmpeg"
def _ffmpeg(*args):
    return [_FFMPEG] + list(args)

from config import get_config, Config
from models import VideoScript, VideoSection
from tts.generator import TTSGenerator, TTSResult
from scenes.sections import SCENE_MAP

logger = logging.getLogger(__name__)


class VideoCompositor:
    def __init__(self, config: Config = None, script: VideoScript = None):
        self.config = config or get_config()
        self.script = script
        self.tts_generator = TTSGenerator(self.config)
        
        # TTS settings
        self.voice = self.config.tts.voice
        self.rate = self.config.tts.rate
        self.volume = self.config.tts.volume
        self.pitch = self.config.tts.pitch
        
        # Paths
        self.manim_output_dir = Path(self.config.assets.temp_dir) / "manim_videos"
        self.tts_output_dir = Path(self.config.assets.audio_dir) / "narration"
        self.final_output_dir = Path(self.config.output.output_dir)
        
        self.manim_output_dir.mkdir(parents=True, exist_ok=True)
        self.tts_output_dir.mkdir(parents=True, exist_ok=True)
        self.final_output_dir.mkdir(parents=True, exist_ok=True)

        # Scene to video file mapping
        self.scene_videos: Dict[str, str] = {}
        self.narration_results: List = []

    @staticmethod
    def _resolve_scene_class(section_title: str):
        """Return the best-matching scene class for a section title.

        Priority: exact title match first, then longest substring match.
        """
        exact = None
        longest = None
        longest_len = -1
        for key, cls in SCENE_MAP.items():
            if key == section_title:
                exact = (key, cls)
                break
            if key in section_title and len(key) > longest_len:
                longest = (key, cls)
                longest_len = len(key)
        return exact[1] if exact else (longest[1] if longest else None)

    def render_all_scenes(self, script: VideoScript) -> Dict[str, str]:
        """Render all Manim scenes to video files."""
        scene_files = {}

        for i, section in enumerate(script.sections):
            scene_class = self._resolve_scene_class(section.title)
            if scene_class is None:
                logger.warning(f"No scene class for section: {section.title}")
                continue
            
            output_file = self.manim_output_dir / f"scene_{i:02d}_{section.title[:30]}.mp4"
            scene_files[section.title] = str(output_file)
            
            # Check if already rendered
            if output_file.exists():
                logger.info(f"Scene already rendered: {output_file}")
                continue
            
            logger.info(f"Rendering scene {i+1}/{len(script.sections)}: {section.title}")
            self._render_manim_scene(scene_class, str(output_file))
        
        self.scene_videos = scene_files
        return scene_files

    def _collect_scene_visual_text(self, scene_class) -> List[str]:
        """Run the scene's construct() to collect visual_text_entries.

        Must be called in the manim_env Python environment so manim imports work.
        Returns the list of on-screen text strings recorded via record_visual_text().
        """
        from scenes.sections import SCENE_MAP
        # Reset the per-class state before each run
        scene_instance = scene_class()
        scene_instance.construct()
        return scene_instance.get_visual_text()

    def collect_all_visual_texts(self, script: VideoScript) -> Dict[str, List[str]]:
        """Populate each section's visual_entries by running every scene."""
        visual_map: Dict[str, List[str]] = {}
        for i, section in enumerate(script.sections):
            scene_class = self._resolve_scene_class(section.title)
            if scene_class is None:
                logger.warning(f"No scene class for section: {section.title}")
                continue
            if section.skip_subtitles:
                continue
            logger.info(f"Collecting visual text for section {i+1}: {section.title}")
            entries = self._collect_scene_visual_text(scene_class)
            section.visual_entries = entries
            visual_map[section.title] = entries
            logger.info(f"  → {len(entries)} visual text entries collected")
        return visual_map
    
    def _render_manim_scene(self, scene_class, output_path: str):
        """Render a single Manim scene using subprocess."""
        project_root = Path(__file__).parent.parent

        cmd = [
            'manim', 'render',
            str(project_root / "scenes" / "sections.py"),
            scene_class.__name__,
            '--media_dir', str(self.manim_output_dir.parent),
            '-q', self.config.manim.quality[0],  # l, m, h, 4k
            '-r', f'{self.config.output.resolution[0]},{self.config.output.resolution[1]}',
            '--fps', str(self.config.output.fps),
        ]

        logger.info(f"Running: {' '.join(cmd)}")

        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_root) + ':' + env.get('PYTHONPATH', '')

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900, env=env, cwd=project_root)

        if result.returncode != 0:
            logger.error(f"Manim render failed: {result.stderr}")
            raise RuntimeError(f"Manim render failed: {result.stderr}")

        quality_dir = self.config.manim.quality_dir
        expected = project_root / "assets" / "temp" / "videos" / "sections" / quality_dir / f"{scene_class.__name__}.mp4"
        if not expected.exists() or expected.stat().st_size == 0:
            media_videos = project_root / "assets" / "temp" / "videos"
            candidates = [p for p in media_videos.rglob("*.mp4") if p.stat().st_size > 0]
            if not candidates:
                logger.warning(f"No mp4 output found under {media_videos}")
                raise RuntimeError(f"Manim produced no video for {scene_class.__name__}")
            expected = max(candidates, key=lambda p: p.stat().st_mtime)

        canonical_dir = project_root / "assets" / "temp" / "videos" / "sections" / quality_dir
        canonical_dir.mkdir(parents=True, exist_ok=True)
        canonical_path = canonical_dir / f"{scene_class.__name__}.mp4"
        import shutil
        if expected != canonical_path:
            shutil.move(str(expected), str(canonical_path))

        if Path(output_path) != canonical_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(canonical_path), str(output_path))

        logger.info(f"Canonical scene video: {canonical_path}")
        logger.info(f"Rendered: {output_path}")
    
    async def _generate_silence_fallback(self, output_path: str) -> float:
        """Fallback: write a valid (silence) mp3 so narration never blocks
        compose on a transient edge-tts network failure. Scale-to-fit only
        needs a non-zero narration duration anchor; the actual audio gets
        sliced against the target_duration window anyway."""
        silence_path = output_path
        try:
            result = subprocess.run(_ffmpeg('-y', '-f', 'lavfi',
                '-i', 'anullsrc=r=24000:cl=mono',
                '-t', '5',
                '-c:a', 'libmp3lame', '-b:a', '32k',
                silence_path
            ), capture_output=True, text=True, timeout=60)
            duration = self._get_audio_duration(silence_path)
            if duration > 0:
                return duration
        except Exception as e:
            logger.warning(f"Could not write silence fallback: {e}")
        return 0.0

    async def _generate_audio(self, text: str, output_path: str) -> float:
        """Generate audio file using edge-tts with retry logic, return duration."""
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            duration = self._get_audio_duration(output_path)
            if duration > 0:
                logger.info(f"Reusing existing audio: {output_path}")
                return duration

        max_retries = 3
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=self.voice,
                    rate=self.rate,
                    volume=self.volume,
                    pitch=self.pitch
                )
                
                # Save audio
                await communicate.save(output_path)
                
                # Get duration using ffprobe
                duration = self._get_audio_duration(output_path)
                if duration > 0:
                    return duration
                else:
                    raise ValueError("Generated audio has zero duration")
        
            except Exception as e:
                if attempt == max_retries - 1:
                    # Last resort: write a valid (silence) mp3 so the narration
                    # stage never blocks compose on a transient edge-tts
                    # network failure. Scale-to-fit only needs a non-zero
                    # narration duration anchor; the actual audio content is
                    # sliced against the target_duration window anyway.
                    fallback = self._generate_silence_fallback(output_path)
                    if fallback > 0:
                        return fallback
                    logger.error(f"TTS failed after {max_retries} attempts: {e}")
                    raise
                delay = base_delay * (2 ** attempt)
                logger.warning(f"TTS attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        raise RuntimeError("TTS generation failed after all retries")
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration using manim_env ffprobe (system ffprobe is broken)."""
        try:
            result = subprocess.run(
                [_FFMPEG.replace('ffmpeg', 'ffprobe'), '-v', 'error',
                 '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1',
                 audio_path],
                capture_output=True, text=True, timeout=10,
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0
    
    async def generate_narration(self, text: str, output_path: str, display_text: str = None) -> TTSResult:
        """Generate narration audio with sentence-level timestamps."""
        audio_path = output_path
        display_text = display_text or text

        duration = await self._generate_audio(text, audio_path)

        sentences = self._split_sentences(display_text)
        # Use VAD-based timing when audio exists; falls back to char-ratio estimate
        if Path(audio_path).exists():
            timestamps = self._vad_estimate_timestamps(sentences, audio_path)
        else:
            timestamps = self._estimate_timestamps(sentences, duration)

        return TTSResult(
            audio_path=audio_path,
            duration=duration,
            text=display_text,
            timestamps=timestamps
        )
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences for timestamp estimation."""
        import re
        # Split by Chinese punctuation (and ASCII !?). Do NOT split on '.'
        # (period) because it appears inside URLs (readthedocs.yaml) and
        # version numbers (Sphinx 7.1.2, Ubuntu 22.04), which would shred them.
        sentences = re.split(r'[。！？!?\n]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _estimate_timestamps(self, sentences: List[str], total_duration: float) -> List[Tuple[float, float, str]]:
        """Fallback: estimate per-sentence timing by character-count proportion."""
        total_chars = sum(len(s) for s in sentences)
        if total_chars == 0:
            return []
        timestamps, t = [], 0.0
        for s in sentences:
            d = total_duration * len(s) / total_chars
            timestamps.append((t, t + d, s))
            t += d
        return timestamps

    def _vad_speech_segments(self, audio_path: str, min_silence_sec: float = 0.45) -> List[Tuple[float, float]]:
        """Detect speech segments via ffmpeg silencedetect.

        Returns [(start, end), ...] for each contiguous speech region.
        Trailing silence (edge-tts ~0.9s tail) is excluded.
        """
        try:
            result = subprocess.run(
                _ffmpeg('-i', str(audio_path),
                        '-af', f'silencedetect=noise=-35dB:d={min_silence_sec}',
                        '-f', 'null', '-'),
                capture_output=True, text=True, timeout=60,
            )
        except (subprocess.TimeoutExpired, OSError):
            return []

        pairs: List[Tuple[float, float]] = []
        starts: List[float] = []
        for line in result.stderr.splitlines():
            if 'silence_start: ' in line:
                try:
                    starts.append(float(line.split('silence_start: ')[1]))
                except ValueError:
                    continue
            elif 'silence_end: ' in line:
                try:
                    val = float(line.split('silence_end: ')[1].split('|')[0])
                    if starts:
                        pairs.append((starts.pop(), val))
                except ValueError:
                    continue

        if not pairs:
            return []

        file_dur = self._get_audio_duration(str(audio_path))
        if file_dur <= 0:
            file_dur = pairs[-1][1] + 2.0

        segments: List[Tuple[float, float]] = []
        # First speech: from start to first silence (skip intro noise floor < 0.5s)
        if pairs[0][0] > 0.5:
            segments.append((0.0, pairs[0][0]))
        # Middle segments: between consecutive silences (min 300ms speech)
        for i in range(len(pairs) - 1):
            gap = pairs[i + 1][0] - pairs[i][1]
            if gap > 0.3:
                segments.append((pairs[i][1], pairs[i + 1][0]))
        # Last segment: from last silence end to file end
        if file_dur - pairs[-1][1] > 0.5:
            segments.append((pairs[-1][1], file_dur))

        return segments

    def _vad_estimate_timestamps(
        self, sentences: List[str], audio_path: str,
    ) -> List[Tuple[float, float, str]]:
        """Map sentences to real speech timings via VAD.

        Uses ffmpeg silencedetect to find speech segments, then distributes
        each sentence's duration proportionally within its assigned segment
        based on character count. Falls back to character-ratio estimation
        when VAD detection fails.
        """
        segments = self._vad_speech_segments(audio_path)
        if not segments:
            total_dur = self._get_audio_duration(audio_path)
            return self._estimate_timestamps(sentences, total_dur)

        total_chars = sum(len(s) for s in sentences)
        if total_chars == 0:
            return []

        cum = [0.0]
        for s in sentences:
            cum.append(cum[-1] + len(s))

        total_speech = sum(e - s for s, e in segments)
        if total_speech <= 0:
            return self._estimate_timestamps(sentences, self._get_audio_duration(audio_path))

        def char_to_time(frac: float) -> float:
            """Map a char-fraction [0,1] to an absolute time within speech."""
            speech_acc = 0.0
            for seg_s, seg_e in segments:
                seg_len = seg_e - seg_s
                frac_start = speech_acc / total_speech
                frac_end = (speech_acc + seg_len) / total_speech
                if frac_start <= frac <= frac_end:
                    inner = (frac - frac_start) / (frac_end - frac_start) if frac_end > frac_start else 0
                    return seg_s + inner * seg_len
                speech_acc += seg_len
            return segments[-1][1]

        timestamps: List[Tuple[float, float, str]] = []
        for i, sentence in enumerate(sentences):
            t_start = char_to_time(cum[i] / total_chars)
            t_end = char_to_time(cum[i + 1] / total_chars)
            if t_end <= t_start:
                t_end = t_start + 0.5
            timestamps.append((t_start, t_end, sentence))

        return timestamps

    @staticmethod
    def _normalize_subtitles(entries: List[Tuple[float, float, str]],
                             clip_end: float,
                             min_gap: float = 0.08) -> List[Tuple[float, float, str]]:
        """Clip subtitle end times to clip_end and enforce min_gap between cues.

        Zero-room cues (end <= start after clamping) are dropped rather than
        artificially extended — an invalid cue must not appear in output.
        """
        if not entries:
            return entries
        out = []
        prev_end = 0.0
        for start, end, text in entries:
            start = max(start, 0.0)
            end = min(end, clip_end)
            if start >= clip_end:
                break
            if start < prev_end + min_gap:
                start = prev_end + min_gap
            if end <= start:
                # Zero room: drop this cue rather than fabricate a duration
                continue
            out.append((start, end, text))
            prev_end = end
        return out

    @staticmethod
    def _clamp_subtitles_to_speech(
        entries: List[Tuple[float, float, str]], speech_end_abs: float,
    ) -> List[Tuple[float, float, str]]:
        """Clamp each subtitle's end time to the absolute speech_end boundary."""
        if not entries:
            return entries
        out = []
        for start, end, text in entries:
            if end > speech_end_abs:
                end = speech_end_abs
            if start >= speech_end_abs:
                break
            out.append((start, end, text))
        return out

    @staticmethod
    def _wrap_line(text: str, max_chars: int) -> List[str]:
        """Wrap a single text line to fit within max_chars per line.

        For CJK-dominant text with no word boundaries, splits character-by-
        character so every output line is <= max_chars.
        """
        if len(text) <= max_chars:
            return [text]
        import re
        chunks = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]'
                            r'|[\w]+|[^\s\w]', text)
        lines: List[str] = []
        current: List[str] = []
        current_len = 0
        for chunk in chunks:
            clen = len(chunk)
            sep = 1 if current and chunk[0] not in ' \t' else 0
            if not current:
                current.append(chunk)
                current_len = clen
            elif current_len + sep + clen <= max_chars:
                current.append(chunk)
                current_len += sep + clen
            else:
                lines.append("".join(current))
                current = [chunk]
                current_len = clen
        if current:
            lines.append("".join(current))
        return lines

    @staticmethod
    def _validate_subtitle_order(
        entries: List[Tuple[float, float, str]],
    ) -> None:
        """Assert entries are strictly chronological, non-overlapping, with end>start."""
        if not entries:
            return
        prev_end = -1.0
        for idx, (start, end, text) in enumerate(entries):
            if end <= start:
                raise RuntimeError(
                    f"Subtitle entry {idx} has end<=start: ({start:.3f}, {end:.3f}, {text!r})"
                )
            if start < prev_end - 0.01:
                raise RuntimeError(
                    f"Subtitle entry {idx} overlaps with previous: "
                    f"({start:.3f}, {end:.3f}, {text!r}) after ({prev_end:.3f})"
                )
            prev_end = end
    
    async def generate_all_narrations(self, script: VideoScript, output_dir: Path = None) -> List[TTSResult]:
        """Generate audio for all sections with narration."""
        results = []
        if output_dir is None:
            output_dir = self.tts_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, section in enumerate(script.sections):
            tts_text = section.narration_tts_text
            if not tts_text.strip():
                continue
            
            output_path = output_dir / f"narration_{i:02d}_{section.title[:20]}.mp3"
            logger.info(f"Generating TTS for section {i+1}: {section.title}")
            
            result = await self.generate_narration(tts_text, str(output_path), display_text=section.narration_text)
            marker_path = Path(str(output_path) + ".txt")
            marker_path.write_text(tts_text, encoding="utf-8")
            results.append(result)
        
        return results
    
    _BREAK_CHARS = "，、。！？；：,.!?;:"

    @staticmethod
    def _flatten_for_display(text: str) -> str:
        """Join narration line breaks; keep a space only inside latin words."""
        out: List[str] = []
        for i, ch in enumerate(text):
            if ch in "\r\n":
                prev = out[-1] if out else ""
                nxt = text[i + 1] if i + 1 < len(text) else ""
                if prev.isascii() and prev.isalnum() and nxt.isascii() and nxt.isalnum():
                    out.append(" ")
                continue
            out.append(ch)
        return "".join(out).strip()

    @staticmethod
    def _hard_split(segment: str, max_chars: int):
        """Cut an oversized clause at a word boundary when one exists nearby."""
        cut = max_chars
        if segment[cut:cut + 1] and segment[cut - 1:cut + 1].isascii() and segment[cut:cut + 1].isalnum():
            probe = cut
            while probe > 1 and segment[probe - 1].isascii() and segment[probe - 1].isalnum():
                probe -= 1
            if cut - probe < 8:
                cut = probe
        head = segment[:cut].rstrip()
        return head, segment[cut:].lstrip()

    @classmethod
    def _split_for_display(cls, text: str, max_chars: int) -> List[str]:
        """Split a cue into single-line segments at punctuation boundaries.

        No characters are dropped; segments are concatenated back to the
        original text. Only a clause with no internal punctuation long enough
        to exceed max_chars on its own is cut, and then only at a latin word
        boundary.
        """
        cleaned = cls._flatten_for_display(text)
        if not cleaned or len(cleaned) <= max_chars:
            return [cleaned] if cleaned else []

        clauses: List[str] = []
        buf: List[str] = []
        for ch in cleaned:
            buf.append(ch)
            if ch in cls._BREAK_CHARS:
                clauses.append("".join(buf))
                buf = []
        if buf:
            clauses.append("".join(buf))

        segments: List[str] = []
        current = ""
        for clause in clauses:
            while len(clause) > max_chars:
                head, clause = cls._hard_split(clause, max_chars)
                if current:
                    segments.append(current)
                    current = ""
                segments.append(head)
            if not current:
                current = clause
            elif len(current) + len(clause) <= max_chars:
                current += clause
            else:
                segments.append(current)
                current = clause
        if current:
            segments.append(current)
        return [s for s in segments if s]

    def create_subtitles(self, subtitle_entries: List) -> str:
        srt_path = self.final_output_dir / "subtitles.srt"
        srt_content: List[str] = []
        max_chars = self.config.subtitles.max_chars_per_line
        index = 0
        for start, end, text in subtitle_entries:
            segments = self._split_for_display(text, max_chars)
            if not segments:
                continue
            if len(segments) == 1:
                cues = [(start, end, segments[0])]
            else:
                span = max(end - start, 0.0)
                weight = sum(len(s) for s in segments)
                cues = []
                cursor = start
                for pos, segment in enumerate(segments):
                    if pos == len(segments) - 1:
                        seg_end = end
                    else:
                        seg_end = cursor + span * len(segment) / weight
                        if seg_end <= cursor:
                            seg_end = min(end, cursor + 0.04)
                    cues.append((cursor, seg_end, segment))
                    cursor = seg_end
            for cue_start, cue_end, cue_text in cues:
                index += 1
                srt_content.append(f"{index}")
                srt_content.append(
                    f"{self._format_time(cue_start)} --> {self._format_time(cue_end)}"
                )
                srt_content.append(cue_text)
                srt_content.append("")
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_content))
        return str(srt_path)

    def _format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _safe_audio_clip(self, audio_file: str, total_duration: float) -> AudioClip:
        """Wrap a narration audio file so reads beyond its real length return silence.

        MoviePy's CompositeAudioClip queries every sub-clip's get_frame() for all
        timestamps (the `part is not False` mask only zeroes the result AFTER the
        call). When the narration (e.g. 34.27s) is shorter than the extended video
        clip (e.g. 40s), the underlying audio reader is queried at t=34.28+ and
        raises IOError. This wrapper returns zeros instead.
        """
        import numpy as np
        from moviepy.audio.AudioClip import AudioClip

        raw = AudioFileClip(audio_file)
        real_duration = raw.duration
        fps = raw.fps
        nchannels = raw.nchannels

        def frame_function(t):
            t_arr = np.atleast_1d(np.asarray(t, dtype=float))
            out = np.zeros((len(t_arr), nchannels), dtype=float)
            in_range = (t_arr >= 0) & (t_arr < real_duration)
            if in_range.any():
                out[in_range] = raw.get_frame(t_arr[in_range])
            if np.isscalar(t):
                return out[0]
            return out

        return AudioClip(frame_function, duration=total_duration, fps=fps)

    def _speech_end(self, audio_path: str) -> Optional[float]:
        """Return the timestamp where speech actually ends in a narration file.

        edge-tts mp3s carry ~0.9s of trailing silence, so file duration is
        longer than speech duration. Capping the video against file duration
        would leave a dead-silence tail beyond the 1.5s limit, so the cap
        anchor must be the silence-detected speech end instead.
        """
        cmd = _ffmpeg('-i', str(audio_path),
            '-af', 'silencedetect=noise=-45dB:d=0.4',
            '-f', 'null', '-',
        )
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except (subprocess.TimeoutExpired, OSError):
            return None
        marker = 'silence_start: '
        last = None
        for line in result.stderr.splitlines():
            if marker in line:
                try:
                    last = float(line.split(marker)[1])
                except ValueError:
                    continue
        return last

    def _build_section_subtitles(
        self, section: VideoSection, narration: Optional[TTSResult],
        current_time: float, clip: "VideoFileClip",
    ) -> List[Tuple[float, float, str]]:
        """Build subtitle entries for a single section.

        Returns an empty list when the section has no narration or skip_subtitles.
        Timestamps are scaled to the section window, clamped to speech_end and
        the target-duration boundary, then normalised.
        """
        if not narration or not Path(narration.audio_path).exists():
            return []
        anchor = self._speech_end(narration.audio_path) or narration.duration
        target_duration = min(clip.duration, anchor + 1.0)
        target_duration = max(target_duration, anchor)
        narr_duration = narration.duration or 1.0
        scale = target_duration / narr_duration
        section_subs: List[Tuple[float, float, str]] = []
        for start, end, text in narration.timestamps:
            section_subs.append(
                (current_time + start * scale, current_time + end * scale, text)
            )
        speech_end_abs = current_time + anchor
        boundary = min(current_time + target_duration, speech_end_abs)
        section_subs = self._clamp_subtitles_to_speech(section_subs, speech_end_abs)
        section_subs = self._normalize_subtitles(section_subs, boundary)
        return section_subs

    @staticmethod
    def _pair_narrations(
        sections: List[VideoSection], narration_results: List,
    ) -> List[Optional[TTSResult]]:
        """Pair each section with its TTSResult or None.

        Consumes narration_results only for sections that have non-empty
        narration text. Raises RuntimeError if the count of narrated sections
        does not match len(narration_results).
        """
        narrated_count = sum(
            1 for s in sections if s.narration_text.strip()
        )
        if narrated_count != len(narration_results):
            raise RuntimeError(
                f"Narration count mismatch: {narrated_count} narrated sections "
                f"but {len(narration_results)} results provided"
            )
        paired: List[Optional[TTSResult]] = []
        narr_idx = 0
        for section in sections:
            if section.narration_text.strip() and narr_idx < len(narration_results):
                paired.append(narration_results[narr_idx])
                narr_idx += 1
            else:
                paired.append(None)
        return paired

    def compose_final_video(self, script: VideoScript, narration_results: List) -> str:
        project_root = Path(__file__).parent.parent
        quality_dir = self.config.manim.quality_dir
        manim_media_dir = project_root / "assets" / "temp" / "videos" / "sections" / quality_dir

        clips = []
        audio_clips = []
        subtitle_entries = []
        current_time = 0.0

        narrated_pairs = self._pair_narrations(script.sections, narration_results)

        for i, (section, narration) in enumerate(zip(script.sections, narrated_pairs)):
            scene_class = self._resolve_scene_class(section.title)
            video_path = None
            if section.title in self.scene_videos:
                candidate = self.scene_videos[section.title]
                if Path(candidate).exists():
                    video_path = str(candidate)

            if not video_path and scene_class:
                potential_path = manim_media_dir / f"{scene_class.__name__}.mp4"
                if potential_path.exists():
                    video_path = str(potential_path)

            if not video_path or not Path(video_path).exists():
                raise RuntimeError(
                    f"Missing canonical scene video for section '{section.title}'"
                )

            clip = VideoFileClip(video_path)

            if narration and Path(narration.audio_path).exists():
                anchor = self._speech_end(narration.audio_path) or narration.duration
                target_duration = min(clip.duration, anchor + 1.0)
                target_duration = max(target_duration, anchor)
                audio = self._safe_audio_clip(narration.audio_path, target_duration)
                clip = clip.with_audio(audio)
                clip = clip.with_duration(target_duration)
                audio_clips.append(audio)

            if not section.skip_subtitles:
                section_subs = self._build_section_subtitles(
                    section, narration, current_time, clip
                )
                subtitle_entries.extend(section_subs)

            clips.append(clip)
            current_time += clip.duration

        if not clips:
            raise RuntimeError("No video clips to compose")

        final_video = concatenate_videoclips(clips, method="compose")

        if subtitle_entries:
            self._validate_subtitle_order(subtitle_entries)
            srt_path = self.create_subtitles(subtitle_entries)

        output_path = Path(self.config.output.output_dir) / self.config.output.final_filename
        logger.info(f"Writing final video to: {output_path}")

        if subtitle_entries:
            # ffmpeg burn path: write temp, then burn ASS subtitles
            temp_path = Path(self.config.assets.temp_dir) / "composed_temp.mp4"
            final_video.write_videofile(
                str(temp_path),
                fps=self.config.output.fps,
                codec=self.config.output.codec,
                bitrate=self.config.output.bitrate,
                audio_codec='aac',
                threads=4,
                logger=None
            )
            ass_path = str(Path(srt_path).with_suffix('.ass'))
            if Path(srt_path).suffix.lower() == '.srt':
                # libass (via the ass= filter) only parses ASS, never raw SRT.
                self._srt_to_ass(srt_path, ass_path)
                burn_source = ass_path
            else:
                burn_source = srt_path
            self._burn_ass_to_file(str(temp_path), str(output_path), burn_source)
            temp_path.unlink(missing_ok=True)
        else:
            final_video.write_videofile(
                str(output_path),
                fps=self.config.output.fps,
                codec=self.config.output.codec,
                bitrate=self.config.output.bitrate,
                audio_codec='aac',
                threads=4,
                logger='bar'
            )

        for clip in clips:
            clip.close()
        for audio in audio_clips:
            audio.close()
        final_video.close()

        logger.info(f"Final video saved: {output_path}")
        return str(output_path)

    def _srt_to_ass(self, srt_path: str, ass_path: str) -> None:
        """Convert SRT to ASS with Chinese font, white text, black outline,
        positioned at bottom with configurable margin."""
        cfg = self.config
        margin = cfg.subtitles.margin_bottom
        fontsize = cfg.subtitles.font_size
        font_name = "Heiti SC"

        import re
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        def srt_to_sec(t):
            m = re.match(r'(\d+):(\d+):(\d+),(\d+)', t)
            return int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)) + int(m.group(4))/1000

        blocks = []
        for block in content.strip().split('\n\n'):
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                m = re.search(r'(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)', lines[1])
                if m:
                    blocks.append((srt_to_sec(m.group(1)), srt_to_sec(m.group(2)), '\n'.join(lines[2:])))

        play_res_x, play_res_y = cfg.output.resolution
        margin_v = margin

        ass_lines = [
            "[Script Info]",
            "Title: Generated Subtitles",
            f"PlayResX: {play_res_x}",
            f"PlayResY: {play_res_y}",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Default,{font_name},{fontsize},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,{margin_v},1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]
        for start, end, text in blocks:
            def fmt(t):
                h = int(t // 3600)
                m = int((t % 3600) // 60)
                s = int(t % 60)
                cs = int(round((t - int(t)) * 100))
                if cs >= 100:
                    cs -= 100
                    s += 1
                if s >= 60:
                    s -= 60
                    m += 1
                if m >= 60:
                    m -= 60
                    h += 1
                return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
            safe = text.replace('{', '\\{').replace('}', '\\}').replace('\n', '\\N')
            ass_lines.append(f"Dialogue: 0,{fmt(start)},{fmt(end)},Default,,0,0,0,,{safe}")

        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(ass_lines))

    def _burn_ass_to_file(self, input_mp4: str, output_mp4: str, ass_path: str) -> None:
        """Use ffmpeg to burn ASS subtitles into video. Fast, precise positioning."""
        cmd = _ffmpeg('-y', '-i', input_mp4,
            '-vf', f"ass='{ass_path}'",
            '-c:v', self.config.output.codec,
            '-crf', '19',
            '-preset', 'ultrafast',
            '-c:a', 'aac',
            '-b:a', '192k',
            output_mp4,
        )
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            logger.error(f"ffmpeg burn failed: {result.stderr[-500:]}")
            raise RuntimeError(f"Subtitle burn failed: {result.stderr[-500:]}")
        logger.info(f"Subtitles burned: {output_mp4}")

    async def full_pipeline(self, script: VideoScript) -> str:
        logger.info("=== Starting full video generation pipeline ===")
        
        # Step 1: Render all Manim scenes
        logger.info("Step 1: Rendering Manim scenes...")
        self.render_all_scenes(script)
        
        # Step 2: Collect visual text from scenes + Generate TTS narrations
        logger.info("Step 2: Collecting visual text & Generating TTS narrations...")
        self.collect_all_visual_texts(script)
        narration_results = await self.generate_all_narrations(script)
        
        # Step 3: Compose final video
        logger.info("Step 3: Composing final video...")
        final_path = self.compose_final_video(script, narration_results)
        
        logger.info(f"=== Pipeline complete! Output: {final_path} ===")
        return final_path


async def main():
    """Test the compositor pipeline."""
    from models import VideoScript
    
    script = VideoScript.from_yaml("/Users/mac/video_gen/video-script-structured.yml")
    config = get_config()
    
    compositor = VideoCompositor(config, script)
    
    # Test: render one scene
    compositor.render_all_scenes(script)
    
    # Test: generate narration for one section
    narration_results = await compositor.generate_all_narrations(script)
    
    print("Pipeline test complete")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())