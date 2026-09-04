from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from src.utils.siteinfo import SiteInfo

class PandasUtils:
    def __init__(self):
        pass
    
    @staticmethod
    def create_pandas_from_arrays(metadata, freqs, heights, dop_shifts, sensors, radar_type='cadi'):
        """
            Creates a pandas dataframe from the given input.

            Parameters
            ----------
            metadata : `dict`
                Contains the metadata from a file or multiple files.
            freqs : `numpy.ndarray`
                Contains all the frequencies indexed by time.
            heights : `numpy.ndarray`
                Contains all the heights indexed by time.
            dop_shifts : `numpy.ndarray`
                Contains the doppler values indexed by time.
            sensors : `numpy.ndarray`
                Contains the sensor values in I and Q pairs for each receiver.
            radar_type: `str`
                Contains the radar type. This is either `cadi` or `sameer`. In the case of SAMEER data, the output is in amplitude-phase format instead of I/Q.

            Returns
            -------
            df : `pandas.DataFrame`
                DataFrame containing all the IQ, frequency, and height data indexed by the timestamp from metadata.

        """
        signals_re_im_separate = sensors
        column_names = ['freq (Hz)', 'height (km)', 'dopplershift']
        if radar_type.lower() == 'cadi':
            for i in range(signals_re_im_separate.shape[1]):
                signals_idx = i//2
                if i%2 == 0:
                    column_names.append(f"sensor{signals_idx+1} real")
                else:
                    column_names.append(f"sensor{signals_idx+1} imag")
        elif radar_type.lower() == 'sameer':
            column_names.extend(['receiver_id', 'amplitude', 'phase'])
        else:
            raise ValueError('radar_type must be "cadi" or "sameer"')
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
        time_index = pd.to_datetime(datetime_strs, format='%Y-%m-%d %H:%M:%S')
        time_index = time_index.tz_localize(SiteInfo.from_file(metadata['site']).get_tzinfo(date_of_obs))
        df_sensors = pd.DataFrame.from_dict(dict(zip(column_names, table_data)))
        df_sensors = df_sensors.set_index(time_index)

        return df_sensors
    
    @staticmethod
    def create_arrays_from_pandas(metadata, df_sensors, radar_type='cadi'):
        """
            Reads frequency, height, dopplers, and IQ data from `pandas.DataFrame`.

            Parameters
            ----------
            metadata : `Dict`
                Metadata containing information about the data. This is required to shape the arrays correctly.
            df_sensors : `pandas.DataFrame`
                Contains all the IQ, frequency, height, and doppler data.

            Returns
            -------
            frequency : `numpy.ndarray`
            height : `numpy.ndarray`
            dop_shifts : `numpy.ndarray`
            complex_signal : `numpy.ndarray`

        """
        column_names = ['freq (Hz)', 'height (km)', 'dopplershift']
        noofreceivers = metadata['noofreceivers']
        if radar_type.lower() == "cadi":
            for i in range(2 * noofreceivers):
                signals_idx = i//2
                if i%2 == 0:
                    column_names.append(f"sensor{signals_idx+1} real")
                else:
                    column_names.append(f"sensor{signals_idx+1} imag")
            sensors_all = df_sensors[column_names[len(column_names) - 2 * noofreceivers:]].to_numpy()
            complex_signal = sensors_all.astype(np.int8)
        elif radar_type.lower() == 'sameer':
            sensors_all = df_sensors[['receiver_id', 'amplitude', 'phase']]
            complex_signal = sensors_all
        else:
            raise ValueError('radar_type must be "cadi" or "sameer"')
        height, frequency, dop_shifts = df_sensors['height (km)'].to_numpy(), df_sensors['freq (Hz)'].to_numpy(), df_sensors['dopplershift'].to_numpy()
        

        return frequency, height, dop_shifts, complex_signal

    @staticmethod
    def combine_folder_data(multi_folder_data: List, radar_type: str='cadi') -> Tuple[pd.DataFrame, Dict]:
        """
            Combines multiple folder data into a single DataFrame and unified metadata.

            Parameters
            ----------
            multi_folder_data: `List`
                List of dicts containing data from multiple folders, as given in mainwidgetservice.py
            radar_type: `str`
                Type of radar passed in as an str, can be `'cadi'` or `'sameer'`
            
            Returns
            -------
            combined_df: `pd.DataFrame`
                The combined Pandas dataframe of the multi-folder output
            combined_metadata: `dict`
                The combined metadata dictionaries of the multi-folder output
        """
        dfs = []
        combined_timepartitions = {}
        total_len = 0

        # Sort data by datetime if not already sorted
        multi_folder_data.sort(key=lambda x: x['metadata']['datetime'])

        for data in multi_folder_data:
            df = PandasUtils.create_pandas_from_arrays(
                data['metadata'], 
                data['freqs'], 
                data['heights'], 
                data['dops'], 
                data['signals'],
                radar_type
            )
            dfs.append(df)

            # Create combined timepartitions with full datetime strings
            date_str = data['metadata']['datetime'].strftime('%Y-%m-%d')
            for timestamp, count in data['metadata']['timepartitions'].items():
                combined_key = f"{date_str} {timestamp}"
                combined_timepartitions[combined_key] = count + total_len

            total_len += len(df)

        combined_df = pd.concat(dfs)

        # Use metadata from the first folder as base
        combined_metadata = multi_folder_data[0]['metadata'].copy()
        combined_metadata['timepartitions'] = combined_timepartitions
        # Set datetime to the very first observation's date (already sorted)

        return combined_df, combined_metadata