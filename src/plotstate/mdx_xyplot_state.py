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
import pytz

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
        start_dtime = start_dtime.replace(tzinfo=pytz.UTC)
        end_dtime = end_dtime.replace(tzinfo=pytz.utc)
        df_selection = df.loc[start_dtime:end_dtime]
        selected_frequencies = self.main.freq_selector.selectedItems()
        selected_frequencies = [float(freq) * 1e6 for freq in selected_frequencies]
        xpos, ypos, output_freqs, output_heights, output_df, output_signals, output_xpow = compute_xy(df_selection, self.main.freqs_list, sort_by_freq=True)

        canvas.plot_scatter(
            df_selection.index,
            df_selection['height (km)'],
            xpos,
            ypos, 
            output_xpow,
            output_freqs,
            selected_frequencies,
            self.main.metadata['datetime'],
            self.main.metadata['site']
        )
