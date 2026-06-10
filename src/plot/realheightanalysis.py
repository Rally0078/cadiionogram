#PySide6 FigureCanvas to plot MD4 Ionogram as scatterplot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter, MultipleLocator, FuncFormatter
from matplotlib.lines import Line2D
import numpy as np
from datetime import datetime
from scipy.interpolate import PchipInterpolator
from scipy.integrate import cumulative_trapezoid
from src.ionogramfiltering.noisereduction import *
from src.utils.siteinfo import site_dict


def _convert_f_to_n(f):
    return (f*1e6/8.982)**2
def _convert_n_to_f(n):
    return 8.982*np.sqrt(n) / 1e6

class RealHeightAnalysisCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(16, 9))
        self.main = parent
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.scatter = None
        self.secax = None
        self.colorbar = None
        self.freq_ticks = [1, 2, 4, 6, 8, 10, 15, 20]
        self.freq_limits = (1, 18)
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
        self.mpl_connect("scroll_event", self.on_mouse_scroll)
        self.zoom_factor = 1.2
        self._set_plot_ax()

    def _set_plot_ax(self):
        self.ax.set_xscale('log')
        self.ax.set_xticks(self.freq_ticks)
        self.ax.set_xlim(self.freq_limits)
        self.ax.set_yticks(self.height_ticks)
        self.ax.set_ylim(self.height_limits)
        self.ax.set_xlabel("Frequency (MHz)")
        self.ax.set_ylabel("Virtual height (km)")
        self.ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:g}'))
        self.ax.yaxis.set_minor_locator(MultipleLocator(5))
        
        # Add secondary X axis for electron density
        if self.secax is not None:
            try:
                self.secax.remove()
            except:
                pass
        
        self.secax = self.ax.secondary_xaxis('top', functions=(_convert_f_to_n, _convert_n_to_f))
        self.secax.set_xlabel(r'Electron density ($m^{-3}$)')
        self.secax.xaxis.set_major_formatter(ScalarFormatter())
        self.secax.xaxis.get_major_formatter().set_scientific(True)
        self.secax.xaxis.get_major_formatter().set_powerlimits((0, 0))
        
        self.ax.grid(True, which='major')
    
    def plot_scatter(self, freqs, heights, dops, power, timestamp, site):
        self.freqs = freqs
        self.heights = heights
        self.ax.clear()
        
        self.scatter = self.ax.scatter(freqs / 1e6, heights, s=self.main.scatter_size, c=power, cmap=self.main.colormap, marker='s')
        self.scatter.set_clim(0, self.main.power_limit)

        if self.colorbar:
            # When clearing ax, the colorbar might need to be re-associated or cleared
            try:
                self.colorbar.remove()
                self.colorbar = None
            except:
                pass
        
        if self.colorbar is None:
            self.colorbar = self.figure.colorbar(self.scatter, ax=self.ax)
            self.colorbar.set_label("Power (dB)")
            self.colorbar.set_ticks(np.arange(0, self.main.power_limit + 1, 5))  # Fixed ticks from 0 to power_limit with step of 5
            self.scatter.set_clim(0, self.main.power_limit)  # Set color limits on scatter plot
        
        self.ax.set_title(f"Ionogram site: {site} at {timestamp.strftime('%H:%M:%S %d-%m-%Y')} {site_dict[site].get_tzstr(timestamp)}")
        self._set_plot_ax()
        
        # Re-create the interactive drawing line
        self.line = Line2D([], [], color='red', linewidth=2)
        self.ax.add_line(self.line)

        self.line_polan = Line2D([], [], color='green', linewidth=2, linestyle='--')
        self.ax.add_line(self.line_polan)

        self.fig.subplots_adjust(left=0.1, right=1.05, bottom=0.075, top=0.95)

        self.draw()

    
    def plot_interp(self, interp_freqs, interp_heights):
        interp_freqs = np.array(interp_freqs) # Removed Hz conversion as interp_freqs should already be in MHz
        if self.interp_line is not None and self.interp_line in self.ax.lines:
            self.interp_line.remove()
        self.interp_line = Line2D(interp_freqs, interp_heights, color='magenta', linewidth=1.5, linestyle='--')
        self.ax.add_line(self.interp_line)

        self.draw_idle()

    def plot_polan(self, freqs, real_heights, interp_freqs, interp_heights):
        freqs = np.array(freqs) # Removed Hz conversion as freqs should already be in MHz
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

    def on_mouse_scroll(self, event):
        if event.inaxes != self.ax:
            return

        xdata, ydata = event.xdata, event.ydata
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        if event.button == 'up':  # Zoom in
            scale_factor = 1 / self.zoom_factor
        elif event.button == 'down':  # Zoom out
            scale_factor = self.zoom_factor
        else:
            return

        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

        self.ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        self.ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])
        self.draw_idle()

    def reset_zoom(self):
        self.ax.set_xlim(self.freq_limits)
        self.ax.set_ylim(self.height_limits)
        self.draw_idle()

    def draw_auto_curve(self, freqs, heights, dops, signals):
        freqs = freqs / 1e6 # Convert freqs from Hz to MHz
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
        freqs_interp, heights_interp, unique_freqs, avg_heights = self.get_polan_curve(points, spacing=0.2)
        if len(heights_interp) >= 1:
            self.plot_interp(freqs_interp, heights_interp)
        return freqs_interp, heights_interp, unique_freqs, avg_heights
    
    def get_polan_curve(self, points, spacing=0.2, max_points=54):
        if self.main.polan_interp_mode.upper() == 'OLD':
            return self.compute_matched_curve(points, spacing=spacing, max_points=max_points)
        elif self.main.polan_interp_mode.upper() == 'NEW':
            return self.new_compute_matched_curve(points, spacing=spacing, max_points=max_points)
        else:
            raise ValueError(f"POLAN interpolation mode must be 'old' or 'new', got {self.polan_interp_mode} instead.")


    def draw_manual_curve(self):
        if not self.drawn_points:
            return np.array([]), np.array([])
        points = np.array([(x, y) for x, y in self.drawn_points if x is not None and y is not None])
        if points.size == 0:
            return np.array([]), np.array([])
        if points.shape[0] < 2:
            return np.array([]), np.array([])
        freqs_interp, heights_interp, unique_freqs, avg_heights = self.get_polan_curve(points, spacing=0.1)
        return freqs_interp, heights_interp, unique_freqs, avg_heights

    def compute_matched_curve(self, points, spacing=0.5, max_points=54):
        """
            Interpolate a curve based on some sample inputs(automatic or hand drawn), and return an output curve at fixed frequency steps. 
            Required for POLAN.
        """
        freqs_mhz = points[:, 0] # points[:, 0] is already in MHz from event.xdata
        heights = points[:, 1]

        freqs_rounded = np.round(freqs_mhz, 1)

        unique_freqs, inverse_indices = np.unique(freqs_rounded, return_inverse=True)
        avg_heights = np.zeros_like(unique_freqs)

        for i in range(len(unique_freqs)):
            avg_heights[i] = heights[inverse_indices == i].mean()

        f_min = np.floor(unique_freqs.min() * 10) / 10
        f_max = np.ceil(unique_freqs.max() * 10) / 10
        num_points = min(int(np.round((f_max - f_min) / spacing)) + 1, max_points)
        freqs_interp = np.round(np.linspace(f_min, f_max, num_points), 1)

        interpolator = PchipInterpolator(unique_freqs, avg_heights, extrapolate=False)
        heights_interp = interpolator(freqs_interp)
        mask = ~np.isnan(heights_interp)
        freqs_interp = freqs_interp[mask]
        heights_interp = heights_interp[mask]

        return freqs_interp, heights_interp, unique_freqs, avg_heights
    
    def new_compute_matched_curve(self, points, spacing=0.1, max_points=54):
        """
            Interpolate a curve based on some sample inputs(automatic or hand drawn), and return an output curve at variable frequency steps, experimental. 
            Required for POLAN.
        """
        freqs_mhz = points[:, 0]
        heights = points[:, 1]

        freqs_rounded = np.round(freqs_mhz, 2)

        unique_freqs, inverse_indices = np.unique(freqs_rounded,
                                                return_inverse=True)
        avg_heights = np.zeros_like(unique_freqs)
        for i in range(len(unique_freqs)):
            avg_heights[i] = heights[inverse_indices == i].mean()

        fmin = unique_freqs.min()
        fmax = unique_freqs.max()

        interpolator = PchipInterpolator(unique_freqs, avg_heights,
                                        extrapolate=False)
        dense_x = np.linspace(fmin, fmax, 2000)
        dy_dx = interpolator.derivative()(dense_x)

        arc = np.sqrt(1.0 + dy_dx**2)
        s = cumulative_trapezoid(arc, dense_x, initial=0)
        s_norm = s / s[-1]

        raw_freqs = np.interp(np.linspace(0, 1, max_points), s_norm, dense_x)

        raw_freqs = np.round(raw_freqs, 2)
        raw_freqs = np.sort(raw_freqs)

        raw_freqs[0] = np.round(fmin, 2)
        raw_freqs[-1] = np.round(fmax, 2)

        min_step = 0.01
        filtered = [raw_freqs[0]]

        for f in raw_freqs[1:]:
            if f - filtered[-1] >= min_step - 1e-12:
                filtered.append(f)
            else:
                filtered[-1] = f

        freqs = np.array(filtered)

        max_step = 2.0 * spacing
        expanded = [freqs[0]]
        for i in range(1, len(freqs)):
            prev = freqs[i - 1]
            curr = freqs[i]
            gap = curr - prev

            if gap > max_step + 1e-12:
                # insert missing midpoints at <= 0.1 step
                n_insert = int(np.floor(gap / max_step))
                for k in range(1, n_insert + 1):
                    new_f = prev + k * max_step
                    new_f = np.round(new_f, 2)
                    if new_f < curr - 1e-12:
                        expanded.append(new_f)

            expanded.append(curr)

        freqs_final = np.array(expanded)

        if len(freqs_final) > max_points:
            keep_start = max_points // 2
            keep_end = max_points - keep_start
            freqs_final = np.concatenate([freqs_final[:keep_start],
                                        freqs_final[-keep_end:]])

        heights_final = interpolator(freqs_final)
        mask = ~np.isnan(heights_final)
        freqs_final = freqs_final[mask]
        heights_final = heights_final[mask]

        return freqs_final, heights_final, unique_freqs, avg_heights