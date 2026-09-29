---
name: video-creator
description: 用 YAML 脚本 + Manim + edge-tts + MoviePy 生成带字幕的中文解说视频。用户要求"生成视频 / 制作视频 / 创建视频 / 渲染视频 / video creator / 把脚本做成视频 / 生成教学视频 / 生成评测视频"时使用。工作流: 解析结构化 YAML 视频脚本(支持 text/tts_text 双轨) → 渲染 Manim 动画场景 → edge-tts 生成解说 → MoviePy 拼接合成带字幕成品 MP4。硬性约束: 字幕全部单行(长句按标点切分为多条 cue，禁止截断)、净音区段<1.5s、防前台超时截断、场景文字不得侵入底部字幕带。参考实现位于 /Users/mac/video_gen(承载 MacBook 评测、挤出机、7900XTX 评测、Agnes AI 教程四套项目)。
version: 1.3.0
author: opencode user
license: MIT
platforms: [macos]
---

# Video Creator — YAML 脚本驱动的视频生成管线

把结构化 YAML 脚本自动变成带中文解说和字幕的 1080P 视频。参考实现:`/Users/mac/video_gen`。该目录是**多项目共用**骨架,`scenes/sections.py` 里三套场景类共存。

| 项目 | YAML 脚本 | 场景数 | 成片 |
|---|---|---|---|
| MacBook Pro 本地 AI 评测 | `video-script-structured.yml` | 10 | `output/macbook_pro_*.mp4` |
| 挤出机原理与操作 | `extruder_video_script.yml` | 8 | `output/extruder_principles_and_operation.mp4` |
| 7900XTX 本地 AI 测评 | `gpu_benchmark_script.yml` | 12 | `output/7900XTX_Qwen27B_Guide.mp4` |
| Agnes AI 使用教程 | `agnes_video_script.yml` | 9(规划中) | `output_agnes/agnes_ai_free_tutorial.mp4` |

## 1. 触发与定位

- 用户要求"生成/制作/创建视频"或要把评测/评测报告/脚本转成视频 → 用本 skill。
- 若项目目录已有 `video_gen/` 风格结构(含 `main.py`、`scenes/sections.py`、`compositor/pipeline.py`、`config.yaml`)→ 直接在现成项目上工作,不要另起炉灶。
- 若没有 → 参考 `/Users/mac/video_gen` 复制骨架,或用该项目的引用目录。

## 2. 必须遵守的环境约束

- **Python 环境**: 激活 `manim_env`(micromamba),否则 manim 0.18.0 / MoviePy 无法导入:
  ```bash
  export PATH=/Users/mac/micromamba/envs/manim_env/bin:$PATH
  export PYTHONPATH=/Users/mac/video_gen   # 项目根
  python3 --version                          # 确认在 manim_env 中
  ```
- **ffmpeg 必须用 manim_env 里的**: 系统 ffmpeg 缺 `libSvtAv1Enc`,转码会失败。`compositor/pipeline.py` 顶部已固定 `_FFMPEG = "/Users/mac/micromamba/envs/manim_env/bin/ffmpeg"`,**所有 `_ffmpeg(...)` 调用走这个常量,不要用 `FFMPEG_BINARY` 或 PATH 里的 ffmpeg**。手动验证时也带上完整路径。
- **只能从项目根目录运行** `main.py`(内部用相对路径 + `cwd=project_root`)。
- 本机为 **Intel i7-9750H 纯 CPU**: 渲染单场景 40-90s,渲染 12 场景约 5-15 分钟;合成 1080P@30fps / 20260 帧实测 **~60 分钟**(单核 `write_videofile`,不要试图改 `threads` 提速)。
- **合成绝不可用 bash 工具前台跑**: 工具超时(默认 120s/可设更长但一旦超时)会杀掉进程,mp4 会**静默截断**——moov 元数据声称完整时长,但 mdat 只有前段。断点特征: MoviePy 报 `last valid frame` seek warning、后续按 t≥100s 抽帧无输出、framemd5 行数远小于预期。**必须 nohup 后台 + `kill -0 PID` 轮询日志**。
- **中文字体**: `STHeiti Medium.ttc`(manim 渲染)与 MoviePy 字幕共用;缺字体时 `Text` 会渲染成方块。
- **不要用一次性 python 片段调用 `create_subtitles` 做实验**: 它直接写 `output/subtitles.srt`,会覆盖真实产物(踩过: 验证单行逻辑时把 93 条字幕冲成 2 条测试数据)。写验证请用 pytest + `tmp_path` 并把 `compositor.final_output_dir` 指向临时目录。

