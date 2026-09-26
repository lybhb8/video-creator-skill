#!/usr/bin/env python3
"""
Test script to verify the video generation pipeline components.
Run this before full pipeline to catch issues early.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from models import VideoScript
from config import load_config
from tts.generator import TTSGenerator


def test_yaml_parsing():
    """Test YAML parsing and validation."""
    print("=== Test 1: YAML Parsing ===")
    script = VideoScript.from_yaml("/Users/mac/Desktop/video-script-structured.yml")
    
    assert len(script.sections) == 12, f"Expected 12 sections, got {len(script.sections)}"
    assert script.validation.total_sections == 10
    assert script.validation.hierarchical_structure == "valid"
    
    print(f"✓ Parsed {len(script.sections)} sections")
    print(f"✓ Total sections: {script.validation.total_sections}")
    print(f"✓ With visual prompts: {script.validation.sections_with_visual_prompts}")
    print(f"✓ With narration: {script.validation.sections_with_narration}")
    print(f"✓ Estimated duration: {script.get_total_duration():.1f}s")
    
    for i, section in enumerate(script.sections):
        has_narration = bool(section.narration_text.strip())
        print(f"  Section {i}: {section.title[:40]}... (narration: {has_narration})")
    
    return True


def test_config_loading():
    """Test configuration loading."""
    print("\n=== Test 2: Config Loading ===")
    config = load_config("config.yaml")
    
    assert config.output.resolution == [1920, 1080]
    assert config.output.fps == 30
    assert config.manim.background_color == "#0d1117"
    assert config.tts.voice == "zh-CN-YunxiNeural"
    
    print("✓ Config loaded successfully")
    print(f"  Resolution: {config.output.resolution}")
    print(f"  FPS: {config.output.fps}")
    print(f"  TTS Voice: {config.tts.voice}")
    print(f"  Output dir: {config.output.output_dir}")
    
    return True


async def test_tts_generation():
    """Test TTS generation for one section."""
    print("\n=== Test 3: TTS Generation (first section with narration) ===")
    config = load_config()
    script = VideoScript.from_yaml("/Users/mac/Desktop/video-script-structured.yml")
    
    # Find first section with narration
    test_section = None
    for section in script.sections:
        if section.narration_text.strip():
            test_section = section
            break
    
    if not test_section:
        print("⚠ No section with narration found")
        return True
    
    print(f"Testing TTS for: {test_section.title}")
    print(f"Text length: {len(test_section.narration_text)} chars")
    
    tts = TTSGenerator(config)
    output_dir = Path(config.assets.audio_dir) / "test_narration"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "test_narration.mp3"
    result = await tts.generate_narration(test_section.narration_text, str(output_path))
    
    assert Path(result.audio_path).exists(), "Audio file not created"
    assert result.duration > 0, "Duration should be positive"
    assert len(result.timestamps) > 0, "Should have timestamps"
    
    print(f"✓ TTS generated: {result.audio_path}")
    print(f"  Duration: {result.duration:.1f}s")
    print(f"  Timestamps: {len(result.timestamps)} segments")
    
    return True


def test_manim_import():
    """Test Manim imports and scene classes."""
    print("\n=== Test 4: Manim Imports ===")
    
    try:
        from manim import Scene, Text, VGroup, config as manim_config
        print("✓ Manim core imports OK")
    except ImportError as e:
        print(f"✗ Manim import failed: {e}")
        return False
    
    try:
        from scenes.base import BaseScene, TerminalScene, ChartScene
        from scenes.sections import IntroScene, HardwareScene, SCENE_MAP
        print("✓ Scene classes imported OK")
        print(f"  Available scenes: {len(SCENE_MAP)}")
    except ImportError as e:
        print(f"✗ Scene import failed: {e}")
        return False
    
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("VIDEO GENERATION PIPELINE - COMPONENT TESTS")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: YAML parsing
    try:
        test_yaml_parsing()
    except Exception as e:
        print(f"✗ Test 1 failed: {e}")
        all_passed = False
    
    # Test 2: Config loading
    try:
        test_config_loading()
    except Exception as e:
        print(f"✗ Test 2 failed: {e}")
        all_passed = False
    
    # Test 3: Manim imports
    try:
        if not test_manim_import():
            all_passed = False
    except Exception as e:
        print(f"✗ Test 4 failed: {e}")
        all_passed = False
    
    # Test 4: TTS generation (requires network for edge-tts)
    print("\n=== Test 4: TTS Generation (requires network) ===")
    try:
        await test_tts_generation()
    except Exception as e:
        print(f"⚠ Test 3 (TTS) failed: {e}")
        print("  This may be due to network/edge-tts issues")
        # Don't fail overall for TTS network issues
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL CORE TESTS PASSED")
        print("Pipeline ready for full execution!")
    else:
        print("❌ SOME TESTS FAILED")
        print("Fix issues before running full pipeline")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)