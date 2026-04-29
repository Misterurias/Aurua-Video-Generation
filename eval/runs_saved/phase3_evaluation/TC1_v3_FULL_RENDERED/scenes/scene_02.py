from manim import *

class Scene02(Scene):
    def construct(self):
        title = Text("Negative Gradient: Steepest Descent", font_size=34, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.8)

        # Cost surface as nested ellipses (contour lines of a bowl)
        center = LEFT * 2.5 + DOWN * 0.5
        contours = VGroup(
            Ellipse(width=7.0, height=4.0, color=BLUE_E, stroke_opacity=0.6),
            Ellipse(width=5.5, height=3.1, color=BLUE_D, stroke_opacity=0.7),
            Ellipse(width=4.0, height=2.3, color=BLUE, stroke_opacity=0.8),
            Ellipse(width=2.6, height=1.5, color=BLUE_B, stroke_opacity=0.9),
            Ellipse(width=1.2, height=0.7, color=TEAL, stroke_opacity=1.0),
        )
        for c in contours:
            c.move_to(center)

        self.play(LaggedStart(*[Create(c) for c in contours], lag_ratio=0.15))
        self.wait(0.5)

        # Minimum marker
        minimum = Dot(center, color=YELLOW, radius=0.08)
        min_label = Text("minimum", font_size=20, color=YELLOW).next_to(minimum, DOWN, buff=0.15)
        self.play(FadeIn(minimum), FadeIn(min_label))
        self.wait(0.5)

        # Current parameters dot (on outer contour, upper right)
        current_pos = center + RIGHT * 2.6 + UP * 1.1
        param_dot = Dot(current_pos, color=WHITE, radius=0.11)
        param_label = Text("current params", font_size=20, color=WHITE).next_to(param_dot, UP, buff=0.15)
        self.play(FadeIn(param_dot), Write(param_label))
        self.wait(0.8)

        # Gradient arrow (uphill, away from center)
        direction = (current_pos - center)
        direction_unit = direction / ((direction[0]**2 + direction[1]**2)**0.5)
        grad_end = current_pos + direction_unit * 1.5
        grad_arrow = Arrow(current_pos, grad_end, color=RED, buff=0, stroke_width=6)
        grad_text = Text("gradient", font_size=22, color=RED).next_to(grad_arrow.get_end(), UR, buff=0.1)
        self.play(GrowArrow(grad_arrow), Write(grad_text))
        self.wait(1.2)

        # Negative gradient arrow (downhill, toward center)
        neg_end = current_pos - direction_unit * 1.5
        neg_arrow = Arrow(current_pos, neg_end, color=GREEN, buff=0, stroke_width=6)
        neg_text = Text("−gradient", font_size=22, color=GREEN).next_to(neg_arrow.get_end(), DL, buff=0.1)
        self.play(GrowArrow(neg_arrow), Write(neg_text))
        self.wait(1.0)

        # Steepest descent label
        steepest = Text("steepest descent", font_size=28, color=GREEN, weight=BOLD)
        steepest.to_edge(RIGHT).shift(UP * 1.5 + LEFT * 0.3)
        self.play(FadeIn(steepest))
        self.wait(1.2)

        # Animate the dot moving along the green arrow toward the minimum
        self.play(FadeOut(param_label))
        step1 = current_pos - direction_unit * 1.4
        step2 = center + direction_unit * 0.4
        step3 = center

        self.play(param_dot.animate.move_to(step1), run_time=1.2)
        self.wait(0.3)
        self.play(param_dot.animate.move_to(step2), run_time=1.0)
        self.wait(0.3)
        self.play(param_dot.animate.move_to(step3), run_time=0.9)
        self.play(Indicate(param_dot, color=YELLOW, scale_factor=1.6))
        self.wait(1.5)

        self.play(
            FadeOut(VGroup(title, contours, minimum, min_label, param_dot,
                           grad_arrow, grad_text, neg_arrow, neg_text, steepest))
        )
        self.wait(0.3)