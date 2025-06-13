#PlotState
#Base class for all PlotState classes to be derived from
from abc import ABC, abstractmethod
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
class PlotState(ABC):
    def __init__(self, main_widget):
        self.main = main_widget  # Reference to MainWidget, all required information to the state comes from this reference.

    @abstractmethod
    def create_canvas(self) -> FigureCanvas:
        pass

    @abstractmethod
    def update_canvas(self, canvas):
        pass
