#Concrete implementation for range-time-freq plot
from src.plot.xyplotcanvas import XYPlotCanvas
from src.plotstate.base import PlotState
from datetime import datetime
from src.utils.pandasutils import PandasUtils
from src.utils.cadikvector import compute_xy
from src.utils.powerpreprocessing import convert_amplitude_to_power
from decimal import Decimal, ROUND_HALF_UP, getcontext
import pytz

class MdxXYplotCanvasState(PlotState):
    def create_canvas(self):
        canvas = XYPlotCanvas(self.main)
        self.update_canvas(canvas)
        return canvas

    def update_canvas(self, canvas):
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
        selected_frequencies_decimals = [Decimal(freq) for freq in selected_frequencies]
        selected_frequencies_rounded = [float(item.quantize(Decimal(f"1e-3"))) * 1e6 for item in selected_frequencies_decimals]

        output_xpos, output_ypos, output_freqs, output_heights, _, _, output_xpow = compute_xy(df_selection, self.main.freqs_list, sort_by_freq=False)
        signal_col_names = [f"sensor{i//2 + 1} {'real' if i%2 == 0 else 'imag'}" for i in range(8)]
        power = convert_amplitude_to_power(df_selection[signal_col_names].to_numpy())
        canvas.plot_scatter(
            df_selection.index,
            df_selection['height (km)'],
            df_selection['freq (Hz)'],
            power,
            output_xpos,
            output_ypos, 
            output_xpow,
            output_freqs,
            selected_frequencies_rounded,
            self.main.metadata['datetime'],
            self.main.metadata['site']
        )
