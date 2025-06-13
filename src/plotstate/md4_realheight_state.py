#Concrete implementation of real height analysis with interactive figure
#Handles POLAN input and output
from src.plot.realheightanalysis import RealHeightAnalysisCanvas
from src.plotstate.base import PlotState
from src.utils.powerpreprocessing import convert_amplitude_to_power
import numpy as np

class Md4RealheightAnalysisState(PlotState):
    def create_canvas(self):
        canvas = RealHeightAnalysisCanvas(self.main)
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
        canvas.draw()
