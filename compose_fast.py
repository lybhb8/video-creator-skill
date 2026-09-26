#!/usr/bin/env python3
"""Fast ffmpeg-based video composer."""
import asyncio
import subprocess
import logging
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from models import VideoScript
from config import load_config
from tts.generator import TTSGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

FFMPEG = "/Users/mac/micromamba/envs/manim_env/bin/ffmpeg"

def get_duration(path):
    r = subprocess.run([FFMPEG, '-i', str(path)], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if 'Duration' in line:
            m = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', line)
            if m:
                h, mi, s, ms_str = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
                ms = int(ms_str) * (10 ** (3 - len(ms_str)))
                return h*3600 + mi*60 + s + ms/1000
            break
    return 0.0

def main():
    config = load_config()
    script = VideoScript.from_yaml('video-script-structured.yml')
    tts_gen = TTSGenerator(config)

    manim_dir = Path('/Users/mac/video_gen/assets/temp/videos/sections') / config.manim.quality_dir
    tts_dir = Path('/Users/mac/video_gen/assets/audio/narration')
    out_dir = Path('/Users/mac/video_gen/output')
    tmp_dir = Path('/Users/mac/video_gen/assets/temp')
    out_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Load TTS durations
    logger.info("=== Step 1: TTS ===")
    narrations = []
    for i, section in enumerate(script.sections):
        text = section.narration_tts_text
        if not text.strip():
            narrations.append(None)
            continue
        out_path = tts_dir / f"narration_{i:02d}_{section.title[:20]}.mp3"
        marker_path = Path(str(out_path) + ".txt")
        if out_path.exists() and marker_path.exists() and marker_path.read_text() == text:
            dur = get_duration(str(out_path))
            logger.info(f"  [{i}] {section.title[:35]}: {dur:.1f}s (cached)")
        else:
            logger.info(f"  [{i}] {section.title[:35]}: regenerating...")
            result = asyncio.get_event_loop().run_until_complete(
                tts_gen.generate_narration(text, str(out_path), section.narration_text)
            )
            marker_path.write_text(text)
            dur = result.duration
        narrations.append({'path': str(out_path), 'dur': dur, 'text': section.narration_text, 'skip': section.skip_subtitles, 'entries': getattr(section, 'visual_entries', [])})

    # Step 2: Build segment list with video stretching
    logger.info("=== Step 2: Compose ===")
    segments = []
    subtitles = []
    current_time = 0.0

    # Collect visual text entries for each scene
    from scenes.sections import SCENE_MAP
    visual_map = {}
    for i, section in enumerate(script.sections):
        if section.skip_subtitles:
            continue
        scene_cls = next((v for k, v in SCENE_MAP.items() if k in section.title), None)
        if scene_cls:
            inst = scene_cls()
            inst.construct()
            entries = inst.get_visual_text()
            section.visual_entries = entries
            visual_map[section.title] = entries
            logger.info(f"  [{i}] {section.title[:35]}: {len(entries)} visual entries")

    for i, section in enumerate(script.sections):
        found = None
        for f in manim_dir.glob('*.mp4'):
            if f.stem in section.title or section.title[:10] in f.stem:
                found = f
                break
        if not found:
            from scenes.sections import SCENE_MAP
            for k, v in SCENE_MAP.items():
                if k in section.title:
                    found = manim_dir / f"{v.__name__}.mp4"
                    break
        if not found or not found.exists():
            logger.warning(f"  Scene not found for: {section.title}")
            continue

        vid_dur = get_duration(found)
        n = narrations[i]
        narr_dur = n['dur'] if n else 0
        skip_sub = n['skip'] if n else False

        # Extend video to match narration if needed
        use_path = str(found)
        seg_dur = vid_dur
        # Keep original scene duration (don't extend to match narration)
        segments.append({'vid': use_path, 'aud': n['path'] if n else None, 'dur': seg_dur})
        current_time += seg_dur

        # Generate subtitles (narration sentences first, then visual text at end)
        if n and not skip_sub:
            sentences = re.split(r'[。！？!?\n]+', n['text'])
            sentences = [s.strip() for s in sentences if s.strip()]
            total_chars = sum(len(s) for s in sentences)
            seg_start = current_time - seg_dur
            if total_chars > 0:
                t = seg_start
                for s in sentences:
                    ratio = len(s) / total_chars
                    sd = seg_dur * ratio
                    subtitles.append((t, t + sd, s))
                    t += sd
            # Insert visual text entries after narration
            if n.get('entries'):
                narr_end = seg_start + seg_dur
                vis_count = len(n['entries'])
                vis_start = seg_start + seg_dur * 0.7
                vis_gap = seg_dur * 0.25 / max(vis_count, 1)
                for vi, vt in enumerate(n['entries']):
                    vs = vis_start + vi * vis_gap
                    ve = min(vs + vis_gap * 0.8, narr_end)
                    subtitles.append((vs, ve, vt))

    # Step 3: Concatenate videos
    logger.info("=== Step 3: Concatenate ===")
    concat_list = tmp_dir / 'concat_list.txt'
    with open(concat_list, 'w') as f:
        for seg in segments:
            f.write(f"file '{seg['vid']}'\n")
    composed_path = tmp_dir / 'composed.mp4'
    cmd = [FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_list),
           '-c:v', config.output.codec, '-pix_fmt', 'yuv420p', str(composed_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        logger.error(f"Concat failed: {r.stderr[-300:]}")
        return 1

    # Step 4: Mix audio
    logger.info("=== Step 4: Audio mix ===")
    audio_list = tmp_dir / 'audio_list.txt'
    with open(audio_list, 'w') as f:
        for seg in segments:
            if seg['aud']:
                f.write(f"file '{seg['aud']}'\n")
    mixed_audio = tmp_dir / 'mixed_audio.aac'
    cmd = [FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', str(audio_list),
           '-c:a', 'aac', '-b:a', '192k', str(mixed_audio)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        logger.warning(f"Audio mix warning: {r.stderr[-200:]}")

    # Step 5: Burn subtitles + fuse audio
    logger.info("=== Step 5: Burn subtitles ===")
    srt_path = out_dir / 'subtitles.srt'
    with open(srt_path, 'w', encoding='utf-8') as f:
        for idx, (start, end, text) in enumerate(subtitles, 1):
            def fmt(t):
                s = int(t); ms = int(round((t-s)*1000))
                return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}.{ms:02d}"
            f.write(f"{idx}\n{fmt(start)} --> {fmt(end)}\n{text}\n\n")

    ass_path = tmp_dir / 'subtitles.ass'
    cfg = config
    margin_v = cfg.output.resolution[1] - cfg.subtitles.margin_bottom
    font_name = cfg.manim.font
    ass_lines = [
        "[Script Info]", "Title: Subs",
        f"PlayResX: {cfg.output.resolution[0]}", f"PlayResY: {cfg.output.resolution[1]}", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{font_name},{cfg.subtitles.font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,{margin_v},1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for start, end, text in subtitles:
        def fmt(t):
            s = int(t); ms = int(round((t-s)*1000))
            return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}.{ms:02d}0"
        safe = text.replace('{', '\\{').replace('}', '\\}').replace('\n', '\\N')
        ass_lines.append(f"Dialogue: 0,{fmt(start)},{fmt(end)},Default,,0,0,0,,{safe}")
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ass_lines))

    output_path = out_dir / config.output.final_filename
    burn_cmd = [FFMPEG, '-y']
    if mixed_audio.exists():
        burn_cmd += ['-i', str(mixed_audio)]
    burn_cmd += ['-i', str(composed_path), '-vf', f"ass='{ass_path}'"]
    if mixed_audio.exists():
        burn_cmd += ['-map', '0:a', '-map', '1:v']
    else:
        burn_cmd += ['-map', '0:v']
    burn_cmd += ['-c:v', cfg.output.codec, '-crf', '19', '-preset', 'ultrafast',
               '-c:a', 'aac', '-b:a', '192k', str(output_path)]
    r = subprocess.run(burn_cmd, capture_output=True, text=True)
    if r.returncode != 0:
        logger.error(f"Burn failed: {r.stderr[-500:]}")
        return 1

    logger.info(f"Done: {output_path}")
    print(f"Final video: {output_path}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
