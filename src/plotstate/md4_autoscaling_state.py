#Concrete implementation of MD4 scale ionogram PlotState
#Handles plotting of raw ionograms with MD4
from src.plot.autoscaling import ScaleIonogramCanvas
from src.plotstate.base import PlotState
from src.utils.powerpreprocessing import convert_amplitude_to_power
from src.utils.rawdatadiriterator import RawDataDirIterator

class Md4ScaleIonogramState(PlotState):
    def create_canvas(self):
        canvas = ScaleIonogramCanvas(self.main)
        self.update_canvas(canvas)
        return canvas

    def update_canvas(self, canvas):
        it = RawDataDirIterator(self.main.metadata, self.main.freqs, self.main.heights, self.main.dops, self.main.signals)
        freqs, heights, dops, signals = it[self.main._selected_timestamp]
        if self.main.extension == 'iono':
            power_prethres = signals[:, 1]
            power = power_prethres[power_prethres >=0 ]
            freqs = freqs[power_prethres >= 0] * 1e6
            heights = heights[power_prethres >= 0]
            dops = dops[power_prethres >=0 ]
        elif self.main.extension in ['md3', 'md4']:
            power = convert_amplitude_to_power(signals)
        else:
            raise TypeError("Input data is not the correct type for this canvas")

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
