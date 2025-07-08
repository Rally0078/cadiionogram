import numpy as np
import pandas as pd

class PandasUtils:
    def __init__(self):
        pass
    
    @staticmethod
    def create_pandas_from_arrays(metadata, freqs, heights, dop_shifts, sensors):
        signals_re_im_separate = sensors
        column_names = ['freq (Hz)', 'height (km)', 'dopplershift']

        for i in range(signals_re_im_separate.shape[1]):
            signals_idx = i//2
            if i%2 == 0:
                column_names.append(f"sensor{signals_idx+1} real")
            else:
                column_names.append(f"sensor{signals_idx+1} imag")

        receiver_signals = [signals_re_im_separate[:, i] for i in range(signals_re_im_separate.shape[1])]   #Is this needed?

        table_data = [freqs, heights, dop_shifts, *receiver_signals]
        date_of_obs = metadata['datetime']
        timepartitions = np.array(list(metadata['timepartitions'].values()))
        tmp = timepartitions[0]
        timepartitions = np.diff(timepartitions, prepend=timepartitions[0])
        timepartitions[0] = tmp
        base_date_str = f"{date_of_obs.year:04d}-{date_of_obs.month:02d}-{date_of_obs.day:02d}"
        repeating_indices = np.repeat(list(metadata['timepartitions'].keys()), timepartitions)
        datetime_strs = np.char.add(base_date_str + ' ', repeating_indices)
        datetime_strs = np.char.add(datetime_strs, "+00:00")
        time_index = pd.to_datetime(datetime_strs, format='%Y-%m-%d %H:%M:%S%z', utc=True)
        df_sensors = pd.DataFrame.from_dict(dict(zip(column_names, table_data)))
        df_sensors = df_sensors.set_index(time_index)

        return df_sensors
    
    @staticmethod
    def create_arrays_from_pandas(metadata, df_sensors):
        column_names = ['freq (Hz)', 'height (km)', 'dopplershift']
        noofreceivers = metadata['noofreceivers']
        for i in range(2 * noofreceivers):
            signals_idx = i//2
            if i%2 == 0:
                column_names.append(f"sensor{signals_idx+1} real")
            else:
                column_names.append(f"sensor{signals_idx+1} imag")
        height, frequency, dop_shifts = df_sensors['height (km)'].to_numpy(), df_sensors['freq (Hz)'].to_numpy(), df_sensors['dopplershift'].to_numpy()
        sensors_all = df_sensors[column_names[len(column_names) - 2 * noofreceivers:]].to_numpy()
        complex_signal = sensors_all.astype(np.int8)

        return frequency, height, dop_shifts, complex_signal