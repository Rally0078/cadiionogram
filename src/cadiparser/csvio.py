from .readrawdata import DataReader
import pandas as pd
import numpy as np
from pathlib import Path, PosixPath, WindowsPath
import json
import datetime

type time_partition_dict = dict[int, int]

class CSVtools:
    def __init__(self):
        self.csv_dtypes = {"height (km)": np.int32,
        "frequency (MHz)": np.float64,
        "doppler shift": np.float64,
        "sensor0 (signal unit)": np.complex128,
        "sensor1 (signal unit)": np.complex128,
        "sensor2 (signal unit)": np.complex128,
        "sensor3 (signal unit)": np.complex128
        }

    def write_csv(self, filename: str | Path, output: str | Path, raw_reader: DataReader) -> tuple[dict, Path]:
        """
            Write from a raw md2/md4 file to text files. Writes metadata in JSON and data in csv

            TODO: Description
        """
        metadata, heights, freqs, dop_shifts, sensors = raw_reader.read_raw_data(filename)
        partitions = metadata['timepartitions']

        output_dir = Path(output)
        obs_datetime = metadata['datetime']
        obs_dir_name = f"{obs_datetime.day:02d}{obs_datetime.month:02d}{obs_datetime.year:04d}"
        #Create folder for each day of observation, with the foldername ddmmyyyy
        obs_output_path = output_dir / obs_dir_name
        Path(obs_output_path).mkdir(parents=True, exist_ok=True)
        metadata_path = Path(output_dir / obs_dir_name / f"metadata{obs_datetime.hour:02d}.json")
        metadata['source'] = filename.name if type(filename) == PosixPath or WindowsPath else filename
        metadata['datafiles'] = []
        #Using a two-pointers approach to slice the partitions
        lpointer = 0
        for minute, rpointer in partitions.items():
            #Create dataframe
            #Todo: Rewrite for arbitrary number of receivers. Currently supports only 4 receivers
            df_sensors = pd.DataFrame({
                'height (km)' : heights[lpointer:rpointer],
                'frequency (MHz)' : freqs[lpointer:rpointer]/1e6,
                'doppler shift': dop_shifts[lpointer:rpointer],
                'sensor0 (signal unit)' : sensors[lpointer:rpointer, 0],
                'sensor1 (signal unit)' : sensors[lpointer:rpointer, 1],
                'sensor2 (signal unit)' : sensors[lpointer:rpointer, 2],
                'sensor3 (signal unit)' : sensors[lpointer:rpointer, 3],
            })

            lpointer = rpointer     #Update the left pointer to the previous right pointer
            #Save dataframe to file with timestamp
            df_sensors.to_csv(Path(output_dir / obs_dir_name / f"sensor_data{obs_datetime.hour:02d}{minute:02d}.csv"), index=False)
            metadata['datafiles'].append(f"sensor_data{obs_datetime.hour:02d}{minute:02d}.csv")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4, default=str)
        return metadata, obs_output_path

    def write_csv_day(self, input_dir: Path, extension_str: str, output_dir: str | Path, raw_reader: DataReader):
        """
        Writes a single CSV from a folder containing data for an entire day. Reads both md3 and md4 to write CSV and metadata files for 
        each format.

        TODO: Description
        """
        all_heights, all_freqs, all_dopshifts, all_sensors = np.array([], dtype=np.int32), np.array([], dtype=np.float64), np.array([],dtype=np.float64), np.empty(shape=(0,4), dtype=np.complex128)
        all_metadata, all_heights, all_freqs, all_dopshifts, all_sensors = raw_reader.read_raw_data_dir(input_dir, extension_str)

        obs_datetime: datetime.datetime = all_metadata['datetime']
        obs_dir_name = f"{obs_datetime.day:02d}{obs_datetime.month:02d}{obs_datetime.year:04d}"
        obs_output_path = output_dir / obs_dir_name
        #Create folder if it doesnt exist
        Path(obs_output_path).mkdir(parents=True, exist_ok=True)
        
        metadata_path = Path(obs_output_path / f"metadata_day{extension_str}.json")
        
        with open(metadata_path, 'w') as f:
            json.dump(all_metadata, f, indent=4, default=str)
        timestamp: datetime.datetime = all_metadata['datetime']

        timepartitions = np.array(list(all_metadata['timepartitions'].values()))
        tmp = timepartitions[0]
        timepartitions = np.diff(timepartitions, prepend=timepartitions[0])
        timepartitions[0] = tmp
        
        repeating_indices = np.repeat(list(all_metadata['timepartitions'].keys()), timepartitions)

        repeating_indices = np.array([datetime.datetime.strptime(f"{timestamp.year:04d}-{timestamp.month:02d}-{timestamp.day:02d} {time_str}:00+00:00", 
                                                        '%Y-%m-%d %H:%M:%S%z') for time_str in repeating_indices])
        time_index = pd.to_datetime(repeating_indices).time

        df_sensors = pd.DataFrame({
        'height (km)' : all_heights,
        'frequency (MHz)' : all_freqs/1e6,
        'doppler shift': all_dopshifts,
        'sensor0 (signal unit)' : all_sensors[:, 0],
        'sensor1 (signal unit)' : all_sensors[:, 1],
        'sensor2 (signal unit)' : all_sensors[:, 2],
        'sensor3 (signal unit)' : all_sensors[:, 3],
        }, index=time_index)
        df_sensors.index.name = "timestamp"
        
        df_sensors.to_csv(Path(obs_output_path / f"sensor_data{extension_str}.csv"))
        return all_metadata, obs_output_path

    def read_from_csv(self, filename: Path) -> tuple[dict, np.ndarray, np.ndarray, np.ndarray]:
        """
            Read data from CSV by providing a metadata file
            
            TODO: Description
        """
        with open(filename, 'r') as f:
            json_input = json.load(f)
            json_input['datetime'] = datetime.datetime.strptime(json_input['datetime'], '%Y-%m-%d %H:%M:%S%z')
            datafiles = json_input['datafiles']
            partitions = json_input['timepartitions'] = {int(minute): int(idx) for minute, idx in json_input['timepartitions'].items()}
            length = partitions[max(partitions)]
            noofreceivers = json_input['noofreceivers']
            heights = np.zeros(shape=(length), dtype=np.int32)
            frequencies = np.zeros(shape=(length), dtype=np.float64)
            dop_shifts = np.zeros(shape=(length), dtype=np.float64)
            signals = np.zeros(shape=(length, json_input['noofreceivers']), dtype=np.complex128)
            lpointer = 0
            for rpointer, datafile in zip(partitions.values(), datafiles):
                df = pd.read_csv(Path(filename.parent / datafile))
                for column_name,column_dtype in self.csv_dtypes.items():
                    df[column_name] = df[column_name].astype(column_dtype)
                heights[lpointer:rpointer] = df['height (km)'].to_numpy(dtype=np.int32)
                frequencies[lpointer:rpointer] = df['frequency (MHz)'].to_numpy(dtype=np.float64)
                dop_shifts[lpointer:rpointer] = df['doppler shift'].to_numpy(dtype=np.float64)
                signals[lpointer:rpointer,0] = df['sensor0 (signal unit)'].to_numpy(dtype=np.complex128)
                signals[lpointer:rpointer,1] = df['sensor1 (signal unit)'].to_numpy(dtype=np.complex128)
                signals[lpointer:rpointer,2] = df['sensor2 (signal unit)'].to_numpy(dtype=np.complex128)
                signals[lpointer:rpointer,3] = df['sensor3 (signal unit)'].to_numpy(dtype=np.complex128)
                lpointer = rpointer
            return json_input, heights, frequencies, dop_shifts, signals

    def read_from_csv_day(self, filename: Path) -> tuple[dict, np.ndarray, np.ndarray, np.ndarray]:
        """
            Read whole day's data from CSV by providing a metadata_day file
            
            TODO: Description
        """
        with open(filename, 'r') as f:
            json_input = json.load(f)
            json_input['datetime'] = datetime.datetime.strptime(json_input['datetime'], '%Y-%m-%d %H:%M:%S%z')
            partitions = json_input['timepartitions'] = {minute: int(idx) for minute, idx in json_input['timepartitions'].items()}
            length = partitions[max(partitions)]
            heights = np.zeros(shape=(length), dtype=np.int32)
            frequencies = np.zeros(shape=(length), dtype=np.float64)
            dop_shifts = np.zeros(shape=(length), dtype=np.float64)
            signals = np.zeros(shape=(length, json_input['noofreceivers']), dtype=np.complex128)
            extension = json_input['extension']
            df = pd.read_csv(Path(filename.parent / f"sensor_data{extension}.csv"), index_col=0)
            for column_name,column_dtype in self.csv_dtypes.items():
                df[column_name] = df[column_name].astype(column_dtype)
            heights = df['height (km)'].to_numpy(dtype=np.int32)
            frequencies = df['frequency (MHz)'].to_numpy(dtype=np.float64)
            dop_shifts = df['doppler shift'].to_numpy(dtype=np.float64)
            signals[:,0] = df['sensor0 (signal unit)'].to_numpy(dtype=np.complex128)
            signals[:,1] = df['sensor1 (signal unit)'].to_numpy(dtype=np.complex128)
            signals[:,2] = df['sensor2 (signal unit)'].to_numpy(dtype=np.complex128)
            signals[:,3] = df['sensor3 (signal unit)'].to_numpy(dtype=np.complex128)
            df.index = pd.to_datetime(df.index, format='%H:%M:%S').time
            return json_input, heights, frequencies, dop_shifts, signals

