#Concrete implementation of MD4 display ionogram PlotState
#Handles plotting of raw ionograms with MD4
from src.plot.allionocanvas import AllIonogramCanvas
from src.plotstate.base import PlotState
from datetime import datetime

class Md4DisplayAllIonogramState(PlotState):
    def create_canvas(self):
        canvas = AllIonogramCanvas(self.main)
        self.update_canvas(canvas)
        return canvas

    def update_canvas(self, canvas):
        self.main.reset_zoom_button.setVisible(True)
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

        df_at_time = df.loc[target_dtime]
        
        freqs = df_at_time['freq (Hz)'].to_numpy()
        heights = df_at_time['height (km)'].to_numpy()
        dops = df_at_time['dopplershift'].to_numpy()
        
        signal_col_names = [f"sensor{i//2 + 1} {'real' if i%2 == 0 else 'imag'}" for i in range(8)]
        signals = df_at_time[signal_col_names].to_numpy()

        canvas.plot_scatter(
            freqs,
            heights,
            dops,
            signals,
            target_dtime,
            self.main.metadata['site']
        )
