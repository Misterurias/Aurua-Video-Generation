from manim import *


class Scene04(Scene):
    def construct(self):
        title = Text("Averaging Nudges Across Examples", font_size=32, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        def make_vector(label_text, colors, heights, label_color):
            bars = VGroup()
            for c, h in zip(colors, heights):
                bar = Rectangle(width=0.5, height=h, fill_color=c, fill_opacity=0.85, stroke_width=1, stroke_color=WHITE)
                bars.add(bar)
            bars.arrange(DOWN, buff=0.05)
            label = Text(label_text, font_size=20, color=label_color)
            label.next_to(bars, DOWN, buff=0.2)
            return VGroup(bars, label)

        v1 = make_vector("example 1", [BLUE, GREEN, RED, YELLOW], [0.4, 0.7, 0.3, 0.5], BLUE)
        v2 = make_vector("example 2", [BLUE, GREEN, RED, YELLOW], [0.6, 0.3, 0.5, 0.4], GREEN)
        v3 = make_vector("example 3", [BLUE, GREEN, RED, YELLOW], [0.3, 0.5, 0.6, 0.7], RED)

        v1.move_to(LEFT * 4.5 + UP * 0.3)
        v2.move_to(LEFT * 2.2 + UP * 0.3)
        v3.move_to(LEFT * 0 + UP * 0.3)

        self.play(FadeIn(v1), FadeIn(v2), FadeIn(v3))
        self.wait(1)

        # Averaged vector
        avg = make_vector("averaged", [BLUE, GREEN, RED, YELLOW], [0.43, 0.5, 0.47, 0.53], WHITE)
        avg.move_to(RIGHT * 3.5 + UP * 0.3)
        avg.scale(1.15)

        # Arrows merging
        arrow1 = Arrow(v1[0].get_right(), avg[0].get_left(), buff=0.1, color=BLUE, stroke_width=3)
        arrow2 = Arrow(v2[0].get_right(), avg[0].get_left(), buff=0.1, color=GREEN, stroke_width=3)
        arrow3 = Arrow(v3[0].get_right(), avg[0].get_left(), buff=0.1, color=RED, stroke_width=3)

        self.play(GrowArrow(arrow1), GrowArrow(arrow2), GrowArrow(arrow3))
        self.play(FadeIn(avg))
        self.wait(1)

        avg_label = Text("averaged nudges ≈ −∇C", font_size=24, color=YELLOW)
        avg_label.next_to(avg, UP, buff=0.3)
        self.play(Write(avg_label))
        self.wait(1.5)

        quote = Text(
            '"this collection of averaged nudges is,\nloosely speaking, the negative gradient of the cost function"',
            font_size=20, color=WHITE,
        )
        quote.to_edge(DOWN, buff=0.4)
        self.play(FadeIn(quote))
        self.wait(4)

        self.play(
            FadeOut(v1), FadeOut(v2), FadeOut(v3),
            FadeOut(arrow1), FadeOut(arrow2), FadeOut(arrow3),
            FadeOut(avg), FadeOut(avg_label),
            FadeOut(quote), FadeOut(title),
        )
        self.wait(0.3)