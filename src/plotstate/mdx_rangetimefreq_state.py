#Concrete implementation for range-time-freq plot
from src.plot.rangetimefreqcanvas import RangeTimeFreqCanvas
from src.plotstate.base import PlotState
from src.utils.pandasutils import PandasUtils
from datetime import datetime
from decimal import Decimal
import pandas as pd

class MdxRangeTimeFreqState(PlotState):
    def create_canvas(self):
        canvas = RangeTimeFreqCanvas(self.main)
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
        selected_frequencies = self.main.freq_selector.selectedItems()
        selected_frequencies_decimals = [Decimal(freq) for freq in selected_frequencies]
        selected_frequencies_rounded = [float(item.quantize(Decimal(f"1e-3"))) * 1e6 for item in selected_frequencies_decimals]
    
        canvas.plot_scatter(
            df_selection.index,
            df_selection['height (km)'],
            df_selection['dopplershift'],
            df_selection['freq (Hz)'], 
            self.main.metadata['datetime'],
            self.main.metadata['site'],
            selected_frequencies_rounded
        )
