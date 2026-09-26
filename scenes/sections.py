"""
Specific scene implementations for each section of the video.
"""
from manim import *
from scenes.base import *
from config import get_config
from typing import Dict, List

config = get_config()


class IntroScene(BaseScene):
    """Opening scene: title card + simulated `ollama list` / `ollama ps` terminal."""

    MODELS = [
        ("ministral-3:3b-instruct-2512-q4_K_M", "f04aa1c738f6", "3.0 GB", "9 minutes ago"),
        ("ministral-3:8b", "8f91a4b2e560", "5.2 GB", "2 hours ago"),
        ("unsloth/qwen2.5-omni-7b-q4-k-m", "22a54436c251", "4.7 GB", "About an hour ago"),
        ("mistral:7b-instruct", "6577803aa9a0", "4.4 GB", "3 hours ago"),
        ("unsloth/gemma-4-E4B-it-qat-GGUF", "ee16c091ef96", "4.2 GB", "10 hours ago"),
        ("nemotron-3-nano:4b", "6cc467f05439", "2.8 GB", "34 hours ago"),
        ("qwen3.5:9.7b", "c7d8e9f0a1b2", "6.6 GB", "2 days ago"),
        ("llama3.1:8b-instruct-q8_0", "a1b2c3d4e5f6", "8.5 GB", "3 days ago"),
        ("llama3.1:8b-instruct-q4_0", "1a2b3c4d5e6f", "4.7 GB", "5 days ago"),
    ]

    def construct(self):
        self.record_visual_text("MacBook Pro 本地运行 AI 大模型评测")
        self.record_visual_text("2026 MacBook Pro 跑大模型，能有多快？")
        title = self.create_title("MacBook Pro 本地运行 AI 大模型评测", scale=0.85)
        subtitle = self.create_subtitle("2026 MacBook Pro 跑大模型，能有多快？")
        header = VGroup(title, subtitle).arrange(DOWN, buff=0.5).to_edge(UP, buff=0.5)

        self.play(Write(title, run_time=1.5))
        self.play(FadeIn(subtitle, shift=UP * 0.3), run_time=0.8)
        self.wait(0.5)

        term = TerminalSimulator(title="macbook-pro — ollama",
                                  width=13.2, height=5.4, font_size=13)
        term.build()
        term.terminal.next_to(header, DOWN, buff=0.45)
        self.play(FadeIn(term.terminal, run_time=0.4))
        self.wait(0.2)

        self.record_visual_text("ollama list")
        term.add_command(self, "user@macbook-pro:~$ ", "ollama list", wait=0.15)
        self.add_ollama_list_rows(term)
        self.record_visual_text("ollama ps")
        term.add_command(self, "user@macbook-pro:~$ ", "ollama ps", wait=0.15)
        self.add_ollama_ps_rows(term)
        self.wait(0.5)

    def add_ollama_list_rows(self, term):
        """Type the ``ollama list`` table: header + 9 installed models."""
        self.record_visual_text("ollama list 模型列表：NAME / ID / SIZE / MODIFIED")
        term.add_line(self, "NAME".ljust(42) + " " + "ID".ljust(16) + " " +
                      "SIZE".ljust(11) + " MODIFIED",
                      color="#8b949e", font_size=12, run_time=0.4, wait=0.1)
        for name, mid, size, modified in self.MODELS:
            row = name.ljust(42) + " " + mid.ljust(16) + " " + size.ljust(11) + " " + modified
            term.add_line(self, row, color="#9da5b4", font_size=12, run_time=0.8)

    def add_ollama_ps_rows(self, term):
        """Type a short ``ollama ps`` snapshot (qwen3.5 pegging the CPU)."""
        self.record_visual_text("ollama ps 运行中：qwen3.5 占用 CPU 100%")
        term.add_line(self, "NAME".ljust(42) + " " + "ID".ljust(16) + " " +
                      "CPU".ljust(11) + " UNTIL",
                      color="#8b949e", font_size=12, run_time=0.4, wait=0.1)
        term.add_line(self, "qwen3.5:9.7b".ljust(42) + " " + "c7d8e9f0a1b2".ljust(16) +
                      " " + "100%".ljust(11) + " Until 4 minutes left",
                      color="#d29922", font_size=12, run_time=0.8, wait=0.1)


class HardwareScene(BaseScene):
    """硬件环境: system_profiler 终端流程 + 关键规格标注卡."""

    def construct(self):
        self.record_visual_text("测试环境：2019 MacBook Pro 16,1")
        title = self.create_title("测试环境：2019 MacBook Pro 16,1").to_edge(UP)
        self.play(Write(title))

        term = TerminalSimulator(title="macbook-pro — system_profiler",
                                  width=8.6, height=5.4, font_size=12)
        term.build()
        term.terminal.shift(LEFT * 2.2).shift(DOWN * 0.15)
        self.play(FadeIn(term.terminal, run_time=0.4))
        self.wait(0.2)

        self.record_visual_text("system_profiler SPHardwareDataType")
        term.add_command(self, "user@macbook-pro:~$ ",
                         "system_profiler SPHardwareDataType", wait=0.2)

        self.record_visual_text("硬件概览：MacBook Pro 16寸 2019款")
        term.add_line(self, "Hardware Overview:", color="#8b949e",
                      indent=0.6, lag=0.0, weight=BOLD, run_time=0.6)
        self.record_visual_text("Model Name: MacBook Pro 16-inch 2019")
        term.add_line(self, "    Model Name: MacBook Pro (16-inch, 2019)",
                      color="#9da5b4", indent=0.6, lag=0.0, run_time=0.9)
        self.record_visual_text("芯片: Intel Core i7-9750H")
        line_chip = term.add_line(self, "    Chip: Intel Core i7-9750H",
                                  color="#9da5b4", indent=0.6, lag=0.0, run_time=0.9)
        self.record_visual_text("核心数: 6核")
        term.add_line(self, "    Total Number of Cores: 6",
                      color="#9da5b4", indent=0.6, lag=0.0, run_time=0.7)
        self.record_visual_text("内存: 32GB")
        line_mem = term.add_line(self, "    Memory: 32 GB",
                                 color="#9da5b4", indent=0.6, lag=0.0, run_time=0.7)
        self.record_visual_text("显卡: AMD Radeon Pro 5300M 4GB")
        line_gpu = term.add_line(self, "    Chipset Model: AMD Radeon Pro 5300M",
                                 color="#9da5b4", indent=0.6, lag=0.0, run_time=0.9)
        self.record_visual_text("显存: 4GB")
        term.add_line(self, "    VRAM (total): 4 GB",
                      color="#9da5b4", indent=0.6, lag=0.0, run_time=0.7, wait=0.2)

        self.record_visual_text("i7-9750H · 6核12线程 · 2.6/4.5GHz")
        self.pop_tag(term, line_chip, "i7-9750H · 6核12线程 · 2.6/4.5GHz",
                     config.manim.accent_color)
        self.record_visual_text("内存: 32GB DDR4")
        self.pop_tag(term, line_mem, "32GB DDR4", config.manim.success_color)
        self.record_visual_text("显卡: RX 5300M 4GB（Intel Mac 无法使用）")
        self.pop_tag(term, line_gpu, "RX 5300M · 4GB", config.manim.warning_color)

        self.record_visual_text("⚠ Ollama 在 Intel Mac 仅 CPU 推理，GPU 用不上")
        warn = Text("⚠ Ollama 在 Intel Mac 仅 CPU 推理，GPU 用不上",
                    font=self.get_chinese_font(), color=config.manim.warning_color,
                    font_size=16, weight=BOLD)
        warn_bg = RoundedRectangle(
            width=warn.width + 0.6, height=warn.height + 0.3,
            corner_radius=0.12, fill_color=config.manim.terminal_bg,
            fill_opacity=0.95, stroke_color=config.manim.warning_color, stroke_width=2,
        )
        warn_box = VGroup(warn_bg, warn).center()
        warn_box.to_edge(DOWN, buff=0.3).shift(RIGHT * 3.0)
        self.play(FadeIn(warn_box, shift=UP * 0.3), run_time=0.5)
        self.wait(0.3)

        self.record_visual_text("ollama --version")
        term.add_command(self, "user@macbook-pro:~$ ", "ollama --version", wait=0.15)
        self.record_visual_text("Ollama 版本: 0.14.0")
        term.add_line(self, "ollama version is 0.14.0", color="#9da5b4",
                      indent=0.6, lag=0.0, run_time=0.8, wait=0.2)
        self.wait(0.5)

    def pop_tag(self, term, anchor, text, color):
        """弹出右侧规格标注卡，垂直对齐到对应终端行."""
        label = Text(text, font=self.get_chinese_font(), color=color,
                     font_size=15, weight=BOLD)
        bg = RoundedRectangle(
            width=label.width + 0.5, height=label.height + 0.3,
            corner_radius=0.12, fill_color=config.manim.terminal_bg,
            fill_opacity=0.95, stroke_color=color, stroke_width=2,
        )
        card = VGroup(bg, label).center()
        card.move_to([term.terminal.get_right()[0] + 0.5 + card.width / 2,
                      anchor.get_center()[1], 0])
        self.play(FadeIn(card, shift=LEFT * 0.2), run_time=0.45)
        self.wait(0.5)


class QuestionsScene(BaseScene):
    """Test questions introduction."""
    
    def construct(self):
        self.record_visual_text("5 道统一考题，覆盖不同能力维度")
        title = self.create_title("5 道统一考题，覆盖不同能力维度").to_edge(UP)
        self.play(Write(title))

        questions = [
            ("1. 逻辑推理", "A farmer has 17 sheep. All but 9 die.\nHow many sheep are left? Explain step by step.", "英文理解、惯用语解析、逻辑推理"),
            ("2. 代码生成", "Write a Python function that checks if a\nstring is a palindrome. Include type hints\nand a docstring.", "编程能力、代码规范、文档完整性"),
            ("3. 中文理解", "用中文简要解释什么是量子纠缠，\n200字以内。", "中文生成质量、知识准确性、简洁性"),
            ("4. 创意写作", "写一首关于秋天的五言绝句，\n四句，每句五个字。只输出诗句。", "中文创作能力、格律遵循、意境表达"),
            ("5. 翻译", "把以下古诗翻译成英文，只输出译文：\n春眠不觉晓，处处闻啼鸟。", "中英翻译质量、古诗理解、文学表达"),
        ]

        q_boxes = VGroup()
        for i, (q_title, q_text, q_dim) in enumerate(questions):
            self.record_visual_text(f"{q_title}：{q_text.replace(chr(10), ' ')} | 考察：{q_dim}")
            q_box = VGroup(
                Text(q_title, font=self.get_chinese_font(), color=config.manim.accent_color, font_size=19),
                Text(q_text, font=self.get_chinese_font(), color=config.manim.text_color, font_size=15, line_spacing=1.15),
                Text(f"考察：{q_dim}", font=self.get_chinese_font(), color=config.manim.success_color, font_size=14),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            q_boxes.add(q_box)

        q_boxes.arrange_in_grid(rows=3, cols=2, buff=(0.35, 0.8)).center().shift(DOWN*0.25)

        for q_box in q_boxes:
            self.play(FadeIn(q_box, shift=RIGHT*0.3), run_time=0.5)
            self.wait(0.25)

        self.record_visual_text("所有题目完全相同，不针对任何模型优化，公平测试")
        note = Text("所有题目完全相同，不针对任何模型优化，公平测试",
                   font=self.get_chinese_font(), color=config.manim.warning_color, font_size=16)
        note.to_edge(DOWN, buff=0.3)
        self.play(Write(note), run_time=0.8)
        self.wait(0.5)


class ModelsScene(BaseScene):
    """Models overview scene."""
    
    def construct(self):
        self.record_visual_text("参测模型一览：9 个模型")
        title = self.create_title("参测模型一览：9 个模型").to_edge(UP)
        self.play(Write(title))

        models = [
            ("Gemma 4", "~4B", "QAT", "4.2 GB", "Google 多模态，QAT 量化保精度"),
            ("Llama 3.1 8B", "8B", "Q8_0", "8.5 GB", "Meta 经典指令微调版"),
            ("Llama 3.1 8B", "8B", "Q4_0", "4.7 GB", "对比测试：不同量化影响"),
            ("Mistral 7B", "7.2B", "Q4_K_M", "4.4 GB", "Mistral AI 经典，逻辑推理强"),
            ("Nemotron 3 Nano", "4B", "Q4_K_M", "2.8 GB", "NVIDIA 轻量推理，全场最小"),
            ("Qwen3.5", "9.7B", "Q4_K_M", "6.6 GB", "阿里混合架构，本机跑得吃力"),
            ("Qwen2.5 Omni", "7.6B", "Q4_K_M", "4.7 GB", "阿里全模态，文本/音频/视觉"),
            ("Ministral 3 3B", "3.8B", "Q4_K_M", "3.0 GB", "Mistral 新一代，262K 上下文+视觉"),
            ("Ministral 3 8B", "8.5B", "Q4_K_M", "5.2 GB", "8B 版初测，质量持平但速度慢 2.4x"),
        ]

        self.record_visual_text("模型对比表：模型 / 参数 / 量化 / 体积 / 特点")
        headers = ["模型", "参数", "量化", "体积", "特点"]
        rows = [[m[0], m[1], m[2], m[3], m[4]] for m in models]
        
        table = Table(
            [headers] + rows,
            include_outer_lines=True,
            line_config={"stroke_width": 1, "color": config.manim.accent_color},
            element_to_mobject_config={"font_size": 13, "font": self.get_chinese_font(), "color": config.manim.text_color},
            h_buff=0.8,
            v_buff=0.2,
        )
        
        self.apply_row_colors(table, n_rows=10, n_cols=5)
        
        # Highlight Ministral rows
        for col in range(1, 6):
            table.get_cell((9, col)).set_fill(config.manim.accent_color, opacity=0.2)
            table.get_cell((10, col)).set_fill(config.manim.warning_color, opacity=0.2)
        
        table.scale_to_fit_width(15).center()
        
        self.play(Write(Text("9 个模型逐行出现", font=self.get_chinese_font(), color=config.manim.accent_color, font_size=16).next_to(title, DOWN)))
        self.play(Create(table), run_time=3)
        self.wait(0.5)


class SpeedResultsScene(BaseScene):
    """Speed benchmark results with animated bar chart (manual, no LaTeX)."""
    
    def construct(self):
        self.record_visual_text("速度测试结果：平均耗时排名")
        title = self.create_title("速度测试结果：平均耗时排名").to_edge(UP)
        self.play(Write(title))

        # Data from benchmark
        data = [
            ("llama3.1\nQ4_0", 11.3),
            ("mistral\n7b", 12.0),
            ("Ministral 3\n3B", 21.2),
            ("Qwen2.5\nOmni", 28.3),
            ("nemotron\n3-nano", 42.0),
            ("llama3.1\nQ8_0", 45.2),
            ("gemma-4", 49.5),
            ("Ministral 3\n8B", 50.4),
            ("qwen3.5", 170),
        ]
        self.record_visual_text("速度排名条形图：各模型5题平均耗时（秒）")
        
        max_val = 180.0
        bar_height_max = 2.4
        n_bars = len(data)
        chart_w = 12.5
        gap = chart_w / n_bars
        bar_w = 0.8
        baseline_y = -1.4
        half_w = chart_w / 2
        
        colors = ([config.chart_colors[0]] * 2 + [config.chart_colors[1]] +
                  [config.chart_colors[2]] + [config.chart_colors[3]] * 2 +
                  [config.chart_colors[4]] + [config.chart_colors[5]] + [config.chart_colors[6]])
        
        bars = VGroup()
        bars_name = VGroup()
        bars_val = VGroup()
        
        for i, (name, val) in enumerate(data):
            h = max(val / max_val * bar_height_max, 0.05)
            x = -half_w + gap * (i + 0.5)
            bar = Rectangle(
                width=bar_w, height=h,
                fill_color=colors[i], fill_opacity=0.85,
                stroke_width=1,
            )
            bar.move_to(np.array([x, baseline_y + h / 2, 0]))
            bars.add(bar)
            
            name_txt = Text(name, font=self.get_chinese_font(), font_size=10, color=config.manim.text_color)
            name_txt.next_to(bar, DOWN, buff=0.12)
            bars_name.add(name_txt)
            
            val_txt = Text(f"{val}s", font=self.get_chinese_font(), font_size=11, color=config.manim.text_color)
            val_txt.next_to(bar, UP, buff=0.05)
            bars_val.add(val_txt)
        
        # Axes (pure Line + DecimalNumber, no LaTeX)
        x_axis = Line(
            np.array([-half_w, baseline_y, 0]), np.array([half_w, baseline_y, 0]),
            color=config.manim.text_color, stroke_width=2,
        )
        y_axis = Line(
            np.array([-half_w, baseline_y, 0]), np.array([-half_w, baseline_y + bar_height_max + 0.3, 0]),
            color=config.manim.text_color, stroke_width=2,
        )
        
        chart_title_text = Text("5 题平均耗时（秒）", font=self.get_chinese_font(), font_size=14, color=config.manim.text_color)
        chart_title_text.next_to(x_axis, UP, buff=0.35)
        
        y_label = Text("耗时 (秒)", font=self.get_chinese_font(), font_size=13, color=config.manim.text_color)
        y_label.next_to(y_axis, LEFT, buff=0.15).rotate(90 * DEGREES)
        
        chart_group = VGroup(x_axis, y_axis, bars, bars_name, bars_val, chart_title_text, y_label)
        chart_group.center().shift(DOWN * 0.15)
        
        # Key insights
        self.record_visual_text("llama3.1 Q4_0 最快：11.3s")
        self.record_visual_text("Mistral 7B 紧随：12.0s（唯一答对逻辑题的快模型）")
        self.record_visual_text("Ministral 3 3B：21.2s（创意写作 3.5s、翻译 2.6s 全场最快）")
        self.record_visual_text("Qwen3.5 超时：>170s 基本不可用")
        insight = VGroup(
            Text("🏆 llama3.1 Q4_0 最快：11.3s", font=self.get_chinese_font(), color=config.manim.success_color, font_size=16),
            Text("⚡ Mistral 7B 紧随：12.0s（唯一答对逻辑题的快模型）", font=self.get_chinese_font(), color=config.manim.accent_color, font_size=16),
            Text("🚀 Ministral 3 3B：21.2s（创意写作 3.5s、翻译 2.6s 全场最快）", font=self.get_chinese_font(), color=config.manim.warning_color, font_size=16),
            Text("⏱️ Qwen3.5 超时：>170s 基本不可用", font=self.get_chinese_font(), color=config.manim.error_color, font_size=16),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).to_edge(DOWN)
        
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.08), run_time=2)
        self.play(Write(chart_title_text), Write(y_label), run_time=0.5)
        self.play(Write(bars_val), run_time=0.6)
        self.play(FadeIn(insight, shift=UP*0.3), run_time=1.5)
        self.wait(0.5)


