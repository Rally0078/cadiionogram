#Concrete implementation of MD4 display ionogram PlotState
#Handles plotting of raw ionograms with MD4
from src.plot.skymapcanvas import SkymapCanvas
from src.plotstate.base import PlotState
from src.utils.powerpreprocessing import convert_amplitude_to_power
import pandas as pd
from datetime import datetime

class MdxSkymapState(PlotState):
    def create_canvas(self):
        canvas = SkymapCanvas(self.main)
        self.update_canvas(canvas)
        return canvas

    def update_canvas(self, canvas):
        #self.main.reset_zoom_button.setVisible(True)
        df = self.main.combined_df
        date_of_obs = self.main.metadata['datetime']
        
        target_time_str = self.main._selected_timestamp
        if self.main.multi_folder_checkbox.isChecked():
            time_obj = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
            target_dtime = time_obj
        else:
            time_obj = datetime.strptime(target_time_str.split(' ')[-1], "%H:%M:%S")
            target_dtime = time_obj.replace(year=date_of_obs.year, month=date_of_obs.month, day=date_of_obs.day)
        target_dtime = target_dtime.replace(tzinfo=date_of_obs.tzinfo)

        df_at_time = df.loc[target_dtime:target_dtime]
        
        freqs = df_at_time['freq (Hz)'].to_numpy()
        heights = df_at_time['height (km)'].to_numpy()
        dops = df_at_time['dopplershift'].to_numpy()
        
        signal_col_names = [f"sensor{i//2 + 1} {'real' if i%2 == 0 else 'imag'}" for i in range(8)]
        signals = df_at_time[signal_col_names].to_numpy()

        if self.main.extension == 'iono':
            power_prethres = signals[:, 1]
            power = power_prethres[power_prethres >= 0]
            freqs = freqs[power_prethres >= 0] * 1e6
            heights = heights[power_prethres >= 0]
            dops = dops[power_prethres >= 0]
        elif self.main.extension in ['md3', 'md4']:
            power = convert_amplitude_to_power(signals)
        else:
            raise TypeError("Input data is not the correct type for this canvas")
        ndops = self.main.metadata['ndops']
        npulses_avgd = self.main.metadata['npulses_avgd']
        pps = self.main.metadata['pps']
        dopsn2 = 1/(self.main.metadata['ndops'] * npulses_avgd/pps)
        mindopfreq = (0 - ndops/2) * dopsn2
        maxdopfreq = (ndops - ndops/2) * dopsn2
        canvas.plot_scatter(
            self.main.df_all_outputs.loc[target_dtime, 'zenith'],
            self.main.df_all_outputs.loc[target_dtime, 'azimuth'], 
            self.main.df_all_outputs.loc[target_dtime,'dopplershift'],
            target_dtime,
            self.main.metadata['site'],
            ndops=self.main.metadata['ndops'],
            mindopfreq=mindopfreq,
            maxdopfreq=maxdopfreq
        )
