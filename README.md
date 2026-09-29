# Video Creator Pipeline / 视频生成管线

A YAML-driven automated video generation pipeline using Manim animations, edge-tts narration, and MoviePy composition with burned-in Chinese subtitles.
用 YAML 脚本驱动，Manim 动画 + edge-tts 解说 + MoviePy 合成带烧录字幕的中文视频管线。

[English](#english) · [中文](#中文)

---

<!-- EN -->
<h2 id="english">English</h2>

### Overview / 概述

This repo contains the shared skeleton for generating review/tutorial videos:

| Project / 项目 | Script / 脚本 | Sections / 章节 | Output / 成片 |
|---|---|---|---|
| MacBook Pro Local AI Benchmark / MacBook 本地 AI 评测 | `video-script-structured.yml` | 10 | `output/macbook_pro_*.mp4` |
| Extruder Principles & Operation / 挤出机原理与操作 | `extruder_video_script.yml` | 8 | `output/extruder_principles_and_operation.mp4` |
| 7900XTX Local AI Review / 7900XTX 本地 AI 测评 | `gpu_benchmark_script.yml` | 12 | `output/7900XTX_Qwen27B_Guide.mp4` |
| Agnes AI Tutorial / Agnes AI 使用教程 | `agnes_video_script.yml` | 9 | `output_agnes/agnes_ai_free_tutorial.mp4` |

**Pipeline / 管线流程:**
```
YAML Script → Manim Scenes → TTS (edge-tts) → MoviePy Composition → Final MP4
脚本        → Manim 场景    → 语音    → 合成+字幕       → 成品 MP4
```

### Architecture / 架构

```
video_gen/
├── main.py                    # CLI orchestrator (all/render/tts/compose steps)
├── compose_fast.py            # ffmpeg-only composer (MoviePy-free, faster on CPU)
├── compose_agnes_isolated.py  # Isolated compose for new projects (separate output dirs)
├── burn_agnes_only.py         # Standalone ASS subtitle burner
├── config.yaml                # All configuration (colors, fonts, TTS voice, timings)
├── models.py                  # Data models (VideoScript, VideoSection, SectionContent)
├── config.py                  # Config loader
├── scenes/
│   ├── base.py                # Base scene classes, helpers (zebra stripes, etc.)
│   └── sections.py            # All scene classes (GPU*, Extruder*, MacBook*) + SCENE_MAP
├── tts/
│   └── generator.py           # edge-tts integration
├── compositor/
│   └── pipeline.py            # MoviePy composition, subtitle generation, burning
├── assets/
│   ├── images/                # Static assets (*_small for scenes, raw originals)
│   ├── audio/narration/       # Generated mp3 files (cached with .txt markers)
│   └── temp/                  # Render cache (manim_videos/, videos/sections/)
├── tests/
│   ├── test_subtitle_fixes.py          # 33 tests for subtitle logic
│   └── test_gpu_visual_unification.py  # 23 tests for GPU visual style
└── output*/                   # Final video output (gitignored)
```

### Installation / 安装

```bash
# System deps (macOS) — ffmpeg MUST be from manim_env (system ffmpeg lacks libSvtAv1Enc)
brew install cairo pango pkg-config manim

# Python env (micromamba recommended)
micromamba create -n manim_env python=3.11
micromamba activate manim_env
pip install -r requirements.txt
```

Key dependencies / 核心依赖:
- `manim==0.18.0` — Animation engine (cairo backend)
- `moviepy==1.0.3` — Video composition
- `edge-tts==6.1.9` — Microsoft Edge TTS (requires internet)
- `pyyaml` — YAML parsing

### Quick Start / 快速开始

```bash
# Activate environment
export PATH=/Users/mac/micromamba/envs/manim_env/bin:$PATH
export PYTHONPATH=/Users/mac/video_gen
python3 --version   # confirm manim_env

# Dry-run (validate script only)
python3 main.py --dry-run

# Full pipeline
python3 main.py --step all

# Incremental steps (debug-friendly)
python3 main.py --step render    # Render Manim scenes only
python3 main.py --step tts       # Generate TTS audio only (cached)
python3 main.py --step compose   # Compose final video (background!)
```

**⚠️ Critical: Never run compose in the foreground.** i7-9750H needs ~60 min for a 20k-frame 1080P video. Use:
```bash
nohup python3 main.py --script gpu_benchmark_script.yml --step compose > /tmp/vf/compose.log 2>&1 &
echo "PID=$!" && while kill -0 $! 2>/dev/null; do sleep 60; done
grep -E "Subtitles burned|Final video saved" /tmp/vf/compose.log
```

### YAML Script Format / YAML 脚本格式

```yaml
sections:
  - title: "【开场】7900XTX 本地 AI 测评"
    time_range: "0:00 - 0:40"
    content:
      - type: "画面描述"
        text: "蓝宝石 NITRO+ WHITE 7900 XT 产品图"
      - type: "解说词"
        text: "一张 AMD RX 7900 XTX，24GB 显存，跑本地大模型是什么体验"
        tts_text: "一张 AMD RX 7900 XTX，24GB 显存，跑本地大模型是甚么体验"
    skip_subtitles: false   # omit or true for title-only scenes
validation:
  total_sections: 12
```

**Dual-track `text` / `tts_text`:**
- `text` — displayed in subtitles (preserve correct characters like URLs: `readthedocs.io`)
- `tts_text` — sent to edge-tts (substitute homophones for pronunciations, replace `.` with 「点」for URLs)

### Key Workflows / 关键工作流

**Cache invalidation (after changing scene code):**
```bash
# Delete BOTH caches or compose reads stale files
rm -f assets/temp/manim_videos/scene_11_*.mp4 \
      assets/temp/videos/sections/1080p30/GPUOutroScene.mp4
python3 main.py --step render
python3 main.py --step compose   # nohup in background
```

**Single scene manual re-render:**
```bash
manim render scenes/sections.py GPUOutroScene --media_dir assets/temp -q m -r 1920,1080 --fps 30
cp assets/temp/videos/videos/sections/1080p30/GPUOutroScene.mp4 \
   assets/temp/videos/sections/1080p30/GPUOutroScene.mp4
```

### Hard Constraints / 硬性约束

| Rule / 规则 | Detail / 说明 |
|---|---|
| Subtitles single-line / 字幕单行 | Long lines split at punctuation via `_split_for_display`; never truncated |
| Silence < 1.5s / 净音 < 1.5s | `target_duration` anchored to `_speech_end`, not file duration (edge-tts has ~0.9s tail silence) |
| Scene ≤ narration + 1.0s / 场景 ≤ 旁白+1s | Scenes longer than narration create dead silence at tail |
| Bottom 195px safe zone / 底部安全区 | Scene text must not enter the bottom 195px (subtitle band) |
| No foreground compose / 禁止前台合成 | ffmpeg timeout silently truncates mp4; use nohup + `kill -0 PID` polling |
| FFmpeg from manim_env / ffmpeg 来源 | System ffmpeg lacks `libSvtAv1Enc`; use `_FFMPEG` constant in pipeline.py |
| `*_small` images for scenes / 小图用于场景 | Raw large images cause aliasing; scenes use `*_small` variants |

### Verification / 验证

```bash
export FF=/Users/mac/micromamba/envs/manim_env/bin/ffmpeg
cd /Users/mac/video_gen

# 1) Frame count integrity (prevent truncation)
$FF -v error -i output/7900XTX_Qwen27B_Guide.mp4 -map 0:v -f framemd5 - 2>/dev/null | wc -l
# expect: 20262 lines (= 20260 frames + 2)

# 2) Silence check (all segments < 1.5s)
$FF -i output/7900XTX_Qwen27B_Guide.mp4 -af silencedetect=noise=-45dB:d=0.4 -f null - 2>&1 \
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

### Baseline / 基准 (frozen 2026-09-26)

**7900XTX成片 `output/7900XTX_Qwen27B_Guide.mp4`:**
- Duration: 675.333s / 20,260 frames / 188,292,897 bytes
- MD5: `8e513119a42031fd1d56d4628e5dd41a`
- Subtitles: 196 cues, all single-line, max 30 chars
- Outro layout: 6 text blocks, spacing 87-88px, top margin 47px, bottom margin 195px

### Visual Style Rules / 视觉规范

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

本项目是多项目共用的视频生成骨架，承载四套视频项目：MacBook 评测、挤出机原理、7900XTX 评测、Agnes AI 教程。

### 安装

```bash
# 激活 manim_env
export PATH=/Users/mac/micromamba/envs/manim_env/bin:$PATH
export PYTHONPATH=/Users/mac/video_gen

# 系统依赖（ffmpeg 必须用 manim_env 里的，系统 ffmpeg 缺 libSvtAv1Enc）
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
nohup python3 main.py --script gpu_benchmark_script.yml --step compose > /tmp/vf/compose.log 2>&1 &
echo "PID=$!" && while kill -0 $! 2>/dev/null; do sleep 60; done
```

### 双轨 text / tts_text

| 字段 | 用途 | 示例 |
|---|---|---|
| `text` | 字幕显示原文 | `readthedocs.io`、版本号 `Sphinx 7.1.2` |
| `tts_text` | 发给 edge-tts 的读音文本 | URL 里 `.` → 「点」、多音字换同音字 |

```yaml
- type: "解说词"
  text: "README 只有一行字：extruder.readthedocs.io"
  tts_text: "README 只有一航字：extruder 点 readthedocs 点 io"
```

### 缓存失效（改场景代码后必做）

```bash
# 两处缓存都要删，否则 compose 读旧文件
rm -f assets/temp/manim_videos/scene_11_*.mp4 \
      assets/temp/videos/sections/1080p30/GPUOutroScene.mp4
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
export FF=/Users/mac/micromamba/envs/manim_env/bin/ffmpeg
cd /Users/mac/video_gen

# 帧数完整性
$FF -v error -i output/7900XTX_Qwen27B_Guide.mp4 -map 0:v -f framemd5 - 2>/dev/null | wc -l
# 期望: 20262 行 (= 20260 帧 + 2)

# 净音验收（所有 >=1.5s 静音段应为空）
$FF -i output/7900XTX_Qwen27B_Guide.mp4 -af silencedetect=noise=-45dB:d=0.4 -f null - 2>&1 \
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

### 冻结基线（2026-09-26）

**7900XTX 成片 `output/7900XTX_Qwen27B_Guide.mp4`:**
- 时长 `675.333s` / 20,260 帧 / 188,292,897 字节
- MD5 `8e513119a42031fd1d56d4628e5dd41a`
- 字幕 196 条，全部单行，最长 30 字
- 结尾布局：6 个文本块间距 87-88px，顶部留白 47px，底部留白 195px

### 测试

```bash
python3 -m pytest tests/ -v
# test_subtitle_fixes.py: 33 项
# test_gpu_visual_unification.py: 23 项
```

### License

MIT License / 自由使用与修改
