from datetime import timezone
from zoneinfo import ZoneInfo
class TestCADIRawIntegration:
    def test_read_raw(self, test_real_md3, test_real_md4, test_raw_reader):
        for test_file in [test_real_md3, test_real_md4]:
            file_list, metadata, heights, frequencies, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(test_file)
            assert len(freq_list) == metadata['nfreqs']
            assert metadata['extension'] in ['md3', 'md4']
            assert heights.shape == frequencies.shape
            assert heights.shape[0] == sensors.shape[0]
            assert dop_shifts.shape == heights.shape

    def test_read_raw_othersites(self, test_raw_othersites, test_raw_reader):
        for test_file in test_raw_othersites:
            file_list, metadata, heights, frequencies, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(test_file)
            assert len(freq_list) == metadata['nfreqs']
            assert metadata['extension'] in ['md3', 'md4']
            assert heights.shape == frequencies.shape
            assert heights.shape[0] == sensors.shape[0]
            assert dop_shifts.shape == heights.shape
            assert metadata['datetime'].tzinfo == ZoneInfo('Asia/Kolkata')       

    def test_read_rawfull(self, test_raw_dir, test_raw_files_day, test_raw_reader):
        for test_files_single_folder in test_raw_files_day:
            for extension in ['md3', 'md4']:
                files_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data_dir(test_raw_dir / test_files_single_folder, extension)
                assert len(freq_list) == metadata['nfreqs']
                assert metadata['extension'] == extension
                assert heights.shape == freqs.shape
                assert heights.shape[0] == sensors.shape[0]
                assert dop_shifts.shape == heights.shape

    def test_mt_reader(self, test_raw_dir, test_raw_files_day, test_raw_reader):
        for test_files_single_folder in test_raw_files_day:
            for extension in ['md3', 'md4']:
                files_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data_dir(test_raw_dir / test_files_single_folder, extension, multithread=False)
                new_files_list, new_metadata, new_heights, new_freqs, new_freq_list, new_dop_shifts, new_sensors = test_raw_reader.read_raw_data_dir(test_raw_dir / test_files_single_folder, extension, multithread=True)
                assert metadata == new_metadata
                assert (heights == new_heights).all()
                assert (freqs == new_freqs).all()
                assert (dop_shifts == new_dop_shifts).all()
                assert heights.shape[0] == sensors.shape[0]
                assert (sensors == new_sensors).all()
                assert (files_list == new_files_list)
                assert (freq_list == new_freq_list).all()