## 3. 核心流程(三步)

### Step 1 — 准备 YAML 视频脚本

脚本必须含 `sections` 列表,每节至少含 `title` 与 `content`(解说词 `type: 解说词`、画面描述 `type: 画面描述`)。节标题必须命中 `SCENE_MAP`(见第 4 节)。

**text / tts_text 双轨(朗读与字幕分离)**: 解说词可用两块——
- `text`: 字幕与时间戳用的**显示原文**,生僻字保持正确写法(如「一**行**字」、URL 用真点号 `extruder-principles-and-operation.readthedocs.io`、版本号 `Sphinx 7.1.2`、`readthedocs.yaml`、`Ubuntu 22.04`)。
- `tts_text`: 发给 edge-tts 的**读音文本**,可替换:
  - 多音字读错 → 换同音字(「行 háng」→「**航**」)。
  - URL 里 `.` 会被读成英文 dot → 换成「**点**」(「...operation 点 readthedocs 点 io」)。
  - 字幕始终显示 `text`,不显示 `tts_text`。

```yaml
sections:
  - title: "【项目起源】2023年9月"
    content:
      - type: "解说词"
        text: "README 只有一行字：这是 Stevens 和 Covas 合著的那本书。"
        tts_text: "README 只有一航字：这是 Stevens 和 Covas 合著的那本书。"
```

校验脚本:`python3 main.py --dry-run`(只解析验证,不渲染)。

### Step 2 — 渲染 Manim 场景 + 生成 TTS

```bash
cd /Users/mac/video_gen
python3 main.py --step all   # 全流程: render → tts → compose
```

分段运行(便于调试):
```bash
python3 main.py --step render        # 只渲染场景
python3 main.py --step tts           # 只生成解说(复用已有 mp3 + marker 校验)
python3 main.py --step compose       # 只合成(需要场景+音频已就绪)
```

- **增量跳过**: `assets/audio/narration/*.mp3` 已存在且**sidecar marker(.txt)内容 == 当前 tts_text** 则跳过 TTS。渲染跳过靠 `assets/temp/manim_videos/scene_XX_*.mp4` 存在性。
- **改场景代码后必须同时删两处缓存**(只删一处会导致 compose 读到旧文件,表现为"改了没生效"——踩过两次):
  ```bash
  rm -f "assets/temp/manim_videos/scene_11_【结尾】总结.mp4" \
        assets/temp/videos/sections/1080p30/GPUOutroScene.mp4
  ```
  然后 `--step render` 会只重渲这一节,再 `--step compose`。
- 全量重渲:`rm -f assets/temp/manim_videos/scene_*.mp4 assets/temp/videos/sections/1080p30/*.mp4`
- **单场景手动重渲**(compose 从 `assets/temp/videos/sections/1080p30/<SceneClassName>.mp4` 读取,manim 原生输出会多套一层 `videos/`,需手动移动):
  ```bash
  manim render scenes/sections.py GPUOutroScene --media_dir assets/temp -q m -r 1920,1080 --fps 30
  cp assets/temp/videos/videos/sections/1080p30/GPUOutroScene.mp4 \
     assets/temp/videos/sections/1080p30/GPUOutroScene.mp4
  ```
  `--media_dir assets/temp`(不是 `assets/temp/videos`)才能让输出落在预期层级。

### Step 3 — 合成(硬性约束: 净音 < 1.5s)

**净音区段(纯静音)时长必须 < 1.5s**——合成逻辑已内置(`compositor/pipeline.py`):

```
speech_end = _speech_end(narration.audio_path)   # ffmpeg silencedetect 检测真实语音结束点
target_duration = max(min(clip.duration, speech_end + 1.0), speech_end)
```

**为什么锚点是语音结束点而不是文件时长**: edge-tts 的 mp3 **自带 ~0.87-0.90s 尾部静音**,`narration.duration` 是文件时长而非语音时长。若按 `narration.duration + 1.0` 封顶,实际静音 = 文件尾静音(0.87) + 1.0 + 下段前置静音(≈0.2) ≈ 2.1s,静音检测会报超标。

配套另一条铁律: **场景视频时长 ≤ 旁白时长 + 1.0s**。场景比旁白长时,尾部全是死静音(实测开场40s/旁白34.3s → 尾静音5.7s)。两种修法:
- 合成侧封顶(`上述 target_duration` 逻辑)——安全前提是**场景末尾动画在裁剪点之前已播完**。
- 若最后动画出现在旁白结束之后(如工具链场景 step3 在 73s 才出现、旁白 68.7s 就结束),必须**压缩场景内 wait()** 让动画提前,再重渲染该场景——不能只靠裁剪,否则动画被剪掉。

