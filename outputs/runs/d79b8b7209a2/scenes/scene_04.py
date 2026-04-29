from manim import *

class Scene04(Scene):
    def construct(self):
        title = Text("Averaging Gradients Across Examples", font_size=34, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.8)

        # Build three columns of small arrows representing per-example nudges
        def make_column(label_text, directions, color):
            arrows = VGroup()
            for d in directions:
                start = ORIGIN
                end = d
                arr = Arrow(start, end, buff=0, color=color, stroke_width=4, max_tip_length_to_length_ratio=0.25)
                arrows.add(arr)
            arrows.arrange(DOWN, buff=0.25)
            label = Text(label_text, font_size=22, color=WHITE)
            label.next_to(arrows, DOWN, buff=0.3)
            return VGroup(arrows, label)

        dirs1 = [RIGHT * 0.9 + UP * 0.3, RIGHT * 0.7 + DOWN * 0.4, RIGHT * 1.0]
        dirs2 = [RIGHT * 0.6 + UP * 0.5, RIGHT * 0.8, RIGHT * 0.5 + DOWN * 0.2]
        dirs3 = [RIGHT * 1.0 + DOWN * 0.2, RIGHT * 0.9 + UP * 0.2, RIGHT * 0.7 + UP * 0.4]

        col1 = make_column("Example 1", dirs1, BLUE)
        col2 = make_column("Example 2", dirs2, GREEN)
        col3 = make_column("Example 3", dirs3, RED)

        cols = VGroup(col1, col2, col3).arrange(RIGHT, buff=1.2)
        cols.shift(LEFT * 3 + DOWN * 0.3)

        self.play(FadeIn(col1), FadeIn(col2), FadeIn(col3))
        self.wait(1.2)

        # Highlight averaging step
        plus1 = Text("+", font_size=36, color=WHITE).move_to((col1.get_right() + col2.get_left()) / 2)
        plus2 = Text("+", font_size=36, color=WHITE).move_to((col2.get_right() + col3.get_left()) / 2)
        self.play(Write(plus1), Write(plus2))
        self.wait(0.6)

        self.play(
            Indicate(col1[0], color=YELLOW),
            Indicate(col2[0], color=YELLOW),
            Indicate(col3[0], color=YELLOW),
            run_time=1.2,
        )
        self.wait(0.5)

        # Averaged arrow on the right
        avg_arrow = Arrow(ORIGIN, RIGHT * 1.6 + UP * 0.15, buff=0, color=YELLOW, stroke_width=8)
        avg_arrow.shift(RIGHT * 4.2 + DOWN * 0.5)
        avg_label = Text("averaged nudges", font_size=22, color=YELLOW)
        avg_label.next_to(avg_arrow, UP, buff=0.25)
        approx = Text("≈ negative gradient", font_size=22, color=WHITE)
        approx.next_to(avg_arrow, DOWN, buff=0.3)

        # Arrow flow from columns to averaged result
        flow = Arrow(cols.get_right() + RIGHT * 0.1, avg_arrow.get_left() + LEFT * 0.1,
                     color=WHITE, stroke_width=4, buff=0.1)

        self.play(GrowArrow(flow))
        self.play(GrowArrow(avg_arrow), Write(avg_label))
        self.wait(0.6)
        self.play(Write(approx))
        self.wait(2.5)

        self.play(
            FadeOut(col1), FadeOut(col2), FadeOut(col3),
            FadeOut(plus1), FadeOut(plus2),
            FadeOut(flow), FadeOut(avg_arrow),
            FadeOut(avg_label), FadeOut(approx),
            FadeOut(title),
        )
        self.wait(0.3)