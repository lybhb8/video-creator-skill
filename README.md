# AI Benchmark Video Generator

Automated video generation pipeline for the "MacBook Pro 本地运行 AI 大模型评测" video.

## Architecture

```
YAML Script → Manim Scenes → TTS (edge-tts) → MoviePy Composition → Final MP4
```

## Project Structure

```
video_gen/
├── main.py              # Main orchestrator CLI
├── test_pipeline.py     # Component tests
├── config.yaml          # All configuration
├── requirements.txt     # Python dependencies
├── models.py            # Data models (VideoScript, VideoSection, etc.)
├── config.py            # Config loader
├── scenes/
│   ├── __init__.py
│   ├── base.py          # Base scene classes
│   └── sections.py      # Specific scene implementations
├── tts/
│   ├── __init__.py
│   └── generator.py     # edge-tts integration
├── compositor/
│   ├── __init__.py
│   └── pipeline.py      # MoviePy composition
├── assets/
│   ├── fonts/           # Chinese fonts (PingFang SC, etc.)
│   ├── images/          # Static assets
│   ├── audio/           # Generated narration
│   └── temp/            # Temporary files
└── output/              # Final video output
```

## Installation

### System Dependencies

```bash
# macOS
brew install ffmpeg manim

# For manim with cairo backend
brew install cairo pango pkg-config

# Python dependencies
pip install -r requirements.txt
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

Key packages:
- `manim==0.18.0` - Animation engine
- `moviepy==1.0.3` - Video composition
- `edge-tts==6.1.9` - Microsoft Edge TTS
- `pyyaml` - Config parsing

## Usage

### Quick Test (verify setup)

```bash
python test_pipeline.py
```

### Full Pipeline

```bash
# Run complete pipeline
python main.py

# Or with options
python main.py --script /path/to/script.yml --config config.yaml
```

### Step-by-step

```bash
# 1. Only render Manim scenes
python main.py --step render

# 2. Only generate TTS
python main.py --step tts

# 3. Only compose (needs pre-rendered scenes + TTS)
python main.py --step compose
```

### Test Single Section

```bash
# Render section 0 (intro) only
python main.py --step render --section 0
```

### Dry Run (validation only)

```bash
python main.py --dry-run
```

## Configuration

Edit `config.yaml` to customize:

- **Output**: resolution, fps, codec, bitrate
- **Manim**: quality, colors, fonts
- **Timing**: per-section duration estimates
- **TTS**: voice, rate, pitch
- **Subtitles**: font, position, styling
- **Charts**: color palette

## YAML Script Format

The input script (`video-script-structured.yml`) contains:

```yaml
sections:
  - title: "【开场】0:00 - 0:45"
    time_range: "0:00 - 0:45"
    content:
      - type: "画面描述"
        text: "黑屏渐入 → MacBook Pro 产品图..."
      - type: "解说词"
        text: "一台 2019 年的 MacBook Pro..."
    visual_prompts:
      - "MacBook Pro 产品图"
      - "终端界面: ollama list 命令结果"

validation:
  total_sections: 10
  hierarchical_structure: "valid"
  ...
```

Content types:
- `画面描述` - Visual description (triggers TerminalScene, ChartScene, etc.)
- `解说词` - Narration text (used for TTS + subtitles)
- `技术参数表` - Technical specifications table

## Scene Types

| Section Keywords | Scene Class | Visual Output |
|------------------|-------------|---------------|
| 终端, 命令 | `TerminalScene` | Animated terminal with typed commands |
| 图, 排名, 对比 | `ChartScene` | Animated bar charts |
| 表格 | `TableScene` | Animated data tables |
| 默认 | `TextAnimationScene` | Synced text animation |

## Output

Final video: `output/macbook_pro_ai_benchmark.mp4`

- Resolution: 1920x1080 @ 30fps
- Codec: H.264 / AAC
- Subtitles: Embedded Chinese subtitles
- Audio: edge-tts Chinese narration

## Troubleshooting

### Manim not found
```bash
brew install manim
# or
pip install manim
```

### Font issues (Chinese)
Ensure Chinese fonts installed:
```bash
# macOS
brew install --cask font-pingfang-sc
```

### edge-tts network issues
The TTS generator uses Microsoft Edge TTS which requires internet. If it fails:
1. Check network connectivity
2. Try different voice in config.yaml
3. Use cached audio if available

### Memory issues during render
Reduce quality in config.yaml:
```yaml
manim:
  quality: "medium"  # or "low"
```

## License

MIT License - Feel free to use and modify.