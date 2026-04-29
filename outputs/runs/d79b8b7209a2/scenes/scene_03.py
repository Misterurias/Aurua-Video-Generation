from manim import *

class Scene03(Scene):
    def construct(self):
        title = Text("Activation Influences Gradient", font_size=34, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.8)

        # Input neurons
        n_high = Circle(radius=0.5, color=BLUE, fill_opacity=0.6)
        n_high.shift(LEFT * 4 + UP * 1.5)
        n_low = Circle(radius=0.5, color=BLUE, fill_opacity=0.6)
        n_low.shift(LEFT * 4 + DOWN * 1.5)

        # Output neuron
        n_out = Circle(radius=0.6, color=GREEN, fill_opacity=0.6)
        n_out.shift(RIGHT * 3)

        # Activation labels
        high_val = Text("0.9", font_size=24, color=WHITE).move_to(n_high.get_center())
        low_val = Text("0.1", font_size=24, color=WHITE).move_to(n_low.get_center())
        out_label = Text("output", font_size=22, color=WHITE).next_to(n_out, DOWN, buff=0.2)

        high_tag = Text("high activation (0.9)", font_size=22, color=YELLOW)
        high_tag.next_to(n_high, LEFT, buff=0.3)
        low_tag = Text("low activation (0.1)", font_size=22, color=GREY_B)
        low_tag.next_to(n_low, LEFT, buff=0.3)

        self.play(
            Create(n_high), Create(n_low), Create(n_out),
            FadeIn(high_val), FadeIn(low_val), FadeIn(out_label),
        )
        self.play(FadeIn(high_tag), FadeIn(low_tag))
        self.wait(0.8)

        # Edges
        edge_high = Line(n_high.get_right(), n_out.get_left(), color=WHITE, stroke_width=3)
        edge_low = Line(n_low.get_right(), n_out.get_left(), color=WHITE, stroke_width=3)
        self.play(Create(edge_high), Create(edge_low))
        self.wait(0.5)

        # Gradient nudge arrows on edges
        # Big arrow on high-activation edge
        mid_high = edge_high.point_from_proportion(0.5)
        big_arrow = Arrow(
            start=mid_high + LEFT * 0.9 + DOWN * 0.3,
            end=mid_high + RIGHT * 0.9 + UP * 0.3,
            color=RED, buff=0, stroke_width=8,
        )
        big_label = Text("large nudge", font_size=20, color=RED)
        big_label.next_to(big_arrow, UP, buff=0.15)

        # Small arrow on low-activation edge
        mid_low = edge_low.point_from_proportion(0.5)
        small_arrow = Arrow(
            start=mid_low + LEFT * 0.25 + UP * 0.15,
            end=mid_low + RIGHT * 0.25 + DOWN * 0.15,
            color=ORANGE, buff=0, stroke_width=4,
        )
        small_label = Text("small nudge", font_size=18, color=ORANGE)
        small_label.next_to(small_arrow, DOWN, buff=0.15)

        self.play(GrowArrow(big_arrow), FadeIn(big_label))
        self.wait(0.6)
        self.play(GrowArrow(small_arrow), FadeIn(small_label))
        self.wait(0.8)

        # Indicate
        self.play(Indicate(big_arrow, color=RED, scale_factor=1.3))
        self.wait(0.3)

        # Caption
        caption = Text("larger activation → larger gradient component",
                       font_size=26, color=YELLOW, weight=BOLD)
        caption.to_edge(DOWN, buff=0.5)
        self.play(Write(caption))
        self.wait(2.5)

        self.play(
            FadeOut(VGroup(
                title, n_high, n_low, n_out, high_val, low_val, out_label,
                high_tag, low_tag, edge_high, edge_low,
                big_arrow, small_arrow, big_label, small_label, caption,
            ))
        )