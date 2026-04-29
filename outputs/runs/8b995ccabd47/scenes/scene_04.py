from manim import *
import random

class Scene04(Scene):
    def construct(self):
        title = Text("Averaging Nudges Across Training Examples", font_size=32, color=YELLOW)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.8)

        # Build a grid of training example icons with small arrows
        random.seed(7)
        icons = VGroup()
        arrows = VGroup()
        rows, cols = 3, 5
        nudges = []
        for r in range(rows):
            for c in range(cols):
                box = Square(side_length=0.6, color=BLUE, fill_opacity=0.2, stroke_width=2)
                box.move_to(np.array([-3.6 + c * 1.0, 1.4 - r * 1.1, 0]))
                # small nudge value between -1 and 1
                nudge = random.uniform(-1, 1)
                nudges.append(nudge)
                arr = Arrow(
                    start=box.get_center() + DOWN * 0.05,
                    end=box.get_center() + RIGHT * (0.45 * nudge) + DOWN * 0.05,
                    buff=0,
                    stroke_width=3,
                    max_tip_length_to_length_ratio=0.4,
                    color=GREEN if nudge > 0 else RED,
                )
                icons.add(box)
                arrows.add(arr)

        grid = VGroup(icons, arrows).move_to(ORIGIN + UP * 0.3)
        grid_label = Text("training examples & their suggested nudges", font_size=22, color=WHITE)
        grid_label.next_to(grid, UP, buff=0.3)

        self.play(FadeIn(icons, lag_ratio=0.05), run_time=1.5)
        self.play(Write(grid_label))
        self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.05), run_time=2)
        self.wait(1.2)

        # Collect arrows: animate all moving toward center and averaging
        avg = sum(nudges) / len(nudges)
        center_point = DOWN * 0.5

        avg_arrow = Arrow(
            start=center_point + LEFT * 0,
            end=center_point + RIGHT * (1.8 * avg / max(abs(avg), 0.3)),
            buff=0,
            stroke_width=8,
            color=YELLOW,
        )

        self.play(
            FadeOut(icons),
            FadeOut(grid_label),
            *[a.animate.move_to(center_point).set_opacity(0.4) for a in arrows],
            run_time=1.8,
        )
        self.play(
            FadeOut(arrows),
            GrowArrow(avg_arrow),
            run_time=1.2,
        )

        avg_label = Text("averaged nudges  ≈  −∇C", font_size=28, color=YELLOW)
        avg_label.next_to(avg_arrow, UP, buff=0.4)
        self.play(Write(avg_label))
        self.wait(1.5)

        # Move everything up to make room for number line
        top_group = VGroup(avg_arrow, avg_label)
        self.play(top_group.animate.shift(UP * 1.3), FadeOut(title), run_time=1)

        # Number line for the weight
        nl = NumberLine(
            x_range=[-3, 3, 1],
            length=8,
            include_numbers=False,
            color=WHITE,
        )
        nl.shift(DOWN * 1.2)
        w_label = Text("w", font_size=26, color=WHITE)

        dot = Dot(color=BLUE, radius=0.14).move_to(nl.n2p(1.2))
        w_label.next_to(dot, UP, buff=0.2)

        self.play(Create(nl), FadeIn(dot), Write(w_label))
        self.wait(0.5)

        # Shift in direction of avg
        direction = 1 if avg > 0 else -1
        new_x = 1.2 + direction * 1.6
        new_pos = nl.n2p(new_x)

        update_label = Text("parameter update", font_size=26, color=GREEN)
        update_label.next_to(nl, DOWN, buff=0.5)

        shift_arrow = Arrow(
            start=nl.n2p(1.2) + UP * 0.5,
            end=new_pos + UP * 0.5,
            buff=0.1,
            color=GREEN,
            stroke_width=5,
        )

        self.play(GrowArrow(shift_arrow))
        self.play(
            dot.animate.move_to(new_pos),
            w_label.animate.next_to(Dot().move_to(new_pos), UP, buff=0.2),
            run_time=1.5,
        )
        self.play(Write(update_label))
        self.wait(2)

        self.play(
            FadeOut(VGroup(top_group, nl, dot, w_label, shift_arrow, update_label))
        )
        self.wait(0.3)