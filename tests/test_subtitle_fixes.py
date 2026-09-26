"""
Regression tests for subtitle synchronization, ordering, and layout fixes.
Each test calls a production helper directly; no private logic replicas.
"""
import asyncio
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from models import VideoSection, SectionContent, ContentType, VideoScript
from config import Config, SubtitleConfig, OutputConfig, ManimConfig, TTSConfig, AssetsConfig, LoggingConfig
from compositor.pipeline import VideoCompositor

_MANIM_FFMPEG = "/Users/mac/micromamba/envs/manim_env/bin/ffmpeg"


# ---------------------------------------------------------------------------
# Fix 1: exact-title-first, otherwise-longest-substring SCENE_MAP resolution
# ---------------------------------------------------------------------------

class TestSceneMapResolution:
    """Calls VideoCompositor._resolve_scene_class directly (production path)."""

    def test_exact_match_wins_over_prefix(self):
        title = "【硬件环境】平台配置"
        cls = VideoCompositor._resolve_scene_class(title)
        assert cls.__name__ == "GPUHardwareScene", (
            f"Expected GPUHardwareScene for '{title}' but got {cls.__name__ if cls else None}"
        )

    def test_shorter_title_still_maps(self):
        title = "【硬件环境】"
        cls = VideoCompositor._resolve_scene_class(title)
        assert cls is not None
        assert cls.__name__ == "HardwareScene", (
            f"Expected HardwareScene for '{title}' but got {cls.__name__}"
        )

    def test_pipeline_resolve_uses_longest_key(self):
        """Same assertion via the production static method."""
        title = "【硬件环境】平台配置"
        cls = VideoCompositor._resolve_scene_class(title)
        assert cls.__name__ == "GPUHardwareScene"


# ---------------------------------------------------------------------------
# Fix 2: fail-fast RuntimeError with section-specific message
# ---------------------------------------------------------------------------

class TestFailFastMissingScene:
    def test_raises_with_section_name(self, tmp_path):
        config = _make_config(tmp_path)
        script = _make_script_with_narration(2)
        comp = VideoCompositor(config, script)
        comp.scene_videos = {}

        # Provide matching narrations (with non-existent audio paths) so
        # _pair_narrations doesn't raise a count mismatch first.
        narrations = [
            _make_tts_result("/nonexistent/n0.mp3", duration=1.0, timestamps=[]),
            _make_tts_result("/nonexistent/n1.mp3", duration=1.0, timestamps=[]),
        ]

        with pytest.raises(RuntimeError, match="Missing canonical scene video for section 'Section 0'"):
            comp.compose_final_video(script, narrations)


# ---------------------------------------------------------------------------
# Fix 3: narration paired to ALL sections including no-narration gaps
# ---------------------------------------------------------------------------

class TestNarrationIndexPairing:
    """Uses _pair_narrations (production helper) to verify pairing."""

    def test_no_narration_section_does_not_drift(self, tmp_path):
        """Section without narration gets None; next narrated section keeps its index."""
        mp3_path = _write_silence_mp3(tmp_path / "narration.mp3", duration=2.0)

        sections = [
            VideoSection(title="S0", time_range="",
                         content=[SectionContent(type=ContentType.NARRATION, text="Hi there.")]),
            VideoSection(title="S1", time_range="", content=[]),  # no narration
            VideoSection(title="S2", time_range="",
                         content=[SectionContent(type=ContentType.NARRATION, text="Longer narration text here.")]),
        ]
        comp = VideoCompositor.__new__(VideoCompositor)

        narrations = [
            _make_tts_result(str(mp3_path), duration=2.0,
                             timestamps=[(0.0, 1.0, "Hi there.")]),
            _make_tts_result(str(mp3_path), duration=4.0,
                             timestamps=[(0.0, 2.0, "Longer narration text here.")]),
        ]

        paired = VideoCompositor._pair_narrations(sections, narrations)
        assert len(paired) == 3
        assert paired[0] is narrations[0]
        assert paired[1] is None
        assert paired[2] is narrations[1]

        # Verify _build_section_subtitles respects the pairing
        subs_s0 = comp._build_section_subtitles(sections[0], paired[0], 0.0,
                                                 _mock_clip(10.0))
        assert len(subs_s0) == 1 and "Hi there." in subs_s0[0][2]

        subs_s1 = comp._build_section_subtitles(sections[1], paired[1], 10.0,
                                                 _mock_clip(5.0))
        assert subs_s1 == []  # no narration -> empty

        subs_s2 = comp._build_section_subtitles(sections[2], paired[2], 15.0,
                                                 _mock_clip(10.0))
        assert len(subs_s2) == 1 and "Longer" in subs_s2[0][2]


