from manim import *

class Scene02(Scene):
    def construct(self):
        title = Text("Negative Gradient: Path of Steepest Descent", font_size=32, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.8)

        # Cost surface as concentric ellipses (contour lines)
        center = LEFT * 2.5 + DOWN * 0.3
        contours = VGroup()
        colors = [BLUE_E, BLUE_D, BLUE_C, BLUE_B, BLUE_A]
        for i, c in enumerate(colors):
            e = Ellipse(width=1.2 + i * 1.0, height=0.8 + i * 0.7, color=c, stroke_width=2)
            e.move_to(center)
            contours.add(e)

        min_dot = Dot(center, color=GREEN, radius=0.07)
        min_label = Text("min", font_size=20, color=GREEN).next_to(min_dot, DOWN, buff=0.1)

        self.play(Create(contours, lag_ratio=0.2), run_time=2)
        self.play(FadeIn(min_dot), FadeIn(min_label))
        self.wait(0.6)

        # Current parameter position (on outer contour, upper right of center)
        current_pos = center + RIGHT * 2.0 + UP * 1.2
        param_dot = Dot(current_pos, color=RED, radius=0.1)
        param_label = Text("current", font_size=20, color=RED).next_to(param_dot, UR, buff=0.1)

        self.play(FadeIn(param_dot), Write(param_label))
        self.wait(0.8)

        # Gradient arrow points uphill (away from min)
        uphill_dir = (current_pos - center)
        uphill_dir = uphill_dir / (uphill_dir[0]**2 + uphill_dir[1]**2)**0.5
        grad_end = current_pos + uphill_dir * 1.3
        grad_arrow = Arrow(current_pos, grad_end, color=RED, buff=0, stroke_width=5)
        grad_text = Text("gradient (uphill)", font_size=22, color=RED).next_to(grad_arrow, RIGHT, buff=0.15)

        self.play(GrowArrow(grad_arrow), Write(grad_text))
        self.wait(1.2)

        # Negative gradient arrow points downhill (toward min)
        neg_end = current_pos - uphill_dir * 1.3
        neg_arrow = Arrow(current_pos, neg_end, color=GREEN, buff=0, stroke_width=5)
        neg_text = Text("−gradient (downhill)", font_size=22, color=GREEN).next_to(neg_arrow, LEFT, buff=0.15).shift(DOWN*0.2)

        self.play(GrowArrow(neg_arrow), Write(neg_text))
        self.wait(1.5)

        # Bottom caption
        caption = Text("negative gradient → most efficient path to lower cost",
                       font_size=26, color=YELLOW)
        caption.to_edge(DOWN, buff=0.5)
        self.play(Write(caption))
        self.wait(1.0)

        # Animate dot moving along negative gradient toward the minimum
        self.play(FadeOut(param_label), FadeOut(grad_arrow), FadeOut(grad_text))
        self.wait(0.3)

        # Step the dot down in stages toward min
        step1 = current_pos + (center - current_pos) * 0.4
        step2 = current_pos + (center - current_pos) * 0.75
        step3 = center

        # Update neg arrow to follow dot
        self.play(param_dot.animate.move_to(step1),
                  neg_arrow.animate.put_start_and_end_on(step1, step1 + (center - step1)/((center-step1)[0]**2+(center-step1)[1]**2)**0.5 * 1.0),
                  neg_text.animate.next_to(step1, LEFT, buff=1.4),
                  run_time=1.5)
        self.wait(0.3)
        self.play(param_dot.animate.move_to(step2),
                  neg_arrow.animate.put_start_and_end_on(step2, step2 + (center - step2)/((center-step2)[0]**2+(center-step2)[1]**2+0.001)**0.5 * 0.7),
                  run_time=1.2)
        self.wait(0.3)
        self.play(param_dot.animate.move_to(step3),
                  FadeOut(neg_arrow), FadeOut(neg_text),
                  run_time=1.0)
        self.play(Indicate(param_dot, color=GREEN, scale_factor=1.5))
        self.wait(1.5)

        self.play(FadeOut(VGroup(title, contours, min_dot, min_label, param_dot, caption)))
        self.wait(0.3)