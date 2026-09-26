"""
Base Manim scene classes and utilities for video generation.
"""
from manim import *
from config import get_config
from typing import List, Optional
import textwrap

config = get_config()


class BaseScene(Scene):
    """Base scene with common configuration."""

    # Per-instance list filled by each subclass's construct() with on-screen text.
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera.background_color = config.manim.background_color
        self.default_font = config.manim.font
        self.code_font = config.manim.code_font
        self.visual_text_entries: List[str] = []

    def get_chinese_font(self):
        return config.manim.font

    def get_code_font(self):
        return config.manim.code_font

    def create_title(self, text: str, scale: float = 0.72) -> Text:
        return Text(text, font=self.get_chinese_font(), color=config.manim.text_color).scale(scale)

    def create_subtitle(self, text: str, scale: float = 0.45) -> Text:
        return Text(text, font=self.get_chinese_font(), color=config.manim.accent_color).scale(scale)

    def get_visual_text(self) -> List[str]:
        """Return all on-screen text entries collected during construct()."""
        return list(self.visual_text_entries)

    def record_visual_text(self, text: str) -> None:
        """Append a line of on-screen text to the visual entry list."""
        self.visual_text_entries.append(text)

    def apply_zebra_stripes(self, table, n_rows: int, n_cols: int,
                            opacity: float = 0.10, start_row: int = 2,
                            step: int = 2, color: Optional[str] = None) -> None:
        """Apply alternating row shading to a manim Table (row 1 = header).

        Must be called BEFORE semantic color fills (✅/❌/⚠️, column highlights)
        so those background colors win on marked cells while untouched rows
        still show the zebra pattern.
        """
        if color is None:
            color = config.chart_colors[7]  # neutral gray #8b949e
        for row in range(start_row, n_rows + 1, step):
            for col in range(1, n_cols + 1):
                table.get_cell((row, col)).set_fill(color, opacity=opacity)
    
    def apply_row_colors(self, table, n_rows: int, n_cols: int,
                         opacity: float = 0.08, start_row: int = 2,
                         n_chart_colors: Optional[int] = None) -> None:
        """Color each data row (row 1 = header) with a distinct chart color.

        Every row gets its own hue from the chart palette at a low opacity so
        tables read as per-row color bands instead of gray zebra stripes. Call
        BEFORE semantic fills (✅/❌/⚠️, column highlights) so those background
        colors still win on marked cells; the header row keeps its base fill.
        Font sizes are untouched (no size change → screen occupancy stays
        reasonable).
        """
        palette = config.chart_colors
        n = n_chart_colors or len(palette)
        for row in range(start_row, n_rows + 1):
            color = palette[(row - start_row) % n]
            for col in range(1, n_cols + 1):
                table.get_cell((row, col)).set_fill(color, opacity=opacity)
    
    def create_body_text(self, text: str, scale: float = 0.45, line_spacing: float = 1.3) -> VGroup:
        """Create wrapped body text that fits screen width."""
        lines = textwrap.wrap(text, width=50)
        text_objects = []
        for line in lines:
            t = Text(line, font=self.get_chinese_font(), color=config.manim.text_color).scale(scale)
            text_objects.append(t)
        group = VGroup(*text_objects).arrange(DOWN, aligned_edge=LEFT, buff=0.15 * line_spacing)
        return group
    
    def create_code_block(self, code: str, language: str = "python") -> Code:
        return Code(
            code_string=code,
            language=language,
            background="rectangle",
            background_config={"fill_color": config.manim.terminal_bg, "fill_opacity": 1},
            font=self.get_code_font(),
            style="monokai",
            line_spacing=0.6,
            font_size=18,
        )

    def load_screenshot(self, filename: str, max_width: float = 6.0, max_height: float = 4.0):
        """Load a PNG screenshot from assets/screenshots/ and scale it to fit.

        Returns an ImageMobject centered at ORIGIN.
        """
        import os
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "assets", "screenshots", filename)
        img = ImageMobject(path)
        img.scale_to_fit_width(max_width).scale_to_fit_height(max_height)
        img.center()
        return img

    def _pad_to(self, target: float, mob=None, lo: float = 0.55, hi: float = 1.0,
                period: float = 2.6) -> None:
        """Extend the scene until the scene clock reaches ``target`` seconds.

        Uses ``self.renderer.time`` (sum of all play run_times and wait
        durations, quantized to +/- 1 frame) as the scene clock. If ``mob`` is
        given it subtly breathes its opacity between ``lo`` and ``hi`` in
        ``period``-second cycles so the hold stays visually alive; otherwise
        plain waits fill the remainder. The leftover (< one period) is
        consumed by a final wait, so the rendered duration lands on ``target``
        within frame precision.
        """
        remaining = target - self.renderer.time
        if remaining <= 0:
            return
        if mob is not None and remaining > period:
            n = int(remaining // period)
            half = period / 2.0
            for _ in range(n):
                self.play(mob.animate.set_opacity(lo), run_time=half)
                self.play(mob.animate.set_opacity(hi), run_time=half)
            remaining = target - self.renderer.time
        if remaining > 0:
            self.wait(remaining)


class TerminalSimulator:
    """Simulates a realistic terminal workflow inside the CURRENT scene.

    The legacy ``TerminalScene`` typed into an invisible scene (its animations
    played on a never-rendered renderer), so commands never appeared on screen.
    This class instead plays every animation through the containing scene:

    * styled terminal window (traffic lights + title bar + content area)
    * character-by-character command typing effect (FadeIn lag reveals)
    * dimmed output lines with optional per-line color/speed/indent
    * scrolling cursor position that tracks typed rows

    Usage inside any scene::

        term = TerminalSimulator(title="macbook-pro — ollama")
        term.present(self, commands=[
            {"prompt": "user@macbook-pro:~$ ", "command": "ollama list",
             "output": "NAME ..."},
        ])
    """

    def __init__(self, commands=None, width=13.8, height=6.6, font_size=14,
                 title="macbook-pro — zsh", line_h=0.30):
        self.commands = commands or []
        self.width = width
        self.height = height
        self.font_size = font_size
        self.title = title
        self.terminal = None
        self.content_area = None
        self.content = VGroup()
        self.line = 0
        self.line_h = line_h

    def build(self) -> VGroup:
        """Construct the terminal window shell + content area. Returns window."""
        bg = Rectangle(
            width=self.width, height=self.height,
            fill_color=config.manim.terminal_bg, fill_opacity=1,
            stroke_color=config.manim.accent_color, stroke_width=1.5,
        )
        bar_h = 0.42
        bar = Rectangle(width=self.width, height=bar_h,
                        fill_color="#2d333b", fill_opacity=1, stroke_width=0)
        bar.move_to(bg.get_top() + DOWN * bar_h / 2)
        dots = VGroup(*[
            Circle(radius=0.05, fill_color=c, fill_opacity=1, stroke_width=0)
            for c in ("#ff5f56", "#ffbd2e", "#27ca4f")
        ]).arrange(RIGHT, buff=0.08).move_to(bar.get_left() + RIGHT * 0.42)
        title_txt = Text(self.title, font=config.manim.code_font,
                         color="#8b949e", font_size=11).move_to(bar.get_center())
        content = Rectangle(
            width=self.width - 0.4, height=self.height - bar_h - 0.1,
            fill_color=config.manim.terminal_bg, fill_opacity=1, stroke_width=0,
        )
        content.move_to(bg.get_center() + DOWN * bar_h / 2)

        self.terminal = VGroup(bg, bar, dots, title_txt, content)
        self.content_area = content
        return self.terminal

    def reset(self):
        """Clear typed content so the window can host a second command block."""
        self.content = VGroup()
        self.line = 0

    def cursor(self):
        """Current typing position (left edge of content area, top-down)."""
        ca = self.content_area
        y = ca.get_top()[1] - 0.28 - self.line * self.line_h
        return np.array([ca.get_left()[0], y, 0])

    def add_line(self, scene, text, color=None, font_size=None, run_time=None,
                 lag=0.10, indent=0.45, wait=0.0, weight=None, font=None):
        """Type one logical line; ``\n`` in text adds extra rows on screen."""
        if font is None:
            font = config.manim.code_font
        if font_size is None:
            font_size = self.font_size
        if color is None:
            color = config.manim.terminal_text
        last = None
        for part in text.split("\n"):
            t = Text(part, font=font, color=color,
                     font_size=font_size, weight=weight or NORMAL)
            pos = self.cursor()
            t.align_to(self.content_area, LEFT).shift(RIGHT * indent)
            t.move_to([t.get_center()[0], pos[1], 0])
            rt = run_time if run_time is not None else min(0.05 * len(part) + 0.2, 1.6)
            scene.play(FadeIn(t, shift=RIGHT * 0.2, lag_ratio=lag), run_time=rt)
            self.content.add(t)
            self.line += 1
            last = t
        if wait:
            scene.wait(wait)
        return last

    def add_command(self, scene, prompt, command, lag=0.12, run_time=None,
                    wait=0.15, font=None):
        """Type ``prompt + command`` with the prompt tinted differently."""
        if font is None:
            font = config.manim.code_font
        pos = self.cursor()

        def _place(mob):
            mob.align_to(self.content_area, LEFT).shift(RIGHT * 0.45)
            mob.move_to([mob.get_center()[0], pos[1], 0])
            return mob

        if prompt and command:
            p = Text(prompt, font=font,
                     color=config.manim.terminal_prompt, font_size=self.font_size)
            c = Text(command, font=font,
                     color=config.manim.terminal_text, font_size=self.font_size,
                     weight=BOLD)
            row = VGroup(p, c).arrange(RIGHT, buff=0.0)
            _place(row)
            scene.play(FadeIn(p, shift=RIGHT * 0.2, lag_ratio=0.1),
                       run_time=min(0.04 * len(prompt) + 0.2, 0.8))
            scene.play(FadeIn(c, shift=RIGHT * 0.2, lag_ratio=lag),
                       run_time=run_time or min(0.05 * len(command) + 0.2, 1.5))
            self.content.add(row)
        else:
            t = Text(prompt + command, font=font,
                     color=config.manim.terminal_prompt, font_size=self.font_size,
                     weight=BOLD)
            _place(t)
            scene.play(FadeIn(t, shift=RIGHT * 0.2, lag_ratio=lag),
                       run_time=run_time or min(0.05 * len(prompt + command) + 0.2, 1.5))
            self.content.add(t)
        self.line += 1
        if wait:
            scene.wait(wait)

    def run_command(self, scene, cmd: dict):
        """Play one command block: prompt+command, then its output lines."""
        prompt = cmd.get("prompt", "user@macbook-pro:~$ ")
        command = cmd.get("command", "")
        if command:
            self.add_command(scene, prompt, command,
                             wait=cmd.get("after_command", 0.2))
        output = cmd.get("output", "")
        if output:
            for entry in output.rstrip("\n").split("\n"):
                if isinstance(entry, dict):
                    self.add_line(scene, entry["text"],
                                  color=entry.get("color"),
                                  font_size=entry.get("font_size"),
                                  lag=entry.get("lag", 0.0),
                                  indent=entry.get("indent", 0.45))
                else:
                    self.add_line(scene, entry, color="#9da5b4",
                                  font_size=self.font_size - 1, lag=0.0,
                                  indent=0.45)
            scene.wait(cmd.get("after_output", 0.25))

    def present(self, scene, commands=None, hold=0.5):
        """Fade in the window then run the whole command sequence."""
        if self.terminal is None:
            self.build()
        scene.play(FadeIn(self.terminal, run_time=0.5))
        scene.wait(hold)
        for cmd in (commands or self.commands):
            self.run_command(scene, cmd)
        return self.terminal


class TerminalScene(BaseScene):
    """Standalone terminal scene (kept for tests/back-compat).

    Prefer embedding :class:`TerminalSimulator` inside a richer scene for full
    control; this thin wrapper plays the same command sequence standalone.
    """

    def __init__(self, commands=None, **kwargs):
        self.commands = commands or []
        super().__init__(**kwargs)

    def construct(self):
        sim = TerminalSimulator(commands=self.commands)
        sim.present(self)


class ChartScene(BaseScene):
    """Scene for displaying charts and data visualizations."""
    
    def construct_bar_chart(self, data: dict, title: str, y_label: str = "", colors: List[str] = None):
        """Create an animated bar chart."""
        if colors is None:
            colors = config.chart_colors
        
        chart = BarChart(
            values=list(data.values()),
            bar_names=list(data.keys()),
            y_range=[0, max(data.values()) * 1.2, max(data.values()) / 5],
            bar_colors=colors[:len(data)],
            bar_width=0.6,
            bar_fill_opacity=0.8,
            bar_stroke_width=1,
            y_axis_config={"font_size": 20, "color": config.manim.text_color},
            x_axis_config={"font_size": 20, "color": config.manim.text_color},
        )
        
        title_text = self.create_title(title).to_edge(UP)
        
        self.play(Write(title_text))
        self.play(Create(chart), run_time=2)
        self.wait(1)
        
        return chart


class TableScene(BaseScene):
    """Scene for displaying data tables."""
    
    def construct_table(self, headers: List[str], rows: List[List[str]], title: str, 
                       highlight_rows: List[int] = None, highlight_color: str = None):
        """Create an animated table."""
        if highlight_color is None:
            highlight_color = config.manim.success_color
        
        table = Table(
            [headers] + rows,
            include_outer_lines=True,
            line_config={"stroke_width": 1, "color": config.manim.accent_color},
            element_to_mobject_config={"font_size": 18, "font": self.get_chinese_font()},
            h_buff=1.0,
            v_buff=0.3,
        )
        
        # Style header row
        for i in range(len(headers)):
            table.get_cell((1, i+1)).set_fill(config.manim.accent_color, opacity=0.2)
        
        # Highlight specific rows
        if highlight_rows:
            for row_idx in highlight_rows:
                for col_idx in range(len(headers) + 1):
                    cell = table.get_cell((row_idx + 1, col_idx + 1))
                    cell.set_fill(highlight_color, opacity=0.2)
        
        title_text = self.create_title(title).to_edge(UP)
        table.next_to(title_text, DOWN, buff=0.5)
        table.scale_to_fit_width(13)
        
        self.play(Write(title_text))
        self.play(Create(table), run_time=2)
        self.wait(1)
        
        return table


class TextAnimationScene(BaseScene):
    """Scene for animated text display (narration sync)."""
    
    def __init__(self, text: str, **kwargs):
        super().__init__()
        self.narration_text = text
    
    def construct(self):
        # Create scrolling/synced text
        paragraphs = self.narration_text.split('\n\n')
        
        for para in paragraphs:
            if not para.strip():
                continue
            text_obj = self.create_body_text(para.strip(), scale=0.5)
            text_obj.center()
            
            self.play(FadeIn(text_obj, shift=UP*0.3), run_time=1)
            self.wait(2)
            self.play(FadeOut(text_obj, shift=UP*0.3), run_time=0.5)
            self.wait(0.3)


def create_section_scene(section_data, config) -> Scene:
    """Factory function to create appropriate scene for a section."""
    title = section_data.title
    
    # Map section types to scene classes
    if "终端" in section_data.visual_text or "命令" in section_data.visual_text:
        # Extract commands from visual description
        return TerminalScene(commands=extract_commands(section_data.visual_text))
    
    elif "图" in title or "排名" in title or "对比" in title:
        return ChartScene()
    
    elif "表格" in title:
        return TableScene()
    
    else:
        return TextAnimationScene(section_data.narration_text)


def extract_commands(visual_text: str) -> List[dict]:
    """Extract terminal commands from visual description."""
    commands = []
    lines = visual_text.split('\n')
    for line in lines:
        if '`' in line or '$' in line:
            # Simple extraction - can be enhanced
            parts = line.split('`')
            if len(parts) >= 2:
                commands.append({
                    'prompt': 'user@mac:~$ ',
                    'command': parts[1],
                    'output': '',
                    'delay': 0.02
                })
    return commands if commands else [{
        'prompt': 'user@mac:~$ ',
        'command': 'ollama list',
        'output': 'NAME                                    ID              SIZE      MODIFIED\nministral-3:3b-instruct-2512-q4_K_M   f04aa1c738f6    3.0 GB    9 minutes ago',
        'delay': 0.02
    }]