"""Smoke test: confirm Manim renders a trivial scene."""
from manim import *


class HelloWorld(Scene):
    def construct(self):
        title = Text("Aurua renderer is alive", font_size=48, color=YELLOW)
        circle = Circle(radius=1.5, color=BLUE).next_to(title, DOWN, buff=0.8)

        self.play(Write(title))
        self.play(Create(circle))
        self.wait(1)
        self.play(Indicate(circle))
        self.wait(1)
        self.play(FadeOut(title), FadeOut(circle))