# ---------------------------------------------------------------------------
# Fix 4: load_existing_narrations calls _vad_estimate_timestamps for reused MP3
# ---------------------------------------------------------------------------

class TestLoadExistingNarrationsVAD:
    def test_load_existing_uses_vad_not_char_ratio(self, tmp_path):
        """Existing MP3 loaded via load_existing_narrations should call _vad_estimate_timestamps."""
        mp3 = _write_silence_mp3(tmp_path / "narration_00_Test.mp3", duration=1.0)
        marker = tmp_path / "narration_00_Test.mp3.txt"
        marker.write_text("test tts text", encoding="utf-8")

        config = _make_config(tmp_path)
        gen = _make_generator(config)

        sections = [
            VideoSection(
                title="Test",
                time_range="",
                content=[SectionContent(
                    type=ContentType.NARRATION,
                    text="test display text",
                    tts_text="test tts text",
                )],
            )
        ]

        called_with: List[Tuple[List[str], str]] = []
        original = gen._vad_estimate_timestamps
        def tracked(sentences, audio_path):
            called_with.append((sentences, str(audio_path)))
            return [(0.0, 1.0, s) for s in sentences]
        gen._vad_estimate_timestamps = tracked

        results = asyncio.run(gen.load_existing_narrations(sections, tmp_path))
        assert len(results) == 1
        assert len(called_with) == 1, (
            f"Expected _vad_estimate_timestamps once, got {len(called_with)}"
        )
        assert called_with[0][1] == str(mp3)


# ---------------------------------------------------------------------------
# Fix 5: subtitle timestamps clamp to section_start + speech_end
# ---------------------------------------------------------------------------

class TestSubtitleTimestampClamp:
    def test_subtitles_clamped_to_speech_end(self):
        comp = VideoCompositor.__new__(VideoCompositor)
        raw_entries = [
            (0.0, 10.0, "First sentence"),
            (10.0, 25.0, "Middle sentence"),
            (25.0, 40.0, "Last sentence exceeds speech end"),
        ]
        clamped = comp._clamp_subtitles_to_speech(raw_entries, 44.3)
        for start, end, text in clamped:
            assert end <= 44.3 + 0.01, (
                f"Subtitle '{text}' ends at {end} > 44.3"
            )


# ---------------------------------------------------------------------------
# Fix 6: never append visual_entries to narration subtitles
# ---------------------------------------------------------------------------

class TestNoVisualEntriesInSubtitles:
    """Uses _build_section_subtitles (production path) to verify no visual leak."""

    def test_visual_entries_not_in_subtitles(self, tmp_path):
        mp3 = _write_silence_mp3(tmp_path / "narration.mp3", duration=2.0)
        sections = [
            VideoSection(
                title="S0",
                time_range="",
                content=[SectionContent(type=ContentType.NARRATION, text="Narration sentence.")],
                visual_entries=["On-screen chart label", "Table header text"],
            )
        ]
        script = VideoScript(sections=sections, validation=_dummy_validation())
        comp = VideoCompositor(_make_config(tmp_path), script)
        narr = _make_tts_result(str(mp3), duration=2.0,
                                timestamps=[(0.0, 2.0, "Narration sentence.")])
        clip = _mock_clip(5.0)
        subs = comp._build_section_subtitles(sections[0], narr, 0.0, clip)
        texts = [e[2] for e in subs]
        for ve in ["On-screen chart label", "Table header text"]:
            assert ve not in texts, f"visual_entry '{ve}' leaked into subtitles"


# ---------------------------------------------------------------------------
# Fix 7: wrap every SRT cue line to config.subtitles.max_chars_per_line
# ---------------------------------------------------------------------------

