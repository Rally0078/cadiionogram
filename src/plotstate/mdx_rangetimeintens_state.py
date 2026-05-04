#Concrete implementation for range-time-freq plot
from src.plot.rangetimeintenscanvas import RangeTimeIntensCanvas
from src.plotstate.base import PlotState
from src.utils.powerpreprocessing import convert_amplitude_to_power
from src.ionogramfiltering.noisereduction import o_x_separation
from src.utils.pandasutils import PandasUtils
from datetime import datetime
from decimal import Decimal
import pandas as pd

class MdxRangeTimeIntensState(PlotState):
    def create_canvas(self):
        canvas = RangeTimeIntensCanvas(self.main)
        self.update_canvas(canvas)
        return canvas

    def update_canvas(self, canvas):
        df = self.main.combined_df
        date_of_obs = self.main.metadata['datetime']
        
        # Combined timestamps are "YYYY-MM-DD HH:MM:SS"
        # We always want to parse the full string if it contains the date
        if ' ' in self.main._selected_timestamp:
            start_dtime = datetime.strptime(self.main._selected_timestamp, "%Y-%m-%d %H:%M:%S")
            end_dtime = datetime.strptime(self.main._right_selected_timestamp, "%Y-%m-%d %H:%M:%S")
        else:
            # Fallback
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
        if self.main.md3_checkbox.isChecked():
            selected_frequencies = self.main.freq_selector.selectedItems()
            selected_frequencies_decimals = [Decimal(freq) for freq in selected_frequencies]
            selected_frequencies_rounded = [float(item.quantize(Decimal(f"1e-3"))) * 1e6 for item in selected_frequencies_decimals]
            power = convert_amplitude_to_power(df_selection[signal_col_names].to_numpy())
            canvas.plot_scatter(
            df_selection.index,
            df_selection['height (km)'],
            power,
            df_selection['freq (Hz)'], 
            self.main.metadata['datetime'],
            self.main.metadata['site'],
            True,
            selected_frequencies_rounded
        )
        else:
            selected_frequencies = self.main.freqs_list
            selected_frequencies_rounded = selected_frequencies
            freq_selection, height_selection, dop_selection, signals_selection = o_x_separation(df_selection['freq (Hz)'], 
                           df_selection['height (km)'], 
                           df_selection['dopplershift'],
                           df_selection[signal_col_names].to_numpy())
            canvas.plot_scatter(
                freq_selection.index,
                height_selection,
                convert_amplitude_to_power(signals_selection),
                freq_selection, 
                self.main.metadata['datetime'],
                self.main.metadata['site'],
                False
            )
