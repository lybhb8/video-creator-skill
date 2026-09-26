"""Reusable UI simulation components for Agnes AI tutorial scenes."""
from manim import *
from typing import List, Optional, Tuple


class TerminalWindow(VGroup):
    """Dark terminal window with title bar, prompt, and command output."""

    def __init__(
        self,
        title: str = "Terminal",
        width: float = 10.0,
        height: float = 5.0,
        font_size: int = 14,
        title_color: str = "#c9d1d9",
        bg_color: str = "#0d1117",
        code_color: str = "#e6edf3",
        prompt_color: str = "#7ee787",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.width = width
        self.height = height
        self.font_size = font_size

        # Background
        bg = RoundedRectangle(
            corner_radius=0.15, width=width, height=height,
            fill_color=bg_color, fill_opacity=1, stroke_color="#30363d", stroke_width=1.5,
        )
        self.bg = bg

        # Title bar
        title_bar = Rectangle(
            width=width, height=0.4, fill_color="#161b22", fill_opacity=1,
            stroke_color="#30363d", stroke_width=1,
        ).move_to(bg.get_top() + DOWN * 0.2)
        self.title_bar = title_bar

        # Window dots
        dots = VGroup()
        for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
            dot = Circle(radius=0.06, fill_color=color, fill_opacity=1, stroke_width=0)
            dot.move_to(title_bar.get_left() + RIGHT * (0.3 + i * 0.18))
            dots.add(dot)
        self.dots = dots

        # Title text
        title_text = Text(title, font_size=11, color=title_color).move_to(title_bar)
        self.title_text = title_text

        # Code area (scrollable content region)
        code_top = title_bar.get_bottom()[1] - 0.1
        code_bottom = bg.get_bottom()[1] + 0.15
        code_height = code_top - code_bottom
        self.code_region = Rectangle(
            width=width - 0.3, height=code_height,
            fill_color=bg_color, fill_opacity=0, stroke_width=0,
        ).move_to([(bg.get_left()[0] + bg.get_right()[0]) / 2, (code_top + code_bottom) / 2, 0])

        self.add(self.bg, self.title_bar, self.dots, self.title_text, self.code_region)

    def type_line(
        self, scene: Scene, text: str, color: str = "#e6edf3",
        font_size: Optional[int] = None, run_time: float = 0.4,
        wait: float = 0.1, y_offset: float = 0.0,
    ) -> Text:
        """Type a single line into the terminal and return the mobject."""
        fs = font_size or self.font_size
        line = Text(text, font=MONO_FONT, font_size=fs, color=color)
        # Place below title bar, inside code region
        existing = [m for m in self.code_region.submobjects if isinstance(m, Text)]
        row = len(existing)
        x = self.code_region.get_left()[0] + 0.15
        y = self.code_region.get_top()[1] - 0.25 - row * (fs * 0.022) + y_offset
        line.move_to([x + line.width / 2, y, 0])
        self.code_region.add(line)
        scene.play(AddTextLetterByLetter(line, run_time=run_time))
        if wait > 0:
            scene.wait(wait)
        return line

    def add_output(
        self, scene: Scene, text: str, color: str = "#8b949e",
        font_size: Optional[int] = None, run_time: float = 0.3,
        wait: float = 0.05,
    ) -> Text:
        """Add output text (no typing animation, just fade in)."""
        fs = font_size or self.font_size
        line = Text(text, font=MONO_FONT, font_size=fs, color=color)
        existing = [m for m in self.code_region.submobjects if isinstance(m, Text)]
        row = len(existing)
        x = self.code_region.get_left()[0] + 0.15
        y = self.code_region.get_top()[1] - 0.25 - row * (fs * 0.022)
        line.move_to([x + line.width / 2, y, 0])
        self.code_region.add(line)
        scene.play(FadeIn(line, shift=UP * 0.05), run_time=run_time)
        if wait > 0:
            scene.wait(wait)
        return line


class BrowserWindow(VGroup):
    """Browser window with address bar and content area."""

    def __init__(
        self,
        url: str = "https://agnes-ai.com",
        width: float = 12.0,
        height: float = 7.0,
        bg_color: str = "#ffffff",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.width = width
        self.height = height

        # Window frame
        frame = RoundedRectangle(
            corner_radius=0.2, width=width, height=height,
            fill_color=bg_color, fill_opacity=1, stroke_color="#d0d7de", stroke_width=1.5,
        )
        self.frame = frame

        # Title bar
        title_bar = Rectangle(
            width=width, height=0.5, fill_color="#f6f8fa", fill_opacity=1,
            stroke_color="#d0d7de", stroke_width=1,
        ).move_to(frame.get_top() + DOWN * 0.25)
        self.title_bar = title_bar

        # Window dots
        dots = VGroup()
        for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
            dot = Circle(radius=0.06, fill_color=color, fill_opacity=1, stroke_width=0)
            dot.move_to(title_bar.get_left() + RIGHT * (0.3 + i * 0.18))
            dots.add(dot)

        # Address bar
        addr_bg = RoundedRectangle(
            corner_radius=0.1, width=width - 2.0, height=0.28,
            fill_color="#ffffff", fill_opacity=1, stroke_color="#d0d7de", stroke_width=1,
        ).move_to(title_bar)
        addr_text = Text(url, font_size=11, color="#656d76").move_to(addr_bg)
        lock_icon = Text("🔒", font_size=10).next_to(addr_bg, LEFT, buff=0.1)

        # Content area
        content_top = title_bar.get_bottom()[1] - 0.1
        content_bottom = frame.get_bottom()[1] + 0.15
        content_height = content_top - content_bottom
        self.content_area = Rectangle(
            width=width - 0.3, height=content_height,
            fill_color=bg_color, fill_opacity=0, stroke_width=0,
        ).move_to([(frame.get_left()[0] + frame.get_right()[0]) / 2, (content_top + content_bottom) / 2, 0])

        self.add(self.frame, self.title_bar, dots, addr_bg, lock_icon, addr_text, self.content_area)

    def add_element(
        self, scene: Scene, mobject: Mobject, position: str = "center", **kwargs
    ):
        """Place a mobject in the content area."""
        pos_map = {
            "center": self.content_area.get_center(),
            "top": self.content_area.get_top() + DOWN * 0.5,
            "bottom": self.content_area.get_bottom() + UP * 0.5,
            "left": self.content_area.get_left() + RIGHT * 1.0,
            "right": self.content_area.get_right() + LEFT * 1.0,
        }
        target = pos_map.get(position, self.content_area.get_center())
        mobject.move_to(target)
        self.content_area.add(mobject)
        scene.play(FadeIn(mobject, shift=UP * 0.1), **kwargs)


class HighlightEffect(VGroup):
    """Animated highlight effect: colored border + glow that pulses."""

    def __init__(
        self,
        target: Mobject,
        color: str = "#58a6ff",
        buff: float = 0.15,
        pulse: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.target = target
        self.color = color

        # Highlight border
        border = SurroundingRectangle(
            target, color=color, buff=buff, corner_radius=0.08,
            stroke_width=3, stroke_opacity=0.9,
        )
        self.border = border

        # Glow effect
        glow = SurroundingRectangle(
            target, color=color, buff=buff + 0.1, corner_radius=0.12,
            stroke_width=6, stroke_opacity=0.3,
        )
        self.glow = glow

        self.add(self.border, self.glow)

    def animate_in(self, scene: Scene, run_time: float = 0.5, **kwargs):
        """Fade in the highlight effect."""
        scene.play(
            Create(self.border, run_time=run_time),
            FadeIn(self.glow, run_time=run_time),
            **kwargs,
        )

    def pulse_animation(self, scene: Scene, runs: int = 2, run_time_per: float = 0.6):
        """Pulse the glow effect."""
        for _ in range(runs):
            scene.play(
                self.glow.animate.set_stroke(opacity=0.6, width=8),
                run_time=run_time_per / 2,
            )
            scene.play(
                self.glow.animate.set_stroke(opacity=0.3, width=6),
                run_time=run_time_per / 2,
            )


class StepIndicator(VGroup):
    """Numbered step indicator for multi-step tutorials."""

    def __init__(
        self,
        steps: List[str],
        current: int = 0,
        width: float = 10.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.steps = steps
        self.current = current

        # Step boxes
        self.boxes = VGroup()
        self.labels = VGroup()
        step_width = width / len(steps)

        for i, step_text in enumerate(steps):
            # Box
            box = Rectangle(
                width=step_width - 0.1, height=0.5,
                fill_color="#1f6feb" if i == current else "#21262d",
                fill_opacity=1, stroke_color="#30363d", stroke_width=1,
            )
            # Number
            num = Text(str(i + 1), font_size=14, color="white" if i == current else "#8b949e")
            num.move_to(box)
            # Label
            label = Text(step_text, font_size=10, color="#c9d1d9").next_to(box, DOWN, buff=0.05)

            self.boxes.add(box)
            self.labels.add(VGroup(num, label))

        self.boxes.arrange(RIGHT, buff=0.05)
        self.labels.move_to(self.boxes.get_center() + DOWN * 0.5)

        self.add(self.boxes, self.labels)

    def highlight_step(self, scene: Scene, step: int, run_time: float = 0.3):
        """Highlight a specific step."""
        # Reset all
        for i, box in enumerate(self.boxes):
            box.set_fill("#1f6feb" if i == step else "#21262d")
            self.labels[i][0].set_color("white" if i == step else "#8b949e")
        scene.play(*[Transform(self.boxes[i], self.boxes[i]) for i in range(len(self.boxes))], run_time=run_time)