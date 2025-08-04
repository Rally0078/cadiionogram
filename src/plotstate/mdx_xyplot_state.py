#Concrete implementation for range-time-freq plot
from src.plot.xyplotcanvas import XYPlotCanvas
from src.plotstate.base import PlotState
import numpy as np
from datetime import datetime
from src.utils.powerpreprocessing import convert_amplitude_to_power
from src.utils.rawdatadiriterator import RawDataDirIterator
from src.utils.cadikvector import compute_xy
import pandas as pd

class MdxXYplotCanvasState(PlotState):
    def create_canvas(self):
        canvas = XYPlotCanvas(self.main)
        self.update_canvas(canvas)
        return canvas

    def update_canvas(self, canvas):
        freqs = self.main.freqs[self.main.lpointer:self.main.rpointer]
        heights = self.main.heights[self.main.lpointer:self.main.rpointer]
        dops = self.main.dops[self.main.lpointer:self.main.rpointer]
        signals = self.main.signals[self.main.lpointer:self.main.rpointer]
        timepartitions_dict = self.main.metadata['timepartitions']
        left_index = list(timepartitions_dict.keys()).index(self.main._selected_timestamp)
        right_index = list(timepartitions_dict.keys()).index(self.main._right_selected_timestamp)
        date_of_obs = self.main.metadata['datetime']
        timepartitions = np.array(list(timepartitions_dict.values()))
        tmp = timepartitions[0]
        timepartitions = np.diff(timepartitions, prepend=timepartitions[0])
        timepartitions[0] = tmp
        repeating_indices = np.repeat(list(timepartitions_dict.keys()), timepartitions)

        repeating_indices = np.array([datetime.strptime(f"{date_of_obs.year:04d}-{date_of_obs.month:02d}-{date_of_obs.day:02d} {time_str}+00:00", 
                                                        '%Y-%m-%d %H:%M:%S%z') for time_str in repeating_indices])
        time_index = pd.to_datetime(repeating_indices, utc=True)
        select_time_index = time_index[self.main.lpointer:self.main.rpointer]
        output_idxs, xpos, ypos, output_freqs, output_heights, output_df, output_signals, output_xpow = compute_xy(freqs, self.main.freqs_list, heights, dops, signals, sort_by_freq=False)

        canvas.plot_scatter(
            select_time_index,
            heights,
            xpos,
            ypos, 
            output_xpow,
            output_idxs,
            self.main.metadata['datetime'],
            self.main.metadata['site']
        )
