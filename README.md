# Video Creator Pipeline / 视频生成管线

A YAML-driven automated video generation pipeline using Manim animations, edge-tts narration, and MoviePy composition with burned-in Chinese subtitles.
用 YAML 脚本驱动，Manim 动画 + edge-tts 解说 + MoviePy 合成带烧录字幕的中文视频管线。

[English](#english) · [中文](#中文)

---

<!-- EN -->
<h2 id="english">English</h2>

### Overview

This repo is the shared skeleton for generating review/tutorial videos. Each project lives as a separate YAML script + scene subclass set in `scenes/sections.py`.

**Pipeline:**
```
YAML Script → Manim Scenes → TTS (edge-tts) → MoviePy Composition → Final MP4
脚本        → Manim 场景    → 语音    → 合成+字幕       → 成品 MP4
```

### Architecture

```
video_gen/
├── main.py                 # CLI orchestrator (all/render/tts/compose steps)
├── compose_fast.py         # ffmpeg-only composer (MoviePy-free, faster on CPU)
├── config.yaml             # All configuration (colors, fonts, TTS voice, timings)
├── models.py               # Data models (VideoScript, VideoSection, SectionContent)
├── config.py               # Config loader
├── scenes/
│   ├── base.py             # Base scene classes, helpers (zebra stripes, etc.)
│   └── sections.py         # Scene classes + SCENE_MAP (add new projects here)
├── tts/
│   └── generator.py        # edge-tts integration
├── compositor/
│   └── pipeline.py         # MoviePy composition, subtitle generation, burning
├── assets/
│   ├── images/             # Static assets (*_small for scenes, raw originals)
│   ├── audio/narration/    # Generated mp3 files (cached with .txt markers)
│   └── temp/               # Render cache (manim_videos/, videos/sections/)
├── tests/                  # Regression tests for subtitle + visual logic
└── output*/                # Final video output (gitignored)
```

### Installation

```bash
# System deps (macOS) — ffmpeg MUST be from manim_env (system ffmpeg lacks libSvtAv1Enc)
brew install cairo pango pkg-config manim

# Python env (micromamba recommended)
micromamba create -n manim_env python=3.11
micromamba activate manim_env
pip install -r requirements.txt
```

Key dependencies:
- `manim==0.18.0` — Animation engine (cairo backend)
- `moviepy==1.0.3` — Video composition
- `edge-tts==6.1.9` — Microsoft Edge TTS (requires internet)
- `pyyaml` — YAML parsing

### Quick Start

```bash
# Activate environment
export PATH=<manim_env_bin_path>
export PYTHONPATH=$(pwd)
python3 --version   # confirm correct env

# Dry-run (validate script only)
python3 main.py --dry-run

# Full pipeline
python3 main.py --step all

# Incremental steps
python3 main.py --step render   # Render Manim scenes only
python3 main.py --step tts      # Generate TTS audio only (cached)
python3 main.py --step compose  # Compose final video (background!)
```

**⚠️ Critical: Never run compose in the foreground.** ~60 min for a 20k-frame 1080P video on i7 CPU. Use:
```bash
nohup python3 main.py --script <your_script>.yml --step compose > /tmp/vf/compose.log 2>&1 &
echo "PID=$!" && while kill -0 $! 2>/dev/null; do sleep 60; done
grep -E "Subtitles burned|Final video saved" /tmp/vf/compose.log
```

### YAML Script Format

```yaml
sections:
  - title: "【开场】Your Project Title"
    time_range: "0:00 - 0:40"
    content:
      - type: "画面描述"
        text: "Scene visual description"
      - type: "解说词"
        text: "Subtitle display text (preserved as-is)"
        tts_text: "TTS pronunciation text (homophone substitutions, URL dots → 点)"
    skip_subtitles: false
validation:
  total_sections: N
```

**Dual-track `text` / `tts_text`:**
- `text` — displayed in subtitles (preserve correct characters: URLs, version numbers)
- `tts_text` — sent to edge-tts (substitute homophones for pronunciations, replace `.` with 「点」for URLs)

### Adding a New Project

1. Create a YAML script with `sections` list
2. Add scene classes to `scenes/sections.py`
3. Add title→class mappings to `SCENE_MAP`
4. Run `python3 main.py --dry-run` to validate

### Key Workflows

**Cache invalidation (after changing scene code):**
```bash
# Delete BOTH caches or compose reads stale files
rm -f assets/temp/manim_videos/scene_*.mp4 \
      assets/temp/videos/sections/1080p30/*.mp4
python3 main.py --step render
python3 main.py --step compose   # nohup in background
```

**Single scene manual re-render:**
```bash
manim render scenes/sections.py YourSceneName --media_dir assets/temp -q m -r 1920,1080 --fps 30
# manim outputs to assets/temp/videos/videos/sections/1080p30/
# move to canonical location if needed
```

### Hard Constraints

| Rule | Detail |
|---|---|
| Subtitles single-line | Long lines split at punctuation via `_split_for_display`; never truncated |
| Silence < 1.5s | `target_duration` anchored to `_speech_end`, not file duration (edge-tts has ~0.9s tail silence) |
| Scene ≤ narration + 1.0s | Scenes longer than narration create dead silence at tail |
| Bottom 195px safe zone | Scene text must not enter the bottom 195px (subtitle band) |
| No foreground compose | ffmpeg timeout silently truncates mp4; use nohup + `kill -0 PID` polling |
| FFmpeg from manim_env | System ffmpeg lacks `libSvtAv1Enc`; use `_FFMPEG` constant in pipeline.py |
| `*_small` images for scenes | Raw large images cause aliasing; scenes use `*_small` variants |

### Verification

```bash
export FF=<manim_env_ffmpeg_path>
cd /path/to/your/project

# 1) Frame count integrity (prevent truncation)
$FF -v error -i output/final.mp4 -map 0:v -f framemd5 - 2>/dev/null | wc -l
# expect: N+2 lines (= frame count + 2)

# 2) Silence check (all segments < 1.5s)
$FF -i output/final.mp4 -af silencedetect=noise=-45dB:d=0.4 -f null - 2>&1 \
  | grep -E "silence_(start|end)" | sed 's/^.*\] //' | paste - - \
  | awk '{split($0,a,"duration: "); split(a[2],b," "); if(b[1]+0>=1.5) print $0 " <<< OVER"}'

# 3) Subtitle single-line check
python3 -c "
raw=open('output/subtitles.srt').read()
blocks=[b for b in raw.strip().split('\n\n') if b.strip()]
print('cues',len(blocks),
      '| non-single-line',sum(1 for b in blocks if len(b.splitlines())!=3),
      '| max len',max(len(b.splitlines()[2]) for b in blocks))
"
# expect: non-single-line 0, max len <= 30
```

### Visual Style Rules

**Monochrome + single accent color (no rainbow tables):**
- Body text: `#c9d1d9`, accent: `#6cb4ee`, background: `#0d1117`
- Tables: zebra stripes only (`apply_zebra_stripes`, neutral gray, opacity 0.10)
- Charts: best item in accent color, rest in gray (`#8b949e`)
- Pure white `#FFFFFF` only in subtitles

**Layout: single chained `arrange()`, no manual offsets:**
```python
block = VGroup(l1, l2, l3).arrange(DOWN, buff=0.55)
block.scale_to_fit_height(6.2)
block.move_to(ORIGIN).shift(UP * 0.55)
```

---

<!-- ZH -->
<h2 id="中文">中文</h2>

### 概述

本项目是多项目共用的视频生成骨架。每个项目对应一个 YAML 脚本 + `scenes/sections.py` 中的场景类。

### 安装

```bash
# 激活 manim_env（ffmpeg 必须来自 manim_env，系统 ffmpeg 缺 libSvtAv1Enc）
export PATH=<manim_env_bin_path>
export PYTHONPATH=$(pwd)

# 系统依赖
brew install cairo pango pkg-config manim
pip install -r requirements.txt
```

### 核心流程

```
YAML 脚本 → Manim 场景渲染 → edge-tts 生成解说 → MoviePy 拼接 + 烧录字幕 → 成品 MP4
```

### 关键命令

```bash
# 校验脚本（不渲染）
python3 main.py --dry-run

# 全流程
python3 main.py --step all

# 分段运行
python3 main.py --step render   # 只渲染场景
python3 main.py --step tts      # 只生成语音
python3 main.py --step compose  # 只合成（必须后台！）

# 后台合成（重要！前台会被超时截断 mp4）
nohup python3 main.py --script <你的脚本>.yml --step compose > /tmp/vf/compose.log 2>&1 &
echo "PID=$!" && while kill -0 $! 2>/dev/null; do sleep 60; done
```

### 双轨 text / tts_text

| 字段 | 用途 | 示例 |
|---|---|---|
| `text` | 字幕显示原文 | URL、版本号保持原样 |
| `tts_text` | 发给 edge-tts 的读音文本 | 多音字换同音字、URL 里 `.` → 「点」 |

```yaml
- type: "解说词"
  text: "README 只有一行字：project.readthedocs.io"
  tts_text: "README 只有一航字：project 点 readthedocs 点 io"
```

### 新增项目

1. 创建 YAML 脚本（含 `sections` 列表）
2. 在 `scenes/sections.py` 添加场景类
3. 在 `SCENE_MAP` 添加标题→类映射
4. `python3 main.py --dry-run` 校验

### 缓存失效（改场景代码后必做）

```bash
# 两处缓存都要删，否则 compose 读旧文件
rm -f assets/temp/manim_videos/scene_*.mp4 \
      assets/temp/videos/sections/1080p30/*.mp4
python3 main.py --step render
python3 main.py --step compose
```

### 硬性约束速查

| 约束 | 原因 |
|---|---|
| 字幕全部单行 | 超长按标点切多条 cue，禁止截断 |
| 净音 < 1.5s | edge-tts 自带 ~0.9s 尾静音，锚点用 `_speech_end` 而非文件时长 |
| 场景 ≤ 旁白 + 1s | 超出则尾部死静音，需压缩 wait() 重渲 |
| 底部 195px 安全区 | 字幕带区域，场景文字禁止侵入 |
| 禁止前台跑 compose | 工具超时（默认 120s）会静默截断 mp4 |
| ffmpeg 必须来自 manim_env | 系统 ffmpeg 缺 libSvtAv1Enc |
| 图片用 *_small 版 | 大图过采样会导致锯齿变形 |

### 确定性验证

```bash
export FF=<manim_env_ffmpeg_path>
cd /path/to/your/project

# 帧数完整性（防截断）
$FF -v error -i output/final.mp4 -map 0:v -f framemd5 - 2>/dev/null | wc -l
# 期望: 帧数+2 行

# 净音验收（所有 >=1.5s 静音段应为空）
$FF -i output/final.mp4 -af silencedetect=noise=-45dB:d=0.4 -f null - 2>&1 \
  | grep -E "silence_(start|end)" | paste - - \
  | awk '{if(index($0,"duration: ")>0) {split($0,a,"duration: "); split(a[2],b," "); if(b[1]+0>=1.5) print}}'

# 字幕单行检查
python3 -c "
raw=open('output/subtitles.srt').read()
blocks=[b for b in raw.strip().split('\n\n') if b.strip()]
print('cues',len(blocks),
      '| non-single-line',sum(1 for b in blocks if len(b.splitlines())!=3),
      '| max len',max(len(b.splitlines()[2]) for b in blocks))
"
# 期望: non-single-line 0, max len <= 30
```

### 视觉规范

**单色系 + 单一强调色（零容忍彩虹风）：**
- 正文 `#c9d1d9`，强调 `#6cb4ee`，背景 `#0d1117`
- 表格只用斑马纹（中性灰 opacity 0.10），柱状图最佳项用强调色、其余灰阶
- 纯白 `#FFFFFF` 仅允许出现在字幕

**布局：单链式 arrange，禁止手填偏移：**
```python
block = VGroup(l1, l2, l3).arrange(DOWN, buff=0.55)
block.scale_to_fit_height(6.2)     # 内容变多时自动缩放
block.move_to(ORIGIN).shift(UP * 0.55)  # 只允许一个整体偏移
```

### 测试

```bash
python3 -m pytest tests/ -v
```

### License

MIT License / 自由使用与修改
