import pytest
from pathlib import Path
import numpy as np
from cadiparser import csvio, readrawdata
import pandas as pd
import subprocess
import re
import datetime

class TestCADIRaw:
    @pytest.mark.order(1)
    def test_read_rawmd4(self, test_files_md4, test_raw_reader):
        for input_file in test_files_md4:
            metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(input_file)
            assert type(metadata) == dict
            assert type(metadata['timepartitions']) == dict
            assert heights.shape == freqs.shape
            assert heights.shape[0] == sensors.shape[0]
            assert dop_shifts.shape == heights.shape

    @pytest.mark.order(2)
    def test_read_rawfull(self, test_raw_files_day, test_raw_reader):
        for test_files_single_folder in test_raw_files_day:
            files_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data_dir(test_files_single_folder, 'md3')
            assert metadata['extension'] == 'md3'
            assert heights.shape == freqs.shape
            assert heights.shape[0] == sensors.shape[0]
            assert dop_shifts.shape == heights.shape
            files_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data_dir(test_files_single_folder, 'md4')
            assert metadata['extension'] == 'md4'
            assert heights.shape == freqs.shape
            assert heights.shape[0] == sensors.shape[0]
            assert dop_shifts.shape == heights.shape

    @pytest.mark.order(3)
    def test_mt_reader(self, test_raw_files_day, test_raw_reader):
        for test_files_single_folder in test_raw_files_day:
            files_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data_dir(test_files_single_folder, 'md3', multithread=False)
            files_list, new_metadata, new_heights, new_freqs, new_frq_list, new_dop_shifts, new_sensors = test_raw_reader.read_raw_data_dir(test_files_single_folder, 'md3', multithread=True)
            assert metadata == new_metadata
            assert (heights == new_heights).all()
            assert (freqs == new_freqs).all()
            assert (dop_shifts == new_dop_shifts).all()
            assert heights.shape[0] == sensors.shape[0]
            assert (sensors == new_sensors).all()
            files_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data_dir(test_files_single_folder, 'md4', multithread=False)
            files_list, new_metadata, new_heights, new_freqs, new_freq_list, new_dop_shifts, new_sensors = test_raw_reader.read_raw_data_dir(test_files_single_folder, 'md4', multithread=True)
            assert metadata == new_metadata
            assert (heights == new_heights).all()
            assert (freqs == new_freqs).all()
            assert (dop_shifts == new_dop_shifts).all()
            assert heights.shape[0] == sensors.shape[0]
            assert (sensors == new_sensors).all()