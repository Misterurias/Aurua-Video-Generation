from manim import *

class Scene04(Scene):
    def construct(self):
        title = Text("Averaging Nudges → Negative Gradient", font_size=34, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.8)

        # Helper to make a small gradient vector column
        def make_vec(values, color=BLUE):
            entries = VGroup(*[Text(v, font_size=20, color=color) for v in values])
            entries.arrange(DOWN, buff=0.12)
            box = Rectangle(
                width=entries.width + 0.4,
                height=entries.height + 0.3,
                color=color,
                stroke_width=2,
            )
            box.move_to(entries.get_center())
            return VGroup(box, entries)

        vec1 = make_vec(["+0.21", "−0.13", "+0.05", "−0.42"], BLUE)
        vec2 = make_vec(["+0.18", "−0.20", "+0.11", "−0.35"], GREEN)
        vec3 = make_vec(["+0.24", "−0.09", "+0.02", "−0.46"], RED)

        label1 = Text("training example 1", font_size=20, color=BLUE)
        label2 = Text("training example 2", font_size=20, color=GREEN)
        label3 = Text("training example 3", font_size=20, color=RED)

        row1 = VGroup(label1, vec1).arrange(RIGHT, buff=0.4)
        row2 = VGroup(label2, vec2).arrange(RIGHT, buff=0.4)
        row3 = VGroup(label3, vec3).arrange(RIGHT, buff=0.4)

        rows = VGroup(row1, row2, row3).arrange(DOWN, buff=0.4)
        rows.shift(LEFT * 3.2 + DOWN * 0.3)

        self.play(FadeIn(row1, shift=RIGHT))
        self.wait(0.4)
        self.play(FadeIn(row2, shift=RIGHT))
        self.wait(0.4)
        self.play(FadeIn(row3, shift=RIGHT))
        self.wait(1.0)

        # Summation symbol with division
        sum_label = Text("(1/3) · Σ", font_size=36, color=WHITE)
        sum_label.move_to(RIGHT * 1.2 + DOWN * 0.3)
        self.play(Write(sum_label))
        self.wait(0.5)

        # Arrows merging from each vector to the sum point
        arrow1 = Arrow(vec1.get_right(), sum_label.get_left(), buff=0.15, color=BLUE, stroke_width=3)
        arrow2 = Arrow(vec2.get_right(), sum_label.get_left(), buff=0.15, color=GREEN, stroke_width=3)
        arrow3 = Arrow(vec3.get_right(), sum_label.get_left(), buff=0.15, color=RED, stroke_width=3)

        self.play(GrowArrow(arrow1), GrowArrow(arrow2), GrowArrow(arrow3))
        self.wait(1.0)

        # Averaged vector on the right
        avg_vec = make_vec(["+0.21", "−0.14", "+0.06", "−0.41"], YELLOW)
        avg_vec.move_to(RIGHT * 4.3 + DOWN * 0.3)

        merge_arrow = Arrow(sum_label.get_right(), avg_vec.get_left(), buff=0.15, color=YELLOW, stroke_width=4)

        self.play(GrowArrow(merge_arrow))
        self.play(FadeIn(avg_vec, shift=RIGHT))
        self.wait(0.6)

        avg_label = Text("−∇C", font_size=30, color=YELLOW, weight=BOLD)
        avg_label.next_to(avg_vec, UP, buff=0.25)
        sub_label = Text("negative gradient (average)", font_size=18, color=YELLOW)
        sub_label.next_to(avg_vec, DOWN, buff=0.25)

        self.play(Write(avg_label), FadeIn(sub_label))
        self.play(Indicate(avg_vec, color=YELLOW, scale_factor=1.1))
        self.wait(2.5)

        self.play(
            FadeOut(rows), FadeOut(arrow1), FadeOut(arrow2), FadeOut(arrow3),
            FadeOut(sum_label), FadeOut(merge_arrow),
            FadeOut(avg_vec), FadeOut(avg_label), FadeOut(sub_label),
            FadeOut(title),
        )