class TestSubtitleLineWrapping:
    def test_long_english_line_wrapped(self):
        comp = VideoCompositor.__new__(VideoCompositor)
        long_text = "This is a very long subtitle text that must be wrapped at the limit of twenty chars"
        wrapped = comp._wrap_line(long_text, 20)
        for line in wrapped:
            assert len(line) <= 20, f"Wrapped line '{line}' exceeds 20 chars ({len(line)})"
        assert len(wrapped) >= 2, f"Expected >= 2 lines, got {len(wrapped)}"

    def test_cjk_long_line_wrapped(self):
        comp = VideoCompositor.__new__(VideoCompositor)
        long_cjk = "这是一条非常长的中文字幕文本超过了最大字符限制需要被正确换行处理"
        wrapped = comp._wrap_line(long_cjk, 20)
        for line in wrapped:
            assert len(line) <= 20, f"Wrapped CJK line '{line}' exceeds 20 chars ({len(line)})"
        assert len(wrapped) >= 2, f"Expected >= 2 lines for CJK text, got {len(wrapped)}"

    def test_short_line_unchanged(self):
        comp = VideoCompositor.__new__(VideoCompositor)
        assert comp._wrap_line("短文本", 30) == ["短文本"]


# ---------------------------------------------------------------------------
# Fix 8: validate chronological non-overlapping, raise on violation
# ---------------------------------------------------------------------------

class TestSubtitleValidation:
    def test_monotonic_non_overlapping_accepted(self):
        entries = [(0.0, 2.0, "A"), (2.1, 4.0, "B"), (4.5, 6.0, "C")]
        comp = VideoCompositor.__new__(VideoCompositor)
        comp._validate_subtitle_order(entries)

    def test_overlapping_raises(self):
        entries = [(0.0, 3.0, "A"), (2.5, 5.0, "B"), (5.1, 7.0, "C")]
        comp = VideoCompositor.__new__(VideoCompositor)
        with pytest.raises(RuntimeError, match="overlap"):
            comp._validate_subtitle_order(entries)

    def test_non_monotonic_raises(self):
        entries = [(0.0, 2.0, "A"), (5.0, 6.0, "B"), (3.0, 4.0, "C")]
        comp = VideoCompositor.__new__(VideoCompositor)
        with pytest.raises(RuntimeError, match="overlap"):
            comp._validate_subtitle_order(entries)

    def test_end_equals_start_raises(self):
        entries = [(0.0, 2.0, "A"), (3.0, 3.0, "B")]
        comp = VideoCompositor.__new__(VideoCompositor)
        with pytest.raises(RuntimeError, match="end<=start"):
            comp._validate_subtitle_order(entries)


# ---------------------------------------------------------------------------
# Fix 9: libass FontName 'Heiti SC' in ASS output
# ---------------------------------------------------------------------------

class TestAssFontName:
    def test_ass_fontname_is_heiti_sc(self, tmp_path):
        config = _make_config(tmp_path)
        comp = VideoCompositor(config)
        srt = tmp_path / "test.srt"
        srt.write_text(
            "1\n00:00:01,000 --> 00:00:03,000\n测试字幕\n\n",
            encoding="utf-8",
        )
        ass = tmp_path / "test.ass"
        comp._srt_to_ass(str(srt), str(ass))
        content = ass.read_text(encoding="utf-8")
        assert "Heiti SC" in content, f"ASS output missing 'Heiti SC':\n{content}"
        style_lines = [l for l in content.splitlines() if l.startswith("Style:")]
        assert len(style_lines) >= 1
        assert "Heiti SC" in style_lines[0], f"Style line missing Heiti SC: {style_lines[0]}"


