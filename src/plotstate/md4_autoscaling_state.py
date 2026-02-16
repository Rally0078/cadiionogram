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
        self.main.save_scale_button.setVisible(True)
        self.main.f_scale_box.setVisible(True)
        self.main.e_scale_box.setVisible(True)
        self.main.ie_scale_box.setVisible(True)
        self.main.clear_scale_button.setVisible(True)
        self.main.reset_zoom_button.setVisible(True)
        self.main.es_scaling_label.setVisible(True)
        self.main.es_scaling_dropdown.setVisible(True)
        it = RawDataDirIterator(self.main.metadata, self.main.freqs, self.main.heights, self.main.dops, self.main.signals)
        freqs, heights, dops, signals = it[self.main._selected_timestamp]
        if self.main.extension == 'iono':
            power_prethres = signals[:, 1]
            power = power_prethres[power_prethres >=0 ]
            freqs = freqs[power_prethres >= 0]
            heights = heights[power_prethres >= 0]
            dops = dops[power_prethres >=0 ]
        elif self.main.extension in ['md3', 'md4']:
            power = convert_amplitude_to_power(signals)
            freqs = freqs
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
