#PySide6 FigureCanvas to plot MD4 Ionogram as scatterplot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter, MultipleLocator, FuncFormatter
from datetime import datetime
import numpy as np
from src.utils.siteinfo import site_dict

class AllIonogramCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(16, 9))
        self.main = parent # Store main widget reference
        super().__init__(self.fig)
        ax1 = self.fig.add_subplot(221)
        ax2 = self.fig.add_subplot(222)
        ax3 = self.fig.add_subplot(223)
        ax4 = self.fig.add_subplot(224)
        self.cbar_ax = self.fig.add_axes(rect=(0.94, 0.15, 0.015, 0.7)) 
        self.axs = [ax1, ax2, ax3, ax4]
        self.scatter = None
        self.colorbar = None
        self.freq_ticks = [1, 2, 4, 6, 8, 10, 15, 20]
        self.freq_limits = (1, 18)
        self.height_ticks = np.arange(0, 1100, 100)
        self.height_limits = (50, 1100)

        self._set_plot_ax()
        #self.mpl_connect("scroll_event", self.on_mouse_scroll)
        self.zoom_factor = 1.2
        #self.plot_initial()

    def _set_plot_ax(self):
        for ax in self.axs:
            ax.set_xscale('log')
            ax.set_xticks(self.freq_ticks)
            ax.set_xlim(self.freq_limits)
            ax.set_yticks(self.height_ticks)
            ax.set_ylim(self.height_limits)
            ax.set_xlabel("Frequency (MHz)")
            ax.set_ylabel("Virtual height (km)")
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:g}'))
            ax.yaxis.set_minor_locator(MultipleLocator(5))
            ax.grid()

    def plot_scatter(self, freqs, heights, dops, signals, timestamp, site):
        #self.fig.tight_layout(pad=3)
        for idx, ax in enumerate(self.axs):
            ax.clear()
            self.scatter = ax.scatter(freqs / 1e6, heights, s=self.main.scatter_size, c=10*np.log10(signals[:,idx]**2 + signals[:,idx+1]**2), cmap=self.main.colormap, marker='s')
            self.scatter.set_clim(0, self.main.power_limit)

            """if self.colorbar:
                self.colorbar.update_ticks()
                #self.colorbar.set_clim(signals.min(), signals.max())  # Update color limits
            else:
                # Create the colorbar if it doesn't exist
                self.colorbar = self.figure.colorbar(self.scatter, ax=ax)
                self.colorbar.set_label("Power (dB)")
                self.colorbar.set_ticks(np.arange(0, self.main.power_limit + 1, 5))  # Fixed ticks from 0 to power_limit with step of 5
                self.scatter.set_clim(0, self.main.power_limit)  # Set color limits on scatter plot"""
            ax.set_title(f"Receiver {idx+1}")
        self.fig.suptitle(f"Ionogram site: {site} at {timestamp.strftime("%H:%M:%S %d-%m-%Y")} {site_dict[site].get_tzstr(timestamp)}", y=0.99)
        self.colorbar = self.figure.colorbar(self.scatter, cax=self.cbar_ax)
        self.colorbar.set_label("Power (dB)")
        self.colorbar.set_ticks(np.arange(0, self.main.power_limit + 1, 5))  # Fixed ticks from 0 to power_limit with step of 5
        self.scatter.set_clim(0, self.main.power_limit)  # Set color limits on scatter plot
        self._set_plot_ax()
        self.fig.subplots_adjust(left=0.07, right=0.92, bottom=0.07, top=0.93)
        self.draw()

    def reset_zoom(self):
        pass