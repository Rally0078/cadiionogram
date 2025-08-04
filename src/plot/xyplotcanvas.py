#PySide6 FigureCanvas to plot MD4 Ionogram as scatterplot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.ticker import ScalarFormatter, MultipleLocator
from datetime import datetime, timedelta
import numpy as np
from src.utils.siteinfo import site_dict

class XYPlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(10, 8))
        
        super().__init__(self.fig)
        self.is_hidden = True
        self.ax_range = self.fig.add_subplot(311)
        self.ax_ew = self.fig.add_subplot(312)
        self.ax_ns = self.fig.add_subplot(313)
        self.scatter_range = None
        self.scatter_ew = None
        self.scatter_ns = None
        self.axs = [self.ax_range, self.ax_ew, self.ax_ns]
        
        self._set_plot_ax()
        #self.plot_initial()
        self.is_hidden = False
        self.setHidden(self.is_hidden)

    def _set_plot_ax(self):
        self.ax_range.set_ylabel("Range (km)")
        self.ax_ns.set_ylabel("NS (km)")
        self.ax_ew.set_ylabel("EW (km)")
        for ax in self.axs:
            ax.set_xlabel("Time")
            date_format = mdates.DateFormatter("%H:%M")
            ax.xaxis.set_major_formatter(date_format)
            #ax.grid()

    def plot_scatter(self, time_index, heights, x, y, xpow, filter_idxs, date, site):
        for ax in self.axs:
            ax.clear()
        self.fig.tight_layout(pad=3)
        self.setHidden(self.is_hidden)
        
        self.fig.suptitle(f"NS, EW, Range timeseries plot at site: {site} on {date.day:02d}-{date.month:02d}-{date.year:04d} {site_dict[site].timezone}")
        self.ax_range.plot(time_index, heights, marker='s', linewidth=0, markersize=3)
        self.ax_ew.plot(time_index[filter_idxs], x, linewidth=1)
        self.ax_ns.plot(time_index[filter_idxs], y, linewidth=1)
        for ax in self.axs:
            ax.set_xlim(time_index[0], time_index[-1])

            xaxis_timedelta = timedelta(hours=3) if len(np.unique(time_index)) > 72 else timedelta(hours=2) if len(np.unique(time_index)) > 36 else timedelta(minutes=30) if len(np.unique(time_index)) > 12 else timedelta(minutes=15)
            ax.set_xticks(np.arange(datetime(year=time_index[0].year, month=time_index[0].month, day=time_index[0].day, 
                                             hour=0, minute=0, second=0), datetime(year=time_index[-1].year, month=time_index[-1].month, day=time_index[-1].day, 
                                             hour=time_index[-1].hour, minute=time_index[-1].minute, second=0) + timedelta(minutes=30), xaxis_timedelta))
            ax.margins(x=0,y=0)
        self._set_plot_ax()
        

        self.fig.subplots_adjust(left=0.1, right=0.95, bottom=0.075, top=0.95)
        self.draw()