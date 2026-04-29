from manim import *

class Scene03(Scene):
    def construct(self):
        title = Text("Gradient of Cost", font_size=40, color=YELLOW, weight=BOLD)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        # Parameter labels
        params = ["w₁", "w₂", "w₃", "b₁", "b₂"]
        magnitudes = [3.5, 1.2, 4.5, 0.6, 2.0]  # gradient magnitudes
        colors = [BLUE, BLUE, ORANGE, LIGHT_GRAY, BLUE]

        labels = VGroup()
        bars = VGroup()
        rows = VGroup()

        for i, (p, mag, col) in enumerate(zip(params, magnitudes, colors)):
            label = Text(p, font_size=28, color=WHITE)
            bar = Rectangle(
                width=mag,
                height=0.4,
                fill_color=col,
                fill_opacity=0.9,
                stroke_color=col,
                stroke_width=1,
            )
            bar.next_to(label, RIGHT, buff=0.4)
            # Align left edge of bar
            bar.align_to(label, LEFT).shift(RIGHT * 0.6 + (bar.width / 2) * RIGHT)
            row = VGroup(label, bar)
            labels.add(label)
            bars.add(bar)
            rows.add(row)

        rows.arrange(DOWN, buff=0.4, aligned_edge=LEFT)
        rows.shift(LEFT * 2 + DOWN * 0.3)

        # Arrow from title to bar chart
        arrow = Arrow(
            start=title.get_bottom() + DOWN * 0.1,
            end=rows.get_top() + UP * 0.1,
            color=YELLOW,
            buff=0.1,
        )
        self.play(GrowArrow(arrow))
        self.wait(0.3)

        # Draw labels first
        self.play(*[Write(lbl) for lbl in labels])
        self.wait(0.3)

        # Animate bars growing
        for bar in bars:
            self.play(Create(bar), run_time=0.4)
        self.wait(1)

        # Highlight high-sensitivity bar (w3, index 2)
        high_bar = bars[2]
        high_label = Text("high sensitivity", font_size=24, color=ORANGE, weight=BOLD)
        high_label.next_to(high_bar, RIGHT, buff=0.3)
        self.play(Indicate(high_bar, color=ORANGE, scale_factor=1.15))
        self.play(FadeIn(high_label, shift=RIGHT * 0.3))
        self.wait(1.5)

        # Highlight low-sensitivity bar (b1, index 3)
        low_bar = bars[3]
        low_label = Text("low sensitivity", font_size=24, color=LIGHT_GRAY)
        low_label.next_to(low_bar, RIGHT, buff=0.3)
        self.play(Indicate(low_bar, color=LIGHT_GRAY, scale_factor=1.15))
        self.play(FadeIn(low_label, shift=RIGHT * 0.3))
        self.wait(2)

        # Final pause to let viewer absorb
        self.wait(1.5)

        self.play(
            FadeOut(title),
            FadeOut(arrow),
            FadeOut(rows),
            FadeOut(high_label),
            FadeOut(low_label),
        )