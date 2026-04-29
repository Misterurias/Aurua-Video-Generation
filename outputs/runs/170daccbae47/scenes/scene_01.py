from manim import *

class Scene01(Scene):
    def construct(self):
        title = Text("Negative Gradient", font_size=38, color=YELLOW, weight=BOLD)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        # Build a small neural network on the left
        node1 = Circle(radius=0.35, color=WHITE, fill_opacity=0.2).shift(LEFT*4.5 + UP*1.5)
        node2 = Circle(radius=0.35, color=WHITE, fill_opacity=0.2).shift(LEFT*4.5 + DOWN*1.5)
        node3 = Circle(radius=0.35, color=WHITE, fill_opacity=0.2).shift(LEFT*1.5 + DOWN*0)

        n1_label = Text("a₁", font_size=22).move_to(node1.get_center())
        n2_label = Text("a₂", font_size=22).move_to(node2.get_center())
        n3_label = Text("a₃", font_size=22).move_to(node3.get_center())

        # Connections (weights)
        conn1 = Line(node1.get_right(), node3.get_left(), color=BLUE, stroke_width=4)
        conn2 = Line(node2.get_right(), node3.get_left(), color=BLUE, stroke_width=4)

        w1_label = Text("w₁", font_size=22, color=BLUE).next_to(conn1.get_center(), UP, buff=0.1)
        w2_label = Text("w₂", font_size=22, color=BLUE).next_to(conn2.get_center(), DOWN, buff=0.1)

        # Bias indicator on node3
        bias_marker = Text("b₁", font_size=22, color=ORANGE).next_to(node3, RIGHT, buff=0.2)

        network = VGroup(node1, node2, node3, n1_label, n2_label, n3_label,
                         conn1, conn2, w1_label, w2_label, bias_marker)

        self.play(Create(VGroup(node1, node2, node3)),
                  Write(VGroup(n1_label, n2_label, n3_label)))
        self.play(Create(VGroup(conn1, conn2)),
                  Write(VGroup(w1_label, w2_label)))
        self.play(Write(bias_marker))
        self.wait(0.8)

        # Vector on the right
        vec_label = Text("−∇C", font_size=32, color=YELLOW, weight=BOLD).shift(RIGHT*3.8 + UP*2.6)

        bracket_l = Line(UP*1.2, DOWN*1.2).shift(RIGHT*2.8 + UP*0.2)
        bracket_r = Line(UP*1.2, DOWN*1.2).shift(RIGHT*4.8 + UP*0.2)
        btl = Line(LEFT*0.2, RIGHT*0.0).shift(RIGHT*2.8 + UP*1.4)
        bbl = Line(LEFT*0.2, RIGHT*0.0).shift(RIGHT*2.8 + DOWN*1.0)
        btr = Line(LEFT*0.0, RIGHT*0.2).shift(RIGHT*4.8 + UP*1.4)
        bbr = Line(LEFT*0.0, RIGHT*0.2).shift(RIGHT*4.8 + DOWN*1.0)

        comp1 = Text("w₁", font_size=26, color=BLUE).shift(RIGHT*3.8 + UP*0.9)
        comp2 = Text("w₂", font_size=26, color=BLUE).shift(RIGHT*3.8 + UP*0.2)
        comp3 = Text("b₁", font_size=26, color=ORANGE).shift(RIGHT*3.8 + DOWN*0.5)

        vector = VGroup(bracket_l, bracket_r, btl, bbl, btr, bbr, comp1, comp2, comp3)

        self.play(Write(vec_label))
        self.play(Create(VGroup(bracket_l, bracket_r, btl, bbl, btr, bbr)))
        self.play(FadeIn(comp1), FadeIn(comp2), FadeIn(comp3))
        self.wait(0.8)

        # Arrows from network to vector components
        arr1 = Arrow(w1_label.get_right(), comp1.get_left(), color=BLUE, buff=0.15, stroke_width=3)
        arr2 = Arrow(w2_label.get_right(), comp2.get_left(), color=BLUE, buff=0.15, stroke_width=3)
        arr3 = Arrow(bias_marker.get_right(), comp3.get_left(), color=ORANGE, buff=0.15, stroke_width=3)

        self.play(GrowArrow(arr1))
        self.play(GrowArrow(arr2))
        self.play(GrowArrow(arr3))
        self.wait(0.8)

        annotation = Text("one component per parameter", font_size=24, color=WHITE)
        annotation.to_edge(DOWN, buff=0.6)
        self.play(Write(annotation))
        self.wait(2.5)

        self.play(FadeOut(VGroup(title, network, vec_label, vector,
                                  arr1, arr2, arr3, annotation)))
        self.wait(0.3)