## 4. 场景类与 `SCENE_MAP`

`scenes/sections.py` 定义场景类,`SCENE_MAP` 把节标题映射到类。**节标题必须命中 map** 否则 `render_all_scenes` 跳过该节(仅 warning)。

**节标题解析必须走"精确优先 + 最长子串"**(`VideoCompositor._resolve_scene_class`),render / collect / compose 三处共用同一个 resolver。踩过的坑: 用"首个子串匹配"时,GPU 项目的 `【硬件环境】平台配置` 会被 MacBook 项目的 `HardwareScene` 抢走(两者都含"硬件环境"),整节渲染成错误的 8×2 MacBook 参数表。规则:
1. 先找**完全相等**的 key;
2. 没有则取**最长**的子串匹配 key;
3. 仍无命中 → warning 跳过。
`【开场】`/`【结尾】` 是多项目共抢的短 key,新项目优先用独占长前缀(如 `【开场】7900XTX 本地 AI 测评`、`【结尾】总结`)。

**MacBook 评测项目**(`video-script-structured.yml`):

| SCENE_MAP key | 场景类 | 呈现内容 |
|---|---|---|
| `MacBook Pro 本地运行AI大模型评测` | `IntroScene` | 标题 + 副标题 + 终端动画(独占 key) |
| `【硬件环境】` | `HardwareScene` | 8×2 硬件参数表(有斑马纹) |
| `【测试题目介绍】` | `QuestionsScene` | 5 道考题卡片,3×2 网格 |
| `【参测模型一览】` | `ModelsScene` | 10×5 模型表格(有斑马纹) |
| `【速度测试结果】` | `SpeedResultsScene` | 耗时条形图 + 洞察文本 |
| `【准确率对比】` | `AccuracyScene` | 6×10 准确率表(有斑马纹) + 迷你条形图 |
| `【重点模型：Ministral 3 3B】` | `Ministral3BScene` | 亮点卡片(左3+右2双列) + 终端演示 |
| `【Ministral 3 3B vs 8B vs 8B 对比】` | `ComparisonScene` | 11×5 三方对比表(有斑马纹) |
| `【综合排名与选择建议】` | `RankingScene` | 6 模型 3×2 网格卡 + 推荐框 |
| `【技术说明】` | `TechSpecsScene` | 7×2 技术参数表(有斑马纹) |

**挤出机项目**(`extruder_video_script.yml`):

| SCENE_MAP key | 场景类 | 呈现内容 |
|---|---|---|
| `【开场】` | `ExtruderIntroScene` | 标题 + 挤出机产品图 + 工具应用 + 关键问题(34.4s) |
| `【项目起源】` | `ExtruderOriginScene` | 2023年9月 bobolin 建仓,README 一句话(21.0s) |
| `【翻译工具链】` | `ExtruderToolsScene` | MinerU + DeepL 双列 + PDF/API 三步(67.9s) |
| `【翻译历程时间线】` | `ExtruderTimelineScene` | 2023.9→2026.9 六节点时间线 + 虚线(52.4s) |
| `【技术栈】` | `ExtruderTechStackScene` | Sphinx/MyST/rtd-theme/RTD + 构建环境(39.9s) |
| `【校译】` | `ExtruderProofreadingScene` | 校译难点多项 + 结论 + 电镜图(38.0s) |
| `【访问方式】` | `ExtruderAccessScene` | 浏览器窗口 mockup(三色灯+URL)+ 免费阅读(23.0s) |
| `【结尾】` | `ExtruderOutroScene` | 开源精神总结(28.1s) |

**7900XTX 项目**(`gpu_benchmark_script.yml`,key 全部用 GPU 前缀避免串场):