class AccuracyScene(BaseScene):
    """Accuracy comparison scene with color-coded table."""
    
    def construct(self):
        self.record_visual_text("准确率对比：Ministral 3 全胜")
        title = self.create_title("准确率对比：Ministral 3 全胜").to_edge(UP)
        self.play(Write(title))

        self.record_visual_text("准确率对比表：题目 / 正确答案 / 10个模型表现")
        headers = ["题目", "正确答案", "gemma-4", "llama3.1-Q8", "llama3.1-Q4", "mistral", "nemotron", "Qwen2.5-Omni", "qwen3.5", "Ministral 3B"]
        rows = [
            ["逻辑推理", "9", "✅9", "❌8", "❌8", "✅9", "✅9", "✅9", "✅9", "✅9"],
            ["代码生成", "回文函数", "✅完整", "✅完整", "✅完整", "✅简洁", "✅优秀", "✅完整", "⏰超时", "✅完整+测试"],
            ["中文理解", "量子纠缠", "✅详细", "✅简洁", "✅合理", "✅合理", "✅简洁", "✅清晰", "⏰超时", "✅准确⚠️混英文"],
            ["创意写作", "五言绝句", "✅合律", "❌格式错", "❌格式错", "⚠️5行", "✅合律", "✅合律", "⏰超时", "✅合律"],
            ["古诗翻译", "春眠不觉晓", "✅优秀", "✅准确", "✅准确", "✅准确", "✅合理", "✅优美", "⏰超时", "✅优美"],
        ]
        
        table = Table(
            [headers] + rows,
            include_outer_lines=True,
            line_config={"stroke_width": 1, "color": config.manim.accent_color},
            element_to_mobject_config={"font_size": 12, "font": self.get_chinese_font(), "color": config.manim.text_color},
            h_buff=0.5,
            v_buff=0.15,
        )
        
        self.apply_row_colors(table, n_rows=6, n_cols=10)
        
        # Color code cells
        for row_idx, row in enumerate(rows):
            for col_idx, cell_text in enumerate(row):
                cell = table.get_cell((row_idx + 2, col_idx + 1))
                if "❌" in cell_text or "超时" in cell_text:
                    cell.set_fill(config.manim.error_color, opacity=0.3)
                elif "✅" in cell_text:
                    cell.set_fill(config.manim.success_color, opacity=0.15)
                elif "⚠️" in cell_text:
                    cell.set_fill(config.manim.warning_color, opacity=0.2)
        
        # Highlight Ministral 3B column (last column)
        for row_idx in range(6):
            table.get_cell((row_idx + 1, 10)).set_fill(config.manim.accent_color, opacity=0.2)
        
        table.scale_to_fit_width(16).center()
        
        self.play(Write(title))
        self.play(Create(table), run_time=3)
        self.wait(0.5)


class Ministral3BScene(BaseScene):
    """重点模型: ollama run 实时问答终端流程."""

    def construct(self):
        self.record_visual_text("重点模型：Ministral 3 3B — 惊喜表现")
        title = self.create_title("重点模型：Ministral 3 3B — 惊喜表现").to_edge(UP)
        self.play(Write(title))

        term = TerminalSimulator(title="macbook-pro — ministral-3:3b",
                                  width=13.6, height=6.6, font_size=13, line_h=0.24)
        term.build()
        term.terminal.next_to(title, DOWN, buff=0.4)
        self.play(FadeIn(term.terminal, run_time=0.5))
        self.wait(0.3)

        self.record_visual_text("ollama run ministral-3:3b-instruct-2512-q4_K_M")
        term.add_command(self, "user@macbook-pro:~$ ",
                         "ollama run ministral-3:3b-instruct-2512-q4_K_M", wait=0.4)

        zh = self.get_chinese_font()
        prompt_col = config.manim.terminal_prompt
        ok_col = config.manim.success_color
        txt = config.manim.terminal_text

        # Q1 逻辑推理
        self.record_visual_text("问题1: A farmer has 17 sheep. All but 9 die. How many left?")
        term.add_line(self,
                      ">>> A farmer has 17 sheep. All but 9 die. How many sheep are left?",
                      color=prompt_col, lag=0.0, run_time=1.4)
        self.record_visual_text("答案: All but 9 die means 9 sheep did not die — the answer is 9.")
        term.add_line(self,
                      "All but 9 die means 9 sheep did not die — the answer is 9.",
                      color=txt, lag=0.0, run_time=1.4)
        self.record_visual_text("✓ 27.3s")
        term.add_line(self, "✓ 27.3s", color=ok_col, weight=BOLD, run_time=0.5, wait=0.15)

        # Q2 代码生成
        self.record_visual_text("问题2: Write a Python function that checks if a string is a palindrome.")
        term.add_line(self,
                      ">>> Write a Python function that checks if a string is a palindrome.",
                      color=prompt_col, lag=0.0, run_time=1.0)
        self.record_visual_text("答案: def is_palindrome(s: str) -> bool — 完整docstring+类型提示")
        term.add_line(self,
                      "def is_palindrome(s: str) -> bool:  # type hints + docstring",
                      color=txt, lag=0.0, run_time=1.0)
        term.add_line(self, "    return s == s[::-1]",
                      color=txt, lag=0.0, run_time=0.8)
        self.record_visual_text("✓ 41.2s")
        term.add_line(self, "✓ 41.2s", color=ok_col, weight=BOLD, run_time=0.5, wait=0.15)

        # Q3 中文理解
        self.record_visual_text("问题3: 用中文简要解释什么是量子纠缠，200字以内。")
        term.add_line(self, ">>> 用中文简要解释什么是量子纠缠，200字以内。",
                      color=prompt_col, lag=0.0, run_time=1.0, font=zh)
        self.record_visual_text("答案: 量子纠缠指两个粒子相互关联...")
        term.add_line(self, "量子纠缠指两个粒子相互关联，测量其中一个会瞬间影响另一个，",
                      color=txt, lag=0.0, run_time=1.0, font=zh)
        term.add_line(self, "即使相隔很远——爱因斯坦称之为幽灵般的超距作用。",
                      color=txt, lag=0.0, run_time=1.0, font=zh)
        self.record_visual_text("⚠ 混入英文 instantaneously")
        term.add_line(self, "⚠ 回答准确，但混入英文 instantaneously",
                      color=config.manim.warning_color, lag=0.0, run_time=1.0, font=zh)
        self.record_visual_text("✓ 32.1s")
        term.add_line(self, "✓ 32.1s", color=ok_col, weight=BOLD, run_time=0.5, wait=0.15)

        # Q4 创意写作
        self.record_visual_text("问题4: 写一首关于秋天的五言绝句，四句每句五个字。")
        term.add_line(self, ">>> 写一首关于秋天的五言绝句，四句每句五个字。只输出诗句。",
                      color=prompt_col, lag=0.0, run_time=1.0, font=zh)
        self.record_visual_text("风吹落叶黄，天高月更明，田野秋意浓，归鸟飞云情。")
        term.add_line(self, "风吹落叶黄，天高月更明，",
                      color=txt, lag=0.0, run_time=0.8, font=zh)
        term.add_line(self, "田野秋意浓，归鸟飞云情。",
                      color=txt, lag=0.0, run_time=0.8, font=zh)
        self.record_visual_text("✓ 3.5s 🏆 全场最快")
        term.add_line(self, "✓ 3.5s 🏆 全场最快", color=ok_col, weight=BOLD,
                      run_time=0.5, font=zh, wait=0.15)

        # Q5 古诗翻译
        self.record_visual_text("问题5: 把古诗翻译成英文，只输出译文：春眠不觉晓，处处闻啼鸟。")
        term.add_line(self, ">>> 把古诗翻译成英文，只输出译文：春眠不觉晓，处处闻啼鸟。",
                      color=prompt_col, lag=0.0, run_time=1.0, font=zh)
        self.record_visual_text("Morning sleep did not wake me, Everywhere the birds sing their dawn.")
        term.add_line(self, "Morning sleep did not wake me,",
                      color=txt, lag=0.0, run_time=1.0)
        term.add_line(self, "Everywhere the birds sing their dawn.",
                      color=txt, lag=0.0, run_time=1.0)
        self.record_visual_text("✓ 2.6s 🏆 全场最快")
        term.add_line(self, "✓ 2.6s 🏆 全场最快", color=ok_col, weight=BOLD,
                      run_time=0.5, font=zh, wait=0.15)

        self.record_visual_text("✦ 5/5 全对 · 平均 21.2s · 3.0GB · 262K上下文 · 支持视觉")
        term.add_line(self, "✦ 5/5 全对 · 平均 21.2s · 3.0GB · 262K上下文 · 支持视觉",
                      color=config.manim.accent_color, weight=BOLD,
                      run_time=1.2, font=zh, wait=0.4)
        self.wait(0.5)


class ComparisonScene(BaseScene):
    """Ministral 3B vs 8B vs Mistral 7B comparison."""
    
    def construct(self):
        self.record_visual_text("三方对比：Ministral 3B vs 8B vs Mistral 7B")
        title = self.create_title("三方对比：Ministral 3B vs 8B vs Mistral 7B").to_edge(UP)
        self.play(Write(title))

        self.record_visual_text("对比表：对比项 / 3B / 8B / 7B / 胜者")
        headers = ["对比项", "Ministral 3B", "Ministral 8B", "Mistral 7B", "胜者"]
        rows = [
            ["参数/架构", "3.8B/mistral3", "8.5B/mistral3", "7.2B/mistral", "—"],
            ["上下文窗口", "262K", "262K", "32K", "Ministral (8倍)"],
            ["体积", "3.0 GB", "5.2 GB", "4.4 GB", "3B 最小"],
            ["视觉能力", "✅ 支持", "✅ 支持", "❌ 无", "Ministral"],
            ["逻辑题", "✅9 (27s)", "✅9 (75s)", "✅9 (7.9s)", "平局(速度Mistral)"],
            ["代码题", "✅完整+测试", "✅完整+说明", "✅简洁", "3B/8B"],
            ["中文题", "✅偶混英文", "✅详细准确", "✅合理", "8B"],
            ["创意写作", "✅完美(3.5s)", "✅完美(8.7s)", "⚠️5行", "3B/8B"],
            ["翻译", "✅优美(2.6s)", "✅押韵(7.7s)", "✅简洁(4.9s)", "3B"],
            ["平均耗时", "21.2s", "50.4s", "12.0s", "3B/Mistral分场景"],
        ]
        
        table = Table(
            [headers] + rows,
            include_outer_lines=True,
            line_config={"stroke_width": 1, "color": config.manim.accent_color},
            element_to_mobject_config={"font_size": 12, "font": self.get_chinese_font(), "color": config.manim.text_color},
            h_buff=0.6,
            v_buff=0.14,
        )
        
        self.apply_row_colors(table, n_rows=11, n_cols=5)
        
        # Highlight 3B column
        for row_idx in range(11):
            table.get_cell((row_idx + 1, 2)).set_fill(config.manim.accent_color, opacity=0.15)
        
        table.scale_to_fit_width(15.5).center()

        self.play(Write(title))
        self.play(Create(table), run_time=3)
        # Hold table for full narration (~48s audio, ~5s animation → need ~43s wait)
        self.wait(43)


class RankingScene(BaseScene):
    """Final ranking and recommendations."""
    
    def construct(self):
        self.record_visual_text("综合排名与选择建议")
        title = self.create_title("综合排名与选择建议").to_edge(UP)
        self.play(Write(title))

        # Ranking
        ranks = [
            ("🥇 1", "Ministral 3 3B", "综合首选：质量高、速度快、体积小、262K上下文+视觉", config.manim.accent_color),
            ("🥈 2", "Mistral 7B", "速度首选：12秒平均，逻辑正确，秒级问答最佳", config.manim.success_color),
            ("🥉 3", "Nemotron 3 Nano", "资源受限首选：2.8GB最小，5/5全对", config.manim.warning_color),
            ("4️⃣ 4", "Qwen2.5 Omni", "多模态首选：需图片/音频输入时选它", config.chart_colors[3]),
            ("5️⃣ 5", "gemma-4", "创意/翻译备选：文学性强", config.chart_colors[4]),
            ("6️⃣ 6", "llama3.1-Q4_0", "极致速度11.3s但逻辑错，仅限简单任务", config.manim.error_color),
        ]
        for rank, name, desc, color in ranks:
            self.record_visual_text(f"{rank} {name}：{desc}")
        
        rank_items = VGroup()
        for rank, name, desc, color in ranks:
            item = VGroup(
                Text(rank, font=self.get_chinese_font(), color=color, font_size=22, weight=BOLD),
                Text(name, font=self.get_chinese_font(), color=config.manim.text_color, font_size=19),
                Text(desc, font=self.get_chinese_font(), color=config.manim.text_color, font_size=15),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.05)
            rank_items.add(item)
        
        rank_items.arrange_in_grid(rows=3, cols=2, buff=(0.45, 1.2)).center().shift(UP*0.4)
        
        self.play(Write(title))
        for item in rank_items:
            self.play(FadeIn(item, shift=RIGHT*0.3), run_time=0.5)
        
        # Recommendation box
        rec_box = VGroup(
            Text("💡 精简方案", font=self.get_chinese_font(), color=config.manim.accent_color, font_size=20, weight=BOLD),
            Text("保留 1 个 → Ministral 3 3B（一个模型打天下）", font=self.get_chinese_font(), color=config.manim.text_color, font_size=14),
            Text("保留 2 个 → + Mistral 7B（覆盖秒级场景）", font=self.get_chinese_font(), color=config.manim.text_color, font_size=14),
            Text("保留 3 个 → + Qwen2.5 Omni（多模态）或 Nemotron（迷你）", font=self.get_chinese_font(), color=config.manim.text_color, font_size=14),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        
        bg = RoundedRectangle(
            width=rec_box.width + 0.8, height=rec_box.height + 0.4,
            corner_radius=0.12,
            fill_color=config.manim.terminal_bg,
            fill_opacity=0.9,
            stroke_color=config.manim.accent_color,
            stroke_width=2,
        )
        
        rec_group = VGroup(bg, rec_box).center().to_edge(DOWN)
        self.play(FadeIn(rec_group, shift=UP*0.5), run_time=1)
        # Hold for full narration (~48s, animation ~5s → need ~43s total)
        self.wait(43)


class OutroScene(BaseScene):
    """Closing scene."""
    
    def construct(self):
        self.record_visual_text("2026 年，3GB 的小模型就能打到 7B 的水平")
        self.record_visual_text("本地跑大模型已经不是实验，是完全可以日常使用的工具")
        self.record_visual_text("完整评测报告和测试数据已整理成文档")
        # Main message
        lines = VGroup(
            Text("2026 年，3GB 的小模型", font=self.get_chinese_font(), color=config.manim.accent_color, font_size=28, weight=BOLD),
            Text("就能打到 7B 的水平，速度还快一倍", font=self.get_chinese_font(), color=config.manim.text_color, font_size=23),
            Text("", font=self.get_chinese_font(), font_size=15),
            Text("本地跑大模型已经不是实验", font=self.get_chinese_font(), color=config.manim.success_color, font_size=23, weight=BOLD),
            Text("是完全可以日常使用的工具", font=self.get_chinese_font(), color=config.manim.text_color, font_size=21),
            Text("", font=self.get_chinese_font(), font_size=15),
            Text("完整评测报告和测试数据", font=self.get_chinese_font(), color=config.manim.text_color, font_size=19),
            Text("已整理成文档，需要的可以看", font=self.get_chinese_font(), color=config.manim.text_color, font_size=19),
        ).arrange(DOWN, buff=0.18).center()
        
        self.play(Write(lines[0], run_time=1.5))
        for line in lines[1:]:
            if line.text:
                self.play(FadeIn(line, shift=UP*0.2), run_time=0.6)
            else:
                self.wait(0.2)
        
        self.wait(2)
        
        url_text = Text("https://zhuanlan.zhihu.com/p/2082017146067014915",
                       font=self.get_code_font(), color=config.manim.accent_color, font_size=16)
        url_label = Text("完整评测报告", font=self.get_chinese_font(), color=config.manim.warning_color, font_size=18)
        url_group = VGroup(url_label, url_text).arrange(DOWN, buff=0.15)
        url_group.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(url_group, shift=UP*0.3), run_time=1)
        self.wait(2)

        self.record_visual_text("https://zhuanlan.zhihu.com/p/2082017146067014915")
        self.record_visual_text("完整评测就到这里，我们下次见")
        final = VGroup(
            Text("这次评测就到这里", font=self.get_chinese_font(), color=config.manim.text_color, font_size=22),
            Text("我们下次见 👋", font=self.get_chinese_font(), color=config.manim.accent_color, font_size=25, weight=BOLD),
        ).arrange(DOWN, buff=0.3).center()
        
        self.play(FadeIn(final, shift=UP*0.3), run_time=1.5)
        # Hold for full narration (~20s, animation ~7s → need ~13s total)
        self.wait(13)


class TechSpecsScene(BaseScene):
    """Technical specifications footer."""
    
    def construct(self):
        self.record_visual_text("技术说明")
        title = self.create_title("技术说明").to_edge(UP)
        self.play(Write(title))

        self.record_visual_text("技术参数表：视频时长/画面比例/字幕/配乐建议/画面节奏/转场")
        specs = [
            ("视频时长", "约 7-8 分钟"),
            ("画面比例", "16:9（横屏）"),
            ("字幕", "全程中文字幕"),
            ("配乐建议", "科技感背景音乐，节奏平稳"),
            ("画面节奏", "每个镜头 5-10 秒，数据表格停留 8-12 秒"),
            ("转场", "渐隐渐出为主，数据表格用滑入动画"),
        ]
        
        table = Table(
            [["项目", "内容"]] + specs,
            include_outer_lines=True,
            line_config={"stroke_width": 1, "color": config.manim.accent_color},
            element_to_mobject_config={"font_size": 17, "font": self.get_chinese_font(), "color": config.manim.text_color},
            h_buff=2.0,
            v_buff=0.25,
        )
        
        self.apply_row_colors(table, n_rows=7, n_cols=2)
        
        table.scale_to_fit_width(12).center()
        
        self.play(Write(title))
        self.play(Create(table), run_time=1.5)
        self.wait(2)


