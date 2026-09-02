from PySide6.QtCore import QObject, Signal, QRunnable
from datetime import datetime
import pandas as pd
import numpy as np
import polars as pl
from src.utils.cadikvector import compute_xy
from src.utils.cadikvector_new import compute_xy as compute_xy_pl
from src.utils.powerpreprocessing import convert_amplitude_to_power

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
    def __init__(self, date_of_obs, df, selected_timestamp, right_selected_timestamp, freqs_list, site='TIR'):
        super().__init__()
        self.df = df
        self.date_of_obs = date_of_obs
        self.selected_timestamp = selected_timestamp
        self.right_selected_timestamp = right_selected_timestamp
        self.freqs_list = freqs_list
        self.site = site
        self.signals = ComputationSignals()

    def run(self):
        try:
            start_dtime = datetime.strptime(self.selected_timestamp, "%Y-%m-%d %H:%M:%S")
            end_dtime = datetime.strptime(self.right_selected_timestamp, "%Y-%m-%d %H:%M:%S")
            start_dtime = start_dtime.replace(tzinfo=self.date_of_obs.tzinfo)
            end_dtime = end_dtime.replace(tzinfo=self.date_of_obs.tzinfo)
            
            df_selection = self.df.loc[start_dtime:end_dtime]
            df_all_outputs = []
            all_output_freqs = np.array([])
            df_selection.index.name = 'datetime'
            for dtime in np.unique(df_selection.index):
                df_output, output_freqs, output_heights, output_dops, output_signals, output_xpow = compute_xy_pl(
                    pl.from_pandas(df_selection.loc[dtime:dtime].reset_index())
                    ,self.freqs_list, sort_by_freq=False, site=self.site
                )
                if len(df_output) > 0:
                    df_output = df_output.to_pandas()
                    df_output.set_index("datetime", drop=True, inplace=True)
                    df_output['freq (Hz)'] = output_freqs.to_numpy()
                    df_output['dopplershift'] = output_dops.to_numpy()
                    df_output['xpower1 (dB)'] = 10*np.log10(output_xpow['x1_pow'].to_numpy())
                    df_output['xpower2 (dB)'] = 10*np.log10(output_xpow['x2_pow'].to_numpy())
                    all_output_freqs = np.concatenate([all_output_freqs, output_freqs])
                    df_all_outputs.append(df_output)
            df_all_outputs = pd.concat(df_all_outputs)
                
            
            self.signals.finished.emit(df_all_outputs, all_output_freqs)
        except Exception as e:
            self.signals.error.emit(f"An unexpected error occurred during computation: {e}")
