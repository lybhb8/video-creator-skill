#!/usr/bin/env python3
"""
Main orchestrator for AI Benchmark Video Generation.
Parses YAML script -> Renders Manim scenes -> Generates TTS -> Composes final video.
"""
import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from models import VideoScript
from config import get_config, load_config
from compositor.pipeline import VideoCompositor


def setup_logging(config):
    """Configure logging."""
    log_file = Path(config.logging.file)
    if not log_file.is_absolute():
        log_file = Path(config.assets.temp_dir) / Path(config.logging.file).name
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


async def main():
    parser = argparse.ArgumentParser(description="Generate AI Benchmark Video from YAML script")
    parser.add_argument(
        '--script', '-s',
        default="/Users/mac/Desktop/video-script-structured.yml",
        help='Path to structured YAML video script'
    )
    parser.add_argument(
        '--config', '-c',
        default="config.yaml",
        help='Path to config YAML'
    )
    parser.add_argument(
        '--step', '-t',
        choices=['all', 'render', 'tts', 'compose'],
        default='all',
        help='Pipeline step to run'
    )
    parser.add_argument(
        '--section', '-n',
        type=int,
        help='Render only specific section index (for testing)'
    )
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Parse and validate only, no rendering'
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    # Load script
    logger.info(f"Loading script from: {args.script}")
    script = VideoScript.from_yaml(args.script)
    
    logger.info(f"Script loaded: {len(script.sections)} sections")
    logger.info(f"Validation: {script.validation}")
    logger.info(f"Estimated duration: {script.get_total_duration():.1f} seconds")
    
    if args.dry_run:
        logger.info("Dry run complete - script validated successfully")
        return 0
    
    # Initialize compositor
    compositor = VideoCompositor(config, script)
    
    try:
        if args.step in ['all', 'render']:
            logger.info("=== Step 1: Rendering Manim Scenes ===")
            if args.section is not None:
                # Render single section
                section = script.sections[args.section]
                logger.info(f"Rendering section {args.section}: {section.title}")
                # TODO: Implement single section render
            else:
                compositor.render_all_scenes(script)
            logger.info("Scene rendering complete")
        
        narration_results = None
        
        if args.step in ['all', 'tts']:
            logger.info("=== Step 2: Generating TTS Narrations ===")
            narration_results = await compositor.generate_all_narrations(script, Path(config.assets.audio_dir) / "narration")
            logger.info("TTS generation complete")
        
        if args.step in ['all', 'compose']:
            logger.info("=== Step 3: Composing Final Video ===")
            # Use narration results from step 2, or load existing TTS files if skipped
            if narration_results is None:
                from tts.generator import TTSGenerator
                tts_gen = TTSGenerator(config)
                narration_results = await tts_gen.load_existing_narrations(
                    script.sections, 
                    Path(config.assets.audio_dir) / "narration"
                )
            final_path = compositor.compose_final_video(script, narration_results)
            logger.info(f"Final video: {final_path}")
        
        logger.info("=== Pipeline completed successfully! ===")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)