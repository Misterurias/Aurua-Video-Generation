from manim import *

class Scene01(Scene):
    def construct(self):
        # Title
        title = Text("The Cost Function", font_size=34, color=YELLOW).to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        # Small neural network on the left
        layer1 = VGroup(*[Circle(radius=0.12, color=BLUE, fill_opacity=0.6) for _ in range(4)])
        layer1.arrange(DOWN, buff=0.2)
        layer2 = VGroup(*[Circle(radius=0.12, color=BLUE, fill_opacity=0.6) for _ in range(3)])
        layer2.arrange(DOWN, buff=0.3)
        layer2.next_to(layer1, RIGHT, buff=0.6)

        # Output layer (10 digits)
        output = VGroup(*[Circle(radius=0.15, color=WHITE, fill_opacity=0.4) for _ in range(10)])
        output.arrange(DOWN, buff=0.1)
        output.next_to(layer2, RIGHT, buff=0.6)

        # Network guess highlighted in red (e.g., index 7)
        guess_idx = 7
        output[guess_idx].set_color(RED).set_fill(RED, opacity=0.9)

        # Connections (sparse, for visual)
        connections = VGroup()
        for n1 in layer1:
            for n2 in layer2:
                connections.add(Line(n1.get_right(), n2.get_left(), stroke_width=0.7, stroke_opacity=0.4))
        for n2 in layer2:
            for n3 in output:
                connections.add(Line(n2.get_right(), n3.get_left(), stroke_width=0.5, stroke_opacity=0.3))

        network = VGroup(connections, layer1, layer2, output)
        network.move_to(LEFT * 4.2 + DOWN * 0.3)

        net_label = Text("Network output", font_size=20, color=WHITE)
        net_label.next_to(output, UP, buff=0.3)

        self.play(Create(layer1), Create(layer2), run_time=1)
        self.play(Create(connections), run_time=1)
        self.play(FadeIn(output), Write(net_label))
        self.wait(0.5)

        # Desired output vector on the right
        desired = VGroup(*[Circle(radius=0.15, color=WHITE, fill_opacity=0.2) for _ in range(10)])
        desired.arrange(DOWN, buff=0.1)
        desired.move_to(LEFT * 0.3 + DOWN * 0.3)

        correct_idx = 3
        desired[correct_idx].set_color(GREEN).set_fill(GREEN, opacity=0.9)

        desired_label = Text("Desired output", font_size=20, color=WHITE)
        desired_label.next_to(desired, UP, buff=0.3)

        self.play(FadeIn(desired), Write(desired_label))
        self.wait(0.5)

        # Cost Function box
        cost_box = Rectangle(width=2.0, height=1.0, color=YELLOW, fill_opacity=0.2)
        cost_box.move_to(RIGHT * 3 + DOWN * 0.3)
        cost_text = Text("Cost\nFunction", font_size=20, color=YELLOW).move_to(cost_box.get_center())

        self.play(Create(cost_box), Write(cost_text))
        self.wait(0.3)

        # Arrows from pairs to cost box
        arrows = VGroup()
        for i in range(10):
            mid = (output[i].get_center() + desired[i].get_center()) / 2
            a = Arrow(mid, cost_box.get_left(), buff=0.05, stroke_width=2,
                     max_tip_length_to_length_ratio=0.08, color=BLUE_C)
            arrows.add(a)

        self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.05), run_time=1.5)
        self.wait(0.5)

        # Cost scalar emerging
        cost_scalar = Text("Cost = 3.42", font_size=26, color=RED, weight=BOLD)
        cost_scalar.next_to(cost_box, RIGHT, buff=0.4)
        out_arrow = Arrow(cost_box.get_right(), cost_scalar.get_left(), buff=0.1, color=RED, stroke_width=3)

        self.play(GrowArrow(out_arrow), Write(cost_scalar))
        self.wait(1)

        # Caption
        caption = Text("Goal: minimize cost by adjusting weights and biases",
                      font_size=24, color=GREEN)
        caption.to_edge(DOWN, buff=0.5)
        self.play(Write(caption))
        self.wait(2.5)

        self.play(
            FadeOut(network), FadeOut(net_label),
            FadeOut(desired), FadeOut(desired_label),
            FadeOut(arrows), FadeOut(cost_box), FadeOut(cost_text),
            FadeOut(out_arrow), FadeOut(cost_scalar),
            FadeOut(caption), FadeOut(title)
        )
        self.wait(0.3)