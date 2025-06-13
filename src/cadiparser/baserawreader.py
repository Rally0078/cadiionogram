#Base class for all raw readers
#All raw data readers must subclass this to conform to the API for uniformity
from abc import ABC, abstractmethod
from pathlib import Path
import numpy as np

type time_partition_dict = dict[str, int]

class DataReader(ABC):
    @abstractmethod
    def read_raw_data(self, filename: Path, 
                      cached: bool = False, cache_dir: Path | None = None) -> tuple[list, dict, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        pass
    @abstractmethod
    def read_raw_data_dir(self, input_dir: Path, extension: str, 
                          multithread=False, backend='threading', 
                          cached=False, cache_dir: Path | None = None) -> tuple[list, dict, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        pass