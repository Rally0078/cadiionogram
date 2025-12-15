#PySide6 FigureCanvas to plot MD4 Ionogram as scatterplot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter, MultipleLocator
from datetime import datetime
import numpy as np
from src.utils.siteinfo import site_dict
from src.plotstate.scaling_region_state import ScaleRegionValues

class ScaleIonogramCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(16, 9))
        self.main = parent
        super().__init__(self.fig)
        self.is_hidden = True
        self.ax = self.fig.add_subplot(111)
        self.scatter = None
        self.colorbar = None
        self.freq_ticks = [1, 2, 4, 6, 8, 10, 15, 20]
        self.freq_limits = (1, 18)
        self.height_ticks = np.arange(0, 1100, 100)
        self.height_limits = (50, 1100)
        self.scaled_values_lines = ScaleRegionValues(self.ax)
        self._set_plot_ax()
        self.mpl_connect("button_press_event", self.on_mouse_press)
        self.legend = None
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
        formatter.set_powerlimits((0, 0))  # Force 1e6 scale
        self.ax.xaxis.set_major_formatter(formatter)
        self.ax.yaxis.set_minor_locator(MultipleLocator(5))
        self.ax.grid()

    def plot_scatter(self, freqs, heights, dops, signals, timestamp, date: datetime, site):
        self.ax.clear()
        self.fig.tight_layout(pad=3)
        self.setHidden(self.is_hidden)
        self.scatter = self.ax.scatter(freqs/1e6, heights, s=6, c=signals, cmap='turbo_r', marker='s')
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
        self.ax.set_title(f"Ionogram site: {site} at time {timestamp} {date.day:02d}-{date.month:02d}-{date.year:04d} {site_dict[site].timezone}")
        self._set_plot_ax()
        #self.fig.tight_layout()
        self.fig.subplots_adjust(left=0.1, right=1.05, bottom=0.075, top=0.95)
        # Reset lines
        self.scaled_values_lines.clear_all()
        self.legend = self.ax.legend()
        self.draw()

    def on_mouse_press(self, event):
        #Get current scale region mode
        if self.main.f_scale_box.isChecked():
            text_legend = 'F'
        elif self.main.e_scale_box.isChecked():
            text_legend = 'E'
        elif self.main.ie_scale_box.isChecked():
            text_legend = 'IE'
        else:
            raise KeyError("No valid region selected for manual scaling")
        self.scaled_values_lines.set_region(text_legend)
        # Only respond to left or right clicks inside axes
        if event.inaxes != self.ax:
            return
        if event.button == 1:  # Left click -> scale height
            # Create a new line or clear old one
            self.scaled_values_lines.h = event.ydata

        elif event.button == 3:  # Right click -> scale frequency
            self.scaled_values_lines.f = event.xdata
        self.handle_legend()
        self.draw()

    def handle_legend(self):
        if self.legend is not None:
            self.legend.remove()
            self.draw()
        lines = []
        for s in self.scaled_values_lines._state.values():
            for line in [s['hline'], s['fline']]:
                if line is not None:
                    lines.append(line)
        if not lines:
            return
        labels = [line.get_label() for line in lines]
        
        self.legend = self.ax.legend(handles=lines, labels=labels)
    def clean_canvas(self):
        self.scaled_values_lines.clear_all()
        if self.legend is not None:
            self.legend.remove()
            self.legend = None
        self.draw()