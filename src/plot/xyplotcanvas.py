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
        self.is_hidden = False
        self.setHidden(self.is_hidden)
        self.cbar = None

    def _set_plot_ax(self, site):
        self.ax_range.set_ylabel("Range (km)")
        self.ax_ns.set_ylabel("NS (km)")
        self.ax_ew.set_ylabel("EW (km)")
        for ax in self.axs:
            ax.set_xlabel(f"Time in {site_dict[site].timezone}")
            date_format = mdates.DateFormatter("%H:%M")
            ax.xaxis.set_major_formatter(date_format)
            #ax.grid()

    def plot_scatter(self, time_index, heights, freqs, power, x, y, xpow, output_freqs, selected_frequencies, date, site):
        for ax in self.axs:
            ax.clear()
        self.fig.tight_layout(pad=3)
        self.setHidden(self.is_hidden)
        legend = self.fig.legend()
        legend.remove()
        self.fig.suptitle(f"NS, EW, Range timeseries plot at site: {site} on {date.day:02d}-{date.month:02d}-{date.year:04d} {site_dict[site].timezone}")
        print(f"Selected frequencies: {selected_frequencies}")
        if len(selected_frequencies) == 1:
            selected_heights = heights.iloc[np.argwhere(np.isclose(freqs, selected_frequencies[0], atol=1e-12)).flatten()]
            sc = self.ax_range.scatter(selected_heights.index, selected_heights, s=3, c=power[np.argwhere(np.isclose(freqs, selected_frequencies[0], atol=1e-12)).flatten()], 
                                  label=f"{selected_frequencies[0]/1e6} MHz")
            if not self.cbar:
                self.cbar = self.fig.colorbar(sc, ax=self.ax_range)
            else:
                self.cbar.update_ticks()
        else:
            for freq in np.unique(selected_frequencies):
                self.ax_range.plot(heights.iloc[np.argwhere(np.isclose(freqs, freq, atol=1e-12)).flatten()], marker='s', linewidth=0, markersize=3, label=f"{freq/1e6} MHz")  
        for freq in np.unique(selected_frequencies):
            self.ax_ew.plot(x.iloc[np.argwhere(np.isclose(output_freqs, freq, atol=1e-12)).flatten()], linewidth=0, marker='s', markersize=3, label=f"{freq/1e6} MHz")
            self.ax_ew.set_ylim(-1000, 1000)
            self.ax_ns.plot(y.iloc[np.argwhere(np.isclose(output_freqs, freq, atol=1e-12)).flatten()], linewidth=0, marker='s', markersize=3, label=f"{freq/1e6} MHz")
            self.ax_ns.set_ylim(-1000, 1000)    
        for ax in self.axs:
            ax.set_xlim(time_index[0], time_index[-1])
            xaxis_timedelta = timedelta(hours=3) if len(np.unique(time_index)) > 72 else timedelta(hours=2) if len(np.unique(time_index)) > 36 else timedelta(minutes=30) if len(np.unique(time_index)) > 12 else timedelta(minutes=15)
            ax.set_xticks(np.arange(datetime(year=time_index[0].year, month=time_index[0].month, day=time_index[0].day, 
                                             hour=time_index[0].hour, minute=0, second=0), datetime(year=time_index[-1].year, month=time_index[-1].month, day=time_index[-1].day, 
                                             hour=time_index[-1].hour, minute=time_index[-1].minute, second=0) + timedelta(minutes=30), xaxis_timedelta))
            ax.margins(x=0,y=0)
        self._set_plot_ax(site)
        self._update_legend()

        self.fig.subplots_adjust(left=0.1, right=0.95, bottom=0.075, top=0.95)
        self.draw()
    def _update_legend(self):
        for legend in self.fig.legends:
            legend.remove()
        handles, labels = self.ax_ew.get_legend_handles_labels()
        self.fig.legend(handles, labels, loc='upper right')