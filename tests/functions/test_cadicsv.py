import pytest
from pathlib import Path
import numpy as np
from cadiparser import csvio, readrawdata
import pandas as pd
import subprocess
import re
import datetime

class TestCADIcsv:
    def test_write_csv_md3(self, test_files_md3, test_get_types, test_csvio, test_raw_reader):
        output_dir = Path("./output/md3")
        #Export data from dataframe to CSV
        for input_file in test_files_md3:
            metadata, output_path = test_csvio.write_csv(input_file, output_dir, test_raw_reader)
            #Import data from CSV into dataframe
            assert metadata['source'] == input_file.name
            assert input_file.exists()
            assert output_path.exists()
            assert len(metadata['datafiles']) != 0
            assert len(metadata['timepartitions']) == len(metadata['datafiles'])
            total_length = 0
            for file, (minute, idx) in zip(metadata['datafiles'], metadata['timepartitions'].items()):
                csv_path = Path(output_path / file)
                assert csv_path.exists()
                df_test = pd.read_csv(csv_path)
                for column_name,column_dtype in test_get_types.items():
                    df_test[column_name] = df_test[column_name].astype(column_dtype)
                total_length += len(df_test)
            assert total_length == max(metadata['timepartitions'].values())

    def test_write_csv(self, test_get_all_files, test_get_types, test_csvio, test_raw_reader):
        output_dir = Path("./output/md4")
        csv_writer = csvio.CSVtools()
        #Export data from dataframe to CSV
        for input_file in test_get_all_files:
            metadata, output_path = test_csvio.write_csv(input_file, output_dir, test_raw_reader)
            #Import data from CSV into dataframe
            assert metadata['source'] == input_file.name
            assert input_file.exists()
            assert output_path.exists()
            assert len(metadata['datafiles']) != 0
            assert len(metadata['timepartitions']) == len(metadata['datafiles'])
            total_length = 0
            for file, (minute, idx) in zip(metadata['datafiles'], metadata['timepartitions'].items()):
                csv_path = Path(output_path / file)
                assert csv_path.exists()
                df_test = pd.read_csv(csv_path)
                for column_name,column_dtype in test_get_types.items():
                    df_test[column_name] = df_test[column_name].astype(column_dtype)
                total_length += len(df_test)
            assert total_length == max(metadata['timepartitions'].values())
    
    def test_write_csv_day(self, test_raw_files_day, test_csvio, test_raw_reader):
        for test_files_single_folder in test_raw_files_day:
            output_dir = Path("./outputsingle")

            metadata, _ = test_csvio.write_csv_day(test_files_single_folder,'md3', output_dir, test_raw_reader, multithread=True)
            filename = f"sensor_data{metadata['extension']}.csv"
            obs_datetime: datetime.datetime = metadata['datetime']
            folder_name = f"{obs_datetime.day:02d}{obs_datetime.month:02d}{obs_datetime.year:04d}"
            command = f"ls D:\\Programming\\Work\\displayionogram\\outputsingle\\{folder_name}\\{filename} | Get-Content | Measure-Object -Line"
            result = subprocess.run(['powershell.exe', '-Command', command], capture_output=True, text=True)
            no_of_lines = int(re.findall(r'\d+', result.stdout)[0]) -1
            metadata_no_of_lines = max(metadata['timepartitions'].values())
            assert no_of_lines == metadata_no_of_lines, f"Assertion failed for {filename}"

            metadata, _ = test_csvio.write_csv_day(test_files_single_folder,'md4', output_dir, test_raw_reader, multithread=True)
            filename = f"sensor_data{metadata['extension']}.csv"
            obs_datetime: datetime.datetime = metadata['datetime']
            folder_name = f"{obs_datetime.day:02d}{obs_datetime.month:02d}{obs_datetime.year:04d}"
            command = f"ls D:\\Programming\\Work\\displayionogram\\outputsingle\\{folder_name}\\{filename} | Get-Content | Measure-Object -Line"
            result = subprocess.run(['powershell.exe', '-Command', command], capture_output=True, text=True)
            no_of_lines = int(re.findall(r'\d+', result.stdout)[0]) -1
            metadata_no_of_lines = max(metadata['timepartitions'].values())
            assert no_of_lines == metadata_no_of_lines, f"Assertion failed for {filename}"

    def test_read_csv(self, test_files_md4, test_csvio, test_raw_reader):
        testfiles_dir = Path('./output/md4/09042025')
        for input_file in test_files_md4:
            metadata, heights, freqs, dop_shifts, sensors = test_raw_reader.read_raw_data(input_file)
            hour = metadata['datetime'].hour

            new_metadata, new_heights, new_freqs, new_dop_shifts, new_sensors = test_csvio.read_from_csv(Path(testfiles_dir / f"metadata{hour:02d}.json"))
            assert metadata['site'] == new_metadata['site']
            assert metadata['datetime'] == new_metadata['datetime']
            assert metadata['noofreceivers'] == new_metadata['noofreceivers']
            assert metadata['timepartitions'] == new_metadata['timepartitions']
            assert new_heights.shape == heights.shape
            assert new_freqs.shape == freqs.shape
            assert new_sensors.shape == sensors.shape
            assert new_dop_shifts.shape == dop_shifts.shape

    def test_read_csv_day(self, test_raw_files_day, test_files_md3_day, test_files_md4_day, test_csvio, test_raw_reader):
        for test_raw_dir, test_metadata_file in zip(test_raw_files_day, test_files_md3_day):
            metadata, height, freq, dop_shifts, signal = test_raw_reader.read_raw_data_dir(test_raw_dir, extension='md3', multithread=True)
            new_metadata, new_height, new_freq, new_dop_shifts, new_signal = test_csvio.read_from_csv_day(test_metadata_file)

            assert height.shape == new_height.shape
            assert freq.shape == new_freq.shape
            assert signal.shape == new_signal.shape
            assert metadata['timepartitions'] == new_metadata['timepartitions']
            assert (signal == new_signal).all()
            assert (height == new_height).all()
            assert (dop_shifts == new_dop_shifts).all()
        for test_raw_dir, test_metadata_file in zip(test_raw_files_day, test_files_md4_day):
            metadata, height, freq, dop_shifts, signal = test_raw_reader.read_raw_data_dir(test_raw_dir, extension='md4', multithread=True)
            new_metadata, new_height, new_freq, new_dop_shifts, new_signal = test_csvio.read_from_csv_day(test_metadata_file)
            
            assert height.shape == new_height.shape
            assert freq.shape == new_freq.shape
            assert signal.shape == new_signal.shape
            assert metadata['timepartitions'] == new_metadata['timepartitions']
            assert (height == new_height).all()
            assert (signal == new_signal).all()
            assert (dop_shifts == new_dop_shifts).all()
    