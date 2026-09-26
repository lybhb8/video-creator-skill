#!/usr/bin/env python3
"""Burn Agnes subtitles (ASS) onto the already-composed temp video."""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models import VideoScript
from config import load_config
from compositor.pipeline import VideoCompositor

SCRIPT = "/Users/mac/video_gen/agnes_video_script.yml"
TEMP_DIR = "assets/temp_agnes"
OUTPUT_DIR = "output_agnes"
FINAL_NAME = "agnes_ai_free_tutorial.mp4"


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    config = load_config("config.yaml")
    config.output.output_dir = OUTPUT_DIR
    config.assets.temp_dir = TEMP_DIR
    config.output.final_filename = FINAL_NAME

    script = VideoScript.from_yaml(SCRIPT)
    compositor = VideoCompositor(config, script)

    temp_mp4 = Path(TEMP_DIR) / "composed_temp.mp4"
    out_mp4 = Path(OUTPUT_DIR) / FINAL_NAME
    srt = Path(OUTPUT_DIR) / "subtitles.srt"
    ass = Path(OUTPUT_DIR) / "subtitles.ass"

    if not temp_mp4.exists():
        raise SystemExit(f"Missing composed temp: {temp_mp4}")
    if not srt.exists():
        raise SystemExit(f"Missing srt: {srt}")

    compositor._srt_to_ass(str(srt), str(ass))
    compositor._burn_ass_to_file(str(temp_mp4), str(out_mp4), str(ass))
    logging.getLogger(__name__).info(f"=== BURN DONE: {out_mp4} ===")
    return str(out_mp4)


if __name__ == "__main__":
    result = main()
    print(f"FINAL_PATH={result}")