# ============================================================
# Extruder Principles and Operation — 中文版推广视频场景
# ============================================================

class ExtruderIntroScene(BaseScene):
    """开场：书名 + 副标题 + 挤出机应用"""
    def construct(self):
        title = self.create_title("挤出机原理与操作", scale=0.85)
        subtitle = self.create_subtitle("一部经典的中文版诞生记")
        VGroup(title, subtitle).arrange(DOWN, buff=0.5).center()
        self.play(Write(title, run_time=2))
        self.play(FadeIn(subtitle, shift=UP * 0.3), run_time=1)
        self.wait(8)
        
        try:
            extruder_img = ImageMobject("assets/images/extruder/eta_extruder.jpg")
            extruder_img.scale_to_fit_width(5)
            extruder_img.to_edge(LEFT, buff=1.0).shift(DOWN * 0.5)
            self.play(FadeIn(extruder_img))
            self.wait(3)
        except:
            pass
        
        apps = VGroup(
            Text("矿泉水瓶", font=self.get_chinese_font(), color=config.manim.text_color).scale(0.35),
            Text("汽车塑料燃油箱", font=self.get_chinese_font(), color=config.manim.text_color).scale(0.35),
            Text("电线电缆", font=self.get_chinese_font(), color=config.manim.text_color).scale(0.35),
        ).arrange(RIGHT, buff=1.0)
        apps.to_edge(DOWN, buff=1.0)
        self.play(FadeIn(apps, shift=UP * 0.2))
        self.wait(5)
        
        info = Text("Stevens & Covas 著 · 1995年出版", font=self.get_chinese_font(), color=config.manim.accent_color).scale(0.3)
        info.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(info))
        self.wait(10)
        
        if 'extruder_img' in dir():
            self.play(extruder_img.animate.set_opacity(0.2))
        
        question = Text("但问题是：它没有中文版", font=self.get_chinese_font(), color=config.manim.warning_color).scale(0.5)
        question.move_to(ORIGIN)
        self.play(FadeIn(question, shift=UP * 0.3))
        self.wait(6)


class ExtruderOriginScene(BaseScene):
    """项目起源：2023年9月首次提交"""
    def construct(self):
        title = self.create_title("项目起源").to_edge(UP)
        date = Text("2023 年 9 月 25 日", font=self.get_chinese_font(), color=config.manim.accent_color).scale(0.6)
        desc = Text("GitHub 首次提交", font=self.get_chinese_font(), color=config.manim.text_color).scale(0.5)
        repo = Text("lybhb8/Extruder-Principles-and-Operation", font=self.get_code_font(), color=config.manim.success_color).scale(0.35)
        VGroup(title, date, desc, repo).arrange(DOWN, buff=0.6).center()
        self.play(Write(title))
        self.wait(3)
        self.play(FadeIn(date, shift=UP * 0.2))
        self.wait(4)
        self.play(FadeIn(desc, shift=UP * 0.2))
        self.wait(4)
        self.play(FadeIn(repo, shift=UP * 0.2))
        self.wait(6)


class ExtruderToolsScene(BaseScene):
    """翻译工具链：MinerU + DeepL"""
    def construct(self):
        title = self.create_title("翻译工具链").to_edge(UP)
        mineru = Text("MinerU", font=self.get_code_font(), color=config.manim.accent_color).scale(0.6)
        mineru_desc = Text("PDF → 结构化文本", font=self.get_chinese_font(), color=config.manim.text_color).scale(0.4)
        mineru_detail = Text("上海人工智能实验室开源", font=self.get_chinese_font(), color=config.manim.text_color).scale(0.3)
        deepl = Text("DeepL", font=self.get_code_font(), color=config.manim.success_color).scale(0.6)
        deepl_desc = Text("Ctrl+C / Ctrl+V → API 批量调用", font=self.get_chinese_font(), color=config.manim.text_color).scale(0.4)
        deepl_detail = Text("2026年初开放 API Key", font=self.get_chinese_font(), color=config.manim.text_color).scale(0.3)
        left = VGroup(mineru, mineru_desc, mineru_detail).arrange(DOWN, buff=0.3)
        right = VGroup(deepl, deepl_desc, deepl_detail).arrange(DOWN, buff=0.3)
        tools = VGroup(left, right).arrange(RIGHT, buff=2.0)
        VGroup(title, tools).arrange(DOWN, buff=0.8).center()
        self.play(Write(title))
        self.wait(3)
        self.play(FadeIn(mineru), FadeIn(mineru_desc))
        self.wait(8)
        self.play(FadeIn(mineru_detail))
        self.wait(10)
        self.play(FadeIn(deepl), FadeIn(deepl_desc))
        self.wait(9)
        self.play(FadeIn(deepl_detail))
        self.wait(13)
        
        try:
            barrier_img = ImageMobject("assets/images/extruder/compuplast_barrier_screw_small.png")
            barrier_img.scale_to_fit_width(4)
            barrier_img.to_edge(LEFT, buff=0.5).shift(DOWN * 0.3)
            mixing_img = ImageMobject("assets/images/extruder/compuplast_mixing_small.png")
            mixing_img.scale_to_fit_width(4)
            mixing_img.to_edge(RIGHT, buff=0.5).shift(DOWN * 0.3)
            self.play(FadeIn(barrier_img), FadeIn(mixing_img))
            self.wait(5)
        except:
            pass
        
        step1 = Text("PDF → LaTeX + 表格 + 图片", font=self.get_chinese_font(), color=config.manim.warning_color).scale(0.35)
        step2 = Text("Ctrl+C → Ctrl+V × 无数次", font=self.get_chinese_font(), color=config.manim.warning_color).scale(0.35)
        step3 = Text("API 批量调用 · 速度陡增", font=self.get_chinese_font(), color=config.manim.warning_color).scale(0.35)
        steps = VGroup(step1, step2, step3).arrange(DOWN, buff=0.3).to_edge(DOWN, buff=1.0)
        self.play(FadeIn(step1))
        self.wait(4)
        self.play(FadeIn(step2))
        self.wait(4)
        self.play(FadeIn(step3))
        self.wait(2)


class ExtruderTimelineScene(BaseScene):
    """翻译历程时间线"""
    def construct(self):
        title = self.create_title("三年时间线").to_edge(UP)
        events = [
            ("2023.9", "项目启动"),
            ("2024", "沉寂期"),
            ("2025 初", "第3-5章密集提交"),
            ("2026 初", "DeepL API 开放"),
            ("2026.8", "trans_end"),
            ("2026.9", "收尾校译"),
        ]
        items = []
        for date_str, desc in events:
            d = Text(date_str, font=self.get_code_font(), color=config.manim.accent_color).scale(0.4)
            t = Text(desc, font=self.get_chinese_font(), color=config.manim.text_color).scale(0.35)
            items.append(VGroup(d, t).arrange(RIGHT, buff=0.3))
        timeline = VGroup(*items).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        VGroup(title, timeline).arrange(DOWN, buff=0.5).center()
        self.play(Write(title))
        self.wait(3)
        for i, item in enumerate(items):
            self.play(FadeIn(item, shift=RIGHT * 0.3), run_time=0.8)
            self.wait(6)
        
        line = DashedLine(
            start=items[0].get_left() + LEFT * 0.2,
            end=items[-1].get_left() + LEFT * 0.2,
            color=config.manim.text_color,
            stroke_width=1
        )
        self.play(Create(line))
        self.wait(5)


class ExtruderTechStackScene(BaseScene):
    """技术栈：Sphinx + MyST + ReadTheDocs"""
    def construct(self):
        title = self.create_title("技术栈").to_edge(UP)
        techs = [
            ("Sphinx 7.1.2", config.manim.accent_color),
            ("MyST Markdown", config.manim.success_color),
            ("sphinx-rtd-theme", config.manim.warning_color),
            ("ReadTheDocs", config.manim.accent_color),
        ]
        items = []
        for name, color in techs:
            t = Text(name, font=self.get_code_font(), color=color).scale(0.5)
            items.append(t)
        grid = VGroup(*items).arrange_in_grid(rows=2, cols=2, buff=0.6)
        VGroup(title, grid).arrange(DOWN, buff=0.8).center()
        self.play(Write(title))
        self.wait(3)
        for i, item in enumerate(items):
            self.play(FadeIn(item, shift=UP * 0.2), run_time=0.6)
            self.wait(5)
        
        stats = VGroup(
            Text("约 16,000 行", font=self.get_chinese_font(), color=config.manim.text_color).scale(0.35),
            Text("12 章正文 + 附录 + 索引", font=self.get_chinese_font(), color=config.manim.text_color).scale(0.35),
            Text("700+ 张图片", font=self.get_chinese_font(), color=config.manim.text_color).scale(0.35),
        ).arrange(DOWN, buff=0.25).to_edge(DOWN, buff=1.0)
        self.play(FadeIn(stats, shift=UP * 0.2))
        self.wait(5)
        
        try:
            film_die_img = ImageMobject("assets/images/extruder/eta_7layer_small.jpg")
            film_die_img.scale_to_fit_width(5)
            film_die_img.to_edge(LEFT, buff=0.8).shift(UP * 0.5)
            self.play(FadeIn(film_die_img))
            self.wait(4)
        except:
            pass
        
        env = VGroup(
            Text("Ubuntu 22.04 · Python 3.10", font=self.get_code_font(), color=config.manim.success_color).scale(0.3),
            Text("自动构建 · 自动发布", font=self.get_chinese_font(), color=config.manim.text_color).scale(0.3),
        ).arrange(DOWN, buff=0.2).to_edge(DOWN, buff=0.5)
        self.play(FadeIn(env, shift=UP * 0.2))
        self.wait(6)


class ExtruderProofreadingScene(BaseScene):
    """校译：术语修正"""
    def construct(self):
        title = self.create_title("校译").to_edge(UP)
        before1 = Text("模具", font=self.get_chinese_font(), color=config.manim.error_color).scale(0.7)
        arrow1 = Text("→", font=self.get_code_font(), color=config.manim.text_color).scale(0.7)
        after1 = Text("模头", font=self.get_chinese_font(), color=config.manim.success_color).scale(0.7)
        row1 = VGroup(before1, arrow1, after1).arrange(RIGHT, buff=0.4)
        before2 = Text("\\mathbf", font=self.get_code_font(), color=config.manim.error_color).scale(0.6)
        arrow2 = Text("→", font=self.get_code_font(), color=config.manim.text_color).scale(0.7)
        after2 = Text("\\mathrm", font=self.get_code_font(), color=config.manim.success_color).scale(0.6)
        row2 = VGroup(before2, arrow2, after2).arrange(RIGHT, buff=0.4)
        fixes = VGroup(row1, row2).arrange(DOWN, buff=0.6)
        VGroup(title, fixes).arrange(DOWN, buff=0.8).center()
        self.play(Write(title))
        self.wait(3)
        self.play(FadeIn(before1), FadeIn(arrow1), FadeIn(after1))
        self.wait(8)
        self.play(FadeIn(before2), FadeIn(arrow2), FadeIn(after2))
        self.wait(8)
        
        more = VGroup(
            Text("挤出 / 挤压 混用", font=self.get_chinese_font(), color=config.manim.warning_color).scale(0.35),
            Text("图片路径反向 → 相对路径", font=self.get_chinese_font(), color=config.manim.warning_color).scale(0.35),
            Text("52 条交叉引用警告清零", font=self.get_chinese_font(), color=config.manim.warning_color).scale(0.35),
            Text("附录 E 47 条表格链接打通", font=self.get_chinese_font(), color=config.manim.warning_color).scale(0.35),
        ).arrange(DOWN, buff=0.3).to_edge(DOWN, buff=0.8)
        self.play(FadeIn(more, shift=UP * 0.2))
        self.wait(6)
        
        conclusion = Text("单看都小，连起来却是几十上百处", font=self.get_chinese_font(), color=config.manim.accent_color).scale(0.4)
        conclusion.to_edge(DOWN, buff=0.3)
        self.play(FadeIn(conclusion))
        self.wait(5)
        
        try:
            die_img = ImageMobject("assets/images/extruder/eta_bfws_small.jpg")
            die_img.scale_to_fit_width(4)
            die_img.to_corner(DOWN + RIGHT, buff=0.5)
            self.play(FadeIn(die_img))
            self.wait(3)
        except:
            pass


class ExtruderAccessScene(BaseScene):
    """访问方式：免费在线阅读 + GitHub"""
    def construct(self):
        title = self.create_title("免费在线阅读").to_edge(UP)

        # ---- 浏览器窗口 mockup ----
        win_w, win_h, bar_h = 6.2, 4.6, 0.45
        img_w = 5.9
        win = RoundedRectangle(
            width=win_w, height=win_h, corner_radius=0.12,
            fill_color="#161b22", fill_opacity=1,
            stroke_color="#3d444d", stroke_width=1.5
        ).center()
        bar = Rectangle(width=win_w, height=bar_h, fill_color="#21262d", fill_opacity=1, stroke_width=0)
        bar.move_to(win.get_top() + DOWN * bar_h / 2)
        dots = VGroup(*[
            Circle(radius=0.05, fill_color=c, fill_opacity=1, stroke_width=0)
            for c in ("#ff5f56", "#ffbd2e", "#27ca4f")
        ]).arrange(RIGHT, buff=0.08).move_to(bar.get_left() + RIGHT * 0.4)

        url_rtd = Text(
            "extruder-principles-and-operation.readthedocs.io",
            font=self.get_code_font(), color="#8b949e", font_size=13
        ).move_to(bar)
        url_gh = Text(
            "github.com/lybhb8/Extruder-Principles-and-Operation",
            font=self.get_code_font(), color="#8b949e", font_size=13
        ).move_to(bar)

        content_center = win.get_center() + DOWN * bar_h / 2

        def load_frames(prefix):
            return [
                ImageMobject(f"assets/images/extruder/browser/{prefix}_f{i}.png")
                .scale_to_fit_width(img_w).move_to(content_center)
                for i in range(6)
            ]

        rtd_frames = load_frames("rtd")
        gh_frames = load_frames("gh")

        url_display = Text(
            "extruder-principles-and-operation.readthedocs.io",
            font=self.get_code_font(), color=config.manim.accent_color
        ).scale(0.36)
        note = Text(
            "不需要注册 · 不需要付费 · 浏览器打开就是",
            font=self.get_chinese_font(), color=config.manim.text_color
        ).scale(0.36)
        url_display.next_to(win, DOWN, buff=0.4)
        note.next_to(url_display, DOWN, buff=0.28)

        github_box = VGroup(
            Text("GitHub 仓库", font=self.get_chinese_font(), color=config.manim.warning_color).scale(0.36),
            Text("github.com/lybhb8/Extruder-Principles-and-Operation",
                 font=self.get_code_font(), color=config.manim.success_color).scale(0.32),
            Text("GPL-3.0 开源", font=self.get_code_font(), color=config.manim.warning_color).scale(0.32),
        ).arrange(DOWN, buff=0.2).next_to(win, DOWN, buff=0.4)

        def cycle_frames(frames, hold=0.8):
            self.play(FadeIn(frames[0], run_time=0.4))
            self.wait(hold)
            prev = frames[0]
            for f in frames[1:]:
                self.play(FadeOut(prev, run_time=0.12), FadeIn(f, run_time=0.12))
                self.wait(hold)
                prev = f
            return prev

        # ---- 在线阅读（ReadTheDocs 实际滚动） ----
        self.play(Write(title, run_time=1))
        self.wait(0.5)
        self.play(FadeIn(win), FadeIn(bar), FadeIn(dots), FadeIn(url_rtd), run_time=0.6)
        last_rtd = cycle_frames(rtd_frames, hold=0.8)
        self.wait(1.0)

        self.play(FadeIn(url_display, shift=UP * 0.2), run_time=0.5)
        self.wait(0.8)
        self.play(FadeIn(note, shift=UP * 0.2), run_time=0.5)
        self.wait(1.2)

        # ---- 切换到 GitHub 仓库 ----
        self.play(FadeOut(last_rtd), FadeOut(url_rtd), run_time=0.3)
        self.play(FadeIn(url_gh), run_time=0.3)
        last_gh = cycle_frames(gh_frames, hold=0.8)
        self.play(FadeOut(url_display), FadeOut(note), run_time=0.3)
        self.play(FadeIn(github_box, shift=UP * 0.2), run_time=0.5)
        self.wait(1.5)
        self.wait(2)


class ExtruderOutroScene(BaseScene):
    """结尾：开源精神 + 访问地址 + GitHub"""
    def construct(self):
        title = self.create_title("开源精神").to_edge(UP)
        line1 = Text("三年 · 五十二次提交 · 一部经典的中文版", font=self.get_chinese_font(), color=config.manim.text_color).scale(0.45)
        line2 = Text("它还很年轻，也还有很长的路要走", font=self.get_chinese_font(), color=config.manim.accent_color).scale(0.5)
        line3 = Text("欢迎 Issue & Pull Request", font=self.get_code_font(), color=config.manim.success_color).scale(0.4)
        VGroup(title, line1, line2, line3).arrange(DOWN, buff=0.6).center()
        self.play(Write(title))
        self.play(FadeIn(line1, shift=UP * 0.2))
        self.wait(5)
        self.play(FadeIn(line2, shift=UP * 0.2))
        self.wait(6)
        self.play(FadeIn(line3, shift=UP * 0.2))
        self.wait(3)
        
        VGroup(title, line1, line2, line3).animate.shift(UP * 2).set_opacity(0.3)
        self.wait(1)
        
        url_label = Text("在线阅读", font=self.get_chinese_font(), color=config.manim.warning_color).scale(0.4)
        url = Text("extruder-principles-and-operation.readthedocs.io", font=self.get_code_font(), color=config.manim.accent_color).scale(0.45)
        url_box = VGroup(url_label, url).arrange(DOWN, buff=0.2)
        
        github_label = Text("GitHub 仓库", font=self.get_chinese_font(), color=config.manim.warning_color).scale(0.4)
        github = Text("github.com/lybhb8/Extruder-Principles-and-Operation", font=self.get_code_font(), color=config.manim.success_color).scale(0.4)
        github_box = VGroup(github_label, github).arrange(DOWN, buff=0.2)
        
        urls = VGroup(url_box, github_box).arrange(DOWN, buff=0.8).move_to(ORIGIN)
        
        self.play(FadeIn(urls, shift=UP * 0.3), run_time=1.5)
        self.wait(8)


# ============================================================
# Agnes AI Tutorial — 9 scenes
# ============================================================

