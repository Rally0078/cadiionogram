#PySide6 FigureCanvas to plot MD4 Ionogram as scatterplot
from scipy.interpolate import PchipInterpolator
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter, MultipleLocator, FuncFormatter
from datetime import datetime
import numpy as np
from scipy.integrate import cumulative_trapezoid
from src.utils.siteinfo import SiteInfo
from src.ionogramfiltering.noisereduction import *
from src.plotstate.scaling_region_state import ScaleRegionValues

class AutoScaleIonogramCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(16, 9))
        self.main = parent # Store main widget reference
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.scatter = None
        self.colorbar = None
        self.freq_ticks = [1, 2, 4, 6, 8, 10, 15, 20]
        self.freq_limits = (1, 18)
        self.height_ticks = np.arange(0, 1100, 100)
        self.height_limits = (50, 1100)
        self.scaled_values_lines = ScaleRegionValues(self.ax, 
                                                     self.main.scaling_line_width, labels=
                                                     ['E',
                                                      'F',''])
        self._set_plot_ax()
        self.mpl_connect("button_press_event", self.on_mouse_press)
        self.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.mpl_connect("button_release_event", self.on_mouse_release)
        self.mpl_connect("scroll_event", self.on_mouse_scroll)
        self.zoom_factor = 1.2
        self.legend = None
        self.extra_data = {}
        self.drawing = False
        self.drawn_points = []
        self.line = None
        self.line_polan = None
        self.interp_line = None
        #self.plot_initial()

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
        self.ax.grid()

    def plot_scatter(self, freqs, heights, dops, signals, timestamp, site):
        self.ax.clear()
        self.legend = None  # ax.clear() destroys all artists; reset so _update_legend_box recreates it
        self.fig.tight_layout(pad=3)
        # Use configurable plotting options
        self.scatter = self.ax.scatter(freqs / 1e6, heights, s=self.main.scatter_size, c=signals, cmap=self.main.colormap, marker='s')
        self.scatter.set_clim(0, self.main.power_limit)

        if self.colorbar:
            self.colorbar.update_ticks()
            #self.colorbar.set_clim(signals.min(), signals.max())  # Update color limits
        else:
            # Create the colorbar if it doesn't exist
            self.colorbar = self.figure.colorbar(self.scatter, ax=self.ax)
            self.colorbar.set_label("Power (dB)")
            self.colorbar.set_ticks(np.arange(0, self.main.power_limit + 1, 5))  # Fixed ticks from 0 to power_limit with step of 5
            self.scatter.set_clim(0, self.main.power_limit)  # Set color limits on scatter plot
        self.ax.set_title(f"Ionogram site: {site} at {timestamp.strftime("%H:%M:%S %d-%m-%Y")} {SiteInfo.from_file(site).get_tzstr(timestamp)}")
        self._set_plot_ax()
        self.fig.subplots_adjust(left=0.1, right=1.05, bottom=0.075, top=0.95)
        # Re-create/re-add the interactive drawing line and polan line
        self.line = Line2D([], [], color='red', linewidth=2)
        self.ax.add_line(self.line)

        self.line_polan = Line2D([], [], color='darkblue', linewidth=2, linestyle='--')
        self.ax.add_line(self.line_polan)

        self.drawing = False
        self.drawn_points = []

        # Reset lines
        self.scaled_values_lines.clear_all()
        self._update_legend_box()
        self.draw()

    def on_mouse_press(self, event):
        # Only respond to left or right clicks inside axes
        if event.inaxes != self.ax:
            return

        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            #Get current scale region mode
            if self.main.scale_box1.isChecked():
                text_legend = self.main.config.get('scaling', 'scalingoption1')
            elif self.main.scale_box2.isChecked():
                text_legend = self.main.config.get('scaling', 'scalingoption2')
            elif self.main.scale_box3.isChecked():
                text_legend = self.main.config.get('scaling', 'scalingoption3')
            else:
                raise KeyError("No valid region selected for manual scaling")
            self.scaled_values_lines.set_region(text_legend)
            
            if event.button == 1:  # Left click -> scale height
                # Create a new line or clear old one
                self.scaled_values_lines.h = event.ydata
            elif event.button == 3:  # Right click -> scale frequency
                self.scaled_values_lines.f = event.xdata
            self.handle_legend()
            self.draw()
        else:
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

    def plot_interp(self, interp_freqs, interp_heights):
        interp_freqs = np.array(interp_freqs)
        if self.interp_line is not None and self.interp_line in self.ax.lines:
            self.interp_line.remove()
        self.interp_line = Line2D(interp_freqs, interp_heights, color='magenta', linewidth=1.5, linestyle='--')
        self.ax.add_line(self.interp_line)

        self.draw_idle()

    def plot_polan(self, freqs, real_heights, interp_freqs, interp_heights, extra_data):
        if len(freqs) == 0:
            return
        freqs = np.array(freqs)
        self.extra_data = extra_data  # Store so _update_legend_box can access it
        self.plot_interp(interp_freqs, interp_heights)
        if self.line_polan is None:
            self.line_polan = Line2D(freqs, real_heights, color='darkblue', linewidth=2, linestyle='--')
            self.ax.add_line(self.line_polan)
        else:
            self.line_polan.set_data(freqs, real_heights)
        self.handle_legend()
        self.draw()

    def draw_new_auto_curve(self, df):
        freqs, heights, dops = df['freq (Hz)'].to_numpy(), df['height (km)'].to_numpy(), df['dopplershift'].to_numpy()
        signal_col_names = [f"sensor{i//2 + 1} {'real' if i%2 == 0 else 'imag'}" for i in range(8)]
        signals = df[signal_col_names].to_numpy()

        freqs = freqs / 1e6 # Convert freqs from Hz to MHz
        freqs_omode, heights_omode, _, _ = o_x_separation(freqs, heights, dops, signals, site=self.main.metadata['site'], mode='O')
        autoscale_output = autoscale(freqs_omode, heights_omode, 
                                     freq_list=np.array(self.main.freqs_list)/1e6, 
                                     height_list=np.arange(self.main.metadata['minheight'], self.main.metadata['maxheight'], 3.0),
                                     n_dilations=3,n_erosions=2)
        freq_new_x, height_new_y = autoscale_output['freq_output'], autoscale_output['height_output']
        points = np.array([(x, y) for x, y in zip(freq_new_x, height_new_y)])
        freqs_interp, heights_interp, unique_freqs, avg_heights = self.get_polan_curve(points, spacing=0.1)
        if len(heights_interp) >= 1:
            self.plot_interp(freqs_interp, heights_interp)
            self.scaled_values_lines.set_region('F')

            self.scaled_values_lines.h = height_new_y[0]

            self.scaled_values_lines.f = freq_new_x[-1]
            self.handle_legend()
        return freqs_interp, heights_interp, unique_freqs, avg_heights

    def get_polan_curve(self, points, spacing=0.2, max_points=54):
        if self.main.polan_interp_mode.upper() == 'OLD':
            return self.compute_matched_curve(points, spacing=spacing, max_points=max_points)
        elif self.main.polan_interp_mode.upper() == 'NEW':
            return self.new_compute_matched_curve(points, spacing=spacing, max_points=max_points)
        else:
            raise ValueError(f"POLAN interpolation mode must be 'old' or 'new', got {self.polan_interp_mode} instead.")


    def draw_manual_curve(self, df):
        if not self.drawn_points:
            return np.array([]), np.array([]), np.array([]), np.array([])
        points = np.array([(x, y) for x, y in self.drawn_points if x is not None and y is not None])
        if points.size == 0:
            return np.array([]), np.array([]), np.array([]), np.array([])
        if points.shape[0] < 2:
            return np.array([]), np.array([]), np.array([]), np.array([])
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
    
    def new_compute_matched_curve(self, points, spacing=0.05, max_points=54):
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

    def _update_legend_box(self):
        """Create the custom legend text box once; update its text on subsequent calls."""
        lines = []
        for s in self.scaled_values_lines._state.values():
            for line in [s['hline'], s['fline']]:
                if line is not None:
                    lines.append(line)

        if not lines:
            if self.legend is not None:
                self.legend.set_visible(False)
            return

        parts = [line.get_label() for line in lines]
        if self.extra_data:
            parts.extend(f"{k}: {v}" for k, v in self.extra_data.items())
        box_text = "\n".join(parts)

        if self.legend is not None:
            self.legend.set_text(box_text)
            self.legend.set_visible(True)
        else:
            self.legend = self.ax.text(
                0.01, 0.99, box_text,
                transform=self.ax.transAxes,
                verticalalignment='top',
                horizontalalignment='left',
                fontsize=14,
                family='monospace',
                bbox=dict(
                    boxstyle='round,pad=0.4',
                    facecolor='white',
                    edgecolor='#444444',
                    alpha=0.85,
                    linewidth=1.2,
                )
            )

    def handle_legend(self):
        self._update_legend_box()
    def clean_canvas(self):
        self.scaled_values_lines.clear_all()
        if self.legend is not None:
            self.legend.remove()
            self.legend = None
        self.draw()