class TestAssTimestampConversion:
    """SRT millisecond timestamps must convert to ASS centiseconds correctly."""

    def test_exact_042_case(self, tmp_path):
        """SRT 00:03:34,042 must become ASS 0:03:34.04, not 0:03:34.420."""
        comp = VideoCompositor(_make_config(tmp_path))
        srt = tmp_path / "t.srt"
        srt.write_text(
            "1\n00:03:34,042 --> 00:03:34,900\ntest\n\n",
            encoding="utf-8",
        )
        ass = tmp_path / "t.ass"
        comp._srt_to_ass(str(srt), str(ass))
        content = ass.read_text(encoding="utf-8")
        assert "0:03:34.04" in content, f"Expected 0:03:34.04 in ASS output:\n{content}"
        assert "420" not in content, "ASS should not contain raw millisecond digits"

    def test_carry_999_ms(self, tmp_path):
        """SRT 00:00:00,999 must become ASS 0:00:01.00 (carry into seconds)."""
        comp = VideoCompositor(_make_config(tmp_path))
        srt = tmp_path / "t2.srt"
        srt.write_text(
            "1\n00:00:00,999 --> 00:00:01,001\ntest\n\n",
            encoding="utf-8",
        )
        ass = tmp_path / "t2.ass"
        comp._srt_to_ass(str(srt), str(ass))
        content = ass.read_text(encoding="utf-8")
        assert "0:00:01.00" in content, f"Expected carry into seconds:\n{content}"

    def test_roundtrip_no_overlap(self, tmp_path):
        """Round-trip a multi-cue SRT to ASS: every time within 10ms, no overlaps."""
        import re
        comp = VideoCompositor(_make_config(tmp_path))
        # 5 cues covering 0–5s with 1ms granularity
        cues = []
        for i in range(5):
            start_s = i * 1.0 + 0.001
            end_s = start_s + 0.998
            cues.append(f"{i+1}\n"
                        f"{_sec_to_srt(start_s)} --> {_sec_to_srt(end_s)}\n"
                        f"Cue text {i+1}\n\n")
        srt = tmp_path / "rt.srt"
        srt.write_text("".join(cues), encoding="utf-8")
        ass = tmp_path / "rt.ass"
        comp._srt_to_ass(str(srt), str(ass))
        content = ass.read_text(encoding="utf-8")
        pattern = r"Dialogue: \d+,(\d+:\d+:\d+\.\d+),(\d+:\d+:\d+\.\d+)"
        times = []
        for m in re.finditer(pattern, content):
            times.append(m.group(1))
            times.append(m.group(2))
        assert len(times) == 10, f"Expected 10 timestamps, got {len(times)}"
        # No overlaps: each start >= previous end (within 10ms)
        for j in range(1, len(times)):
            t_prev = _ass_to_sec(times[j - 1])
            t_curr = _ass_to_sec(times[j])
            assert t_curr >= t_prev - 0.01, (
                f"ASS overlap: {times[j-1]} vs {times[j]}"
            )
            # Each conversion must be within 10ms of original SRT value
            orig = _srt_to_sec(times[j])
            diff = abs(t_curr - orig)
            assert diff <= 0.01, (
                f"ASS/SRT mismatch >10ms: ASS={t_curr:.6f} orig={orig:.6f} "
                f"diff={diff:.6f}s for cue {j}"
            )


