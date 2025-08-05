#Concrete implementation for range-time-freq plot
from src.plot.xyplotcanvas import XYPlotCanvas
from src.plotstate.base import PlotState
import numpy as np
from datetime import datetime
from src.utils.powerpreprocessing import convert_amplitude_to_power
from src.utils.pandasutils import PandasUtils
from src.utils.rawdatadiriterator import RawDataDirIterator
from src.utils.cadikvector import compute_xy
import pandas as pd

class MdxXYplotCanvasState(PlotState):
    def create_canvas(self):
        canvas = XYPlotCanvas(self.main)
        self.update_canvas(canvas)
        return canvas

    def update_canvas(self, canvas):
        it = RawDataDirIterator(self.main.metadata, self.main.freqs, self.main.heights, self.main.dops, self.main.signals)
        df = PandasUtils.create_pandas_from_arrays(self.main.metadata, self.main.freqs, self.main.heights, self.main.dops, self.main.signals)
        date_of_obs = self.main.metadata['datetime']
        start_time = datetime.strptime(self.main._selected_timestamp, "%H:%M:%S")
        end_time = datetime.strptime(self.main._right_selected_timestamp, "%H:%M:%S")
        start_dtime = datetime(year=date_of_obs.year, month=date_of_obs.month, day=date_of_obs.day,
                               hour=start_time.hour, minute=start_time.minute, second=start_time.second)
        end_dtime = datetime(year=date_of_obs.year, month=date_of_obs.month, day=date_of_obs.day,
                               hour=end_time.hour, minute=end_time.minute, second=end_time.second)
        freqs = df['freq (Hz)'][start_dtime:end_dtime].to_numpy()
        heights = df['height (km)'][start_dtime:end_dtime].to_numpy()
        dops = df['dopplershift'][start_dtime:end_dtime].to_numpy()
        signal_col_names = [f"sensor{i//2 + 1} real" for i in range(8)]
        signals = df[signal_col_names][start_dtime:end_dtime].to_numpy()
        time_index = df[start_dtime:end_dtime].index
        
        select_time_index = time_index
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
