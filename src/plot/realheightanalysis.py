#PySide6 FigureCanvas to plot MD4 Ionogram as scatterplot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter, MultipleLocator
from matplotlib.lines import Line2D
import numpy as np
from datetime import datetime
from scipy.interpolate import PchipInterpolator
from src.ionogramfiltering.noisereduction import *

class RealHeightAnalysisCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(16, 9))
        
        super().__init__(self.fig)
        self.is_hidden = True
        self.ax = self.fig.add_subplot(111)
        self.scatter = None
        self.colorbar = None
        self.freq_ticks = [1e6, 2e6, 4e6, 6e6, 8e6, 10e6, 15e6, 20e6]
        self.freq_limits = (1e6, 20e6)
        self.height_ticks = np.arange(0, 1100, 100)
        self.height_limits = (50, 1100)
        self.user_points = []
        self.user_point_artists = [] 
        self.drawing = False
        self.drawn_points = []  # List of (x, y) tuples for curve
        self.line = None  # Line2D object for the curve
        self.line_polan = None #Line2D for POLAN real height curve
        self.freqs = np.array([])   # Empty by default
        self.heights = np.array([]) # Empty by default
        self.interp_line = None
        # Connect matplotlib mouse events
        self.mpl_connect("button_press_event", self.on_mouse_press)
        self.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.mpl_connect("button_release_event", self.on_mouse_release)
        self._set_plot_ax()
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

    def plot_scatter(self, freqs, heights, dops, power, timestamp, date: datetime, site):
        self.freqs = freqs
        self.heights = heights
        self.ax.clear()
        self.fig.tight_layout(pad=3)
        self.setHidden(self.is_hidden)
        
        self.scatter = self.ax.scatter(freqs, heights, s=6, c=power, cmap='turbo_r', marker='s')
        self.scatter.set_clim(0, 50)

        if self.colorbar:
            self.colorbar.update_ticks()
        else:
            self.colorbar = self.figure.colorbar(self.scatter, ax=self.ax)
            self.colorbar.set_label("Power (dB)")
            self.colorbar.set_ticks(np.arange(0, 51, 5))  # Fixed ticks from 0 to 50 with step of 5
            self.scatter.set_clim(0, 50)  # Set color limits on scatter plot
        self.ax.set_title(f"Ionogram site: {site} at time {timestamp} {date.day:02d}-{date.month:02d}-{date.year:04d} UTC")
        self._set_plot_ax()
        self.fig.subplots_adjust(left=0.1, right=1.05, bottom=0.075, top=0.95)
        self.drawing = False
        self.drawn_points = []

        # Re-create the interactive drawing line
        self.line = Line2D([], [], color='red', linewidth=2)
        self.ax.add_line(self.line)

        self.line_polan = Line2D([], [], color='green', linewidth=2, linestyle='--')
        self.ax.add_line(self.line_polan)
        self.draw()
    
    def plot_interp(self, interp_freqs, interp_heights):
        interp_freqs = np.array(interp_freqs) * 1e6
        if self.interp_line is not None and self.interp_line in self.ax.lines:
            self.interp_line.remove()
        self.interp_line = Line2D(interp_freqs, interp_heights, color='magenta', linewidth=1.5, linestyle='--')
        self.ax.add_line(self.interp_line)

        self.draw_idle()

    def plot_polan(self, freqs, real_heights, interp_freqs, interp_heights):
        freqs = np.array(freqs)
        freqs = freqs * 1e6
        self.plot_interp(interp_freqs, interp_heights)
        if self.line_polan is None:
            self.line_polan = Line2D(freqs, real_heights, color='green', linewidth=2, linestyle='--')
            self.ax.add_line(self.line_polan)
        else:
            self.line_polan.set_data(freqs, real_heights)
        self.draw()

    def on_mouse_press(self, event):
        # Only respond to left or right clicks inside axes
        if event.inaxes != self.ax:
            return

        if event.button == 1:  # Left click -> start drawing
            self.drawing = True
            self.drawn_points = [(event.xdata, event.ydata)]
            # Create a new line or clear old one
            if self.line is None:
                self.line = Line2D([event.xdata], [event.ydata], color='red', linewidth=2)
                self.ax.add_line(self.line)
            else:
                self.line.set_data([event.xdata], [event.ydata])
            self.draw()

        elif event.button == 3:  # Right click -> clear the curve
            self.drawing = False
            self.drawn_points = []
            if self.line is not None:
                self.line.set_data([], [])
            self.draw()

    def on_mouse_move(self, event):
        if not self.drawing or event.inaxes != self.ax:
            return
        self.drawn_points.append((event.xdata, event.ydata))
        xs, ys = zip(*self.drawn_points)
        self.line.set_data(xs, ys)
        self.draw()

    def on_mouse_release(self, event):
        if event.button == 1 and self.drawing:
            self.drawing = False

    def draw_auto_curve(self, freqs, heights, dops, signals):
        noise_idx, _, _ = freq_filter(freqs, heights)
        freqs_filtered = np.delete(freqs, noise_idx)
        heights_filtered = np.delete(heights, noise_idx)
        dops_filtered = np.delete(dops, noise_idx)
        sensors_filtered = np.delete(signals, noise_idx, axis=0)
        freqs_omode, heights_omode, dops_omode, sensors_omode = o_x_separation(freqs_filtered, heights_filtered, dops_filtered, sensors_filtered)
        new_pix_counts, medians, freq_flayer = calculate_pixbins(freqs_omode, heights_omode)
        freq_new_x = []
        height_new_y = []
        prev_len = 0
        for freq_bin, median in zip(new_pix_counts, medians):
            idx, freq, indices, hgts = freq_bin
            if prev_len >= 1:
                freq_new_x = np.append(freq_new_x, freq)
                height_new_y = np.append(height_new_y, np.median(hgts))
            prev_len = len(hgts)
        points = np.array([(x, y) for x, y in zip(freq_new_x, height_new_y)])
        freqs_interp, heights_interp, unique_freqs, avg_heights = self.compute_matched_curve(points, spacing=0.2)
        if len(heights_interp) >= 1:
            self.plot_interp(freqs_interp, heights_interp)
        return freqs_interp, heights_interp, unique_freqs, avg_heights
    
    def draw_manual_curve(self):
        if not self.drawn_points:
            return np.array([]), np.array([])
        points = np.array([(x, y) for x, y in self.drawn_points if x is not None and y is not None])
        if points.size == 0:
            return np.array([]), np.array([])
        if points.shape[0] < 2:
            return np.array([]), np.array([])
        freqs_interp, heights_interp, unique_freqs, avg_heights = self.compute_matched_curve(points)
        return freqs_interp, heights_interp, unique_freqs, avg_heights

    def compute_matched_curve(self, points, spacing=0.5):
        """
            Interpolate a curve based on some sample inputs(automatic or hand drawn), and return an output curve at fixed frequency steps. 
            Required for POLAN.
        """
        freqs_hz = points[:, 0]
        heights = points[:, 1]

        freqs_mhz = freqs_hz / 1e6
        freqs_rounded = np.round(freqs_mhz, 1)

        unique_freqs, inverse_indices = np.unique(freqs_rounded, return_inverse=True)
        avg_heights = np.zeros_like(unique_freqs)

        for i in range(len(unique_freqs)):
            avg_heights[i] = heights[inverse_indices == i].mean()

        f_min = np.floor(unique_freqs.min() * 10) / 10
        f_max = np.ceil(unique_freqs.max() * 10) / 10
        num_points = int(np.round((f_max - f_min) / spacing)) + 1
        freqs_interp = np.round(np.linspace(f_min, f_max, num_points), 1)

        interpolator = PchipInterpolator(unique_freqs, avg_heights, extrapolate=False)
        heights_interp = interpolator(freqs_interp)
        mask = ~np.isnan(heights_interp)
        freqs_interp = freqs_interp[mask]
        heights_interp = heights_interp[mask]

        return freqs_interp, heights_interp, unique_freqs, avg_heights