class AgnesIntroScene(BaseScene):
    """【Agnes AI 是什么】- title card + capability chips + free banner."""

    def construct(self):
        self.record_visual_text("Agnes AI 免费接入教程")
        title = self.create_title("Agnes AI 免费接入教程", scale=0.85)
        self.record_visual_text("副标题: Claude Code · Opencode · Codex · Hermes 四端免费接入")
        subtitle = self.create_subtitle("Claude Code · Opencode · Codex · Hermes 四端免费接入")
        VGroup(title, subtitle).arrange(DOWN, buff=0.5).to_edge(UP, buff=0.5)
        self.play(Write(title, run_time=2))
        self.play(FadeIn(subtitle, shift=UP * 0.3), run_time=1)
        self.wait(0.5)

        from scenes.ui_components import HighlightEffect
        title_highlight = HighlightEffect(title, color=config.manim.accent_color, buff=0.2)
        title_highlight.animate_in(self, run_time=0.6)
        title_highlight.pulse_animation(self, runs=2, run_time_per=0.5)
        self.wait(0.5)

        self.record_visual_text("能力芯片: 文本 / 图片 / 视频")
        chips = VGroup(
            self._chip("文本", config.manim.accent_color),
            self._chip("图片", config.manim.success_color),
            self._chip("视频", config.manim.warning_color),
        ).arrange(RIGHT, buff=0.8)
        chips.move_to(ORIGIN).shift(UP * 0.4)
        self.play(LaggedStart(
            *[FadeIn(c, shift=UP * 0.3) for c in chips], lag_ratio=0.4, run_time=1.5
        ))
        self.wait(0.5)

        chip_highlights = [HighlightEffect(c, color=config.manim.success_color, buff=0.15) for c in chips]
        for ch in chip_highlights:
            ch.animate_in(self, run_time=0.3)
        self.wait(0.5)

        self.record_visual_text("底部提示: 无限期免费 · 不绑卡 · 无 Token 上限")
        banner = self._chip("无限期免费 · 不绑卡 · 无 Token 上限", config.manim.success_color)
        banner.scale(0.9).to_edge(DOWN, buff=0.8)
        self.play(FadeIn(banner, shift=UP * 0.2), run_time=0.8)
        self.wait(0.3)

        banner_highlight = HighlightEffect(banner, color=config.manim.success_color, buff=0.2)
        banner_highlight.animate_in(self, run_time=0.4)
        banner_highlight.pulse_animation(self, runs=3, run_time_per=0.6)
        self.wait(0.5)

        self.record_visual_text("模态详情: 文本对话 / 图片生成 / 视频生成")
        modals = VGroup(
            self._chip("文本对话", config.manim.accent_color),
            self._chip("图片生成", config.manim.success_color),
            self._chip("视频生成", config.manim.warning_color),
        ).arrange(RIGHT, buff=0.6).move_to(ORIGIN).shift(DOWN * 0.15)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.2) for m in modals], lag_ratio=0.4, run_time=1.2))
        self.wait(0.5)
        self.play(Indicate(modals[1], color=config.manim.success_color), run_time=0.8)

        self.record_visual_text("免费要点: 免绑卡 / 无 Token 上限 / 仅限 RPM")
        free = VGroup(
            self._chip("免绑卡", config.manim.success_color),
            self._chip("无 Token 上限", config.manim.success_color),
            self._chip("仅限 RPM", config.manim.warning_color),
        ).arrange(RIGHT, buff=0.6).move_to(ORIGIN).shift(DOWN * 1.05)
        self.play(LaggedStart(*[FadeIn(f, shift=UP * 0.2) for f in free], lag_ratio=0.4, run_time=1.0))
        self.wait(0.5)
        self._pad_to(41.5, banner)

    def _chip(self, text, color):
        t = Text(text, font=self.get_chinese_font(), color=color, font_size=20, weight=BOLD)
        bg = RoundedRectangle(
            width=t.width + 0.6, height=t.height + 0.35,
            corner_radius=0.15, fill_color=config.manim.terminal_bg,
            fill_opacity=0.95, stroke_color=color, stroke_width=2,
        )
        return VGroup(bg, t)


class AgnesKeyScene(BaseScene):
    """【免费注册获取 Key】- browser mockup + key card + endpoint table + export command."""

    def construct(self):
        self.record_visual_text("注册账号，拿到 API Key")
        title = self.create_title("免费注册获取 Key").to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        from scenes.ui_components import HighlightEffect

        # Show three real screenshots in sequence
        imgs = [
            self.load_screenshot("01_agnes_home.png", max_width=6.5, max_height=4.0),
            self.load_screenshot("02_login.png", max_width=6.5, max_height=4.0),
            self.load_screenshot("03_api_keys.png", max_width=6.5, max_height=4.0),
        ]
        for i, img in enumerate(imgs):
            img.shift(DOWN * 0.3)
            if i == 0:
                self.play(FadeIn(img, shift=UP * 0.2), run_time=0.6)
            else:
                self.play(FadeOut(self.old_img, run_time=0.3), run_time=0.3)
                self.play(FadeIn(img, shift=UP * 0.2), run_time=0.6)
            self.wait(0.3)
            self.old_img = img

        win_highlight = HighlightEffect(img, color=config.manim.accent_color, buff=0.15)
        win_highlight.animate_in(self, run_time=0.4)
        self.wait(0.5)

        self.record_visual_text("密钥卡片: sk-xxxxxxxx（只展示一次）")
        key_card = self._key_card("sk-agnes2026freekey001")
        key_card.next_to(img, RIGHT, buff=0.5).shift(UP * 0.5)
        self.play(FadeIn(key_card, shift=RIGHT * 0.3), run_time=0.5)

        key_highlight = HighlightEffect(key_card, color=config.manim.warning_color, buff=0.1)
        key_highlight.animate_in(self, run_time=0.4)
        key_highlight.pulse_animation(self, runs=2, run_time_per=0.5)
        self.wait(0.5)

        self.record_visual_text("线路表: 国际主 / 国际备用 / 国内")
        table_data = [
            ["线路", "Endpoint"],
            ["国际主站", "https://apihub.agnes-ai.com/v1"],
            ["国际备用", "https://apihub.agnes-ai.cn/v1"],
            ["国内线路", "https://api.agnes-ai.cn/v1"],
        ]
        tbl = Table(
            table_data,
            include_outer_lines=True,
            line_config={"stroke_width": 1, "color": config.manim.accent_color},
            element_to_mobject_config={"font_size": 13, "font": self.get_chinese_font(), "color": config.manim.text_color},
            h_buff=1.0, v_buff=0.2,
        )
        self.apply_row_colors(tbl, n_rows=4, n_cols=2)
        tbl.next_to(img, DOWN, buff=0.4)
        self.play(FadeIn(tbl, shift=UP * 0.2), run_time=0.8)
        self.wait(0.5)

        tbl_highlight = HighlightEffect(tbl, color=config.manim.accent_color, buff=0.1)
        tbl_highlight.animate_in(self, run_time=0.3)
        self.wait(0.5)

        self.record_visual_text("export AGNES_API_KEY=\"sk-…\"")
        term = TerminalSimulator(title="terminal — bash", width=10, height=1.6, font_size=13)
        term.build()
        term.terminal.next_to(tbl, DOWN, buff=0.4)
        self.play(FadeIn(term.terminal, run_time=0.4))
        self.wait(0.3)
        term.add_command(self, "user@mac:~$ ", 'export AGNES_API_KEY="sk-agnes2026freekey001"', wait=0.5)
        term.add_line(self, "✓ exported — 重启终端后生效", color=config.manim.success_color, lag=0.0, run_time=0.5, font_size=13)

        term_highlight = HighlightEffect(term.terminal, color=config.manim.success_color, buff=0.1)
        term_highlight.animate_in(self, run_time=0.3)
        term_highlight.pulse_animation(self, runs=2, run_time_per=0.4)
        self.wait(0.5)

        self.play(Indicate(key_card, color=config.manim.success_color), run_time=0.8)
        self.wait(0.5)
        self._pad_to(42.4, key_card)

    def _key_card(self, key):
        t = Text(key, font=self.get_code_font(), color=config.manim.success_color, font_size=18)
        bg = RoundedRectangle(width=t.width + 0.8, height=t.height + 0.4, corner_radius=0.12,
                               fill_color=config.manim.terminal_bg, fill_opacity=0.95,
                               stroke_color=config.manim.success_color, stroke_width=2)
        warn = Text("⚠ 只显示一次！", font=self.get_chinese_font(),
                     color=config.manim.warning_color, font_size=12)
        warn.next_to(VGroup(bg, t), DOWN, buff=0.15)
        return VGroup(bg, t, warn)


class AgnesModelsScene(BaseScene):
    """【模型一览】- 5-row model table with zebra stripes and highlight."""

    def construct(self):
        self.record_visual_text("模型一览")
        title = self.create_title("模型一览").to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        models = [
            ["agnes-2.5-flash", "文本+视觉", "512K · 工具调用 · 深度思考", config.manim.success_color],
            ["agnes-2.0-flash", "文本+视觉", "1M 上下文", config.manim.accent_color],
            ["agnes-1.5-flash", "轻量多模态", "快速响应", config.manim.text_color],
            ["agnes-image-2.1-flash", "图片", "最高4K出图/编辑", config.manim.warning_color],
            ["agnes-video-v2.0", "视频", "文生视频 ~18s 异步轮询", config.manim.warning_color],
        ]
        self.record_visual_text("模型表: 模型 / 类型 / 亮点")
        headers = ["模型", "类型", "亮点"]
        rows = [[m[0], m[1], m[2]] for m in models]
        tbl = Table(
            [headers] + rows,
            include_outer_lines=True,
            line_config={"stroke_width": 1, "color": config.manim.accent_color},
            element_to_mobject_config={"font_size": 14, "font": self.get_chinese_font(), "color": config.manim.text_color},
            h_buff=0.8, v_buff=0.2,
        )
        self.apply_row_colors(tbl, n_rows=6, n_cols=3)
        for col in range(1, 4):
            tbl.get_cell((2, col)).set_fill(config.manim.success_color, opacity=0.18)
        tbl.scale_to_fit_width(12).center().shift(DOWN * 0.2)

        self.play(Create(tbl), run_time=2)
        self.wait(0.8)
        for i in range(1, 6):
            row_rect = tbl.get_rows()[i]
            self.play(FadeIn(row_rect, shift=RIGHT * 0.2), run_time=0.4)
            self.wait(0.3)
        self.record_visual_text("推荐: agnes-2.5-flash 编码主力")
        row_hl = SurroundingRectangle(tbl.get_rows()[1], color=config.manim.success_color, buff=0.06, stroke_width=2)
        self.play(Create(row_hl), run_time=0.5)
        self.wait(0.6)
        self.record_visual_text("图片/视频模型用法一致，仅换模型名")
        note = Text("图片/视频模型用法一致 · 换模型名即可", font=self.get_chinese_font(), color=config.manim.warning_color, font_size=14)
        note.next_to(tbl, DOWN, buff=0.3)
        self.play(FadeIn(note, shift=UP * 0.2), run_time=0.5)
        self.wait(1.2)
        self._pad_to(44.5, tbl)


class AgnesCCSwitchScene(BaseScene):
    """【CC-Switch 配置】- flow diagram + install hint + toggle mockup."""

    def construct(self):
        self.record_visual_text("CC-Switch 协议翻译代理")
        title = self.create_title("CC-Switch 配置（协议翻译代理）").to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        self.record_visual_text("流程图: Claude Code / Codex -> CC-Switch -> Agnes API")
        nodes = VGroup(
            self._node("Claude Code", config.manim.accent_color),
            self._node("Codex", config.manim.warning_color),
            self._node("CC-Switch", config.manim.success_color),
            self._node("Agnes API", config.manim.success_color),
        ).arrange(RIGHT, buff=0.4).move_to(ORIGIN).shift(UP * 0.6)
        self.play(LaggedStart(
            *[FadeIn(n, shift=UP * 0.2) for n in nodes[:2]], lag_ratio=0.5, run_time=0.8
        ))
        self.play(FadeIn(nodes[2], shift=UP * 0.2), run_time=0.5)
        self.play(FadeIn(nodes[3], shift=UP * 0.2), run_time=0.5)
        a1 = CurvedArrow(nodes[0].get_right(), nodes[2].get_left(), color=config.manim.text_color, stroke_width=2)
        a2 = CurvedArrow(nodes[1].get_right(), nodes[2].get_left(), color=config.manim.text_color, stroke_width=2)
        a3 = CurvedArrow(nodes[2].get_right(), nodes[3].get_left(), color=config.manim.success_color, stroke_width=2)
        self.play(Indicate(a1), Indicate(a2), run_time=0.6)
        self.play(Flash(a3, flash_radius=0.25, color=config.manim.success_color), run_time=0.6)
        self.wait(0.5)

        self.record_visual_text("安装: github.com/farion1231/cc-switch Releases")
        install_chip = self._chip("下载: github.com/farion1231/cc-switch Releases", config.manim.warning_color)
        install_chip.to_edge(DOWN, buff=1.2)
        self.play(FadeIn(install_chip, shift=UP * 0.2), run_time=0.5)
        self.wait(0.8)

        self.record_visual_text("CC-Switch 配置界面: 主开关 / 添加供应商 / 模型映射 / 连接成功 / 完成")
        ss_imgs = [
            self.load_screenshot("04_cc_switch.png", max_width=6.0, max_height=3.6),
            self.load_screenshot("05_add_supplier_form.png", max_width=6.0, max_height=3.6),
            self.load_screenshot("06_model_mapping.png", max_width=6.0, max_height=3.6),
            self.load_screenshot("07_connection_success.png", max_width=6.0, max_height=3.6),
            self.load_screenshot("08_config_complete.png", max_width=6.0, max_height=3.6),
        ]
        ss_group = Group(*ss_imgs).arrange(RIGHT, buff=0.3).next_to(nodes, DOWN, buff=0.5)
        for i, img in enumerate(ss_imgs):
            if i == 0:
                self.play(FadeIn(img, shift=RIGHT * 0.2), run_time=0.5)
            else:
                self.play(FadeIn(ss_imgs[i], shift=RIGHT * 0.2), run_time=0.4)
            self.wait(0.35)
        self.old_ss = ss_imgs[-1]

        self.record_visual_text("装完首次打开需彻底重启终端")
        tip = Text("装完首次打开 → 彻底重启终端", font=self.get_chinese_font(), color=config.manim.warning_color, font_size=14)
        tip.next_to(install_chip, UP, buff=0.1)
        self.play(FadeIn(tip, shift=UP * 0.2), run_time=0.5)
        self.wait(0.8)
        self._pad_to(50.3, ss_imgs[0])

    def _node(self, text, color):
        t = Text(text, font=self.get_chinese_font(), color=color, font_size=16, weight=BOLD)
        bg = RoundedRectangle(width=t.width + 0.6, height=t.height + 0.35, corner_radius=0.15,
                               fill_color=config.manim.terminal_bg, fill_opacity=0.95,
                               stroke_color=color, stroke_width=2)
        return VGroup(bg, t)

    def _chip(self, text, color):
        t = Text(text, font=self.get_chinese_font(), color=color, font_size=14)
        bg = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.25, corner_radius=0.1,
                               fill_color=config.manim.terminal_bg, fill_opacity=0.9,
                               stroke_color=color, stroke_width=1.5)
        return VGroup(bg, t)


