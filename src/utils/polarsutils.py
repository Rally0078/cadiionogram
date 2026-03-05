import numpy as np
import polars as pl

class PolarsUtils:
    def __init__(self):
        pass
    
    @staticmethod
    def create_polars_from_arrays(metadata, freqs, heights, dop_shifts, sensors):
        """
            Creates a polars dataframe from the given input.

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
                Contains the sensor values in I and Q pairs for each receiver. Note: **Currently supports only CADI's MDx format**.

            Returns
            -------
            df : `polars.DataFrame`
                DataFrame containing all the IQ, frequency, and height data with a datetime column from metadata.

        """
        signals_re_im_separate = sensors
        column_names = ['freq (Hz)', 'height (km)', 'dopplershift']

        for i in range(signals_re_im_separate.shape[1]):
            signals_idx = i//2
            if i%2 == 0:
                column_names.append(f"sensor{signals_idx+1} real")
            else:
                column_names.append(f"sensor{signals_idx+1} imag")

        receiver_signals = [signals_re_im_separate[:, i] for i in range(signals_re_im_separate.shape[1])]

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
        
        # Create polars dataframe with data dictionary
        data_dict = dict(zip(column_names, table_data))
        # Convert datetime strings to polars datetime
        # Polars datetime parsing - convert to list first for better compatibility
        datetime_list = [str(datetime_str) for datetime_str in datetime_strs]
        # Parse datetime strings with timezone
        datetime_series = pl.Series("datetime", datetime_list).str.to_datetime(
            format='%Y-%m-%d %H:%M:%S%z',
            strict=False
        )
        # Ensure timezone is set to UTC if not already set
        if datetime_series.dtype.time_zone is None:
            datetime_series = datetime_series.dt.replace_time_zone('UTC')
        
        data_dict["datetime"] = datetime_series
        df_sensors = pl.DataFrame(data_dict)
        # Note: Order is preserved as arrays are provided (same as pandas index order)

        return df_sensors
    
    @staticmethod
    def create_arrays_from_polars(metadata, df_sensors):
        """
            Reads frequency, height, dopplers, and IQ data from `polars.DataFrame`.

            Parameters
            ----------
            metadata : `Dict`
                Metadata containing information about the data. This is required to shape the arrays correctly.
            df_sensors : `polars.DataFrame`
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
        for i in range(2 * noofreceivers):
            signals_idx = i//2
            if i%2 == 0:
                column_names.append(f"sensor{signals_idx+1} real")
            else:
                column_names.append(f"sensor{signals_idx+1} imag")
        height = df_sensors['height (km)'].to_numpy()
        frequency = df_sensors['freq (Hz)'].to_numpy()
        dop_shifts = df_sensors['dopplershift'].to_numpy()
        sensor_column_names = column_names[len(column_names) - 2 * noofreceivers:]
        sensors_all = df_sensors.select(sensor_column_names).to_numpy()
        complex_signal = sensors_all.astype(np.int8)

        return frequency, height, dop_shifts, complex_signal
