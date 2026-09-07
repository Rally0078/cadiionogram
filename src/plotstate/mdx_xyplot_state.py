#Concrete implementation for range-time-freq plot
import pandas as pd

from src.plot.xyplotcanvas import XYPlotCanvas
from src.plotstate.base import PlotState
from datetime import datetime
from src.utils.pandasutils import PandasUtils
from src.utils.powerpreprocessing import convert_amplitude_to_power
from decimal import Decimal

class MdxXYplotCanvasState(PlotState):
    def create_canvas(self):
        canvas = XYPlotCanvas(self.main)
        self.update_canvas(canvas)
        return canvas

    def update_canvas(self, canvas):
        df = self.main.combined_df
        date_of_obs: datetime = self.main.metadata['datetime']
        
        if ' ' in self.main._selected_timestamp:
            start_dtime = datetime.strptime(self.main._selected_timestamp, "%Y-%m-%d %H:%M:%S")
            end_dtime = datetime.strptime(self.main._right_selected_timestamp, "%Y-%m-%d %H:%M:%S")
        else:
            start_time = datetime.strptime(self.main._selected_timestamp, "%H:%M:%S")
            end_time = datetime.strptime(self.main._right_selected_timestamp, "%H:%M:%S")
            start_dtime = datetime(year=date_of_obs.year, month=date_of_obs.month, day=date_of_obs.day,
                                   hour=start_time.hour, minute=start_time.minute, second=start_time.second)
            end_dtime = datetime(year=date_of_obs.year, month=date_of_obs.month, day=date_of_obs.day,
                                   hour=end_time.hour, minute=end_time.minute, second=end_time.second)
            
        start_dtime = start_dtime.replace(tzinfo=date_of_obs.tzinfo)
        end_dtime = end_dtime.replace(tzinfo=date_of_obs.tzinfo)

        df_selection = df.loc[start_dtime:end_dtime]
        signal_col_names = [f"sensor{i//2 + 1} {'real' if i%2 == 0 else 'imag'}" for i in range(8)]
        power = convert_amplitude_to_power(df_selection[signal_col_names].to_numpy())
        canvas.plot_scatter(
            df_selection.index,
            df_selection['height (km)'],
            df_selection['freq (Hz)'],
            power,
            self.main.df_all_outputs['xpos'],
            self.main.df_all_outputs['ypos'], 
            self.main.all_output_freqs,
            selected_frequencies_rounded,
            self.main.metadata['datetime'],
            self.main.metadata['site']
        )
