#Concrete implementation of MD4 display ionogram PlotState
#Handles plotting of raw ionograms with MD4
from src.plot.ionogramcanvas import IonogramCanvas
from src.plotstate.base import PlotState
from src.utils.powerpreprocessing import convert_amplitude_to_power
import numpy as np

class Md4DisplayIonogramState(PlotState):
    def create_canvas(self):
        canvas = IonogramCanvas(self.main)
        self.update_canvas(canvas)
        return canvas

    def update_canvas(self, canvas):
        freqs = self.main.freqs[self.main.lpointer:self.main.rpointer]
        heights = self.main.heights[self.main.lpointer:self.main.rpointer]
        dops = self.main.dops[self.main.lpointer:self.main.rpointer]
        signals = self.main.signals[self.main.lpointer:self.main.rpointer]

        power = convert_amplitude_to_power(signals)

        canvas.plot_scatter(
            freqs,
            heights,
            dops,
            power,
            self.main._selected_timestamp,
            self.main.metadata['datetime'],
            self.main.metadata['site']
        )
