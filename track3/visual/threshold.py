"""Paste into the Wanim Playground to explore the simulated USDC/USDT price gate."""
from manim import *

# The web player supplies its own keyboard-accessible labels and slider.
HOST_CONTROLS = False

EXAMPLES = [9990, 9950, 9930]
POSITIONS = [-4.45, 0.45, 5.35]
GRID = "#314045"
GREEN = "#85D8B5"
BOUNDARY = "#DDEBD7"
ALERT = "#FFA579"
MUTED = "#A7B7B5"
BACKGROUND = "#142125"


def y_for(units):
    return (units - 10000) * 0.032


def mark_color(units):
    deviation = abs(units - 10000)
    if deviation > 50:
        return ALERT
    if deviation == 50:
        return BOUNDARY
    return GREEN


class QuoteThreshold(InteractiveScene):
    def blueprint(self):
        self.camera.background_color = BACKGROUND
        left, right = -5.20, 6.20
        band = Rectangle(width=right-left, height=3.2, stroke_width=0,
                         fill_color="#1C3532", fill_opacity=1)
        band.move_to([(left+right)/2, 0, 0])
        self.add(band)
        for units in [9900, 9950, 10000, 10050, 10100]:
            y = y_for(units)
            color = "#65857A" if abs(units - 10000) == 50 else GRID
            self.add(Line([left, y, 0], [right, y, 0], color=color, stroke_width=2))
        for x in POSITIONS:
            self.add(Line([x, -3.20, 0], [x, 3.20, 0], color=GRID, stroke_width=1))
        self.links = []
        for i in [0, 1]:
            start = [POSITIONS[i], y_for(EXAMPLES[i]), 0]
            end = [POSITIONS[i+1], y_for(EXAMPLES[i+1]), 0]
            link = Line(start, end, color=GREEN, stroke_width=5)
            self.links.append(link)
            self.add(link)
        self.dots = []
        for x in POSITIONS:
            point = Dot(radius=0.095, color=GREEN).move_to([x, 0, 0])
            self.dots.append(point)
            self.add(point)
        self.halo = Circle(radius=0.21, stroke_width=3, color=GREEN,
                           fill_color=GREEN, fill_opacity=0.10)
        self.add(self.halo)

        if not HOST_CONTROLS:
            self.add(Text("SIMULATED USDC / USDT  |  Request callback above 50 bp",
                          font_size=22, color="#EEF4ED").move_to([0, 3.66, 0]))
            for units, label in [[9900, "0.990"], [9950, "0.995"], [10000, "1.000"],
                                 [10050, "1.005"], [10100, "1.010"]]:
                self.add(Text(label, font_size=19, color=MUTED).move_to([-6.18, y_for(units), 0]))
            self.add(Text("Move the third quote", font_size=16, color=MUTED).move_to([-3.9, -3.65, 0]))
            slider = Slider(start=[-1.8, -3.67, 0], end=[5.35, -3.67, 0],
                            value_range=(9900, 10100), init_value=9930, color=GREEN)
            self.add(slider)
            self.add_reaction(lambda _: self.set_sample(2, int(round(slider.get_value())), 1))
            self.set_sample(2, 9930, 1)
        else:
            self.set_sample(0, 9990, 1)

    def set_sample(self, sample, units, progress):
        """Reveal earlier fixture samples and draw the current (possibly custom) quote."""
        threshold = abs(units - 10000)
        color = mark_color(units)
        x = POSITIONS[sample]
        if sample > 0:
            x = POSITIONS[sample-1] + (POSITIONS[sample] - POSITIONS[sample-1]) * max(0.001, progress)
        point = [x, y_for(units), 0]
        for i in [0, 1]:
            link = self.links[i]
            if i < sample:
                start = [POSITIONS[i], y_for(EXAMPLES[i]), 0]
                end = point if i+1 == sample else [POSITIONS[i+1], y_for(EXAMPLES[i+1]), 0]
                link.put_start_and_end_on(start, end)
                link.set_stroke(color=color if i+1 == sample else mark_color(EXAMPLES[i+1]),
                                width=5, opacity=1)
            else:
                link.set_stroke(opacity=0)
        for i in [0, 1, 2]:
            dot = self.dots[i]
            if i < sample:
                dot.move_to([POSITIONS[i], y_for(EXAMPLES[i]), 0])
                dot.set_color(mark_color(EXAMPLES[i])).set_opacity(1)
            elif i == sample:
                dot.move_to(point).set_color(color).set_opacity(1)
            else:
                dot.set_opacity(0)
        self.halo.move_to(point).set_stroke(color=color).set_fill(color=color, opacity=0.12)
        self.post_message("quote", [int(sample), int(units), int(threshold), threshold > 50])