| SCENE_MAP key | 场景类 | 呈现内容 |
|---|---|---|
| `【开场】7900XTX 本地 AI 测评` | `GPUOpenScene` | 官方蓝宝石产品抠图 + 关键结论卡片(分阶段淡入) |
| `【硬件环境】平台配置` | `GPUHardwareScene` | 平台参数表 |
| `【BIOS设置】ReBAR等关键项` | `GPUBIOSScene` | BIOS 开关卡片组 |
| `【环境准备】安装与下载` | `GPUEnvScene` | 终端命令块(≤4 条) |
| `【方案总览】五路对比` | `GPUSolutionsScene` | 五路方案对比表 |
| `【速度结果】Benchmark` | `GPUSpeedScene` | Qwen3.6/3.8 双柱状图(最佳项高亮) |
| `【架构分析】3.8 vs 3.6` | `GPUArchScene` | 架构差异对照 |
| `【量化选择】版本决策` | `GPUQuantScene` | 量化方案对比表 |
| `【VRAM预算】显存够用吗` | `GPUVRAMScene` | 双表并列(各自带模型标题) |
| `【选择建议】按场景选型` | `GPURankingScene` | 场景→方案映射表 |
| `【常见问题】故障排查` | `GPUBackupScene` | 故障卡片组 |
| `【结尾】总结` | `GPUOutroScene` | 四行总结 + 知乎链接卡片 |

## 5. 视觉规范(沉淀自实测,务必遵守)

### 字号(1080P 下)
- `create_title(...)` 默认 `scale=0.72`,**不要超过**;Intro 用了 `0.85`。
- `create_subtitle(...)` 默认 `scale=0.45`。
- 表格文字 `font_size` 基准: 13-18。
- 正文/卡片文字: 14-19 区间,insight 行 16。
- 烧录字幕 `subtitle.font_size=40`(已在 config,勿改回 48——实测 48 偏大)。

### 单色系 + 单一强调色(GPU/评测类表格视频)
用户对"表格和内容颜色太亮""大花脸"零容忍。统一收敛为 **灰白正文 + 单一蓝色强调**:
- 正文 `manim.text_color = #c9d1d9`,强调 `manim.accent_color = #6cb4ee`,背景 `#0d1117`。
- 表格**取消彩虹行色**,只用 `apply_zebra_stripes`(中性灰, opacity 0.10)。
- 柱状图: 最佳项用强调色,其余统一灰阶(`#8b949e` 系),不要给每根柱子上不同色相。
- 卡片统一 `stroke_color=accent_color` + 中性文字;`success/warning/error` 只用于语义标记,不做装饰。
- 验收: 抽帧统计"非字幕区域的纯白像素数",应为 0(字幕是唯一允许纯白 `#FFFFFF` 的元素)。

### 字幕安全区:场景文字禁止侵入底部
烧录字幕占据底部约 195px(1080P)。**场景内任何文字/卡片都不得进入底部 195px**:
- 禁止用 `to_edge(DOWN, ...)` 放正文、说明、链接、告别语。
- 底部留白必须用几何校验确认(见第 7 节),而不是"看起来够"。

### 布局必须用单链式排版,禁止手填偏移
"文字叠在一起"反复出现的根因是**每个元素各自 `shift(UP*/DOWN* x)`**——数值一动就重叠。正确做法是让布局算位置:
```python
block = VGroup(line1, line2, line3, line4).arrange(DOWN, buff=0.55, aligned_edge=ORIGIN)
everything = VGroup(block, closing, zhihu_group).arrange(DOWN, buff=0.55)
everything.scale_to_fit_height(6.2)          # 高度守卫,防顶天立地
everything.move_to(ORIGIN).shift(UP * 0.55) # 只允许一个整体偏移
```
- `buff` 换算: 1080P 下 `buff=0.55` ≈ 48px,`buff=1.0` ≈ 87px。要"明显分开"用 `0.55` 以上。
- `scale_to_fit_height` 是必须的守卫:内容变多时自动缩放,不会顶出画面。
- 实测基线: 6 个文本块间距均匀 87-88px,顶部留白 47px,底部留白 195px(正好等于字幕带)。

### 图片必须用 *_small 缩略版
**大图放进 1080P 场景会被过采样/拉伸变形**(判据: 边缘锯齿 + 比例失真)。参考项目中每张原始图都有配对小图:
```
assets/images/extruder/compuplast_barrier_screw.png        # 原始大图
assets/images/extruder/compuplast_barrier_screw_small.png  # 场景实际使用
```
场景统一 `scale_to_fit_width(...)` 引用 `_small` 版。加新图必须同时准备小图并检查变形。

**产品图必须与评测对象一致,不一致要显式标注**:GPU 视频开场用蓝宝石官网 NITRO+ WHITE **7900 XT**(20GB)产品图,但评测对象是 7900 **XTX**(24GB)。必须加字幕/图注 `外观参考:蓝宝石 NITRO+ WHITE 7900 XT`,不能默认读者会忽略型号差异。