class AgnesClaudeCodeScene(BaseScene):
    """【Claude Code 接入】- flow + config form mockup + param chips + checklist."""

    def construct(self):
        self.record_visual_text("Claude Code 接入（CC-Switch 协议翻译）")
        title = self.create_title("Claude Code 接入（CC-Switch 协议翻译）").to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        from scenes.ui_components import HighlightEffect

        self.record_visual_text("流程图: Claude Code(Anthropic) ✗ -> CC-Switch -> ✓ Agnes")
        cc = self._node("Claude Code", config.manim.error_color)
        ag = self._node("Agnes API", config.manim.success_color)
        VGroup(cc, ag).arrange(RIGHT, buff=2.6).move_to(ORIGIN).shift(UP * 1.5)
        cc_to_ag = CurvedArrow(cc.get_right(), ag.get_left(), color=config.manim.error_color, stroke_width=2)
        cross = Text("✗", font=self.get_code_font(), color=config.manim.error_color, font_size=20)
        cross.move_to(cc_to_ag.get_center())
        self.play(FadeIn(cc), FadeIn(ag), run_time=0.5)
        self.play(Create(cc_to_ag), FadeIn(cross), run_time=0.5)
        self.wait(0.3)

        cc_highlight = HighlightEffect(cc, color=config.manim.error_color, buff=0.15)
        cc_highlight.animate_in(self, run_time=0.3)
        self.wait(0.5)

        cs = self._node("CC-Switch", config.manim.accent_color)
        cs.move_to(ORIGIN).shift(UP * 0.4)
        a1 = CurvedArrow(cc.get_bottom(), cs.get_left(), color=config.manim.success_color, stroke_width=2)
        a2 = CurvedArrow(cs.get_right(), ag.get_bottom(), color=config.manim.success_color, stroke_width=2)
        check = Text("✓", font=self.get_code_font(), color=config.manim.success_color, font_size=20)
        check.move_to(a2.get_center())
        self.play(FadeIn(cs, shift=LEFT * 0.3), run_time=0.4)
        self.play(Indicate(a1), Indicate(a2), run_time=0.6)
        self.play(FadeIn(check), run_time=0.3)

        cs_highlight = HighlightEffect(cs, color=config.manim.accent_color, buff=0.15)
        cs_highlight.animate_in(self, run_time=0.3)
        cs_highlight.pulse_animation(self, runs=2, run_time_per=0.4)
        self.wait(0.5)

        ag_highlight = HighlightEffect(ag, color=config.manim.success_color, buff=0.15)
        ag_highlight.animate_in(self, run_time=0.3)
        self.wait(0.5)

        self.record_visual_text("配置表: 添加供应商 / 模型映射 / 连接成功")
        form_imgs = [
            self.load_screenshot("05_add_supplier_form.png", max_width=5.8, max_height=3.4),
            self.load_screenshot("06_model_mapping.png", max_width=5.8, max_height=3.4),
            self.load_screenshot("07_connection_success.png", max_width=5.8, max_height=3.4),
        ]
        form = Group(*form_imgs).arrange(RIGHT, buff=0.25).move_to(LEFT * 4.4).shift(DOWN * 0.1)
        for i, img in enumerate(form_imgs):
            if i == 0:
                self.play(FadeIn(img, shift=DOWN * 0.2), run_time=0.5)
            else:
                self.play(FadeIn(img, shift=RIGHT * 0.2), run_time=0.4)
            self.wait(0.3)
        self.old_form = form_imgs[-1]

        form_highlight = HighlightEffect(form_imgs[-1], color=config.manim.warning_color, buff=0.1)
        form_highlight.animate_in(self, run_time=0.4)
        self.wait(0.5)

        self.record_visual_text("参数: allowed_openai_params + drop_params")
        chips = VGroup(
            self._chip('allowed_openai_params: ["thinking","context_management"]', config.manim.accent_color),
            self._chip('litellm_settings: {drop_params: true}', config.manim.warning_color),
        ).arrange(DOWN, buff=0.2).next_to(form, DOWN, buff=0.25)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT*0.2) for c in chips], lag_ratio=0.5, run_time=0.8))
        self.wait(0.5)

        chips_highlight = HighlightEffect(chips, color=config.manim.accent_color, buff=0.1)
        chips_highlight.animate_in(self, run_time=0.3)
        self.wait(0.5)

        self.record_visual_text("步骤: 本地路由->启用供应商->重启终端->claude")
        steps = VGroup(
            Text("1. 开启本地路由 Claude 开关", font=self.get_chinese_font(), font_size=14, color=config.manim.text_color),
            Text("2. 启用 Agnes 供应商", font=self.get_chinese_font(), font_size=14, color=config.manim.text_color),
            Text("3. 彻底重启终端", font=self.get_chinese_font(), font_size=14, color=config.manim.warning_color),
            Text("4. 输入 claude", font=self.get_chinese_font(), font_size=14, color=config.manim.success_color),
        ).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        steps.move_to(RIGHT * 4.4).shift(DOWN * 0.4)
        self.play(LaggedStart(*[FadeIn(s, shift=LEFT*0.2) for s in steps], lag_ratio=0.3, run_time=0.8))
        for s in steps:
            self.play(Indicate(s, color=config.manim.success_color), run_time=0.5)
            self.wait(0.2)
        self.record_visual_text("模型映射与 drop_params 过滤提示")
        map_chip = self._chip("Sonnet → 你配置的模型（2.5-flash）", config.manim.success_color)
        drop_chip = self._chip("Unknown parameter → drop_params 过滤", config.manim.warning_color)
        map_group = VGroup(map_chip, drop_chip).arrange(DOWN, buff=0.2).move_to(ORIGIN).shift(DOWN * 2.5)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in map_group], lag_ratio=0.5, run_time=1.0))
        self.wait(1.0)
        for _ in range(2):
            for s in steps:
                self.play(Indicate(s, color=config.manim.accent_color), run_time=0.4)
                self.wait(0.15)
        self.play(Flash(steps[3], flash_radius=0.25, color=config.manim.success_color), run_time=0.6)
        self._pad_to(68.5, form_imgs[0])

    def _node(self, text, color):
        t = Text(text, font=self.get_chinese_font(), color=color, font_size=16, weight=BOLD)
        bg = RoundedRectangle(width=t.width + 0.6, height=t.height + 0.35, corner_radius=0.15,
                               fill_color=config.manim.terminal_bg, fill_opacity=0.95,
                               stroke_color=color, stroke_width=2)
        return VGroup(bg, t)

    def _chip(self, text, color):
        t = Text(text, font=self.get_code_font(), color=color, font_size=13)
        bg = RoundedRectangle(width=t.width + 0.4, height=t.height + 0.25, corner_radius=0.1,
                               fill_color=config.manim.terminal_bg, fill_opacity=0.9,
                               stroke_color=color, stroke_width=1.5)
        return VGroup(bg, t)


class AgnesOpencodeScene(BaseScene):
    """【Opencode 接入】- opencode.json code block + terminal models list."""

    def construct(self):
        self.record_visual_text("Opencode 接入（直接配置，最简单）")
        title = self.create_title("Opencode 接入（直接配置，最简单）").to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        self.record_visual_text("opencode.json: provider agnes with @ai-sdk/openai-compatible")
        code_lines = [
            '{',
            '  "model": "agnes/agnes-2.5-flash",',
            '  "provider": {',
            '    "agnes": {',
            '      "npm": "@ai-sdk/openai-compatible",',
            '      "options": {',
            '        "baseURL": "https://apihub.agnes-ai.com/v1",',
            '        "apiKey": "{env:AGNES_API_KEY}"',
            '      },',
            '      "models": {',
            '        "agnes-2.5-flash": true',
            '      }',
            '    }',
            '  }',
            '}',
        ]
        code_group = VGroup()
        for i, line in enumerate(code_lines):
            t = Text(line, font=self.get_code_font(), color=config.manim.text_color, font_size=14)
            code_group.add(t)
        code_group.arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        code_bg = RoundedRectangle(
            width=code_group.width + 0.5, height=code_group.height + 0.3,
            corner_radius=0.1, fill_color=config.manim.terminal_bg,
            fill_opacity=1, stroke_color=config.manim.accent_color, stroke_width=1,
        )
        code_bg.move_to(code_group.get_center())
        code_block = VGroup(code_bg, code_group).scale(0.7).center().shift(UP * 0.3)
        self.play(FadeIn(code_block, shift=UP * 0.2), run_time=0.8)
        self.wait(0.5)
        # Highlight baseURL line (index 6)
        hl = SurroundingRectangle(code_group[6], color=config.manim.warning_color, buff=0.05, stroke_width=2)
        self.play(Create(hl), run_time=0.4)
        self.wait(0.8)

        self.record_visual_text("/models 列出 agnes-2.5-flash")
        term = TerminalSimulator(title="opencode — terminal", width=9, height=2.2, font_size=12)
        term.build()
        term.terminal.next_to(code_block, DOWN, buff=0.5)
        self.play(FadeIn(term.terminal, run_time=0.4))
        self.wait(0.3)
        term.add_command(self, "user@mac:~$ ", "/models", wait=0.3)
        term.add_line(self, "Available models:", color="#8b949e", lag=0.0, run_time=0.5)
        term.add_line(self, "  agnes/agnes-2.5-flash  <- highlighted",
                      color=config.manim.success_color, lag=0.0, run_time=0.6, font_size=12)
        hl_npm = SurroundingRectangle(code_group[4], color=config.manim.success_color, buff=0.05, stroke_width=2)
        self.play(Create(hl_npm), run_time=0.4)
        self.wait(0.5)
        self.record_visual_text("AGNES_API_KEY 已在 Key 章节导出")
        tip = Text("AGNES_API_KEY 已 export", font=self.get_chinese_font(), color=config.manim.warning_color, font_size=14)
        tip.move_to(LEFT * 5.9 + DOWN * 2.6)
        self.play(FadeIn(tip, shift=UP * 0.2), run_time=0.5)
        self.wait(1.2)
        self.play(Indicate(code_group[10], color=config.manim.success_color), run_time=0.7)
        self._pad_to(46.0, code_block)


class AgnesCodexScene(BaseScene):
    """【Codex 接入】- flow diagram + warning + three toggles + restart alert."""

    def construct(self):
        self.record_visual_text("Codex 接入（CC-Switch 协议翻译）")
        title = self.create_title("Codex 接入（CC-Switch 协议翻译）").to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        self.record_visual_text("流程图: Codex(Responses API) -> CC-Switch -> Agnes(Chat Completions)")
        codex = self._node("Codex", config.manim.warning_color)
        cc = self._node("CC-Switch", config.manim.accent_color)
        ag = self._node("Agnes", config.manim.success_color)
        VGroup(codex, cc, ag).arrange(RIGHT, buff=0.6).move_to(ORIGIN).shift(UP * 0.7)
        self.play(LaggedStart(
            *[FadeIn(n, shift=UP*0.2) for n in [codex, cc, ag]], lag_ratio=0.4, run_time=0.8
        ))
        a1 = CurvedArrow(codex.get_right(), cc.get_left(), color=config.manim.text_color, stroke_width=2)
        a2 = CurvedArrow(cc.get_right(), ag.get_left(), color=config.manim.success_color, stroke_width=2)
        self.play(Indicate(a1), Indicate(a2), run_time=0.6)
        self.wait(0.5)

        self.record_visual_text("地址只到 /v1，勿拼 /chat/completions")
        warn = self._chip("⚠ 地址只到 /v1，勿拼 /chat/completions", config.manim.error_color)
        warn.to_edge(DOWN, buff=1.6)
        self.play(FadeIn(warn, shift=UP * 0.2), run_time=0.5)
        self.play(Flash(warn, flash_radius=0.3, color=config.manim.error_color), run_time=0.5)
        self.wait(0.8)

        self.record_visual_text("开关: 本地路由映射 / 路由总开关 / Codex 开关")
        toggles = VGroup(
            self._toggle("本地路由映射", True, config.manim.success_color),
            self._toggle("路由总开关", True, config.manim.success_color),
            self._toggle("Codex 开关", True, config.manim.success_color),
        ).arrange(DOWN, buff=0.3).move_to(ORIGIN).shift(DOWN * 0.5)
        self.play(LaggedStart(
            *[FadeIn(t, shift=RIGHT*0.2) for t in toggles], lag_ratio=0.4, run_time=0.8
        ))
        self.wait(1)

        self.record_visual_text("必须彻底重启 Codex（结束进程）")
        alert = Text("⚠ 必须彻底重启 Codex（结束进程），光关窗口没用！",
                     font=self.get_chinese_font(), color=config.manim.error_color, font_size=16, weight=BOLD)
        alert.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(alert, shift=UP * 0.2), run_time=0.5)
        self.record_visual_text("协议翻译: Responses API -> Chat Completions")
        map_chip = self._chip("Responses API → Chat Completions（协议翻译）", config.manim.accent_color)
        map_chip.next_to(VGroup(codex, cc, ag), UP, buff=0.2)
        self.play(FadeIn(map_chip, shift=UP * 0.2), run_time=0.5)
        self.wait(1.0)
        for t in toggles:
            self.play(Indicate(t, color=config.manim.success_color), run_time=0.5)
            self.wait(0.3)
        for _ in range(2):
            for t in toggles:
                self.play(Indicate(t, color=config.manim.accent_color), run_time=0.4)
                self.wait(0.15)
        self.play(Flash(alert, flash_radius=0.4, color=config.manim.error_color), run_time=0.6)
        self.wait(0.8)
        self._pad_to(67.2, toggles)

    def _node(self, text, color):
        t = Text(text, font=self.get_chinese_font(), color=color, font_size=16, weight=BOLD)
        bg = RoundedRectangle(width=t.width + 0.6, height=t.height + 0.35, corner_radius=0.15,
                               fill_color=config.manim.terminal_bg, fill_opacity=0.95,
                               stroke_color=color, stroke_width=2)
        return VGroup(bg, t)

    def _chip(self, text, color):
        t = Text(text, font=self.get_chinese_font(), color=color, font_size=14)
        bg = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.3, corner_radius=0.1,
                               fill_color=config.manim.terminal_bg, fill_opacity=0.9,
                               stroke_color=color, stroke_width=1.5)
        return VGroup(bg, t)

    def _toggle(self, label, on, color):
        t = Text(label, font=self.get_chinese_font(), color=config.manim.text_color, font_size=15)
        dot = Circle(radius=0.12, fill_color=config.manim.terminal_bg, stroke_color=color, stroke_width=2)
        if on:
            dot.set_fill(color)
        thumb = VGroup(
            RoundedRectangle(width=0.7, height=0.3, corner_radius=0.15,
                             fill_color="#30363d", stroke_color="#484f58", stroke_width=1),
            dot,
        ).arrange(RIGHT, buff=0.15).shift(LEFT * 0.2)
        state = Text("ON", font=self.get_code_font(), color=color, font_size=14)
        return VGroup(t, thumb, state).arrange(RIGHT, buff=0.4)


class AgnesHermesScene(BaseScene):
    """【Hermes 接入】- terminal typing 4 commands sequentially then launch."""

    def construct(self):
        self.record_visual_text("Hermes 接入（四条命令）")
        title = self.create_title("Hermes 接入（四条命令）").to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        term = TerminalSimulator(title="hermes — zsh", width=11, height=4.8, font_size=13)
        term.build()
        term.terminal.center().shift(UP * 0.2)
        self.play(FadeIn(term.terminal, run_time=0.5))
        self.wait(0.3)

        commands = [
            'hermes config set model.provider custom',
            'hermes config set model.base_url https://apihub.agnes-ai.com/v1',
            'hermes config set model.api_key sk-...',
            'hermes config set model.default agnes-2.5-flash',
        ]
        prompts = ["user@mac:~$ "] * 4
        for i, (prompt, cmd) in enumerate(zip(prompts, commands)):
            self.record_visual_text(cmd)
            term.add_command(self, prompt, cmd, wait=0.3)
            confirm = f"✓ {cmd.split(' ')[-1]} set"
            term.add_line(self, confirm, color=config.manim.success_color,
                          lag=0.0, run_time=0.5, font_size=12)
            self.wait(0.3)

        self.record_visual_text("hermes -> Agnes 对话成功")
        term.add_command(self, "user@mac:~$ ", "hermes", wait=0.3)
        success_line = term.add_line(self, "✓ Agnes AI connected — agnes-2.5-flash",
                                     color=config.manim.success_color, lag=0.0,
                                     run_time=0.6, font_size=13)
        self.play(Flash(success_line, flash_radius=0.3, color=config.manim.success_color), run_time=0.5)
        self.record_visual_text("四条命令即可接入")
        recap = VGroup(*[
            Text(t, font=self.get_chinese_font(), color=config.manim.success_color, font_size=11)
            for t in ("provider custom", "base_url apihub.agnes-ai.com/v1",
                      "api_key sk-...", "default agnes-2.5-flash")
        ]).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        recap.next_to(term.terminal, DOWN, buff=0.15)
        self.play(LaggedStart(*[FadeIn(r, shift=LEFT*0.2) for r in recap], lag_ratio=0.3, run_time=1.2))
        self.wait(1.0)
        self._pad_to(39.0, term.terminal)


class AgnesOutroScene(BaseScene):
    """【避坑指南与总结】- 2x2 pitfall cards + summary banner + link chips."""

    def construct(self):
        self.record_visual_text("避坑指南与总结")
        title = self.create_title("避坑指南与总结").to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        self.record_visual_text("4 个坑卡片: 只到/v1 / 三个开关全开 / sk开头勿带空格 / 彻底重启进程")
        pitfalls = [
            ("只到 /v1", "Base URL 不要拼 /chat/completions", config.manim.error_color),
            ("三个开关全开", "本地路由映射 + 路由总开关 + 客户端开关", config.manim.warning_color),
            ("sk 开头勿带空格", "复制 Key 不要带前后空格，不加 Bearer", config.manim.accent_color),
            ("彻底重启进程", "光关窗口不算，必须结束进程", config.manim.success_color),
        ]
        positions = [
            LEFT * 2.5 + UP * 1.0,
            RIGHT * 2.5 + UP * 1.0,
            LEFT * 2.5 + DOWN * 0.6,
            RIGHT * 2.5 + DOWN * 0.6,
        ]
        cards = []
        for (ptitle, desc, color), pos in zip(pitfalls, positions):
            cards.append(self._pitfall_card(ptitle, desc, color))
            self.play(FadeIn(cards[-1], shift=UP * 0.3), run_time=0.5)
            self.wait(0.4)

        self.record_visual_text("总结: 四个助手 · 一条 Key · 零成本")
        banner = self._chip("四个助手 · 一条 Key · 零成本", config.manim.success_color)
        banner.scale(1.0).to_edge(DOWN, buff=1.8)
        self.play(FadeIn(banner, shift=UP * 0.2), run_time=0.6)
        self.play(banner.animate.set_opacity(0.6), run_time=0.5)
        self.play(banner.animate.set_opacity(1.0), run_time=0.5)
        self.wait(0.8)

        self.record_visual_text("链接: AgnesAI-Labs/skills · wiki.agnes-ai.com")
        links = VGroup(
            self._chip("AgnesAI-Labs/skills", config.manim.accent_color),
            self._chip("wiki.agnes-ai.com", config.manim.success_color),
        ).arrange(RIGHT, buff=0.5).to_edge(DOWN, buff=0.8)
        self.play(FadeIn(links, shift=UP * 0.2), run_time=0.5)
        for c in cards:
            self.play(Indicate(c, color=config.manim.success_color), run_time=0.5)
            self.wait(0.2)
        self.record_visual_text("一句话: 免费 Key + 协议翻译 = 四端全通")
        strip = self._chip("免费 Key + CC-Switch/直接配置 = 四端全通", config.manim.accent_color)
        strip.next_to(banner, DOWN, buff=0.05)
        self.play(FadeIn(strip, shift=UP * 0.2), run_time=0.5)
        self.wait(1.2)
        for _ in range(2):
            for c in cards:
                self.play(Indicate(c, color=config.manim.accent_color), run_time=0.4)
                self.wait(0.15)
        self._pad_to(65.3, links)

    def _pitfall_card(self, title_t, desc, color):
        t = Text(title_t, font=self.get_chinese_font(), color=color, font_size=18, weight=BOLD)
        d = Text(desc, font=self.get_chinese_font(), color=config.manim.text_color, font_size=13)
        content = VGroup(t, d).arrange(DOWN, buff=0.15)
        bg = RoundedRectangle(width=content.width + 0.6, height=content.height + 0.4, corner_radius=0.15,
                               fill_color=config.manim.terminal_bg, fill_opacity=0.95,
                               stroke_color=color, stroke_width=2)
        return VGroup(bg, content)

    def _chip(self, text, color):
        t = Text(text, font=self.get_chinese_font(), color=color, font_size=16, weight=BOLD)
        bg = RoundedRectangle(width=t.width + 0.6, height=t.height + 0.35, corner_radius=0.15,
                               fill_color=config.manim.terminal_bg, fill_opacity=0.95,
                               stroke_color=color, stroke_width=2)
        return VGroup(bg, t)


# Extruder Book Content Intro — 书籍内容简介视频（≤5min）
# ============================================================

