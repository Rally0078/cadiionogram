"""
    Base raw reader for all ionogram file types. 

    API specification
    ---
    All reader classes must subclass the abstract class `DataReader`, providing overrides to the abstract methods as follows:

    Methods
    ---------
    read_raw_data : Reads ionogram data from a file.

    read_raw_data_dir : Reads ionogram data from a directory containing one or more files.
"""
from abc import ABC, abstractmethod
from pathlib import Path
import numpy as np


class DataReader(ABC):
    @staticmethod
    @abstractmethod
    def read_raw_data(filename: Path) -> tuple[list, dict, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        pass
    @staticmethod
    @abstractmethod
    def read_raw_data_dir(input_dir: Path, extension: str, 
                          multithread=False, backend='threading') -> tuple[list, dict, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        pass