### 表格行染色(斑马纹/行色/语义色)
`scenes/base.py` 提供两个行染色 helper,均可选:
- `apply_zebra_stripes(table, n_rows, n_cols, start_row=2, step=2, color=#8b949e, opacity=0.10)`: 从数据行 1(第 0 行为表头)起**隔行**整行填充。
- `apply_row_colors(table, n_rows, n_cols, start_row=2, ...)`: 每行一个 chart 调色板色相,`opacity=0.08`(不做字号缩放)。**彩虹风,新视频不要用**。

**顺序铁律(helper 与手动 set_fill 通用)**: 行底色**在前**,✅/❌/⚠️ 语义状态色与列高亮**在后**,否则语义色会被底色覆盖或底色看不见。要加斑马纹就先调 helper 再上语义色。

### 场景时长与旁白同步(净音前置要求)
- **场景动画必须 ≤ 旁白时长**。渲染后必须对账: `ffmpeg -i scene.mp4` 的 Duration vs 旁白 mp3 时长。
- 场景 < 旁白 → 合成自动冻结尾帧补齐(会产生大量 `last valid frame` warning,正常);场景 > 旁白 → 死静音,需压缩 wait() + 重渲染。
- 压缩 wait 时**优先缩中段留白**,保证最后动画仍在旁白结束前完整出现。

### 防文字重叠(元素多时用网格)
- 卡片/列表超过 4-5 个元素时**必须**用网格而非纵向堆叠:
  - 5 张卡 → `arrange_in_grid(rows=3, cols=2, buff=(0.35, 0.8))` 居中偏下。
  - 6 项 → `arrange_in_grid(rows=3, cols=2, buff=(0.45, 1.2))` 居中偏上,底部留推荐框。
  - 不对称布局 → 左右两组分别 `shift(LEFT/RIGHT * 3.2)`。
- 多元素同屏出现会重叠(开场图 + 关键结论 + 卡片同时显示)→ 改**分阶段淡入**,一次只显示一组。
- 图表标签容易漏:创建了 `names36/names38` 之类变量但**忘了 `add()` / 忘了 `self.play()`**,画面上就缺标签。写完图表检查每个 Text 是否都进了 scene。

## 6. 字幕规范(硬性: 全部单行)

**用户明确要求: 每条字幕必须是一行,不允许折行。**

### 规则
1. `create_subtitles` 写出的每条 cue 恰好 3 行:`序号` / `时间` / **一行文本**。
2. 超过 `subtitles.max_chars_per_line`(当前 30)**不许截断**——必须按标点切成**多条 cue**,按字数比例瓜分原时间段。
3. 切分后所有 cue 拼起来必须与原文**完全一致**(不丢字)。
4. 首条起点 = 原 cue 起点,末条终点 = 原 cue 终点。

### 实现(已落地 `VideoCompositor._split_for_display`)
```
_flatten_for_display  换行符: 中文之间直接合并, 英文之间保留空格 ("Hello\nWorld" -> "Hello World")
_hard_split           仅当单句无任何标点且超长时, 在英文单词边界兜底切开
_split_for_display    优先按 ，、。！？；：,.!?;: 切; 贪心装箱保证每段 <= max_chars
create_subtitles      按 len(segment)/总字数 比例分配时间, 末条强制对齐原 end
```

效果对比(7900XTX 成片):

| 项 | 截断式(错) | 标点切分式(对) |
|---|---|---|
| 字幕条数 | 93 | 196 |
| 多行字幕 | 64 条 | 0 条 |
| 最长一行 | 30 字(句子腰斩) | 30 字(完整句) |
| 文本丢失 | 有 | 无 |

切分实例:
```
一张 AMD RX 7900 XTX，24GB 显存，   |  跑本地大模型是什么体验
这是 AMD 2022 年底推出的 RDNA3 架构旗舰卡，  |  96 个计算单元，6144 个流处理器，
```

### 与 `_split_sentences` 的区别(勿混淆)
- `_split_sentences`(TTS 时间戳切分):断句符**必须**是 `[。！？!?\n]+`,**不能含 `.`**——否则 `readthedocs.yaml`、`Sphinx 7.1.2` 会被切断。
- `_split_for_display`(字幕显示切分):断句符**含** `.` 和 `,`(显示层要适应中英混排),因为它同时承担"折行保护"职责,不含 `.` 会让长英文句超 30 字。

