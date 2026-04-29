from manim import *

class Scene03(Scene):
    def construct(self):
        title = Text("Activation Magnitude Drives Influence", font_size=32, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        # Two source neurons
        neuron_A = Circle(radius=0.5, color=YELLOW, fill_opacity=0.8).shift(LEFT*4 + UP*1.5)
        neuron_B = Circle(radius=0.5, color=BLUE, fill_opacity=0.25).shift(LEFT*4 + DOWN*1.5)

        # Target neuron
        neuron_out = Circle(radius=0.6, color=WHITE, fill_opacity=0.3).shift(RIGHT*2)

        label_A = Text("a = 0.9", font_size=26, color=YELLOW).next_to(neuron_A, LEFT, buff=0.3)
        label_B = Text("a = 0.1", font_size=26, color=BLUE).next_to(neuron_B, LEFT, buff=0.3)
        label_out = Text("z", font_size=28, color=WHITE).move_to(neuron_out.get_center())

        # Connections
        line_A = Line(neuron_A.get_right(), neuron_out.get_left(), color=YELLOW, stroke_width=5)
        line_B = Line(neuron_B.get_right(), neuron_out.get_left(), color=BLUE, stroke_width=2)

        wA_label = Text("w_A", font_size=24, color=YELLOW).next_to(line_A.get_center(), UP, buff=0.15)
        wB_label = Text("w_B", font_size=24, color=BLUE).next_to(line_B.get_center(), DOWN, buff=0.15)

        self.play(
            FadeIn(neuron_A), FadeIn(neuron_B), FadeIn(neuron_out),
            Write(label_A), Write(label_B), Write(label_out),
        )
        self.play(Create(line_A), Create(line_B), Write(wA_label), Write(wB_label))
        self.wait(1)

        # Nudge arrows on each weight
        nudge_A = Arrow(start=ORIGIN, end=UP*0.6, color=GREEN, buff=0).next_to(wA_label, RIGHT, buff=0.2)
        nudge_B = Arrow(start=ORIGIN, end=UP*0.6, color=GREEN, buff=0).next_to(wB_label, RIGHT, buff=0.2)
        nudge_text_A = Text("Δw", font_size=20, color=GREEN).next_to(nudge_A, RIGHT, buff=0.1)
        nudge_text_B = Text("Δw", font_size=20, color=GREEN).next_to(nudge_B, RIGHT, buff=0.1)

        self.play(GrowArrow(nudge_A), GrowArrow(nudge_B), Write(nudge_text_A), Write(nudge_text_B))
        self.wait(0.8)

        # Resulting bars
        bar_label = Text("Resulting Δz", font_size=22, color=WHITE).shift(RIGHT*4.5 + UP*2.5)

        baseline = Line(RIGHT*3.5 + DOWN*1.5, RIGHT*6 + DOWN*1.5, color=GREY)

        bar_A = Rectangle(width=0.6, height=0.01, color=YELLOW, fill_opacity=0.9, fill_color=YELLOW)
        bar_A.move_to(RIGHT*4.0 + DOWN*1.5)
        bar_A.align_to(baseline, DOWN)

        bar_B = Rectangle(width=0.6, height=0.01, color=BLUE, fill_opacity=0.9, fill_color=BLUE)
        bar_B.move_to(RIGHT*5.5 + DOWN*1.5)
        bar_B.align_to(baseline, DOWN)

        bar_A_lbl = Text("w_A", font_size=20, color=YELLOW).next_to(RIGHT*4.0 + DOWN*1.5, DOWN, buff=0.2)
        bar_B_lbl = Text("w_B", font_size=20, color=BLUE).next_to(RIGHT*5.5 + DOWN*1.5, DOWN, buff=0.2)

        self.play(Write(bar_label), Create(baseline), Write(bar_A_lbl), Write(bar_B_lbl))
        self.wait(0.3)

        # Grow bars proportionally to activation
        target_A = Rectangle(width=0.6, height=2.7, color=YELLOW, fill_opacity=0.9, fill_color=YELLOW)
        target_A.next_to(baseline.get_start() + RIGHT*0.5, UP, buff=0).shift(RIGHT*0)
        target_A.move_to(RIGHT*4.0 + DOWN*1.5 + UP*1.35)

        target_B = Rectangle(width=0.6, height=0.3, color=BLUE, fill_opacity=0.9, fill_color=BLUE)
        target_B.move_to(RIGHT*5.5 + DOWN*1.5 + UP*0.15)

        self.play(Transform(bar_A, target_A), Transform(bar_B, target_B), run_time=2)
        self.wait(1)

        # Indicate the larger one
        self.play(Indicate(bar_A, color=YELLOW, scale_factor=1.1))
        self.wait(0.5)

        # Conclusion text
        conclusion = Text("larger activation → stronger influence on cost",
                          font_size=28, color=GREEN).to_edge(DOWN)
        self.play(Write(conclusion))
        self.wait(2.5)

        self.play(
            FadeOut(title), FadeOut(conclusion),
            FadeOut(neuron_A), FadeOut(neuron_B), FadeOut(neuron_out),
            FadeOut(label_A), FadeOut(label_B), FadeOut(label_out),
            FadeOut(line_A), FadeOut(line_B),
            FadeOut(wA_label), FadeOut(wB_label),
            FadeOut(nudge_A), FadeOut(nudge_B),
            FadeOut(nudge_text_A), FadeOut(nudge_text_B),
            FadeOut(bar_A), FadeOut(bar_B),
            FadeOut(bar_label), FadeOut(baseline),
            FadeOut(bar_A_lbl), FadeOut(bar_B_lbl),
        )
        self.wait(0.3)