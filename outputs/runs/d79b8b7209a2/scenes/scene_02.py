from manim import *

class Scene02(Scene):
    def construct(self):
        # Title
        title = Text("Negative Gradient: Steepest Descent", font_size=34, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.8)

        # Axes
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 5, 1],
            x_length=8,
            y_length=4.5,
            axis_config={"color": WHITE, "include_tip": True},
        ).shift(DOWN * 0.5)

        x_label = Text("w", font_size=26).next_to(axes.x_axis.get_end(), RIGHT, buff=0.2)
        y_label = Text("Cost", font_size=26).next_to(axes.y_axis.get_end(), UP, buff=0.2)

        self.play(Create(axes), Write(x_label), Write(y_label))
        self.wait(0.5)

        # Bowl-shaped parabola: C(w) = 0.5 * w^2 + 0.3
        parabola = axes.plot(lambda w: 0.5 * w**2 + 0.3, x_range=[-2.8, 2.8], color=BLUE)
        self.play(Create(parabola), run_time=1.5)
        self.wait(0.5)

        # Starting dot on the curve
        start_w = -2.2
        start_point = axes.c2p(start_w, 0.5 * start_w**2 + 0.3)
        dot = Dot(start_point, color=RED, radius=0.12)
        self.play(FadeIn(dot, scale=1.5))
        self.wait(0.5)

        # Arrow pointing downhill (toward the minimum)
        end_w = -0.6
        end_point = axes.c2p(end_w, 0.5 * end_w**2 + 0.3)
        arrow = Arrow(start_point, end_point, color=GREEN, buff=0.15, stroke_width=6)
        arrow_label = Text("negative gradient direction", font_size=24, color=GREEN)
        arrow_label.next_to(arrow, UP, buff=0.3).shift(LEFT * 0.3)

        self.play(GrowArrow(arrow), Write(arrow_label))
        self.wait(1.5)

        # Annotation
        annotation = Text("most efficient decrease", font_size=26, color=YELLOW, weight=BOLD)
        annotation.next_to(axes, DOWN, buff=0.3)
        self.play(FadeIn(annotation))
        self.wait(0.8)

        # Animate dot sliding down the curve toward the minimum
        def update_dot(mob, alpha):
            w = start_w + alpha * (0.0 - start_w)
            mob.move_to(axes.c2p(w, 0.5 * w**2 + 0.3))

        self.play(UpdateFromAlphaFunc(dot, update_dot), run_time=3)
        self.wait(1)

        # Indicate minimum
        self.play(Indicate(dot, color=YELLOW, scale_factor=1.6))
        self.wait(1.5)

        # Fade out
        self.play(
            FadeOut(title), FadeOut(axes), FadeOut(parabola),
            FadeOut(dot), FadeOut(arrow), FadeOut(arrow_label),
            FadeOut(annotation), FadeOut(x_label), FadeOut(y_label),
        )
        self.wait(0.3)