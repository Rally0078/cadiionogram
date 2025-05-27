#PySide6 FigureCanvas to plot MD4 Ionogram as scatterplot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter, MultipleLocator
from datetime import datetime
import numpy as np

class IonogramCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(16, 9))
        
        super().__init__(self.fig)
        self.is_hidden = True
        self.ax = self.fig.add_subplot(111)
        self.scatter = None
        self.colorbar = None
        self.freq_ticks = [1e6, 2e6, 4e6, 6e6, 8e6, 10e6, 15e6, 20e6]
        self.freq_limits = (1e6, 18e6)
        self.height_ticks = np.arange(0, 1100, 100)
        self.height_limits = (50, 1100)

        self._set_plot_ax()
        #self.plot_initial()
        self.is_hidden = False
        self.setHidden(self.is_hidden)

    def _set_plot_ax(self):
        self.ax.set_xscale('log')
        self.ax.set_xlim(self.freq_limits)
        self.ax.set_xticks(self.freq_ticks)
        self.ax.set_yticks(self.height_ticks)
        self.ax.set_ylim(self.height_limits)
        self.ax.set_xlabel("Frequency (MHz)")
        self.ax.set_ylabel("Virtual height (km)")
        formatter = ScalarFormatter(useMathText=True)
        formatter.set_powerlimits((6, 6))  # Force 1e6 scale
        self.ax.xaxis.set_major_formatter(formatter)
        self.ax.yaxis.set_minor_locator(MultipleLocator(5))
        self.ax.grid()

    def plot_scatter(self, freqs, heights, signals, timestamp, date: datetime, site):
        self.ax.clear()
        self.fig.tight_layout(pad=3)
        self.setHidden(self.is_hidden)
        self.scatter = self.ax.scatter(freqs, heights, s=6, c=signals, cmap='turbo_r', marker='s')
        self.scatter.set_clim(0, 50)

        if self.colorbar:
            self.colorbar.update_ticks()
            #self.colorbar.set_clim(signals.min(), signals.max())  # Update color limits
        else:
            # Create the colorbar if it doesn't exist
            self.colorbar = self.figure.colorbar(self.scatter, ax=self.ax)
            self.colorbar.set_label("Power (dB)")
            self.colorbar.set_ticks(np.arange(0, 51, 5))  # Fixed ticks from 0 to 50 with step of 5
            self.scatter.set_clim(0, 50)  # Set color limits on scatter plot
        self.ax.set_title(f"Ionogram site: {site} at time {timestamp} {date.day:02d}-{date.month:02d}-{date.year:04d} UTC")
        self._set_plot_ax()
        #self.fig.tight_layout()
        self.fig.subplots_adjust(left=0.1, right=1.05, bottom=0.075, top=0.95)
        self.draw()