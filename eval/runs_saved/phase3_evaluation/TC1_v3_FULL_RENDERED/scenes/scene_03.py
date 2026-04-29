from manim import *

class Scene03(Scene):
    def construct(self):
        title = Text("Magnitude = Sensitivity", font_size=38, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.8)

        # Gradient vector recap
        grad_label = Text("∇C =", font_size=30)
        components = VGroup(
            Text("0.90", font_size=26, color=RED),
            Text("0.12", font_size=26, color=WHITE),
            Text("0.05", font_size=26, color=BLUE),
            Text("0.30", font_size=26, color=WHITE),
        ).arrange(DOWN, buff=0.2)

        bracket_l = Text("[", font_size=72)
        bracket_r = Text("]", font_size=72)
        bracket_l.next_to(components, LEFT, buff=0.15)
        bracket_r.next_to(components, RIGHT, buff=0.15)
        vec_group = VGroup(bracket_l, components, bracket_r)
        grad_label.next_to(vec_group, LEFT, buff=0.2)
        full_vec = VGroup(grad_label, vec_group)
        full_vec.move_to(ORIGIN).shift(UP * 0.3)

        self.play(FadeIn(full_vec))
        self.wait(1.2)

        # Highlight the two components we'll compare
        high_comp = components[0]
        low_comp = components[2]
        self.play(Indicate(high_comp, color=RED, scale_factor=1.5),
                  Indicate(low_comp, color=BLUE, scale_factor=1.5))
        self.wait(0.6)

        # Move vector to the left
        self.play(full_vec.animate.scale(0.8).to_edge(LEFT, buff=0.8))
        self.wait(0.4)

        # Build bars on the right
        baseline_y = -2.0
        # Tall bar (high sensitivity)
        tall_bar = Rectangle(
            width=0.8, height=2.7,
            fill_color=RED, fill_opacity=0.9, stroke_color=RED
        )
        tall_bar.move_to([0.5, baseline_y + 2.7/2, 0])
        tall_value = Text("0.90", font_size=24, color=RED)
        tall_value.next_to(tall_bar, UP, buff=0.15)
        tall_caption = Text("high sensitivity", font_size=20, color=RED)
        tall_caption.next_to(tall_bar, DOWN, buff=0.25)
        tall_caption2 = Text("adjust more", font_size=20, color=RED, weight=BOLD)
        tall_caption2.next_to(tall_caption, DOWN, buff=0.1)

        # Short bar (low sensitivity)
        short_bar = Rectangle(
            width=0.8, height=0.25,
            fill_color=BLUE, fill_opacity=0.5, stroke_color=BLUE
        )
        short_bar.move_to([3.5, baseline_y + 0.25/2, 0])
        short_value = Text("0.05", font_size=24, color=BLUE)
        short_value.next_to(short_bar, UP, buff=0.15)
        short_caption = Text("low sensitivity", font_size=20, color=BLUE)
        short_caption.next_to(short_bar, DOWN, buff=0.25).align_to(tall_caption, UP)
        short_caption2 = Text("adjust less", font_size=20, color=BLUE, weight=BOLD)
        short_caption2.next_to(short_caption, DOWN, buff=0.1)

        # Ground line
        ground = Line([-0.5, baseline_y, 0], [4.5, baseline_y, 0], color=WHITE)

        self.play(Create(ground))
        self.play(
            DrawBorderThenFill(tall_bar),
            FadeIn(tall_value),
        )
        self.play(FadeIn(tall_caption), FadeIn(tall_caption2))
        self.wait(0.8)

        self.play(
            DrawBorderThenFill(short_bar),
            FadeIn(short_value),
        )
        self.play(FadeIn(short_caption), FadeIn(short_caption2))
        self.wait(1.2)

        # Final emphasis
        self.play(
            Indicate(tall_bar, color=RED, scale_factor=1.1),
            Indicate(short_bar, color=BLUE, scale_factor=1.1),
        )
        self.wait(2.0)

        self.play(
            FadeOut(VGroup(
                title, full_vec, ground,
                tall_bar, tall_value, tall_caption, tall_caption2,
                short_bar, short_value, short_caption, short_caption2,
            ))
        )
        self.wait(0.3)