"""
TTS Module using edge-tts for Chinese narration generation.
"""
import asyncio
import edge_tts
import subprocess
import tempfile
import os
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
import logging

from config import load_config

logger = logging.getLogger(__name__)

@dataclass
class TTSResult:
    audio_path: str
    duration: float
    text: str
    timestamps: List[Tuple[float, float, str]]  # (start, end, text)


class TTSGenerator:
    def __init__(self, config=None):
        self.config = config or load_config()
        self.voice = self.config.tts.voice
        self.rate = self.config.tts.rate
        self.volume = self.config.tts.volume
        self.pitch = self.config.tts.pitch
    
    async def _generate_audio(self, text: str, output_path: str) -> float:
        """Generate audio file using edge-tts with retry logic, return duration."""
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
                    logger.error(f"TTS failed after {max_retries} attempts: {e}")
                    raise
                delay = base_delay * (2 ** attempt)
                logger.warning(f"TTS attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        raise RuntimeError("TTS generation failed after all retries")
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration, using ffprobe with a moviepy fallback."""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_path
            ], capture_output=True, text=True, timeout=10)
            duration = result.stdout.strip()
            if duration:
                return float(duration)
            logger.warning(f"ffprobe returned empty output for {audio_path}; using moviepy fallback")
        except Exception as e:
            logger.warning(f"Could not get duration for {audio_path} via ffprobe: {e}; using moviepy fallback")
        
        try:
            from moviepy.audio.io.AudioFileClip import AudioFileClip
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            audio.close()
            return duration
        except Exception as e:
            logger.warning(f"Could not get duration for {audio_path} via moviepy: {e}")
            return 0.0
    
    async def generate_narration(self, text: str, output_path: str, display_text: str = None) -> TTSResult:
        """Generate narration audio with sentence-level timestamps.

        `text` is what gets sent to edge-tts (may contain homophone/pronunciation
        fixes). `display_text` is the original text used for subtitle timestamps.

        Timestamps are derived from VAD (ffmpeg silencedetect) when the audio
        file is available, falling back to character-count proportionality.
        """
        audio_path = output_path
        display_text = display_text or text

        duration = await self._generate_audio(text, audio_path)

        sentences = self._split_sentences(display_text)
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

        Returns the complement of all silence intervals within [0, file_duration],
        so trailing silence is never included as a speech segment.
        """
        ffmpeg_cmd = getattr(self, '_ffmpeg_cmd', 'ffmpeg')
        ffprobe_cmd = getattr(self, '_ffprobe_cmd', 'ffprobe')
        try:
            result = subprocess.run(
                [ffmpeg_cmd, '-i', str(audio_path),
                 '-af', f'silencedetect=noise=-35dB:d={min_silence_sec}', '-f', 'null', '-'],
                capture_output=True, text=True, timeout=60,
            )
        except (subprocess.TimeoutExpired, OSError):
            return []
        silences: List[Tuple[float, float]] = []
        starts: List[float] = []
        for line in result.stderr.splitlines():
            if 'silence_start: ' in line:
                try: starts.append(float(line.split('silence_start: ')[1]))
                except ValueError: continue
            elif 'silence_end: ' in line:
                try:
                    val = float(line.split('silence_end: ')[1].split('|')[0])
                    if starts: silences.append((starts.pop(), val))
                except ValueError: continue
        dur_r = subprocess.run([ffprobe_cmd, '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)],
                       capture_output=True, text=True, timeout=10)
        try: file_dur = float(dur_r.stdout.strip())
        except (ValueError, subprocess.CalledProcessError): file_dur = 0.0
        if file_dur <= 0 or not silences:
            return []
        segments: List[Tuple[float, float]] = []
        prev_end = 0.0
        for s_start, s_end in silences:
            if s_start > prev_end + 0.01:
                segments.append((prev_end, s_start))
            prev_end = s_end
        # Append speech after the last internal silence, but only when there
        # is actual remaining duration (avoids emitting a zero-width stub).
        if file_dur > prev_end + 0.01:
            segments.append((prev_end, file_dur))
        return segments

    def _vad_estimate_timestamps(self, sentences: List[str], audio_path: str) -> List[Tuple[float, float, str]]:
        """Map sentences to real speech timings via VAD. Falls back to char-ratio."""
        segments = self._vad_speech_segments(audio_path)
        if not segments:
            dur_r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                            '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)],
                           capture_output=True, text=True, timeout=10)
            try: total_dur = float(dur_r.stdout.strip())
            except: total_dur = 0.0
            return self._estimate_timestamps(sentences, total_dur)
        total_chars = sum(len(s) for s in sentences)
        if total_chars == 0: return []
        cum = [0.0]
        for s in sentences: cum.append(cum[-1] + len(s))
        total_speech = sum(e - s for s, e in segments)
        if total_speech <= 0:
            return self._estimate_timestamps(sentences, self._get_audio_duration(audio_path))
        def char_to_time(frac: float) -> float:
            acc = 0.0
            for seg_s, seg_e in segments:
                seg_len = seg_e - seg_s
                fs, fe = acc / total_speech, (acc + seg_len) / total_speech
                if fs <= frac <= fe:
                    inner = (frac - fs) / (fe - fs) if fe > fs else 0
                    return seg_s + inner * seg_len
                acc += seg_len
            return segments[-1][1]
        timestamps = []
        for i, sentence in enumerate(sentences):
            t_start = char_to_time(cum[i] / total_chars)
            t_end = char_to_time(cum[i + 1] / total_chars)
            if t_end <= t_start: t_end = t_start + 0.5
            timestamps.append((t_start, t_end, sentence))
        return timestamps
    
    async def generate_all_narrations(self, sections: List, output_dir: Path) -> List[TTSResult]:
        """Generate audio for all sections with narration."""
        results = []
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, section in enumerate(sections):
            tts_text = section.narration_tts_text
            if not tts_text.strip():
                continue
            
            output_path = output_dir / f"narration_{i:02d}_{section.title[:20]}.mp3"
            logger.info(f"Generating TTS for section {i+1}: {section.title}")
            
            result = await self.generate_narration(tts_text, str(output_path), display_text=section.narration_text)
            results.append(result)
        
        return results

    async def load_existing_narrations(self, sections: List, output_dir: Path) -> List[TTSResult]:
        """Load already-generated narration files from disk without regenerating.

        Used by the compose step so video/audio remain consistent with the
        durations the scenes were rendered against, and to avoid slow,
        non-deterministic TTS regeneration on every compose run.

        A sidecar marker file stores the exact tts_text used to generate each
        file, so pronunciation overrides (tts_text) are picked up automatically
        when the script changes without relying on mtime.
        """
        results = []
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, section in enumerate(sections):
            tts_text = section.narration_tts_text
            if not tts_text.strip():
                continue

            output_path = output_dir / f"narration_{i:02d}_{section.title[:20]}.mp3"
            marker_path = Path(str(output_path) + ".txt")

            marker_matches = False
            if marker_path.exists():
                try:
                    marker_matches = marker_path.read_text(encoding="utf-8") == tts_text
                except Exception:
                    marker_matches = False

            if output_path.exists() and marker_matches:
                duration = self._get_audio_duration(str(output_path))
                if duration > 0:
                    sentences = self._split_sentences(section.narration_text)
                    timestamps = self._vad_estimate_timestamps(sentences, output_path)
                    logger.info(f"Loaded existing TTS for section {i+1}: {section.title} ({duration:.1f}s)")
                    results.append(TTSResult(
                        audio_path=str(output_path),
                        duration=duration,
                        text=section.narration_text,
                        timestamps=timestamps
                    ))
                    continue

            logger.info(
                f"{'Missing or stale marker for' if output_path.exists() else 'Narration file missing for'} "
                f"section {i+1} ({section.title}); regenerating at {output_path.name}"
            )
            result = await self.generate_narration(tts_text, str(output_path), display_text=section.narration_text)
            marker_path.write_text(tts_text, encoding="utf-8")
            results.append(result)

        return results


async def main():
    """Test TTS generation."""
    from models import VideoScript
    
    script = VideoScript.from_yaml("/Users/mac/Desktop/video-script-structured.yml")
    config = load_config()
    
    tts = TTSGenerator(config)
    output_dir = Path(config.assets.audio_dir) / "narration"
    
    results = await tts.generate_all_narrations(script.sections, output_dir)
    
    for r in results:
        print(f"Generated: {r.audio_path} ({r.duration:.1f}s)")


if __name__ == "__main__":
    asyncio.run(main())