from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter, MultipleLocator, FuncFormatter
from datetime import datetime
import numpy as np
from src.utils.siteinfo import SiteInfo

class EWNSRangeCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(16, 9))
        self.main = parent # Store main widget reference
        super().__init__(self.fig)
        ax1 = self.fig.add_subplot(121)
        ax2 = self.fig.add_subplot(122)
        self.axs = [ax1, ax2]
        self.scatter = None
        self.colorbar = None
        self.cbar_ax = self.fig.add_axes(rect=(0.94, 0.15, 0.015, 0.7)) 

        self.height_ticks = np.arange(0, 1100, 100)
        self.height_limits = (50, 1000)
        self.horizontal_ticks = np.arange(-500, 600, 100)
        self.horizontal_limits = (-500, 500)
        

        self._set_plot_ax()

    def _set_plot_ax(self):
        for ax, label in zip(self.axs, ['East-West', 'North-South']):
            ax.set_xticks(self.horizontal_ticks)
            ax.set_xlim(self.horizontal_limits)
            ax.set_yticks(self.height_ticks)
            ax.set_ylim(self.height_limits)
            ax.set_xlabel(f"{label} (km)")
            ax.set_ylabel("Range (km)")
            ax.xaxis.set_minor_locator(MultipleLocator(10))
            ax.yaxis.set_minor_locator(MultipleLocator(5))
            ax.grid()

    def plot_scatter(self, x, y, range, pow, timestamp, site):
        for ax, label, direction, powlabel in zip(self.axs, ['East-West', 'North-South'], [x,y], ['xpower1 (dB)', 'xpower2 (dB)']):
            ax.clear()
            self.scatter = ax.scatter(direction, range, s=self.main.scatter_size, c=pow[powlabel], cmap=self.main.colormap, marker='s')
            self.scatter.set_clim(0, self.main.power_limit)
            ax.set_title(f"{label} echos")
        self.fig.suptitle(f"EW and NS vs Range for {site} at {timestamp.strftime("%H:%M:%S %d-%m-%Y")} {SiteInfo.from_file(site).get_tzstr(timestamp)}", y=0.99)
        self.colorbar = self.figure.colorbar(self.scatter, cax=self.cbar_ax)
        self.colorbar.set_label("Power (dB)")
        self.colorbar.set_ticks(np.arange(0, self.main.power_limit + 1, 5))  # Fixed ticks from 0 to power_limit with step of 5
        self.scatter.set_clim(0, self.main.power_limit)  # Set color limits on scatter plot
        self._set_plot_ax()
        self.fig.subplots_adjust(left=0.07, right=0.92, bottom=0.07, top=0.93)
        self.draw()

    def reset_zoom(self):
        pass  