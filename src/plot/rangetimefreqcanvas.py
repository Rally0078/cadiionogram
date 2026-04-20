#PySide6 FigureCanvas to plot Ionogram as scatterplot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter, MultipleLocator
import numpy as np
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from src.utils.siteinfo import site_dict


class RangeTimeFreqCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(16, 9))
        
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.scatter = None
        self.colorbar = None
        self.freq_ticks = np.arange(0, 18e6, 2e6)
        self.freq_limits = (1e6, 18e6)

        self._set_plot_ax()

    def _set_plot_ax(self):
        self.ax.set_yticks(self.freq_ticks)
        self.ax.set_ylim(self.freq_limits)
        self.ax.set_ylabel("Virtual Height(km)")
        #self.ax.set_xlabel("Time (UTC)")
        timeformat = mdates.DateFormatter('%H:%M')
        self.ax.xaxis.set_major_formatter(timeformat)
        self.ax.tick_params(axis='both', direction='in')
        self.ax.set_yticks(np.arange(0, 1200, 100))
        self.ax.set_ylim(0, 1000)
        self.ax.margins(x=0.015,y=0)
        self.ax.grid()

    def plot_scatter(self, time_index, heights, dops, freqs, date: datetime, site, selected_frequencies):
        self.ax.clear()
        self.fig.tight_layout(pad=3)
        legend = self.fig.legend()
        legend.remove()
        print(f"Selected frequencies: {selected_frequencies}")            
        for freq in np.unique(selected_frequencies):
            matched_idxs = np.argwhere(np.isclose(freqs, freq, atol=1e-12)).flatten()
            sc = self.ax.scatter(time_index[matched_idxs], heights.iloc[matched_idxs], marker='s', s=15, label=f"{freq/1e6} MHz")  
            self.ax.set_xlim(time_index[0], time_index[-1])
            xaxis_timedelta = timedelta(hours=3) if len(np.unique(time_index)) > 72 else timedelta(hours=2) if len(np.unique(time_index)) > 36 else timedelta(minutes=30) if len(np.unique(time_index)) > 12 else timedelta(minutes=15)
            self.ax.set_xticks(np.arange(datetime(year=time_index[0].year, month=time_index[0].month, day=time_index[0].day, 
                                            hour=time_index[0].hour, minute=0, second=0), datetime(year=time_index[-1].year, month=time_index[-1].month, day=time_index[-1].day, 
                                            hour=time_index[-1].hour, minute=time_index[-1].minute, second=0) + timedelta(minutes=30), xaxis_timedelta))
            self.ax.margins(x=0,y=0)
        self.ax.set_title(f"Virtual height vs Time: {site} on {date.strftime("%d-%m-%Y")} {site_dict[site].get_tzstr(date)}")
        self.ax.set_xlabel(f"Time ({site_dict[site].get_tzstr(date)})")
        self._set_plot_ax()
        self._update_legend()
        #self.fig.tight_layout()
        self.fig.subplots_adjust(left=0.1, right=0.95, bottom=0.075, top=0.95)
        self.draw()
    
    def _update_legend(self):
        for legend in self.fig.legends:
            legend.remove()
        handles, labels = self.ax.get_legend_handles_labels()
        self.fig.legend(handles, labels, loc='upper right')