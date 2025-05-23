#PySide6 FigureCanvas to plot MD4 Ionogram as scatterplot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter, MultipleLocator
from matplotlib.lines import Line2D
import numpy as np

class RealHeightAnalysisCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(16, 9))
        
        super().__init__(self.fig)
        self.is_hidden = True
        self.ax = self.fig.add_subplot(111)
        self.scatter = None
        self.colorbar = None
        self.freq_ticks = np.arange(0, 18e6, 2e6)
        self.freq_limits = (1e6, 18e6)
        self.height_ticks = np.arange(0, 1100, 100)
        self.height_limits = (50, 1100)
        self.user_points = []
        self.user_point_artists = [] 
        self.drawing = False
        self.drawn_points = []  # List of (x, y) tuples for curve
        self.line = None  # Line2D object for the curve

        # Connect matplotlib mouse events
        self.mpl_connect("button_press_event", self.on_mouse_press)
        self.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.mpl_connect("button_release_event", self.on_mouse_release)
        self._set_plot_ax()
        #self.plot_initial()
        self.is_hidden = False
        self.setHidden(self.is_hidden)

    def _set_plot_ax(self):
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

    def plot_scatter(self, freqs, heights, signals, timestamp, site):
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
        self.ax.set_title(f"Ionogram site: {site} at time {timestamp} UTC")
        self._set_plot_ax()
        #self.fig.tight_layout()
        self.fig.subplots_adjust(left=0.1, right=1.05, bottom=0.075, top=0.95)
        self.drawing = False
        self.drawn_points = []

        # Re-create the interactive drawing line
        self.line = Line2D([], [], color='red', linewidth=2)
        self.ax.add_line(self.line)
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
        # Append current point and update line data
        self.drawn_points.append((event.xdata, event.ydata))
        xs, ys = zip(*self.drawn_points)
        self.line.set_data(xs, ys)
        self.draw()

    def on_mouse_release(self, event):
        if event.button == 1 and self.drawing:
            self.drawing = False
            # Drawing finished, curve is ready in self.drawn_points
            # You can add any post-processing here if needed
            # For example, print points:
            # print("Drawn curve points:", self.drawn_points)