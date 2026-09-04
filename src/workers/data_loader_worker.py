from PySide6.QtCore import QObject, Signal, QRunnable
from src.errorhandlers.errorhandling import FolderNotContainingData
from pathlib import Path
import numpy as np

class DataLoaderSignals(QObject):
    """
    Defines the signals available from a running DataLoaderWorker thread.
    """
    finished = Signal(list, dict, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, str)
    error = Signal(str)

class DataLoaderWorker(QRunnable):
    """
    Worker for loading raw data from a directory in a separate thread.
    Emits a signal upon completion with the loaded data or an error message.
    """
    def __init__(self, location: Path, extension: str, raw_reader, radar_type: str='cadi'):
        super().__init__()
        self.location = location
        self.extension = extension
        self.raw_reader = raw_reader
        self.radar_type = radar_type
        self.signals = DataLoaderSignals()

    def run(self):
        try:
            multithread=False
            backend='loky'
            files_list, metadata, heights, freqs, freqs_list, dops, signals = self.raw_reader.read_raw_data_dir(self.location, self.extension, multithread=multithread, backend=backend)
            print(f"Data loading completed. Loaded {len(metadata['timepartitions'].keys())} timestamps. {"Multithread enabled with " + backend + "." if multithread==True else "Single thread."}")
            self.signals.finished.emit(files_list, metadata, heights, freqs, freqs_list, dops, signals, self.radar_type)
        except FolderNotContainingData:
            self.signals.error.emit("You must choose a folder containing the data.")
        except Exception as e:
            self.signals.error.emit(f"An unexpected error occurred during data loading: {e}")
