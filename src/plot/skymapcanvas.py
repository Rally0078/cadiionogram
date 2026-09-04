#PySide6 FigureCanvas to plot MD4 Ionogram as scatterplot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter, MultipleLocator, FuncFormatter
from datetime import datetime
import numpy as np
from src.utils.siteinfo import SiteInfo

class SkymapCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(16, 9))
        self.main = parent # Store main widget reference
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111, projection='polar')
        self.scatter = None
        self.colorbar = None

        self._set_plot_ax()
        self.zoom_factor = 1.2
        #self.plot_initial()

    def _set_plot_ax(self):
        self.ax.set_xticks(np.arange(0,360,45)*np.pi/180)
        self.ax.set_xticklabels(labels=['N', 'NE', 'E','SE','S','SW','W','NW'])#, fontsize=20, fontweight='bold', fontname="Times New Roman")
        self.ax.set_xticks(ticks=np.arange(22.5,360, 45)*np.pi/180, minor=True)
        self.ax.set_xticklabels(labels=['NNE','ENE','ESE','SSE','SSW','WSW','WNW','NNW'], minor=True)
        self.ax.set_xlim(0,360*np.pi/180)
        self.ax.set_yticks(np.arange(0,90,10))
        self.ax.set_yticklabels(labels=np.arange(0,90,10))#, fontsize=20, fontweight='bold', fontname="Times New Roman")
        self.ax.set_ylim(0,90)
        self.ax.set_theta_zero_location('N')
        self.ax.set_theta_direction('clockwise')
        self.ax.grid(visible=True)

    def plot_scatter(self, zenith, azimuth, dops, timestamp, site, ndops=16, mindopfreq=-5, maxdopfreq=5):
        self.ax.clear()
        self.fig.tight_layout(pad=1)
        # Use configurable plotting options
        self.scatter = self.ax.scatter(np.radians(azimuth[zenith <= 60]), zenith[zenith <=60], 
                            marker='s',s=self.main.scatter_size, 
                            c=dops[zenith <= 60], cmap=self.main.colormap, vmin=mindopfreq, vmax=maxdopfreq)
        #self.scatter = self.ax.scatter(freqs / 1e6, heights, s=self.main.scatter_size, c=signals, cmap=self.main.colormap, marker='s')

        if not self.colorbar:
            # Create the colorbar if it doesn't exist
            self.colorbar = self.figure.colorbar(self.scatter, ax=self.ax)
            self.colorbar.set_label("Doppler")
            self.colorbar.ax.set_yticks(np.linspace(mindopfreq, maxdopfreq, ndops+1))
        self.ax.set_title(f"Skymap site: {site} at {timestamp.strftime("%H:%M:%S %d-%m-%Y")} {SiteInfo.from_file(site).get_tzstr(timestamp)}")
        self._set_plot_ax()
        #self.fig.tight_layout()
        self.fig.subplots_adjust(left=0, right=1.05, bottom=0.075, top=0.95)
        self.draw()