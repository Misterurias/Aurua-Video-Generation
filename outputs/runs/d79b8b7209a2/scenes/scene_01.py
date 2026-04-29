from manim import *

class Scene01(Scene):
    def construct(self):
        title = Text("The Gradient Vector ∇C", font_size=36, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        # Build a small neural network on the left side
        # Input layer: 2 nodes, Hidden layer: 2 nodes, Output: 1 node
        net_center = LEFT * 3.5

        in1 = Circle(radius=0.3, color=BLUE).move_to(net_center + UP * 1.2 + LEFT * 1.5)
        in2 = Circle(radius=0.3, color=BLUE).move_to(net_center + DOWN * 1.2 + LEFT * 1.5)
        h1 = Circle(radius=0.3, color=GREEN).move_to(net_center + UP * 1.2 + RIGHT * 0.5)
        h2 = Circle(radius=0.3, color=GREEN).move_to(net_center + DOWN * 1.2 + RIGHT * 0.5)
        out = Circle(radius=0.3, color=RED).move_to(net_center + RIGHT * 2.3)

        nodes = VGroup(in1, in2, h1, h2, out)

        # Edges with labels
        e1 = Line(in1.get_right(), h1.get_left(), color=WHITE)
        e2 = Line(in1.get_right(), h2.get_left(), color=WHITE)
        e3 = Line(in2.get_right(), h1.get_left(), color=WHITE)
        e4 = Line(in2.get_right(), h2.get_left(), color=WHITE)
        e5 = Line(h1.get_right(), out.get_left(), color=WHITE)
        e6 = Line(h2.get_right(), out.get_left(), color=WHITE)
        edges = VGroup(e1, e2, e3, e4, e5, e6)

        w1_lbl = Text("w₁", font_size=18, color=WHITE).next_to(e1.get_center(), UP, buff=0.05)
        w2_lbl = Text("w₂", font_size=18, color=WHITE).next_to(e4.get_center(), DOWN, buff=0.05)
        b1_lbl = Text("b₁", font_size=18, color=WHITE).next_to(h1, UP, buff=0.1)
        b2_lbl = Text("b₂", font_size=18, color=WHITE).next_to(h2, DOWN, buff=0.1)
        edge_labels = VGroup(w1_lbl, w2_lbl, b1_lbl, b2_lbl)

        self.play(Create(nodes), run_time=1.2)
        self.play(Create(edges), run_time=1.2)
        self.play(FadeIn(edge_labels))
        self.wait(1)

        # Vector on the right
        vec_title = Text("∇C =", font_size=28, color=YELLOW).shift(RIGHT * 1.8 + UP * 2.2)

        comps = VGroup(
            Text("∂C/∂w₁", font_size=24),
            Text("∂C/∂w₂", font_size=24),
            Text("∂C/∂b₁", font_size=24),
            Text("∂C/∂b₂", font_size=24),
        ).arrange(DOWN, buff=0.3)
        comps.next_to(vec_title, DOWN, buff=0.3).shift(RIGHT * 0.3)

        lbrack = Line(comps.get_corner(UL) + LEFT * 0.2 + UP * 0.1,
                      comps.get_corner(DL) + LEFT * 0.2 + DOWN * 0.1, color=WHITE)
        ltop = Line(lbrack.get_start(), lbrack.get_start() + RIGHT * 0.2, color=WHITE)
        lbot = Line(lbrack.get_end(), lbrack.get_end() + RIGHT * 0.2, color=WHITE)
        rbrack = Line(comps.get_corner(UR) + RIGHT * 0.2 + UP * 0.1,
                      comps.get_corner(DR) + RIGHT * 0.2 + DOWN * 0.1, color=WHITE)
        rtop = Line(rbrack.get_start(), rbrack.get_start() + LEFT * 0.2, color=WHITE)
        rbot = Line(rbrack.get_end(), rbrack.get_end() + LEFT * 0.2, color=WHITE)
        brackets = VGroup(lbrack, ltop, lbot, rbrack, rtop, rbot)

        self.play(Write(vec_title), Create(brackets), FadeIn(comps))
        self.wait(1)

        # Highlight each component with magnitude and "sensitivity" label
        magnitudes = ["0.8", "0.2", "1.5", "0.4"]
        targets = [(w1_lbl, e1), (w2_lbl, e4), (b1_lbl, h1), (b2_lbl, h2)]

        sens_label = Text("sensitivity", font_size=22, color=YELLOW)

        for i, (comp, mag) in enumerate(zip(comps, magnitudes)):
            edge_lbl, edge_obj = targets[i]
            mag_text = Text(f"= {mag}", font_size=22, color=YELLOW).next_to(comp, RIGHT, buff=0.3)
            sens = sens_label.copy().next_to(mag_text, RIGHT, buff=0.3)

            self.play(
                Indicate(comp, color=YELLOW, scale_factor=1.2),
                Indicate(edge_lbl, color=YELLOW, scale_factor=1.4),
                Indicate(edge_obj, color=YELLOW),
                run_time=0.8,
            )
            self.play(FadeIn(mag_text), FadeIn(sens), run_time=0.6)
            self.wait(0.8)
            self.play(FadeOut(mag_text), FadeOut(sens), run_time=0.4)

        self.wait(1)
        self.play(
            FadeOut(title), FadeOut(nodes), FadeOut(edges), FadeOut(edge_labels),
            FadeOut(vec_title), FadeOut(comps), FadeOut(brackets)
        )
        self.wait(0.3)