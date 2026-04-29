from manim import *

class Scene01(Scene):
    def construct(self):
        title = Text("The Gradient Vector", font_size=36, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        # Build small neural network on the left
        # Input nodes
        i1 = Circle(radius=0.3, color=BLUE).move_to(LEFT*4.5 + UP*1.2)
        i2 = Circle(radius=0.3, color=BLUE).move_to(LEFT*4.5 + DOWN*1.2)
        # Hidden nodes
        h1 = Circle(radius=0.3, color=GREEN).move_to(LEFT*2.5 + UP*1.2)
        h2 = Circle(radius=0.3, color=GREEN).move_to(LEFT*2.5 + DOWN*1.2)
        # Output node
        o1 = Circle(radius=0.3, color=RED).move_to(LEFT*0.5)

        nodes = VGroup(i1, i2, h1, h2, o1)

        # Edges with labels
        e_w1 = Line(i1.get_right(), h1.get_left(), color=WHITE)
        e_w2 = Line(i2.get_right(), h2.get_left(), color=WHITE)
        e_o1 = Line(h1.get_right(), o1.get_left(), color=WHITE)
        e_o2 = Line(h2.get_right(), o1.get_left(), color=WHITE)
        edges = VGroup(e_w1, e_w2, e_o1, e_o2)

        lbl_w1 = Text("w₁", font_size=20, color=YELLOW).next_to(e_w1, UP, buff=0.1)
        lbl_w2 = Text("w₂", font_size=20, color=YELLOW).next_to(e_w2, DOWN, buff=0.1)
        lbl_b1 = Text("b₁", font_size=20, color=ORANGE).next_to(h1, UP, buff=0.1)
        lbl_b2 = Text("b₂", font_size=20, color=ORANGE).next_to(h2, DOWN, buff=0.1)
        labels = VGroup(lbl_w1, lbl_w2, lbl_b1, lbl_b2)

        self.play(FadeIn(nodes), Create(edges))
        self.play(Write(labels))
        self.wait(1)

        # Gradient vector on the right
        grad_title = Text("∇C", font_size=32, color=YELLOW).move_to(RIGHT*3 + UP*2.6)
        self.play(Write(grad_title))

        comps = VGroup(
            Text("∂C/∂w₁", font_size=22),
            Text("∂C/∂w₂", font_size=22),
            Text("∂C/∂b₁", font_size=22),
            Text("∂C/∂b₂", font_size=22),
        ).arrange(DOWN, buff=0.4).move_to(RIGHT*2.5 + DOWN*0.2)

        # Brackets
        lb = Line(comps.get_corner(UL)+LEFT*0.2+UP*0.1,
                  comps.get_corner(DL)+LEFT*0.2+DOWN*0.1, color=WHITE)
        lb_top = Line(lb.get_start(), lb.get_start()+RIGHT*0.2, color=WHITE)
        lb_bot = Line(lb.get_end(), lb.get_end()+RIGHT*0.2, color=WHITE)
        rb = Line(comps.get_corner(UR)+RIGHT*0.2+UP*0.1,
                  comps.get_corner(DR)+RIGHT*0.2+DOWN*0.1, color=WHITE)
        rb_top = Line(rb.get_start(), rb.get_start()+LEFT*0.2, color=WHITE)
        rb_bot = Line(rb.get_end(), rb.get_end()+LEFT*0.2, color=WHITE)
        brackets = VGroup(lb, lb_top, lb_bot, rb, rb_top, rb_bot)

        self.play(FadeIn(comps), Create(brackets))
        self.wait(1)

        # Sensitivity bars
        sens_label = Text("sensitivity", font_size=20, color=WHITE).move_to(RIGHT*5.2 + UP*2.4)
        self.play(Write(sens_label))

        magnitudes = [1.4, 0.6, 1.0, 0.4]
        colors = [YELLOW, BLUE, GREEN, RED]
        bars = VGroup()
        for comp, m, c in zip(comps, magnitudes, colors):
            bar = Rectangle(width=m, height=0.25, fill_color=c, fill_opacity=0.9, stroke_color=c)
            bar.next_to(comp, RIGHT, buff=0.6)
            bar.align_to(comp, LEFT)
            bar.shift(RIGHT*1.2)
            bars.add(bar)

        # Highlight each component in turn with a color pulse and grow its bar
        related_edges = [e_w1, e_w2, h1, h2]
        for comp, bar, c, rel in zip(comps, bars, colors, related_edges):
            self.play(
                Indicate(comp, color=c, scale_factor=1.2),
                Indicate(rel, color=c, scale_factor=1.3),
                GrowFromEdge(bar, LEFT),
                run_time=1.2
            )

        self.wait(2)

        self.play(
            FadeOut(nodes), FadeOut(edges), FadeOut(labels),
            FadeOut(comps), FadeOut(brackets), FadeOut(bars),
            FadeOut(sens_label), FadeOut(grad_title), FadeOut(title)
        )
        self.wait(0.5)