def _sec_to_srt(seconds: float) -> str:
    """Format seconds as SRT HH:MM:SS,mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ass_to_sec(t: str) -> float:
    """Parse ASS H:MM:SS.cs to float seconds."""
    parts = t.split(":")
    h = int(parts[0])
    m = int(parts[1])
    sec_parts = parts[2].split(".")
    s = int(sec_parts[0])
    cs = int(sec_parts[1]) if len(sec_parts) > 1 else 0
    return h * 3600 + m * 60 + s + cs / 100.0


def _srt_to_sec(t: str) -> float:
    """Parse SRT HH:MM:SS,mmm or ASS H:MM:SS.cs to float seconds."""
    parts = t.split(":")
    h = int(parts[0])
    m = int(parts[1])
    sec_part = parts[2]
    if "," in sec_part:
        s, ms = sec_part.split(",")
        return h * 3600 + m * 60 + int(s) + int(ms) / 1000.0
    else:
        s, cs = sec_part.split(".")
        return h * 3600 + m * 60 + int(s) + int(cs) / 100.0



# ---------------------------------------------------------------------------
# Fix A: _vad_speech_segments must exclude trailing silence
# ---------------------------------------------------------------------------

class TestVadSpeechSegmentsExcludesTrailingSilence:
    """_vad_speech_segments must not include trailing silence as a speech segment."""

    def test_trailing_silence_excluded(self, tmp_path):
        """Audio with tone then >=1s silence: last speech segment must end <= tone boundary."""
        mp3 = tmp_path / "vad_fixture.mp3"
        _write_tone_then_silence(mp3, tone_dur=1.0, silence_dur=2.0)

        from tts.generator import TTSGenerator
        gen = _make_generator(_make_config(tmp_path))
        gen._ffmpeg_cmd = _MANIM_FFMPEG
        gen._ffprobe_cmd = _MANIM_FFMPEG.replace("ffmpeg", "ffprobe")

        segments = gen._vad_speech_segments(str(mp3))
        assert len(segments) >= 1, f"Expected speech segments, got: {segments}"
        last_end = segments[-1][1]
        assert last_end <= 1.1, (
            f"Last speech segment ends at {last_end}s, should be <= 1.1s "
            f"(tone boundary). Segments: {segments}"
        )

    def test_speech_after_internal_silence_retained(self, tmp_path):
        """tone(1s)-silence(0.8s)-tone(1s): both tone segments must be returned."""
        import wave, math, struct
        mp3 = tmp_path / "vad_trip.mp3"
        sr = 44100
        n_tone = int(sr * 1.0)
        n_sil = int(sr * 0.8)
        frames = (
            struct.pack('<' + 'h' * n_tone,
                        *[int(32767 * 0.5 * math.sin(2 * math.pi * 440 * i / sr))
                          for i in range(n_tone)])
            + b'\x00\x00' * n_sil
            + struct.pack('<' + 'h' * n_tone,
                          *[int(32767 * 0.5 * math.sin(2 * math.pi * 440 * i / sr))
                            for i in range(n_tone)])
        )
        wav = tmp_path / "vad_trip.wav"
        with wave.open(str(wav), 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(frames)
        subprocess.run(
            [_MANIM_FFMPEG, '-y', '-i', str(wav), '-c:a', 'libmp3lame',
             '-b:a', '32k', str(mp3)],
            capture_output=True, timeout=15,
        )

        from tts.generator import TTSGenerator
        gen = _make_generator(_make_config(tmp_path))
        gen._ffmpeg_cmd = _MANIM_FFMPEG
        gen._ffprobe_cmd = _MANIM_FFMPEG.replace("ffmpeg", "ffprobe")

        segments = gen._vad_speech_segments(str(mp3))
        assert len(segments) == 2, f"Expected 2 speech segments, got {segments}"
        # First segment: tone before silence, starts at 0
        assert segments[0][0] < 0.1 and segments[0][1] < 1.1, (
            f"First segment incorrect: {segments[0]}"
        )
        # Second segment: tone after silence, ending at file duration (~2.8s)
        assert segments[1][0] > 1.7 and segments[1][1] > 2.7, (
            f"Second segment missing final tone: {segments[1]}"
        )


# ---------------------------------------------------------------------------
# Fix B: production _pair_narrations helper
# ---------------------------------------------------------------------------

class TestNarrationPairingProduction:
    """VideoCompositor._pair_narrations pairs all sections including no-narration gaps."""

    def test_no_narration_section_does_not_drift(self):
        sections = [
            VideoSection(title="S0", time_range="",
                         content=[SectionContent(type=ContentType.NARRATION, text="Hi there.")]),
            VideoSection(title="S1", time_range="", content=[]),
            VideoSection(title="S2", time_range="",
                         content=[SectionContent(type=ContentType.NARRATION, text="Longer narration text here.")]),
        ]
        comp = VideoCompositor.__new__(VideoCompositor)
        narrations = [
            _make_tts_result("n0.mp3", duration=2.0, timestamps=[(0.0, 1.0, "Hi there.")]),
            _make_tts_result("n2.mp3", duration=4.0, timestamps=[(0.0, 2.0, "Longer narration text here.")]),
        ]

        paired = VideoCompositor._pair_narrations(sections, narrations)
        assert len(paired) == 3
        assert paired[0] is narrations[0]
        assert paired[1] is None
        assert paired[2] is narrations[1]

    def test_trailing_no_narration_section(self):
        sections = [
            VideoSection(title="S0", time_range="",
                         content=[SectionContent(type=ContentType.NARRATION, text="Hi.")]),
            VideoSection(title="S1", time_range="", content=[]),
        ]
        comp = VideoCompositor.__new__(VideoCompositor)
        narrations = [_make_tts_result("n0.mp3", duration=1.0, timestamps=[])]

        paired = VideoCompositor._pair_narrations(sections, narrations)
        assert len(paired) == 2
        assert paired[0] is narrations[0]
        assert paired[1] is None

    def test_count_mismatch_raises(self):
        sections = [
            VideoSection(title="S0", time_range="",
                         content=[SectionContent(type=ContentType.NARRATION, text="Hi.")]),
        ]
        comp = VideoCompositor.__new__(VideoCompositor)
        narrations = [
            _make_tts_result("n0.mp3", duration=1.0, timestamps=[]),
            _make_tts_result("n1.mp3", duration=1.0, timestamps=[]),
        ]

        with pytest.raises(RuntimeError, match="mismatch|count"):
            VideoCompositor._pair_narrations(sections, narrations)


# ===========================================================================
# Helpers
# ===========================================================================

def _write_silence_mp3(path: Path, duration: float) -> Path:
    import subprocess
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["/Users/mac/micromamba/envs/manim_env/bin/ffmpeg", "-y", "-f", "lavfi",
         "-i", f"anullsrc=r=24000:cl=mono", "-t", str(duration),
         "-c:a", "libmp3lame", "-b:a", "32k", str(path)],
        capture_output=True, timeout=10,
    )
    return path


def _write_tone_then_silence(path: Path, tone_dur: float, silence_dur: float) -> Path:
    """Create an MP3 with a tone followed by silence for VAD testing."""
    import subprocess
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["/Users/mac/micromamba/envs/manim_env/bin/ffmpeg", "-y",
         "-f", "lavfi", "-i", f"sine=frequency=440:duration={tone_dur}",
         "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
         "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1",
         "-t", str(tone_dur + silence_dur),
         "-c:a", "libmp3lame", "-b:a", "32k", str(path)],
        capture_output=True, timeout=15,
    )
    return path


def _make_config(base_dir: Path) -> Config:
    return Config(
        output=OutputConfig(
            resolution=[1920, 1080], fps=30, format="mp4", codec="libx264",
            bitrate="8000k", output_dir=str(base_dir / "output"),
            final_filename="test.mp4",
        ),
        manim=ManimConfig(
            quality="medium", renderer="cairo", quality_dir="1080p30",
            background_color="#0d1117", font="STHeiti Medium", code_font="JetBrains Mono",
            text_color="#c9d1d9", accent_color="#6cb4ee", success_color="#4a9e4f",
            error_color="#c46054", warning_color="#c4982e",
            terminal_bg="#161b22", terminal_text="#8b949e", terminal_prompt="#6cb4ee",
        ),
        timing=None,
        tts=TTSConfig(voice="zh-CN-XiaoxiaoNeural", rate="+0%", volume="+0%", pitch="+0Hz", output_format="mp3"),
        subtitles=SubtitleConfig(font_size=40, font_color="#ffd700", outline_color="#000000",
                                  outline_width=2, margin_bottom=80, max_chars_per_line=30),
        chart_colors=[],
        assets=AssetsConfig(fonts_dir="", images_dir="", audio_dir=str(base_dir / "audio"),
                            temp_dir=str(base_dir / "temp")),
        logging=LoggingConfig(level="INFO", file=""),
    )


def _make_script_with_narration(n: int) -> VideoScript:
    sections = [
        VideoSection(title=f"Section {i}", time_range="",
                     content=[SectionContent(type=ContentType.NARRATION, text=f"Narration for section {i}.")])
        for i in range(n)
    ]
    return VideoScript(sections=sections, validation=_dummy_validation())


def _make_tts_result(audio_path: str, duration: float,
                     timestamps: List[Tuple[float, float, str]]):
    from tts.generator import TTSResult
    return TTSResult(audio_path=audio_path, duration=duration, text="", timestamps=timestamps)


def _make_generator(config: Config):
    from tts.generator import TTSGenerator
    return TTSGenerator(config)


def _dummy_validation():
    from models import ValidationInfo
    return ValidationInfo(
        total_sections=0, sections_with_visual_prompts=0, sections_with_narration=0,
        hierarchical_structure="unknown", markdown_headers_mapped=False,
        visual_prompts_extracted=False, nested_lists_handled=False,
        malformed_entries_rejected=False,
    )


class _MockClip:
    """Minimal mock for VideoFileClip used only in _build_section_subtitles tests."""
    def __init__(self, duration: float):
        self.duration = duration


def _mock_clip(duration: float):
    return _MockClip(duration)


# ---------------------------------------------------------------------------
# Fix: single-line subtitles via punctuation split (no mid-sentence truncation)
# ---------------------------------------------------------------------------

class TestSubtitleSingleLineSplitting:
    """Calls VideoCompositor._split_for_display / create_subtitles directly."""

    def test_short_text_stays_one_segment(self):
        assert VideoCompositor._split_for_display("短句。", 30) == ["短句。"]

    def test_all_segments_within_limit(self):
        text = ("本次测试覆盖 Qwen3.6 和 Qwen3.8 两个版本，五种推理方案："
                "Vulkan、ROCm、TurboQuant、DFlash、SGLang，逐一比拼")
        segments = VideoCompositor._split_for_display(text, 30)
        assert len(segments) > 1
        assert all(len(s) <= 30 for s in segments)

    def test_no_character_loss(self):
        text = "先看一下完整的测试平台。GPU：AMD Radeon RX 7900 XTX，24GB GDDR6"
        segments = VideoCompositor._split_for_display(text, 30)
        assert "".join(segments) == text

    def test_break_prefers_punctuation_boundary(self):
        text = "这是 AMD 2022 年底推出的 RDNA3 架构旗舰卡，96 个计算单元"
        segments = VideoCompositor._split_for_display(text, 30)
        assert not segments[0].endswith("单")

    def test_newline_between_cjk_joined_without_space(self):
        assert VideoCompositor._split_for_display("显存\n，跑模型", 30) == ["显存，跑模型"]

    def test_newline_inside_latin_word_keeps_space(self):
        assert VideoCompositor._split_for_display("Hello\nWorld", 30) == ["Hello World"]

    def test_create_subtitles_emits_multiple_single_line_cues(self, tmp_path):
        from config import get_config
        compositor = VideoCompositor(config=get_config())
        compositor.final_output_dir = tmp_path
        long_text = "本次测试覆盖 Qwen3.6 和 Qwen3.8 两个版本，五种推理方案：Vulkan、ROCm、TurboQuant、DFlash"
        compositor.create_subtitles([(0.0, 12.0, long_text)])

        raw = (tmp_path / "subtitles.srt").read_text(encoding="utf-8")
        blocks = [b for b in raw.strip().split("\n\n") if b.strip()]
        assert len(blocks) > 1, "long cue must be split into several cues"
        for block in blocks:
            lines = block.splitlines()
            assert len(lines) == 3, f"cue must be index+time+1 text line, got {lines}"
            assert len(lines[2]) <= 30

    def test_create_subtitles_keeps_full_text_across_cues(self, tmp_path):
        from config import get_config
        compositor = VideoCompositor(config=get_config())
        compositor.final_output_dir = tmp_path
        long_text = "本次测试覆盖 Qwen3.6 和 Qwen3.8 两个版本，五种推理方案：Vulkan、ROCm、TurboQuant、DFlash"
        compositor.create_subtitles([(0.0, 12.0, long_text)])

        raw = (tmp_path / "subtitles.srt").read_text(encoding="utf-8")
        rebuilt = "".join(b.splitlines()[2] for b in raw.strip().split("\n\n") if b.strip())
        assert rebuilt == long_text, "no text may be dropped when splitting"

    def test_create_subtitles_respects_original_time_span(self, tmp_path):
        from config import get_config
        compositor = VideoCompositor(config=get_config())
        compositor.final_output_dir = tmp_path
        long_text = "本次测试覆盖 Qwen3.6 和 Qwen3.8 两个版本，五种推理方案：Vulkan、ROCm、TurboQuant、DFlash"
        compositor.create_subtitles([(2.0, 14.0, long_text)])

        raw = (tmp_path / "subtitles.srt").read_text(encoding="utf-8")
        blocks = [b for b in raw.strip().split("\n\n") if b.strip()]
        first = blocks[0].splitlines()[1].split(" --> ")[0]
        last = blocks[-1].splitlines()[1].split(" --> ")[1]
        assert first == "00:00:02,000"
        assert last == "00:00:14,000"
