#Concrete implementation of real height analysis with interactive figure
#Handles POLAN input and output
from src.plot.realheightanalysis import RealHeightAnalysisCanvas
from src.plotstate.base import PlotState
import numpy as np

class Md4RealheightAnalysisState(PlotState):
    def create_canvas(self):
        canvas = RealHeightAnalysisCanvas(self.main)
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
            self.main.metadata['site']
        )
