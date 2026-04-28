#Concrete implementation of real height analysis with interactive figure
#Handles POLAN input and output
from src.plot.realheightanalysis import RealHeightAnalysisCanvas
from src.plotstate.base import PlotState
from src.utils.powerpreprocessing import convert_amplitude_to_power
import pandas as pd
from datetime import datetime

class Md4RealheightAnalysisState(PlotState):
    def create_canvas(self):
        canvas = RealHeightAnalysisCanvas(self.main)
        self.update_canvas(canvas)
        return canvas

    def update_canvas(self, canvas):
        self.main.polan_button.setVisible(True)
        self.main.reset_zoom_button.setVisible(True)
        df = self.main.combined_df
        date_of_obs = self.main.metadata['datetime']
        
        # We always want to parse the HH:MM:SS part and use date_of_obs for the date components
        target_time_str = self.main._selected_timestamp.split(' ')[-1]
        time_obj = datetime.strptime(target_time_str, "%H:%M:%S")
        target_dtime = datetime(year=date_of_obs.year, month=date_of_obs.month, day=date_of_obs.day,
                                hour=time_obj.hour, minute=time_obj.minute, second=time_obj.second)

        target_dtime = target_dtime.replace(tzinfo=date_of_obs.tzinfo)

        df_at_time = df.loc[target_dtime]
        
        freqs = df_at_time['freq (Hz)'].to_numpy()
        heights = df_at_time['height (km)'].to_numpy()
        dops = df_at_time['dopplershift'].to_numpy()
        
        signal_col_names = [f"sensor{i//2 + 1} {'real' if i%2 == 0 else 'imag'}" for i in range(8)]
        signals = df_at_time[signal_col_names].to_numpy()

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
