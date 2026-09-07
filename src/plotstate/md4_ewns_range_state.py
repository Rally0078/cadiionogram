from src.plot.ewnsrangecanvas import EWNSRangeCanvas
from src.plotstate.base import PlotState
from src.utils.powerpreprocessing import convert_amplitude_to_power
import numpy as np
from datetime import datetime

class Md4EwnsRangeState(PlotState):
    def create_canvas(self):
        canvas = EWNSRangeCanvas(self.main)
        self.update_canvas(canvas)
        return canvas

    def update_canvas(self, canvas: EWNSRangeCanvas):
        data = self.main.df_all_outputs
        date_of_obs = self.main.metadata['datetime']
        
        target_time_str = self.main._selected_timestamp
        if self.main.multi_folder_checkbox.isChecked():
            time_obj = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
            target_dtime = time_obj
        else:
            time_obj = datetime.strptime(target_time_str.split(' ')[-1], "%H:%M:%S")
            target_dtime = time_obj.replace(year=date_of_obs.year, month=date_of_obs.month, day=date_of_obs.day)
        target_dtime = target_dtime.replace(tzinfo=date_of_obs.tzinfo)

        df_at_time = data.loc[target_dtime:target_dtime]
        canvas.plot_scatter(df_at_time['xpos'], df_at_time['ypos'], 
                df_at_time['zpos'], df_at_time[['xpower1 (dB)', 'xpower2 (dB)']], target_dtime, self.main.metadata['site'])