class BookIntroScene(BaseScene):
    def construct(self):
        self.record_visual_text("书籍简介：挤出机原理与操作")
        title = self.create_title("挤出机原理与操作", scale=0.85)
        subtitle = self.create_subtitle("Extruder Principles and Operation")
        VGroup(title, subtitle).arrange(DOWN, buff=0.4).move_to(ORIGIN).shift(UP * 1.8)
        self.play(Write(title, run_time=1.5))
        self.play(FadeIn(subtitle, shift=UP * 0.3), run_time=0.8)
        self.wait(0.5)

        try:
            img = ImageMobject("assets/images/extruder/eta_extruder_small.jpg")
            img.scale_to_fit_width(4.0).to_edge(LEFT, buff=0.6).shift(UP * 0.3)
            self.play(FadeIn(img), run_time=0.8)
        except:
            pass

        meta = VGroup(
            Text("M.J. Stevens & J.A. Covas  著", font=self.get_chinese_font(),
                 color=config.manim.text_color, font_size=19),
            Text("1995 年第二版 · 塑料挤出领域经典参考书", font=self.get_chinese_font(),
                 color=config.manim.accent_color, font_size=19),
            Text("12 章正文 · 约 16,000 行 · 700+ 配图", font=self.get_chinese_font(),
                 color=config.manim.success_color, font_size=19),
        ).arrange(DOWN, buff=0.25).move_to(RIGHT * 3.2).shift(UP * 0.5)
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.2) for m in meta], lag_ratio=0.4, run_time=1.2))
        self.wait(1.5)
        tagline = Text("面向车间工程师与高分子专业学生", font=self.get_chinese_font(),
                       color=config.manim.warning_color, font_size=20, weight=BOLD)
        tagline.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(tagline, shift=UP * 0.2))
        self._pad_to(28.0, tagline)


class BookOverviewScene(BaseScene):
    def construct(self):
        self.record_visual_text("内容概览：四篇结构")
        title = self.create_title("四篇结构").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)
        parts = [
            ("第一篇", "基础理论", ["第1章 范围与方法", "第2章 挤出工艺与要求",
                                    "第3章 熔体流变特性", "第4章 热与能量特性"], config.manim.accent_color),
            ("第二篇", "核心机理", ["第5章 挤出模头", "第6章 单螺杆熔体流动",
                                    "第7章 固体输送与熔融"], config.manim.success_color),
            ("第三篇", "运行实践", ["第8章 能量平衡", "第9章 单螺杆操作",
                                    "第10章 双螺杆挤出机"], config.manim.warning_color),
            ("第四篇", "系统视角", ["第11章 整体生产流程", "第12章 单台机器应用",
                                    "附录 A & D"], config.manim.text_color),
        ]
        cols = []
        for i, (part_label, part_title, chaps, color) in enumerate(parts):
            cap = Text(part_label, font=self.get_chinese_font(), color=color,
                       font_size=17, weight=BOLD)
            pt = Text(part_title, font=self.get_chinese_font(), color=config.manim.text_color,
                      font_size=15)
            chap_lines = [Text(c, font=self.get_code_font(), color=config.manim.text_color,
                               font_size=11) for c in chaps]
            chap_group = VGroup(*chap_lines).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
            col = VGroup(cap, pt, chap_group).arrange(DOWN, buff=0.10)
            bg = RoundedRectangle(
                width=max(col.width + 0.5, 3.4), height=col.height + 0.55,
                corner_radius=0.15, fill_color=config.manim.terminal_bg, fill_opacity=0.9,
                stroke_color=color, stroke_width=1.5,
            )
            col.move_to(bg.get_center())
            cols.append(VGroup(bg, col))
        VGroup(*cols).arrange_in_grid(rows=2, cols=2, buff=(0.5, 0.5)).center().shift(DOWN * 0.15)
        for i, col in enumerate(cols):
            self.play(FadeIn(col, shift=UP * 0.3 if i < 2 else DOWN * 0.3), run_time=0.5)
            self.wait(0.5)
        note = Text("从理论 → 机理 → 运行 → 整线，体系完整自洽",
                    font=self.get_chinese_font(), color=config.manim.warning_color, font_size=16)
        note.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(note, shift=UP * 0.2))
        self._pad_to(60.0, note)


class BookBasicScene(BaseScene):
    def construct(self):
        self.record_visual_text("基础篇：第1-4章 理论基石")
        title = self.create_title("第1-4章 基础理论").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        chapters = [
            ("第1章  范围与方法",
             "划定操作专著边界；数学只用于阐明\n语言无法表达的效果",
             config.manim.accent_color),
            ("第2章  挤出工艺与要求",
             "先讲工艺需求，再推导设备要求；\n不同产品操作策略完全不同",
             config.manim.success_color),
            ("第3章  熔体流变特性",
             "剪切流动、拉伸流动、弹性效应；\n鲨鱼皮、熔体断裂根源在此",
             config.manim.warning_color),
            ("第4章  热与能量特性",
             "热传导、混合；温度分布与转速的\n定量关系",
             config.manim.text_color),
        ]
        cards = []
        for cap, desc, color in chapters:
            c_title = Text(cap, font=self.get_chinese_font(), color=color,
                           font_size=18, weight=BOLD)
            c_desc = Text(desc, font=self.get_chinese_font(), color=config.manim.text_color,
                          font_size=14, line_spacing=1.2)
            body = VGroup(c_title, c_desc).arrange(DOWN, buff=0.15)
            bg = RoundedRectangle(
                width=body.width + 0.6, height=body.height + 0.4,
                corner_radius=0.12, fill_color=config.manim.terminal_bg, fill_opacity=0.95,
                stroke_color=color, stroke_width=2,
            )
            body.move_to(bg.get_center())
            cards.append(VGroup(bg, body))
        VGroup(*cards).arrange_in_grid(rows=2, cols=2, buff=(0.4, 0.5)).center().shift(DOWN * 0.15)
        for i, card in enumerate(cards):
            self.play(FadeIn(card, shift=UP * 0.3 if i < 2 else DOWN * 0.3), run_time=0.6)
            self.wait(1.5)

        try:
            img = ImageMobject("assets/images/extruder/simple_shear_small.png")
            img.scale_to_fit_width(3.2).to_edge(RIGHT, buff=0.4).shift(UP * 0.8)
            img_label = Text("图3.6  简单剪切", font=self.get_code_font(), color="#8b949e", font_size=11)
            img_label.next_to(img, DOWN, buff=0.05)
            self.play(FadeIn(img, shift=RIGHT * 0.3), run_time=0.6)
            self.play(FadeIn(img_label))
            self.wait(2.0)
        except:
            pass

        bottom = Text("这四章构成后续所有分析的底层逻辑",
                      font=self.get_chinese_font(), color=config.manim.warning_color, font_size=16)
        bottom.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(bottom, shift=UP * 0.2))
        self._pad_to(99.0, bottom)


class BookCoreScene(BaseScene):
    def construct(self):
        self.record_visual_text("核心篇：第5-7章 机理推演")
        title = self.create_title("第5-7章 核心机理").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)
        chapters = [
            ("第5章  挤出模头",
             "口模形状 → 产品尺寸精度\n流道设计不当 → 压力分布不均",
             config.manim.accent_color),
            ("第6章  单螺杆熔体流动",
             "建立简化方程组\n产量、压力、转速 显式关系\n特性曲线交点 = 操作分析核心工具",
             config.manim.success_color),
            ("第7章  固体输送与熔融",
             "塔德莫尔固体床模型\n瞬态成像技术\n固体床过早破裂 → 后果严重",
             config.manim.warning_color),
        ]
        items = []
        for cap, desc, color in chapters:
            c_title = Text(cap, font=self.get_chinese_font(), color=color,
                           font_size=19, weight=BOLD)
            lines = [Text(l, font=self.get_chinese_font(),
                          color=config.manim.text_color, font_size=14)
                     for l in desc.strip().split("\n")]
            c_desc = VGroup(*lines)
            body = VGroup(c_title, c_desc).arrange(DOWN, buff=0.2)
            bg = RoundedRectangle(
                width=body.width + 0.6, height=body.height + 0.4,
                corner_radius=0.12, fill_color=config.manim.terminal_bg, fill_opacity=0.95,
                stroke_color=color, stroke_width=2,
            )
            body.move_to(bg.get_center())
            items.append(VGroup(bg, body))
        VGroup(*items).arrange(RIGHT, buff=0.5).center().shift(DOWN * 0.3)
        for i, item in enumerate(items):
            self.play(FadeIn(item, shift=UP * 0.3), run_time=0.5)
            self.wait(1.8)

        try:
            img = ImageMobject("assets/images/extruder/solid_bed_cross_small.jpg")
            img.scale_to_fit_width(5.0).to_edge(DOWN, buff=0.35).shift(DOWN * 0.2)
            img_label = Text("图7.2  熔融区螺杆通道横截面（理想化示意）",
                             font=self.get_code_font(), color="#8b949e", font_size=11)
            img_label.next_to(img, UP, buff=0.08)
            self.play(FadeIn(img, shift=DOWN * 0.3), run_time=0.7)
            self.play(FadeIn(img_label))
            self.wait(3.0)
        except:
            pass

        bottom = Text("第7章是全书最难也最精彩的部分",
                      font=self.get_chinese_font(), color=config.manim.warning_color, font_size=16)
        bottom.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(bottom, shift=UP * 0.2))
        self._pad_to(142.0, bottom)


class BookAppScene(BaseScene):
    def construct(self):
        self.record_visual_text("应用篇：第8-10章 运行实践")
        title = self.create_title("第8-10章 运行实践").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)
        chapters = [
            ("第8章  能量平衡",
             "机械功率输入 + 热传导 = 聚合物焓变化\n预测熔体温度变化 定量方法",
             config.manim.accent_color),
            ("第9章  单螺杆操作",
             "进料/熔融/熔体输送各段操作变量\n转速、背压、温度分布 交互作用",
             config.manim.success_color),
            ("第10章  双螺杆挤出机",
             "停留时间分布更窄 / 混合更均匀\n反应挤出、粉末喂料、高填充 → 必须用双螺杆",
             config.manim.warning_color),
        ]
        items = []
        for cap, desc, color in chapters:
            c_title = Text(cap, font=self.get_chinese_font(), color=color,
                           font_size=19, weight=BOLD)
            lines = [Text(l, font=self.get_chinese_font(),
                          color=config.manim.text_color, font_size=14)
                     for l in desc.strip().split("\n")]
            c_desc = VGroup(*lines)
            body = VGroup(c_title, c_desc).arrange(DOWN, buff=0.2)
            bg = RoundedRectangle(
                width=body.width + 0.6, height=body.height + 0.4,
                corner_radius=0.12, fill_color=config.manim.terminal_bg, fill_opacity=0.95,
                stroke_color=color, stroke_width=2,
            )
            body.move_to(bg.get_center())
            items.append(VGroup(bg, body))
        VGroup(*items).arrange(RIGHT, buff=0.5).center().shift(DOWN * 0.3)
        for i, item in enumerate(items):
            self.play(FadeIn(item, shift=UP * 0.3), run_time=0.5)
            self.wait(1.8)
        bottom = Text("从单螺杆到双螺杆，覆盖主流工业场景",
                      font=self.get_chinese_font(), color=config.manim.warning_color, font_size=16)
        bottom.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(bottom, shift=UP * 0.2))
        self._pad_to(186.0, bottom)


class BookSysScene(BaseScene):
    def construct(self):
        self.record_visual_text("系统篇：第11-12章 整线语境")
        title = self.create_title("第11-12章 系统视角").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)
        note11 = Text("第11章：挤出质量的定义", font=self.get_chinese_font(),
                      color=config.manim.accent_color, font_size=16, weight=BOLD)
        qualities = VGroup(
            Text("恒定流量 Q 与压力 P", font=self.get_chinese_font(), color=config.manim.text_color, font_size=14),
            Text("熔体温度均匀且稳定", font=self.get_chinese_font(), color=config.manim.text_color, font_size=14),
            Text("聚合物组分充分混合", font=self.get_chinese_font(), color=config.manim.text_color, font_size=14),
            Text("正确的剪切历史", font=self.get_chinese_font(), color=config.manim.text_color, font_size=14),
        ).arrange(DOWN, buff=0.10, aligned_edge=LEFT)
        left_panel = VGroup(note11, qualities).arrange(DOWN, buff=0.18)
        left_bg = RoundedRectangle(
            width=left_panel.width + 0.8, height=left_panel.height + 0.5,
            corner_radius=0.15, fill_color=config.manim.terminal_bg, fill_opacity=0.92,
            stroke_color=config.manim.accent_color, stroke_width=1.5,
        )
        left_panel.move_to(left_bg.get_center())
        left_panel = VGroup(left_bg, left_panel).move_to(LEFT * 3.3).shift(UP * 0.3)
        self.play(FadeIn(left_panel, shift=LEFT * 0.3), run_time=0.6)
        self.play(FadeIn(note11), FadeIn(qualities[0]))
        self.wait(0.8)
        for q in qualities[1:]:
            self.play(FadeIn(q, shift=RIGHT * 0.1))
            self.wait(0.5)

        note12 = Text("第12章：十项诊断清单（现场工程师手册）",
                      font=self.get_chinese_font(), color=config.manim.success_color,
                      font_size=16, weight=BOLD)
        items12 = [
            "① 螺杆尺寸核算  ② 熔体流动性能测试  ③ 热性能测定",
            "④ 热损失测量  ⑤ 机械功率输入  ⑥ 功率-温度关系",
            "⑦ 极限产量  ⑧ 熔体温度空间分布",
            "⑨ 凝胶点移动  ⑩ 背压对熔融的影响",
        ]
        items_g = VGroup(*[
            Text(l, font=self.get_chinese_font(), color=config.manim.text_color, font_size=13)
            for l in items12
        ]).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        right_panel = VGroup(note12, items_g).arrange(DOWN, buff=0.18)
        right_bg = RoundedRectangle(
            width=right_panel.width + 0.8, height=right_panel.height + 0.5,
            corner_radius=0.15, fill_color=config.manim.terminal_bg, fill_opacity=0.92,
            stroke_color=config.manim.success_color, stroke_width=1.5,
        )
        right_panel.move_to(right_bg.get_center())
        right_panel = VGroup(right_bg, right_panel).move_to(RIGHT * 3.3).shift(UP * 0.3)
        self.play(FadeIn(right_panel, shift=RIGHT * 0.3), run_time=0.6)
        self.play(FadeIn(note12), FadeIn(items_g[0]), run_time=0.5)
        self.wait(0.8)
        for item in items_g[1:]:
            self.play(FadeIn(item, shift=LEFT * 0.1))
            self.wait(0.4)
        bottom = Text("工艺放大方法论 · 现场诊断清单",
                      font=self.get_chinese_font(), color=config.manim.warning_color, font_size=16)
        bottom.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(bottom, shift=UP * 0.2))
        self._pad_to(227.0, bottom)


class BookAppendixScene(BaseScene):
    def construct(self):
        self.record_visual_text("附录篇：附录A + 附录D")
        title = self.create_title("附录 A & D").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)
        app_a = VGroup(
            Text("附录A  聚合物的热物理与流动性能", font=self.get_chinese_font(),
                 color=config.manim.accent_color, font_size=18, weight=BOLD),
            Text("玻璃化转变温度 Tg · 结晶熔点 Tm", font=self.get_chinese_font(),
                 color=config.manim.text_color, font_size=15),
            Text("密度 ρ · 比热容 Cp · 导热系数 k", font=self.get_chinese_font(),
                 color=config.manim.text_color, font_size=15),
            Text("20+ 种常见热塑性塑料数据", font=self.get_chinese_font(),
                 color=config.manim.success_color, font_size=15),
        ).arrange(DOWN, buff=0.18)
        app_d = VGroup(
            Text("附录D  熔体泵送段的稳定性", font=self.get_chinese_font(),
                 color=config.manim.warning_color, font_size=18, weight=BOLD),
            Text("压力波动条件 · 熔体断裂发生机制", font=self.get_chinese_font(),
                 color=config.manim.text_color, font_size=15),
            Text("抑制方法", font=self.get_chinese_font(),
                 color=config.manim.success_color, font_size=15),
        ).arrange(DOWN, buff=0.18)
        left = app_a.to_edge(LEFT, buff=1.5).shift(UP * 0.3)
        right = app_d.to_edge(RIGHT, buff=1.5).shift(UP * 0.3)
        self.play(FadeIn(left, shift=LEFT * 0.3), run_time=0.6)
        self.wait(1.0)
        self.play(FadeIn(right, shift=RIGHT * 0.3), run_time=0.6)
        self.wait(1.5)
        close = Text("从理论到应用，从单螺杆到双螺杆，从单机到整线",
                     font=self.get_chinese_font(), color=config.manim.warning_color, font_size=17)
        close.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(close, shift=UP * 0.2))
        self._pad_to(260.0, close)


class BookOutroScene(BaseScene):
    def construct(self):
        self.record_visual_text("结语：免费在线阅读")
        title = self.create_title("免费在线阅读").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        info = VGroup(
            Text("GPL-3.0 协议开源", font=self.get_chinese_font(),
                 color=config.manim.success_color, font_size=18, weight=BOLD),
            Text("无需注册 · 浏览器打开即读", font=self.get_chinese_font(),
                 color=config.manim.text_color, font_size=17),
            Text("英文原版PDF 同步分享于阿里云盘", font=self.get_chinese_font(),
                 color=config.manim.text_color, font_size=17),
        ).arrange(DOWN, buff=0.22).move_to(ORIGIN).shift(UP * 1.1)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.2) for m in info], lag_ratio=0.3, run_time=1.0))
        self.wait(0.6)

        rtd_imgs = []
        for i in range(6):
            try:
                im = ImageMobject(f"assets/images/extruder/browser/rtd_f{i}_small.png")
                im.scale_to_fit_width(4.8)
                rtd_imgs.append(im)
            except:
                break
        if rtd_imgs:
            rtd_label = Text("中文版在线（ReadTheDocs）", font=self.get_chinese_font(),
                             color=config.manim.warning_color, font_size=14)
            rtd_window = RoundedRectangle(width=5.2, height=3.6, corner_radius=0.1,
                                          fill_color=config.manim.terminal_bg, fill_opacity=0.95,
                                          stroke_color=config.manim.accent_color, stroke_width=1.5)
            rtd_window.move_to(LEFT * 3.0).shift(DOWN * 0.4)
            rtd_imgs[0].move_to(rtd_window.get_center())
            rtd_group = Group(rtd_window, rtd_imgs[0], rtd_label)
            rtd_label.next_to(rtd_window, DOWN, buff=0.1)
            self.play(FadeIn(rtd_window), FadeIn(rtd_label), run_time=0.5)
            self.play(FadeIn(rtd_imgs[0]), run_time=0.3)
            prev_rtd = rtd_imgs[0]
            for img in rtd_imgs[1:]:
                self.play(FadeOut(prev_rtd, run_time=0.15), FadeIn(img, run_time=0.15))
                self.wait(0.5)
                prev_rtd = img

        gh_imgs = []
        for i in range(6):
            try:
                im = ImageMobject(f"assets/images/extruder/browser/gh_f{i}_small.png")
                im.scale_to_fit_width(4.8)
                gh_imgs.append(im)
            except:
                break
        if gh_imgs:
            gh_label = Text("GitHub 源码仓库", font=self.get_chinese_font(),
                            color=config.manim.warning_color, font_size=14)
            gh_window = RoundedRectangle(width=5.2, height=3.6, corner_radius=0.1,
                                         fill_color=config.manim.terminal_bg, fill_opacity=0.95,
                                         stroke_color=config.manim.success_color, stroke_width=1.5)
            gh_window.move_to(RIGHT * 3.0).shift(DOWN * 0.4)
            gh_imgs[0].move_to(gh_window.get_center())
            gh_group = Group(gh_window, gh_imgs[0], gh_label)
            gh_label.next_to(gh_window, DOWN, buff=0.1)
            self.play(FadeIn(gh_window), FadeIn(gh_label), run_time=0.5)
            self.play(FadeIn(gh_imgs[0]), run_time=0.3)
            prev_gh = gh_imgs[0]
            for img in gh_imgs[1:]:
                self.play(FadeOut(prev_gh, run_time=0.15), FadeIn(img, run_time=0.15))
                self.wait(0.5)
                prev_gh = img

        final = Text("欢迎提交 Issue 与 Pull Request",
                     font=self.get_chinese_font(), color=config.manim.warning_color, font_size=18, weight=BOLD)
        final.to_edge(DOWN, buff=0.4)
        self.play(FadeIn(final, shift=UP * 0.2))
        self._pad_to(285.0, final)


