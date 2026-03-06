from PySide6.QtCore import QObject, Signal, QRunnable
from datetime import datetime
import pandas as pd
import numpy as np
from src.utils.cadikvector import compute_xy
from src.utils.pandasutils import PandasUtils

class ComputationSignals(QObject):
    """
    Defines the signals available from a running ComputationWorker thread.
    """
    finished = Signal(pd.DataFrame, np.ndarray)
    error = Signal(str)

class ComputationWorker(QRunnable):
    """
    Worker for performing intensive data computations in a separate thread.
    Emits a signal upon completion with the computed data or an error message.
    """
    def __init__(self, metadata, freqs, heights, dops, signals, selected_timestamp, right_selected_timestamp, freqs_list):
        super().__init__()
        self.metadata = metadata
        self.freqs = freqs
        self.heights = heights
        self.dops = dops
        self.raw_signals = signals
        self.selected_timestamp = selected_timestamp
        self.right_selected_timestamp = right_selected_timestamp
        self.freqs_list = freqs_list
        self.signals = ComputationSignals()

    def run(self):
        try:
            df = PandasUtils.create_pandas_from_arrays(self.metadata, self.freqs, self.heights, self.dops, self.raw_signals)
            date_of_obs: datetime = self.metadata['datetime']
            start_time = datetime.strptime(self.selected_timestamp, "%H:%M:%S")
            end_time = datetime.strptime(self.right_selected_timestamp, "%H:%M:%S")
            start_dtime = datetime(year=date_of_obs.year, month=date_of_obs.month, day=date_of_obs.day,
                                hour=start_time.hour, minute=start_time.minute, second=start_time.second, tzinfo=date_of_obs.tzinfo)
            end_dtime = datetime(year=date_of_obs.year, month=date_of_obs.month, day=date_of_obs.day,
                                hour=end_time.hour, minute=end_time.minute, second=end_time.second, tzinfo=date_of_obs.tzinfo)
            
            df_selection = df.loc[start_dtime:end_dtime]
            df_all_outputs = pd.DataFrame()
            all_output_freqs = np.array([])
            
            for dtime in np.unique(df_selection.index):
                df_output, output_freqs, output_heights, output_dops, output_signals, output_xpow = compute_xy(df_selection.loc[dtime], self.freqs_list, sort_by_freq=False)
                df_all_outputs = pd.concat([df_all_outputs if not df_all_outputs.empty else None, df_output])
                all_output_freqs = np.concatenate([all_output_freqs, output_freqs])
            
            self.signals.finished.emit(df_all_outputs, all_output_freqs)
        except Exception as e:
            self.signals.error.emit(f"An unexpected error occurred during computation: {e}")
