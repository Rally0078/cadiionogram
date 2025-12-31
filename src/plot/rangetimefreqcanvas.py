#PySide6 FigureCanvas to plot Ionogram as scatterplot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter, MultipleLocator
import numpy as np
from datetime import datetime
import matplotlib.dates as mdates


class RangeTimeFreqCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(16, 9))
        
        super().__init__(self.fig)
        self.is_hidden = True
        self.ax = self.fig.add_subplot(111)
        self.scatter = None
        self.colorbar = None
        self.freq_ticks = np.arange(0, 18e6, 2e6)
        self.freq_limits = (1e6, 18e6)

        self._set_plot_ax()
        self.is_hidden = False
        self.setHidden(self.is_hidden)

    def _set_plot_ax(self):
        self.ax.set_yticks(self.freq_ticks)
        self.ax.set_ylim(self.freq_limits)
        self.ax.set_ylabel("Virtual Height(km)")
        self.ax.set_xlabel("Time (UTC)")
        timeformat = mdates.DateFormatter('%H:%M')
        self.ax.xaxis.set_major_formatter(timeformat)
        self.ax.tick_params(axis='both', direction='in')
        self.ax.set_yticks(np.arange(0, 1200, 100))
        self.ax.set_ylim(0, 1000)
        self.ax.margins(x=0.015,y=0)
        self.ax.grid()

    def plot_scatter(self, time_index, heights, dops, freqs, date: datetime, site):
        self.ax.clear()
        self.fig.tight_layout(pad=3)
        self.setHidden(self.is_hidden)
        self.time_height_plot = self.ax.scatter(time_index, heights, s=25, 
                           c=freqs/1e6, cmap='turbo_r', vmin=int(np.min(freqs/1e6)), vmax=int(np.max(freqs/1e6)), linewidth=0, marker=',')
        if self.colorbar:
            self.colorbar.update_ticks()
            #self.colorbar.set_clim(signals.min(), signals.max())  # Update color limits
        else:
            # Create the colorbar if it doesn't exist
            self.colorbar = self.figure.colorbar(self.time_height_plot,ticks=np.arange(0, int(np.max(freqs/1e6))+2, 2))
            self.colorbar.set_label("Frequency")
        self.ax.set_title(f"Virtual height vs Time: {site} on {date.strftime("%d-%m-%Y")} UTC")
        self._set_plot_ax()
        #self.fig.tight_layout()
        self.fig.subplots_adjust(left=0.1, right=1.05, bottom=0.075, top=0.95)
        self.draw()