#PySide6 FigureCanvas to plot Ionogram as scatterplot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter, MultipleLocator
import numpy as np

class FrequencyDayCanvas(FigureCanvas):
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
        self.ax.set_ylabel("Frequency (MHz)")
        self.ax.set_xlabel("Time (UTC)")
        formatter = ScalarFormatter(useMathText=True)
        formatter.set_powerlimits((0, 0))  # Force 1e6 scale
        self.ax.yaxis.set_major_formatter(formatter)
        self.ax.grid()

    def plot_scatter(self, freqs, time_index, dops, timestamp, site):
        self.ax.clear()
        self.fig.tight_layout(pad=3)
        self.setHidden(self.is_hidden)
        self.time_height_plot = self.ax.scatter(time_index, freqs/1e6, s=34, 
                           c=dops, cmap='turbo_r', vmin=-3, vmax=3, linewidth=0, marker=',')
        if self.colorbar:
            self.colorbar.update_ticks()
            #self.colorbar.set_clim(signals.min(), signals.max())  # Update color limits
        else:
            # Create the colorbar if it doesn't exist
            self.colorbar = self.figure.colorbar(self.time_height_plot,ticks=np.arange(-5, 5, 0.5))
            self.colorbar.set_label("Doppler Shift")
        self.ax.set_title(f"Frequency vs Time: {site} at time {timestamp} UTC")
        self._set_plot_ax()
        #self.fig.tight_layout()
        self.fig.subplots_adjust(left=0.1, right=1.05, bottom=0.075, top=0.95)
        self.draw()