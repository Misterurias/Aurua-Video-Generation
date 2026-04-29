from manim import *

class Scene02(Scene):
    def construct(self):
        title = Text("Total Cost Across All Training Examples", font_size=32, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.8)

        # Create small network icons (3 dots stacked = mini network)
        def make_mini_net(color=BLUE):
            layer1 = VGroup(*[Dot(radius=0.06, color=color) for _ in range(3)]).arrange(DOWN, buff=0.1)
            layer2 = VGroup(*[Dot(radius=0.06, color=color) for _ in range(2)]).arrange(DOWN, buff=0.1)
            layer3 = Dot(radius=0.06, color=color)
            net = VGroup(layer1, layer2, layer3).arrange(RIGHT, buff=0.2)
            lines = VGroup()
            for d1 in layer1:
                for d2 in layer2:
                    lines.add(Line(d1.get_center(), d2.get_center(), stroke_width=1, color=GREY))
            for d2 in layer2:
                lines.add(Line(d2.get_center(), layer3.get_center(), stroke_width=1, color=GREY))
            return VGroup(lines, net)

        labels_text = ["Example 1", "Example 2", "Example 3", "...", "Example N"]
        cost_values = ["0.42", "0.18", "0.65", "", "0.31"]
        cost_color = GREEN

        items = VGroup()
        cost_labels = VGroup()
        ex_labels = VGroup()

        for i, (lbl, cv) in enumerate(zip(labels_text, cost_values)):
            if lbl == "...":
                icon = Text("· · ·", font_size=28, color=BLUE)
            else:
                icon = make_mini_net()
            cost = Text(cv, font_size=22, color=cost_color) if cv else Text("", font_size=22)
            ex_lbl = Text(lbl, font_size=18, color=WHITE)

            group = VGroup(cost, icon, ex_lbl).arrange(DOWN, buff=0.2)
            items.add(group)
            cost_labels.add(cost)
            ex_labels.add(ex_lbl)

        items.arrange(RIGHT, buff=0.55)
        items.shift(UP * 0.6)

        self.play(*[FadeIn(it) for it in items], run_time=2)
        self.wait(1)

        # Highlight the cost values
        self.play(*[Indicate(c, color=YELLOW) for c in cost_labels if c.text], run_time=1.2)
        self.wait(0.5)

        # Averaging bracket below
        bracket_left = Text("[", font_size=80, color=WHITE)
        bracket_right = Text("]", font_size=80, color=WHITE)
        avg_label = Text("average", font_size=22, color=YELLOW)

        bracket_left.move_to(DOWN * 1.2 + LEFT * 3.5)
        bracket_right.move_to(DOWN * 1.2 + RIGHT * 3.5)
        avg_label.next_to(bracket_left, LEFT, buff=0.2)

        self.play(FadeIn(bracket_left), FadeIn(bracket_right), Write(avg_label))
        self.wait(0.4)

        # Flow costs into bracket
        flowing = []
        target_point = DOWN * 1.2
        for c in cost_labels:
            if c.text:
                flowing.append(c.animate.move_to(target_point).scale(0.6).set_color(YELLOW))
        self.play(*flowing, run_time=1.8)
        self.wait(0.3)

        # Replace with Total Cost value
        total_cost = Text("Total Cost = 0.39", font_size=36, color=YELLOW, weight=BOLD)
        total_cost.move_to(DOWN * 1.2)

        self.play(
            FadeOut(cost_labels),
            FadeIn(total_cost),
        )
        self.wait(1)

        # Function label below
        func_label = Text("Total Cost = f(all weights and biases)", font_size=28, color=WHITE)
        func_label.next_to(total_cost, DOWN, buff=0.6)
        self.play(Write(func_label))
        self.wait(2.5)

        self.play(
            FadeOut(items), FadeOut(bracket_left), FadeOut(bracket_right),
            FadeOut(avg_label), FadeOut(total_cost), FadeOut(func_label),
            FadeOut(title)
        )
        self.wait(0.3)