### 字幕时间轴
- 时间戳来自 edge-tts `WordBoundary`;`_vad_speech_segments` 必须按**静音的补集**求语音区间,不能把尾部静音当语音(否则最后一条字幕会拖进静音区)。踩过:`_vad_speech_segments` 曾追加 `(last_end, file_dur)`,导致"音频结束了字幕还在"。
- 章节配对用 `_pair_narrations`,**数量不匹配直接 `RuntimeError`**;不要用 `zip(sections, narrations)`(会静默截断尾部无旁白的章节,造成后面字幕整体错位)。
- `section.visual_entries`(画面描述)**绝不能进字幕流**,否则画面文案会混进字幕出现"排列无序"。

## 7. 确定性验证(合成后必做)

本机视觉模型不可用(visual-engineering 未配置、multimodal-looker 无模型、主模型无图像输入)。全部用**确定性命令**验收,不靠"看截图":

```bash
export PATH=/Users/mac/micromamba/envs/manim_env/bin:$PATH
export FF=/Users/mac/micromamba/envs/manim_env/bin/ffmpeg
cd /Users/mac/video_gen

# 1) 完整性(防截断): framemd5 行数 = 帧数 + 2 / 截断文件行数会远小于预期
$FF -v error -i output/7900XTX_Qwen27B_Guide.mp4 -map 0:v -f framemd5 - 2>/dev/null | wc -l
#    期望: 675.33s / 20260 帧 -> 20262 行

# 2) 净音验收(硬性): 所有 >=1.5s 静音段应为空
$FF -i output/7900XTX_Qwen27B_Guide.mp4 -af silencedetect=noise=-45dB:d=0.4 -f null - 2>&1 \
  | grep -E "silence_(start|end)" | sed 's/^.*\] //' | paste - - \
  | awk '{split($0,a,"duration: "); split(a[2],b," "); if(b[1]+0>=1.5) print $0 " <<< OVER 1.5s"}'

# 3) 字幕单行 + 无丢字(硬性)
python3 -c "
raw=open('output/subtitles.srt').read()
blocks=[b for b in raw.strip().split('\n\n') if b.strip()]
print('cues',len(blocks),
      '| non-single-line',sum(1 for b in blocks if len(b.splitlines())!=3),
      '| max len',max(len(b.splitlines()[2]) for b in blocks))
"
#    期望: non-single-line 0, max len <= 30

# 4) 帧内容抽检: 确认非纯黑/纯空
for t in 5 70 300 480 660; do
  $FF -y -v error -ss $t -i output/7900XTX_Qwen27B_Guide.mp4 -frames:v 1 /tmp/f_$t.png
  python3 -c "from PIL import Image; im=Image.open('/tmp/f_$t.png').convert('RGB'); print('t=$ss unique=%d' % len(set(im.getdata())))"
done

# 5) 字幕文本正确性: URL/点号/版本号未被 . 切断
grep -c "readthedocs.yaml\|zhuanlan.zhihu.com" output/subtitles.srt   # >0
grep -c "点\|航" output/subtitles.srt                                  # 0(仅 tts_text 发音词不应出现)
```

### 几何布局校验(替代肉眼看图)
"文字叠在一起"必须用数值验证,不能只看截图。用背景色做掩膜,切出文本带,断言间距与边距:

```bash
$FF -y -ss 19 -i assets/temp/videos/sections/1080p30/GPUOutroScene.mp4 -frames:v 1 -update 1 /tmp/chk.png
python3 - <<'PY'
import numpy as np; from PIL import Image
im = Image.open('/tmp/chk.png').convert('RGB'); a = np.asarray(im)
mask = (np.abs(a.astype(int) - np.array([0x0d,0x11,0x17])).sum(axis=2) > 40)
filled = mask.any(axis=1); bands=[]; start=None
for i,v in enumerate(filled):
    if v and start is None: start=i
    if not v and start is not None: bands.append((start,i-1)); start=None
if start is not None: bands.append((start,len(filled)-1))
merged=[]
for b in bands:
    if merged and b[0]-merged[-1][1] <= 12: merged[-1]=(merged[-1][0],b[1])
    else: merged.append(list(b) if False else (b[0],b[1]))
print('top margin', merged[0][0], '| bottom margin', im.size[1]-merged[-1][1])
for i,(s,e) in enumerate(merged):
    gap = s-(merged[i-1][1] if i else 0)
    print(f'band{i+1} y{s}-{e} gap_above={gap}', '<<< OVERLAP' if i and gap<=0 else '')
PY
```
判据: 顶部留白 ≥ 40px、底部留白 ≥ 195px(字幕带)、相邻 band 间距 > 0(间距均匀最好)。

