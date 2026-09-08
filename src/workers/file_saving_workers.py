from PySide6.QtCore import QObject, Signal, QRunnable
from math import isnan

class FileSavingWorkerSignals(QObject):
    started = Signal()
    finished = Signal()
    error = Signal(str)

class FileSavingWorker(QRunnable):
    def __init__(self, df, output_path, require_index=False, sep=','):
        super().__init__()
        self.df = df
        self.output_path = output_path
        self.require_index = require_index
        self.sep = sep
        self.signals = FileSavingWorkerSignals()
    
    def run(self):
        self.signals.started.emit()
        try:
            if self.require_index:
                self.df.to_csv(self.output_path, index=self.require_index, sep=self.sep, datetime_format='%Y %m %d %H %M %S')
            else:
                self.df.to_csv(self.output_path, sep=self.sep)
        except Exception as e:
            self.signals.error.emit(str(e))
        self.signals.finished.emit()

class ImageSavingWorker(QRunnable):
    def __init__(self, figure, output_path):
        super().__init__()
        self.figure = figure
        self.output_path = output_path
        self.signals = FileSavingWorkerSignals()
    
    def run(self):
        self.signals.started.emit()
        try:
            self.figure.savefig(self.output_path, dpi=250, bbox_inches='tight')
        except Exception as e:
            self.signals.error.emit(str(e))
        self.signals.finished.emit()


        