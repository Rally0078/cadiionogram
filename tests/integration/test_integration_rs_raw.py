from zoneinfo import ZoneInfo
import pytest
@pytest.mark.rust_test
class TestCADIRustRawIntegration:
    def test_read_raw_rs(self, test_real_md3, test_real_md4, test_rust_raw_reader):
        for test_file in [test_real_md3, test_real_md4]:
            file_list, metadata, heights, frequencies, freq_list, dop_shifts, sensors = test_rust_raw_reader.read_raw_data(test_file)
            assert len(freq_list) == metadata['nfreqs']
            assert metadata['extension'] in ['md3', 'md4']
            assert heights.shape == frequencies.shape
            assert heights.shape[0] == sensors.shape[0]
            assert dop_shifts.shape == heights.shape
    
    def test_read_raw_rs_othersites(self, test_raw_othersites, test_rust_raw_reader):
        for test_file in test_raw_othersites:
            file_list, metadata, heights, frequencies, freq_list, dop_shifts, sensors = test_rust_raw_reader.read_raw_data(test_file)
            assert len(freq_list) == metadata['nfreqs']
            assert metadata['extension'] in ['md3', 'md4']
            assert heights.shape == frequencies.shape
            assert heights.shape[0] == sensors.shape[0]
            assert dop_shifts.shape == heights.shape
            print(f"Tzinfo {metadata['datetime'].tzinfo}")  
            assert metadata['datetime'].tzinfo == ZoneInfo('Asia/Kolkata')
        
    def test_py_rs_reader_equality_mock(self, mock_raw_file, test_raw_reader, test_rust_raw_reader):
        file_list, metadata, heights, frequencies, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(mock_raw_file)
        file_list_rs, metadata_rs, heights_rs, frequencies_rs, freq_list_rs, dop_shifts_rs, sensors_rs = test_rust_raw_reader.read_raw_data(mock_raw_file)
        assert metadata == dict(metadata_rs)
        assert (heights == heights_rs).all()
        assert (freq_list == freq_list_rs).all()
        assert (frequencies == frequencies_rs).all()
        assert (dop_shifts == dop_shifts_rs).all()
        assert heights.shape[0] == sensors.shape[0]
        assert heights_rs.shape[0] == sensors_rs.shape[0]
        assert (sensors == sensors_rs).all()
    
    def test_py_rs_reader_equality(self, test_real_md3, test_real_md4, test_raw_reader, test_rust_raw_reader):
        for raw_file in [test_real_md3, test_real_md4]:
            file_list, metadata, heights, frequencies, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(raw_file)
            file_list_rs, metadata_rs, heights_rs, frequencies_rs, freq_list_rs, dop_shifts_rs, sensors_rs = test_rust_raw_reader.read_raw_data(raw_file)
            assert metadata == dict(metadata_rs)
            assert (heights == heights_rs).all()
            assert (freq_list == freq_list_rs).all()
            assert (frequencies == frequencies_rs).all()
            assert (dop_shifts == dop_shifts_rs).all()
            assert heights.shape[0] == sensors.shape[0]
            assert heights_rs.shape[0] == sensors_rs.shape[0]
            assert (sensors == sensors_rs).all()
            assert metadata['datetime'].tzinfo == metadata_rs['datetime'].tzinfo
    
    def test_py_rs_reader_equality_othersites(self, test_raw_othersites, test_raw_reader, test_rust_raw_reader):
        for raw_file in test_raw_othersites:
            file_list, metadata, heights, frequencies, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(raw_file)
            file_list_rs, metadata_rs, heights_rs, frequencies_rs, freq_list_rs, dop_shifts_rs, sensors_rs = test_rust_raw_reader.read_raw_data(raw_file)
            assert metadata == dict(metadata_rs)
            assert (heights == heights_rs).all()
            assert (freq_list == freq_list_rs).all()
            assert (frequencies == frequencies_rs).all()
            assert (dop_shifts == dop_shifts_rs).all()
            assert heights.shape[0] == sensors.shape[0]
            assert heights_rs.shape[0] == sensors_rs.shape[0]
            assert (sensors == sensors_rs).all()
            assert metadata['datetime'].tzinfo == metadata_rs['datetime'].tzinfo