## 8. 常见故障与排查

| 症状 | 原因 / 处理 |
|---|---|
| **字幕折行/一大坨** | 走了折行逻辑。必须单行:换行符 flatten + 标点切分成多条 cue。见第 6 节 |
| **字幕在句中被腰斩**(`本次测试覆盖 Qwen3.6 和 Qwe`) | 硬截断。改按标点切分,禁止 `text[:max_chars]` |
| **音频结束了字幕还在** | `_vad_speech_segments` 把尾部静音当语音。改为"静音补集"求语音区间 |
| **字幕时间整体错位/排列无序** | ① `zip` 截断了章节配对 → 用 `_pair_narrations`;② `visual_entries` 混进字幕流;③ SRT→ASS 毫秒换算错 |
| **ASS 时间戳放大 10 倍** | `_srt_to_ass` 曾写 `{ms:02d}0`,042ms 变成 `.420`(4.2s)。必须 `cs=round((t-int(t))*100)` 并处理进位 |
| **渲染的是别的项目的场景** | 标题解析用"首个子串"命中了共抢 key。改"精确优先 + 最长子串" |
| **改了场景代码但成片没变** | 只删了 `manim_videos/scene_XX_*.mp4` 没删 `videos/sections/1080p30/<Class>.mp4`,compose 读了旧文件 |
| **字幕 srt 变成 2 条测试数据** | 一次性 python 片段调 `create_subtitles` 覆盖了产物。验证走 pytest + `tmp_path` |
| `No scene class for section` | 节标题不匹配 SCENE_MAP key;调整标题或补 map |
| **compose 后 framemd5 行数远小于预期** | **前台跑的 compose 被超时杀进程,mp4 静默截断**;nohup 后台重跑 |
| **ffmpeg 报 libSvtAv1Enc / 编码器缺失** | 用了系统 ffmpeg;改用 manim_env 里的 `_FFMPEG` |
| **静音检测 max_silence >= 1.5s** | ① `target_duration` 封顶锚点用了文件时长(含 edge-tts 尾静音)而非 `_speech_end`;② 场景时长 > 旁白+1.0s 且合成未裁剪;③ 末动画晚于旁白结束只能重渲,不能裁 |
| **场景文字叠在一起** | 手填 `shift(UP*/DOWN* x)` 造成重叠。改单链式 `arrange` + `scale_to_fit_height` 守卫,见第 5 节 |
| **正文顶天立地** | 内容变多撑破画面。必须 `scale_to_fit_height` + 只保留一个整体偏移 |
| **底部说明文字被字幕压住** | 用了 `to_edge(DOWN)`。场景文字禁止进入底部 195px |
| **字幕里 URL/版本号被断开一行** | `_split_sentences` 正则含 `.`;必须 `[。！？!?\n]+` |
| 朗读多音字错误 | `tts_text` 换同音字(行行→航);改后 marker 不一致自动重生,勿手动删 mp3 |
| 朗读 URL 出英文 "dot" | `tts_text` 里 `.` 换「点」;字幕仍用 `text` 里的真点号 |
| 图片变形/边缘锯齿 | 用了原始大图;改用 `*_small` 版 + `scale_to_fit_width` |
| manim 找不到模块 | 未设 `PYTHONPATH`,或不在 `manim_env` 中跑 |
| 中文显示为方块 | 字体缺失;确认 `config.manim.font` 指向已装字体(STHeiti Medium.ttc) |
| `Using the last valid frame instead` warning | 场景时长 < 解说词时长,尾部冻结帧补齐;正常现象,非错误(前提: 帧数完整性通过) |
| 渲染超时 900s | 单场景超时;降 `manim.quality` 或拆分场景 |
| 内存不足 | 降 quality;或先 `--step render` 再 `--step compose` 分开跑 |
| 合成极慢 | i7 纯 CPU 正常(20260 帧 ~60min);用 nohup 后台 + tail 日志轮询,勿前台跑 |

## 9. 辅助脚本与替代合成路径

### `compose_fast.py` — ffmpeg 直连合成(MoviePy 不可用时)
纯 ffmpeg 拼接,跳过 MoviePy 的 `write_videofile`(后者在 i7 上极慢且易超时)。
用法:
```bash
python3 compose_fast.py   # 默认读 gpu_benchmark_script.yml,输出到 output/
```
内部流程: ① 加载已有 mp3  narrations → ② 从 `assets/temp/videos/sections/1080p30/*.mp4` 找场景 → ③ ffmpeg concat 拼接视频 + 音频 → ④ ffmpeg ass filter 烧录字幕。字幕切分仍走 `_split_for_display` 逻辑(单行、标点切分),时间戳基于 char-ratio 估算(精度略低于 edge-tts WordBoundary,但足够用)。

