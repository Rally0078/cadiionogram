#Concrete implementation of MD4 display ionogram PlotState
#Handles plotting of raw ionograms with MD4
from src.plot.ionogramcanvas import IonogramCanvas
from src.plotstate.base import PlotState
import numpy as np

class Md4DisplayIonogramState(PlotState):
    def create_canvas(self):
        canvas = IonogramCanvas(self.main)
        self.update_canvas(canvas)
        return canvas

    def update_canvas(self, canvas):
        freqs = self.main.freqs[self.main.lpointer:self.main.rpointer]
        heights = self.main.heights[self.main.lpointer:self.main.rpointer]
        signals = self.main.signals[self.main.lpointer:self.main.rpointer]

        real_signals = np.median(np.abs(signals), axis=1)
        power = np.zeros_like(real_signals)
        mask = real_signals <= 0.0
        power[mask] = 0.0
        power[~mask] = 20 * np.log10(real_signals[~mask])

        canvas.plot_scatter(
            freqs,
            heights,
            power,
            self.main._selected_timestamp,
            self.main.metadata['datetime'],
            self.main.metadata['site']
        )
