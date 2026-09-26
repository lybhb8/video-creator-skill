#!/usr/bin/env python3
"""Isolated compose for the Agnes tutorial.

Runs compose_final_video with UNIQUE output_dir/temp_dir so that a concurrent
MacBook pipeline (which shares the default config.yaml paths) cannot clobber
composed_temp.mp4 / subtitles.srt / the final filename mid-run.

Scene videos are still read from the shared canonical dir
(assets/temp/videos/sections/1080p30/), which is read-only for us.
"""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models import VideoScript
from config import load_config
from compositor.pipeline import VideoCompositor
from tts.generator import TTSGenerator

SCRIPT = "/Users/mac/video_gen/agnes_video_script.yml"
NARRATION_DIR = Path("/Users/mac/video_gen/assets/audio/narration")
OUTPUT_DIR = "output_agnes"
TEMP_DIR = "assets/temp_agnes"
FINAL_NAME = "agnes_ai_free_tutorial.mp4"


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("compose_agnes_isolated")

    config = load_config("config.yaml")
    # Isolate every write path from the shared pipeline.
    config.output.output_dir = OUTPUT_DIR
    config.assets.temp_dir = TEMP_DIR
    config.output.final_filename = FINAL_NAME
    Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    script = VideoScript.from_yaml(SCRIPT)
    logger.info(f"Script loaded: {len(script.sections)} sections")

    compositor = VideoCompositor(config, script)
    tts_gen = TTSGenerator(config)

    narration_results = asyncio.run(
        tts_gen.load_existing_narrations(script.sections, NARRATION_DIR)
    )
    logger.info(f"Loaded {len(narration_results)} existing narrations")

    final_path = compositor.compose_final_video(script, narration_results)
    logger.info(f"=== COMPOSE AGNES DONE: {final_path} ===")
    return final_path


if __name__ == "__main__":
    result = main()
    print(f"FINAL_PATH={result}")