# ============================================================
# ============================================================


# ============================================================
# 7900XTX GPU Benchmark Scenes
# ============================================================

# ============================================================
# 7900XTX GPU Benchmark Scenes — 11 scenes
# ============================================================

class GPUOpenScene(BaseScene):
    """【开场】标题 + GPU实物图 + 关键发现 + 速度对比卡片"""

    def construct(self):
        self.record_visual_text("7900XTX 本地 AI 方案测评")
        title = self.create_title("单卡 7900XTX 运行 Qwen 27B", scale=0.78)
        subtitle = self.create_subtitle("AMD RX 7900 XTX · 24GB · Qwen3.6 / Qwen3.8 完整方案指南")
        header = VGroup(title, subtitle).arrange(DOWN, buff=0.5).to_edge(UP, buff=0.4)
        self.play(Write(title, run_time=1.8))
        self.play(FadeIn(subtitle, shift=UP * 0.3), run_time=0.8)
        self.wait(0.5)

        # GPU 实物卡图（官方透明截图，非 benchmark 机型）
        self.record_visual_text("蓝宝石 NITRO+ WHITE 7900 XT 外观参考")
        try:
            gpu_img = ImageMobject("assets/images/gpu/sapphire_nitro_plus_white_7900xt_small.png")
            gpu_img.scale_to_fit_width(7.2)
            gpu_img.move_to(ORIGIN).shift(DOWN * 0.2)
            self.play(FadeIn(gpu_img, shift=LEFT * 0.3), run_time=1.0)
            caption = Text("外观参考：蓝宝石 NITRO+ WHITE 7900 XT",
                           font=self.get_chinese_font(), color=config.manim.text_color, font_size=11)
            caption.next_to(gpu_img, DOWN, buff=0.15)
            self.play(FadeIn(caption, shift=DOWN * 0.1), run_time=0.5)
        except:
            gpu_img = None
            caption = None
        self.wait(0.8)
        if gpu_img is not None and caption is not None:
            self.play(FadeOut(gpu_img), FadeOut(caption), run_time=0.6)

        self.record_visual_text("关键发现：Vulkan 比 ROCm 快 38-80%")
        key_find = Text("关键发现：Vulkan 在 RDNA3 上比 ROCm 快 38-80%",
                        font=self.get_chinese_font(), color=config.manim.accent_color, font_size=17)
        key_find_box = RoundedRectangle(
            width=key_find.width + 0.8, height=key_find.height + 0.4,
            corner_radius=0.12, fill_color=config.manim.terminal_bg,
            fill_opacity=0.95, stroke_color=config.manim.accent_color, stroke_width=2,
        )
        key_find_box.move_to(key_find.get_center())
        self.play(FadeIn(VGroup(key_find_box, key_find), shift=UP * 0.2), run_time=0.8)
        self.wait(1.0)
        self.play(FadeOut(VGroup(key_find_box, key_find)), run_time=0.5)

        self.record_visual_text("速度对比卡片：DFlash 64-86 t/s · Vulkan+MTP 63-80 t/s · ROCm+MTP 46-54 t/s")
        speed_cards = VGroup(
            self._speed_card("DFlash+PFlash", "64-86 t/s", "极限速度 · 256K ctx", config.manim.accent_color),
            self._speed_card("Vulkan+MTP", "63-80 t/s", "最快后端 · 128K-256K", config.manim.text_color),
            self._speed_card("ROCm+MTP", "46-54 t/s", "最简单 · 8K ctx", config.manim.text_color),
            self._speed_card("TurboQuant", "28-29 t/s", "超长上下文 256K+", config.manim.text_color),
        ).arrange_in_grid(rows=2, cols=2, buff=(0.35, 0.6)).move_to(ORIGIN).shift(DOWN * 0.5)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in speed_cards], lag_ratio=0.3, run_time=1.5))
        self.wait(1.5)
        self._pad_to(58.0, speed_cards)

    def _speed_card(self, name, speed, desc, color):
        t_name = Text(name, font=self.get_chinese_font(), color=config.manim.text_color, font_size=16, weight=BOLD)
        t_speed = Text(speed, font=self.get_code_font(), color=config.manim.text_color, font_size=20)
        t_desc = Text(desc, font=self.get_chinese_font(), color=config.manim.text_color, font_size=12)
        body = VGroup(t_name, t_speed, t_desc).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        bg = RoundedRectangle(
            width=body.width + 0.6, height=body.height + 0.35,
            corner_radius=0.12, fill_color=config.manim.terminal_bg,
            fill_opacity=0.95, stroke_color=color, stroke_width=2,
        )
        body.move_to(bg.get_center())
        return VGroup(bg, body)


class GPUHardwareScene(BaseScene):
    """【硬件环境】测试平台规格表"""

    def construct(self):
        self.record_visual_text("测试平台配置")
        title = self.create_title("测试平台配置").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        headers = ["组件", "型号", "关键规格"]
        rows = [
            ["GPU", "AMD RX 7900 XTX", "24GB GDDR6 · RDNA3 · gfx1100"],
            ["显存位宽", "—", "384-bit"],
            ["计算单元", "—", "96 CU · 6144 流处理器"],
            ["CPU", "Xeon E5-2696 v4", "24核 / 48线程"],
            ["内存", "—", "64GB DDR4"],
            ["系统", "—", "Ubuntu 22.04 / 24.04"],
            ["ReBAR", "—", "必须开启（否则 tg128 仅 13.9 t/s）"],
        ]
        table = Table(
            [headers] + rows,
            include_outer_lines=True,
            line_config={"stroke_width": 1, "color": config.manim.accent_color},
            element_to_mobject_config={"font_size": 14, "font": self.get_chinese_font(), "color": config.manim.text_color},
            h_buff=0.6, v_buff=0.18,
        )
        self.apply_zebra_stripes(table, n_rows=8, n_cols=3)
        # Highlight GPU row
        table.get_cell((2, 1)).set_fill(config.manim.accent_color, opacity=0.15)
        table.get_cell((2, 2)).set_fill(config.manim.accent_color, opacity=0.15)
        table.get_cell((2, 3)).set_fill(config.manim.accent_color, opacity=0.15)
        # Highlight ReBAR row
        table.get_cell((8, 1)).set_fill(config.manim.accent_color, opacity=0.12)
        table.get_cell((8, 2)).set_fill(config.manim.accent_color, opacity=0.12)
        table.get_cell((8, 3)).set_fill(config.manim.accent_color, opacity=0.12)
        table.scale_to_fit_width(12).center().shift(DOWN * 0.15)

        self.play(Create(table), run_time=3)
        self.wait(1.0)
        self._pad_to(38.0, table)


class GPUEnvScene(BaseScene):
    """【环境准备】ROCm 安装 + HuggingFace 模型下载（终端动画）"""

    def construct(self):
        self.record_visual_text("环境准备：ROCm 安装")
        title = self.create_title("环境准备").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        term = TerminalSimulator(title="ubuntu — bash", width=13.2, height=5.0, font_size=12)
        term.build()
        term.terminal.next_to(title, DOWN, buff=0.35)
        self.play(FadeIn(term.terminal, run_time=0.4))
        self.wait(0.2)

        # --- ROCm install ---
        self.record_visual_text("sudo amdgpu-install --usecase=rocm,hip --no-dkms -y")
        term.add_command(self, "user@ubuntu:~$ ",
                         "sudo amdgpu-install --usecase=rocm,hip --no-dkms -y", wait=0.3)
        self.record_visual_text("验证 GPU 识别：rocminfo | grep gfx1100")
        term.add_command(self, "user@ubuntu:~$ ", "rocminfo | grep -i gfx1100", wait=0.2)
        term.add_line(self, "gfx1100                                          # OK",
                      color=config.manim.text_color, lag=0.0, run_time=0.8, font_size=11)
        term.add_command(self, "user@ubuntu:~$ ", "rocm-smi --showmemuse", wait=0.2)
        term.add_line(self, "GPU_MEM_TOTAL  : 24576 MiB  # 24GB OK",
                      color=config.manim.text_color, lag=0.0, run_time=0.8, font_size=11)
        self.wait(0.4)

        # --- HuggingFace download ---
        self.record_visual_text("huggingface-cli download froggeric/Qwen3.6-27B-MTP-GGUF")
        term.add_command(self, "user@ubuntu:~$ ",
                         "huggingface-cli download froggeric/Qwen3.6-27B-MTP-GGUF \\")
        term.add_line(self, '  --include "Qwen3.6-27B-Q4_K_M-mtp.gguf" \\',
                      color="#8b949e", lag=0.0, run_time=0.5, font_size=11)
        term.add_line(self, '  --local-dir ~/models',
                      color="#8b949e", lag=0.0, run_time=0.5, font_size=11)
        self.wait(0.4)

        self.record_visual_text("Qwen3.6-27B-Q4_K_M-mtp.gguf ~15.8GB · DFlash草稿 ~1.7GB")
        info = Text("Qwen3.6 Q4_K_M-mtp: ~15.8 GB  |  DFlash草稿: ~1.7 GB",
                    font=self.get_chinese_font(), color=config.manim.accent_color, font_size=13)
        info.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(info, shift=UP * 0.2))
        self._pad_to(55.0, info)


class GPUSolutionsScene(BaseScene):
    """【方案总览】五方案对比表（含基线）"""

    def construct(self):
        self.record_visual_text("五路推理方案总览")
        title = self.create_title("方案总览与速度对比").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        headers = ["方案", "后端", "解码速度", "Prefill", "最大Context", "难度", "适用场景"]
        rows = [
            ["A. Vulkan+MTP", "Vulkan", "63-80 t/s", "500-900 t/s", "128K-256K", "⭐⭐", "单用户聊天/Agent"],
            ["B. ROCm+MTP", "ROCm/HIP", "46-54 t/s", "700-970 t/s", "8K", "⭐", "快速上手"],
            ["C. TurboQuant", "ROCm/HIP", "28-29 t/s", "~970 t/s", "**256K+**", "⭐⭐", "超长上下文阅读"],
            ["D. DFlash+PFlash", "ROCm", "64-86 t/s", "730 t/s", "256K", "⭐⭐⭐", "极限速度+长上下文"],
            ["E. SGLang", "Triton", "4-8 t/s", "—", "8K", "⭐⭐", "多用户API服务"],
            ["基线·ROCm裸跑", "ROCm", "~28 t/s", "700-900 t/s", "4K", "⭐", "无优化对照"],
        ]
        table = Table(
            [headers] + rows,
            include_outer_lines=True,
            line_config={"stroke_width": 1, "color": config.manim.accent_color},
            element_to_mobject_config={"font_size": 12, "font": self.get_chinese_font(), "color": config.manim.text_color},
            h_buff=0.5, v_buff=0.16,
        )
        self.apply_zebra_stripes(table, n_rows=7, n_cols=7)
        # Highlight A and D rows (fastest)
        for col in range(1, 8):
            table.get_cell((2, col)).set_fill(config.manim.accent_color, opacity=0.12)
            table.get_cell((5, col)).set_fill(config.manim.accent_color, opacity=0.12)
        table.scale_to_fit_width(15).center().shift(DOWN * 0.1)

        self.play(Create(table), run_time=4)
        self.wait(1.0)
        self._pad_to(45.0, table)


class GPUSpeedScene(BaseScene):
    """【速度结果】Qwen3.6 和 Qwen3.8 双条形图 + 关键洞察"""

    def construct(self):
        self.record_visual_text("速度测试结果：Qwen3.6 与 Qwen3.8 对比")
        title = self.create_title("解码速度对比").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        # --- Qwen3.6 bar chart ---
        self.record_visual_text("Qwen3.6-27B Q4_K_M：DFlash最快，Vulkan紧随，ROCm第三")
        sub36 = Text("Qwen3.6-27B Q4_K_M", font=self.get_chinese_font(),
                     color=config.manim.accent_color, font_size=16)
        data36 = [("DFlash", 75), ("Vulkan", 72), ("ROCm+MTP", 50), ("Turbo", 29), ("SGLang", 6)]
        max_v36, bar_h36, n = 85.0, 1.3, len(data36)
        cw36, gap36, bw36 = 10.0, 10.0 / n, 0.65
        half36 = cw36 / 2
        colors = [config.manim.accent_color,
                  "#4a5568", "#6b7280", "#9ca3af", "#d1d5db"]
        bars36, vals36, names36 = VGroup(), VGroup(), VGroup()
        for i, (name, val) in enumerate(data36):
            h = val / max_v36 * bar_h36
            x = -half36 + gap36 * (i + 0.5)
            bar = Rectangle(width=bw36, height=h, fill_color=colors[i], fill_opacity=0.85)
            bar.move_to(np.array([x, -0.5 + h / 2, 0]))
            bars36.add(bar)
            vt = Text(f"{val}t/s", font=self.get_chinese_font(), font_size=10,
                      color=config.manim.text_color)
            vt.next_to(bar, UP, buff=0.04)
            vals36.add(vt)
            nt = Text(name, font=self.get_chinese_font(), font_size=9,
                      color=config.manim.text_color)
            nt.next_to(bar, DOWN, buff=0.08)
            names36.add(nt)

        chart36 = VGroup(bars36, vals36, names36)
        chart36.shift(LEFT * 2.5).shift(UP * 0.35)
        sub36.next_to(chart36, UP, buff=0.25)
        self.play(FadeIn(sub36), run_time=0.4)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars36], lag_ratio=0.08),
                  run_time=2)
        self.play(Write(vals36), Write(names36), run_time=0.5)

        # --- Qwen3.8 bar chart ---
        self.record_visual_text("Qwen3.8-27B UD-Q4_K_M：DFlash仍最快，Vulkan+MTP略降")
        sub38 = Text("Qwen3.8-27B UD-Q4_K_M", font=self.get_chinese_font(),
                     color=config.manim.accent_color, font_size=16)
        data38 = [("DFlash", 65), ("Vulkan+MTP", 44), ("ROCm+MTP", 44), ("Turbo", 29), ("基线", 29)]
        max_v38, bar_h38, n2 = 85.0, 1.3, len(data38)
        cw38, gap38, bw38 = 10.0, 10.0 / n2, 0.65
        half38 = cw38 / 2
        colors2 = [config.manim.accent_color,
                   "#4a5568", "#6b7280", "#9ca3af", "#d1d5db"]
        bars38, vals38, names38 = VGroup(), VGroup(), VGroup()
        for i, (name, val) in enumerate(data38):
            h = val / max_v38 * bar_h38
            x = -half38 + gap38 * (i + 0.5)
            bar = Rectangle(width=bw38, height=h, fill_color=colors2[i], fill_opacity=0.85)
            bar.move_to(np.array([x, -0.5 + h / 2, 0]))
            bars38.add(bar)
            vt = Text(f"{val}t/s", font=self.get_chinese_font(), font_size=10,
                      color=config.manim.text_color)
            vt.next_to(bar, UP, buff=0.04)
            vals38.add(vt)
            nt = Text(name, font=self.get_chinese_font(), font_size=9,
                      color=config.manim.text_color)
            nt.next_to(bar, DOWN, buff=0.08)
            names38.add(nt)

        chart38 = VGroup(bars38, vals38, names38)
        chart38.shift(RIGHT * 2.5).shift(UP * 0.35)
        sub38.next_to(chart38, UP, buff=0.25)
        self.play(FadeIn(sub38), run_time=0.4)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars38], lag_ratio=0.08),
                  run_time=2)
        self.play(Write(vals38), Write(names38), run_time=0.5)

        self.wait(1.0)
        self.record_visual_text("Vulkan 比 ROCm 快 38-80%，因 ROCm 在 gfx1100 上 GPU 利用率 bursty 波动")
        insight = Text("Vulkan 比 ROCm 快 38-80%（gfx1100 ROCm GPU 利用率 bursty 波动）",
                       font=self.get_chinese_font(), color=config.manim.accent_color, font_size=13)
        insight.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(insight, shift=UP * 0.2))
        self._pad_to(72.0, insight)