### `compose_agnes_isolated.py` — 独立输出目录的合成器
用于 Agnes AI 教程等**新项目**,避免与 MacBook/7900XTX 共享 `output/` 和 `assets/temp/` 路径。将 `output_dir` / `temp_dir` 隔离到 `output_agnes/` / `assets/temp_agnes/`,场景视频仍从共享 canonical 路径读取(只读)。

### `burn_agnes_only.py` — 仅在已有 temp mp4 时烧字幕
先由 `compose_agnes_isolated.py` 生成 `assets/temp_agnes/composed_temp.mp4` + `output_agnes/subtitles.srt`,再用此脚本单独执行 `_srt_to_ass` + `_burn_ass_to_file`。

### YAML `skip_subtitles` 字段
`VideoSection.skip_subtitles`(bool):设为 `true` 时该节不生成字幕(适用于纯图或自带字幕的场景)。

## 10. 工作流速查

```bash
# 1. 准备/修改 YAML 脚本(含 text/tts_text 双轨)
# 2. 校验
export PATH=/Users/mac/micromamba/envs/manim_env/bin:$PATH
cd /Users/mac/video_gen
python3 main.py --dry-run
# 3. (改过场景代码才需要)同时删两处缓存;只改一个场景见 Step 2
rm -f "assets/temp/manim_videos/scene_11_【结尾】总结.mp4" \
      assets/temp/videos/sections/1080p30/GPUOutroScene.mp4
python3 main.py --step render
# 4. 后台跑合成(勿前台!)
nohup python3 main.py --script gpu_benchmark_script.yml --step compose > /tmp/vf/compose.log 2>&1 &
echo "PID=$!" && while kill -0 $! 2>/dev/null; do sleep 60; done
grep -E "Subtitles burned|Final video saved" /tmp/vf/compose.log
# 5. 确定性验证(第 7 节): framemd5 / silencedetect / 字幕单行 / 抽帧
# 6. 几何校验(场景改过时): 文本带间距 + 上下边距,见第 7 节脚本
```

## 11. 已冻结基线(2026-09-26)

以下为验收通过的稳定基线,改动前先备份,改动后按第 7 节全量验证:

**7900XTX 成片** `output/7900XTX_Qwen27B_Guide.mp4`
- 时长 `675.333s` / 20,260 帧 / 188,292,897 字节
- MD5 `8e513119a42031fd1d56d4628e5dd41a`
- 字幕 196 条,全部单行,最长 30 字
- 结尾布局: 6 个文本块间距 87-88px,顶部留白 47px,底部留白 195px

**关键文件**
- `gpu_benchmark_script.yml` — 12 节脚本(全部 GPU 前缀 key)
- `config.yaml` — `manim.text_color #c9d1d9` / `accent_color #6cb4ee` / `subtitles.font_size 40` / `max_chars_per_line 30` / `tts.voice zh-CN-XiaoxiaoNeural`
- `compositor/pipeline.py` — `_resolve_scene_class`(精确优先) / `_split_for_display` / `_flatten_for_display` / `_pair_narrations` / `_clamp_subtitles_to_speech` / `_srt_to_ass`(厘秒进位) / `_burn_ass_to_file` / `_FFMPEG` 常量
- `scenes/sections.py` GPU 区域 — 12 个 `GPU*Scene`,统一单色系 + 单链式排版
- `tests/test_subtitle_fixes.py`(33)+ `tests/test_gpu_visual_unification.py`(23)= 56 项回归测试,改字幕或 GPU 场景后必须全绿
- 产品图 `assets/images/gpu/sapphire_nitro_plus_white_7900xt_small.png`(官方 XT 外观参考,非 XTX)

**辅助脚本**(非 MoviePy 合成路径)
- `compose_fast.py` — ffmpeg 直连拼接,跳过 MoviePy,适用于快速迭代替换
- `compose_agnes_isolated.py` — Agnes AI 教程专用,隔离输出到 `output_agnes/` / `assets/temp_agnes/`
- `burn_agnes_only.py` — 在已有 temp mp4 + srt 上单独烧录 ASS 字幕
- `models.py` — `VideoSection.skip_subtitles`(bool),设为 true 时跳过字幕