class GPUArchScene(BaseScene):
    """【Qwen3.8架构】3.6 vs 3.8 对比表（Hybrid Gated DeltaNet 亮点）"""

    def construct(self):
        self.record_visual_text("Qwen3.8 相比 3.6 的关键变化")
        title = self.create_title("Qwen3.8 vs Qwen3.6 架构对比").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        headers = ["特性", "Qwen3.6-27B", "Qwen3.8-27B", "说明"]
        rows = [
            ["架构", "纯 Dense Attention", "Hybrid Gated DeltaNet+全注意力", "3.8 引入线性注意力层"],
            ["全注意力层数", "64/64", "16/64", "48层改用线性注意力（常数空间）"],
            ["MTP 头", "单独训练", "原生集成", "接受率 84.9% vs 79.6%"],
            ["原生 Context", "32K-128K", "262,144（可扩展至1M）", "Hybrid 架构优势"],
            ["视觉编码器", "需额外下载", "内置（可选）", "mmproj 可选"],
            ["工具调用稳定性", "⭐⭐⭐⭐⭐", "⭐⭐⭐☆☆", "论坛反馈 3.8 有退步"],
            ["推理/数学", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐", "3.8 更强"],
        ]
        table = Table(
            [headers] + rows,
            include_outer_lines=True,
            line_config={"stroke_width": 1, "color": config.manim.accent_color},
            element_to_mobject_config={"font_size": 12, "font": self.get_chinese_font(), "color": config.manim.text_color},
            h_buff=0.5, v_buff=0.15,
        )
        self.apply_zebra_stripes(table, n_rows=8, n_cols=4)
        # Highlight 3.8 column
        for row in range(2, 9):
            table.get_cell((row, 3)).set_fill(config.manim.accent_color, opacity=0.15)
        table.scale_to_fit_width(14).center().shift(DOWN * 0.15)

        self.play(Create(table), run_time=3.5)
        self.wait(0.8)
        self._pad_to(55.0, table)


class GPUQuantScene(BaseScene):
    """【量化选择】Qwen3.8 量化版本决策表"""

    def construct(self):
        self.record_visual_text("Qwen3.8 量化版本选择")
        title = self.create_title("量化版本选择（Qwen3.8-27B）").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        headers = ["量化", "体积", "128K ctx VRAM", "262K ctx VRAM", "质量", "推荐场景"]
        rows = [
            ["UD-Q4_K_M", "~16.5 GB", "~21 GB", "~25 GB ❌", "优秀", "默认首选"],
            ["IQ4_XS", "~15.3 GB", "~20 GB", "~24 GB ⚠️", "良好", "最大 context 余量"],
            ["UD-Q4_K_XL", "~17.2 GB", "~22 GB", "超出 ❌", "略好", "质量优先（context受限）"],
            ["TQ3_4S", "~13.8 GB", "~17 GB", "~21 GB ✅", "良好", "262K 唯一可行方案"],
            ["UD-Q5_K_M", "~19.4 GB", "~23 GB", "超出 ❌", "很高", "精度优先（context极紧）"],
            ["Q6_K", "~22.9 GB", "超出 ❌", "超出 ❌", "接近BF16", "❌ 超出 24GB"],
        ]
        table = Table(
            [headers] + rows,
            include_outer_lines=True,
            line_config={"stroke_width": 1, "color": config.manim.accent_color},
            element_to_mobject_config={"font_size": 12, "font": self.get_chinese_font(), "color": config.manim.text_color},
            h_buff=0.4, v_buff=0.14,
        )
        self.apply_zebra_stripes(table, n_rows=7, n_cols=6)
        # Highlight TQ3_4S row
        for col in range(1, 7):
            table.get_cell((5, col)).set_fill(config.manim.accent_color, opacity=0.18)
        table.scale_to_fit_width(14).center().shift(DOWN * 0.15)

        self.play(Create(table), run_time=3.5)
        self.wait(0.8)
        self._pad_to(55.0, table)


class GPUVRAMScene(BaseScene):
    """【VRAM预算】Qwen3.6 + Qwen3.8 显存预算速查表"""

    def construct(self):
        self.record_visual_text("VRAM 预算速查：两种模型各场景显存占用")
        title = self.create_title("24GB 显存预算速查").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        # Two tables side by side
        left_title = Text("Qwen3.6-27B Q4_K_M", font=self.get_chinese_font(),
                          color=config.manim.accent_color, font_size=14, weight=BOLD)
        right_title = Text("Qwen3.8-27B UD-Q4_K_M", font=self.get_chinese_font(),
                           color=config.manim.accent_color, font_size=14, weight=BOLD)
        VGroup(left_title, right_title).arrange(RIGHT, buff=2.0).to_edge(UP, buff=1.15)
        self.play(Write(left_title), Write(right_title), run_time=0.6)

        headers = ["配置", "模型权重", "KV Cache", "MTP开销", "总计", "可行性"]
        rows_l = [
            ["Q4_K_M + 16K", "~15.8G", "~0.5G", "~0.3G", "~16.6G", "✅ 充裕"],
            ["Q4_K_M + 64K", "~15.8G", "~2.0G", "~0.3G", "~18.1G", "✅ 舒适"],
            ["Q4_K_M + 128K", "~15.8G", "~4.0G", "~0.3G", "~20.1G", "✅ 可用"],
            ["Q4_K_M + 256K", "~15.8G", "~8.0G", "~0.3G", "~24.1G", "⚠️ 贴顶"],
            ["IQ4_XS + 256K", "~14.3G", "~7.5G", "~0.3G", "~22.1G", "✅ 最佳平衡"],
        ]
        rows_r = [
            ["UD-Q4_K_M + 16K", "~16.5G", "~0.5G", "~0.3G", "~17.3G", "✅ 充裕"],
            ["UD-Q4_K_M + 32K", "~16.5G", "~1.0G", "~0.3G", "~17.8G", "✅ 舒适"],
            ["UD-Q4_K_M + 128K", "~16.5G", "~4.0G", "~0.3G", "~20.8G", "✅ 可用"],
            ["UD-Q4_K_M + 262K", "~16.5G", "~8.2G", "~0.3G", "~25.0G", "❌ 超出"],
            ["TQ3_4S + 262K", "~13.8G", "~6.8G", "~0.3G", "~20.9G", "✅ 最宽松"],
        ]

        tbl_l = Table([headers] + rows_l, include_outer_lines=True,
                      line_config={"stroke_width": 1, "color": config.manim.accent_color},
                      element_to_mobject_config={"font_size": 12, "font": self.get_chinese_font(), "color": config.manim.text_color},
                      h_buff=0.5, v_buff=0.14)
        self.apply_zebra_stripes(tbl_l, n_rows=6, n_cols=6)
        # Mark feasibility column
        for r in [2, 3, 4, 6]:
            tbl_l.get_cell((r, 6)).set_fill(config.manim.accent_color, opacity=0.12)
        tbl_l.get_cell((5, 6)).set_fill(config.manim.text_color, opacity=0.25)
        tbl_l.scale_to_fit_width(6.6).move_to(LEFT * 3.5).shift(DOWN * 0.4)

        tbl_r = Table([headers] + rows_r, include_outer_lines=True,
                      line_config={"stroke_width": 1, "color": config.manim.accent_color},
                      element_to_mobject_config={"font_size": 12, "font": self.get_chinese_font(), "color": config.manim.text_color},
                      h_buff=0.5, v_buff=0.14)
        self.apply_zebra_stripes(tbl_r, n_rows=6, n_cols=6)
        for r in [2, 3, 4, 6]:
            tbl_r.get_cell((r, 6)).set_fill(config.manim.accent_color, opacity=0.12)
        tbl_r.get_cell((5, 6)).set_fill(config.manim.text_color, opacity=0.25)
        tbl_r.scale_to_fit_width(6.6).move_to(RIGHT * 3.5).shift(DOWN * 0.4)

        self.play(Create(tbl_l), run_time=2.5)
        self.wait(0.5)
        self.play(Create(tbl_r), run_time=2.5)
        self.wait(1.0)

        self.record_visual_text("Qwen3.8 262K 必须用 TQ3_4S；IQ4_XS+262K 需 headless 模式")
        note = Text("TQ3_4S 是 262K 上下文唯一可行方案 · IQ4_XS 需 headless 模式",
                    font=self.get_chinese_font(), color=config.manim.accent_color, font_size=14)
        note.to_edge(DOWN, buff=0.3)
        self.play(FadeIn(note, shift=UP * 0.2))
        self._pad_to(62.0, note)


class GPUBIOSScene(BaseScene):
    """【BIOS设置】ReBAR/4G解码/PCIe/电源管理"""

    def construct(self):
        self.record_visual_text("BIOS 关键设置")
        title = self.create_title("BIOS 关键设置").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        tips = [
            ("Resizable BAR", "必须开启！否则 tg128 仅 13.9 t/s，开启后 37+ t/s（2.7倍差距）"),
            ("Above 4G Decoding", "必须开启，与 ReBAR 配套"),
            ("PCIe Link Speed", "设为 Gen4，勿用 Gen3"),
            ("Power Management", "高性能模式：sudo pm-is-supported --force-high"),
            ("C-States", "可关闭以减轻 GPU 利用率波动"),
        ]
        cards = VGroup()
        for i, (issue, solution) in enumerate(tips):
            t_issue = Text(issue, font=self.get_chinese_font(), color=config.manim.text_color,
                           font_size=16, weight=BOLD)
            t_sol = Text(solution, font=self.get_chinese_font(), color=config.manim.text_color,
                         font_size=13, line_spacing=1.2)
            body = VGroup(t_issue, t_sol).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
            bg = RoundedRectangle(
                width=body.width + 0.6, height=body.height + 0.35,
                corner_radius=0.12, fill_color=config.manim.terminal_bg,
                fill_opacity=0.95, stroke_color=config.manim.accent_color, stroke_width=2,
            )
            body.move_to(bg.get_center())
            cards.add(VGroup(bg, body))

        cards.arrange_in_grid(rows=3, cols=2, buff=(0.35, 0.6)).center().shift(DOWN * 0.15)
        for card in cards:
            self.play(FadeIn(card, shift=RIGHT * 0.2), run_time=0.4)
            self.wait(0.4)

        self.wait(1.5)
        self._pad_to(42.0, cards)


class GPURankingScene(BaseScene):
    """【选择建议】按场景选型决策卡"""

    def construct(self):
        self.record_visual_text("如何选择方案：按场景选型")
        title = self.create_title("按场景选型").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        self.record_visual_text("方案选择建议卡片")
        items = [
            ("🏃 极致速度", "→ Vulkan + MTP\nn_max=4（3.6）或 n_max=2（3.8）"),
            ("📚 超长上下文", "→ TurboQuant tq3_0\n262K context 唯一可行方案"),
            ("🌐 多用户 API", "→ SGLang\n并发吞吐 2-4× llama.cpp"),
            ("😌 不想折腾", "→ ROCm + MTP\n一键编译，context 8K"),
            ("⚡ 极限速度+长上下文", "→ DFlash + PFlash\nDDTree b=8，速度+context兼得"),
            ("🧪 工具调用场景", "→ Qwen3.6\n3.8 工具调用稳定性论坛反馈退步"),
        ]
        cards = VGroup()
        for label, desc in items:
            t_label = Text(label, font=self.get_chinese_font(), color=config.manim.text_color,
                           font_size=15, weight=BOLD)
            t_desc = Text(desc, font=self.get_chinese_font(), color=config.manim.text_color,
                          font_size=12, line_spacing=1.2)
            body = VGroup(t_label, t_desc).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
            bg = RoundedRectangle(
                width=body.width + 0.5, height=body.height + 0.3,
                corner_radius=0.12, fill_color=config.manim.terminal_bg,
                fill_opacity=0.95, stroke_color=config.manim.accent_color, stroke_width=1.5,
            )
            body.move_to(bg.get_center())
            cards.add(VGroup(bg, body))

        cards.arrange_in_grid(rows=3, cols=2, buff=(0.3, 0.5)).center().shift(DOWN * 0.15)
        for card in cards:
            self.play(FadeIn(card, shift=RIGHT * 0.2), run_time=0.4)
            self.wait(0.3)

        self.wait(1.5)
        self._pad_to(65.0, cards)


class GPUBackupScene(BaseScene):
    """【常见问题】故障排查要点（终端 + 卡片）"""

    def construct(self):
        self.record_visual_text("常见问题排查")
        title = self.create_title("常见问题排查").to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        tips = [
            ("Vulkan 编译失败", "必须用 gcc-11 从 shaderc 源码编译 glslc\nconda-forge 版会段错误"),
            ("运行时 OOM", "减小 context：-c 32768 或 -c 16384\n加强 KV cache 量化：-ctk q4_0 -ctv q4_0"),
            ("ROCm 识别不到 GPU", "export HSA_OVERRIDE_GFX_VERSION=11.0.0\n检查 lsmod | grep amdgpu"),
            ("MTP 接受率低", "--spec-draft-n-max 2 提高接受率\n--temp 0.3 降低温度提高可预测性"),
            ("性能远低于预期", "检查 ReBAR 是否在 BIOS 中开启\n确认使用的是 Vulkan 而非 ROCm"),
            ("GTT 隐式溢出（AMD专属）", "Qwen3.8 在 ROCm 下首请求后 decode 骤降 40%\n切换 Vulkan 后端或减小 context"),
        ]
        cards = VGroup()
        for issue, solution in tips:
            t_issue = Text(issue, font=self.get_chinese_font(), color=config.manim.text_color,
                           font_size=14, weight=BOLD)
            t_sol = Text(solution, font=self.get_chinese_font(), color=config.manim.text_color,
                         font_size=11, line_spacing=1.2)
            body = VGroup(t_issue, t_sol).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
            bg = RoundedRectangle(
                width=body.width + 0.5, height=body.height + 0.25,
                corner_radius=0.1, fill_color=config.manim.terminal_bg,
                fill_opacity=0.95, stroke_color=config.manim.accent_color, stroke_width=1.5,
            )
            body.move_to(bg.get_center())
            cards.add(VGroup(bg, body))

        cards.arrange_in_grid(rows=3, cols=2, buff=(0.25, 0.45)).center().shift(DOWN * 0.1)
        for card in cards:
            self.play(FadeIn(card, shift=RIGHT * 0.2), run_time=0.4)
            self.wait(0.35)

        self.wait(1.5)
        self._pad_to(72.0, cards)


class GPUOutroScene(BaseScene):
    """【结尾】总结"""

    def construct(self):
        self.record_visual_text("总结")
        block = VGroup(
            Text("7900XTX + Qwen 27B", font=self.get_chinese_font(),
                 color=config.manim.accent_color, font_size=30, weight=BOLD),
            Text("24GB 显存的本地 AI 终极方案", font=self.get_chinese_font(),
                 color=config.manim.text_color, font_size=21),
            Text("Vulkan+MTP 是 RDNA3 综合性能最优方案", font=self.get_chinese_font(),
                 color=config.manim.text_color, font_size=17),
            Text("Qwen3.8 MTP 接受率 85%，工具调用仍建议 3.6", font=self.get_chinese_font(),
                 color=config.manim.text_color, font_size=17),
        ).arrange(DOWN, buff=0.55, aligned_edge=ORIGIN)

        self.record_visual_text("我们下次见")
        closing = Text("我们下次见 👋", font=self.get_chinese_font(),
                       color=config.manim.accent_color, font_size=21, weight=BOLD)

        self.record_visual_text("完整文章分享：知乎")
        zhihu_label = Text("完整文章分享", font=self.get_chinese_font(),
                           color=config.manim.text_color, font_size=14)
        zhihu_url = Text("https://zhuanlan.zhihu.com/p/2086731295925724100",
                         font=self.get_code_font(), color=config.manim.accent_color, font_size=14)
        zhihu_url.scale_to_fit_width(9.2)
        zhihu_body = VGroup(zhihu_label, zhihu_url).arrange(DOWN, buff=0.22)
        zhihu_card = RoundedRectangle(
            width=zhihu_body.width + 0.7, height=zhihu_body.height + 0.4,
            corner_radius=0.12, fill_color=config.manim.terminal_bg,
            fill_opacity=0.96, stroke_color=config.manim.accent_color, stroke_width=1.5,
        )
        zhihu_card.move_to(zhihu_body.get_center())
        zhihu_group = VGroup(zhihu_card, zhihu_body)

        everything = VGroup(block, closing, zhihu_group).arrange(DOWN, buff=0.55)
        everything.scale_to_fit_height(6.2)
        everything.move_to(ORIGIN).shift(UP * 0.55)

        self.play(Write(block[0], run_time=1.5))
        for line in block[1:]:
            self.play(FadeIn(line, shift=UP * 0.2), run_time=0.6)
        self.wait(0.6)
        self.play(FadeIn(closing, shift=UP * 0.2), run_time=0.8)
        self.wait(0.4)
        self.play(FadeIn(zhihu_group, shift=UP * 0.2), run_time=0.8)
        self.wait(1.0)

        self._pad_to(20.0, everything)

SCENE_MAP = {
    # --- MacBook Pro AI Benchmark ---
    "MacBook Pro 本地运行AI大模型评测": IntroScene,
    "【硬件环境】": HardwareScene,
    "【测试题目介绍】": QuestionsScene,
    "【参测模型一览】": ModelsScene,
    "【速度测试结果】": SpeedResultsScene,
    "【准确率对比】": AccuracyScene,
    "【重点模型：Ministral 3 3B】": Ministral3BScene,
    "【Ministral 3 3B vs 8B 对比】": ComparisonScene,
    "【综合排名与选择建议】": RankingScene,
    "【技术说明】": TechSpecsScene,
    # --- Extruder Principles and Operation (project story) ---
    "【项目起源】": ExtruderOriginScene,
    "【翻译工具链】": ExtruderToolsScene,
    "【翻译历程时间线】": ExtruderTimelineScene,
    "【技术栈】": ExtruderTechStackScene,
    "【校译】": ExtruderProofreadingScene,
    "【访问方式】": ExtruderAccessScene,
    # --- Agnes AI Tutorial ---
    "【Agnes AI 是什么】": AgnesIntroScene,
    "【免费注册获取 Key】": AgnesKeyScene,
    "【模型一览】": AgnesModelsScene,
    "【CC-Switch 配置】": AgnesCCSwitchScene,
    "【Claude Code 接入】": AgnesClaudeCodeScene,
    "【Opencode 接入】": AgnesOpencodeScene,
    "【Codex 接入】": AgnesCodexScene,
    "【Hermes 接入】": AgnesHermesScene,
    "【避坑指南与总结】": AgnesOutroScene,
    # --- Extruder Book Content Intro ---
    "【书籍简介】": BookIntroScene,
    "【内容概览】": BookOverviewScene,
    "【基础篇】": BookBasicScene,
    "【核心篇】": BookCoreScene,
    "【应用篇】": BookAppScene,
    "【系统篇】": BookSysScene,
    "【附录篇】": BookAppendixScene,
    "【结语】": BookOutroScene,
    # --- 7900XTX GPU Benchmark ---
    "【开场】7900XTX 本地 AI 测评": GPUOpenScene,
    "【硬件环境】平台配置": GPUHardwareScene,
    "【BIOS设置】ReBAR等关键项": GPUBIOSScene,
    "【环境准备】安装与下载": GPUEnvScene,
    "【方案总览】五路对比": GPUSolutionsScene,
    "【速度结果】Benchmark": GPUSpeedScene,
    "【架构分析】3.8 vs 3.6": GPUArchScene,
    "【量化选择】版本决策": GPUQuantScene,
    "【VRAM预算】显存够用吗": GPUVRAMScene,
    "【选择建议】按场景选型": GPURankingScene,
    "【常见问题】故障排查": GPUBackupScene,
    "【结尾】总结": GPUOutroScene,
}
