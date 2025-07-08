class TestCADIRaw:
    def test_read_rawmd4(self, mock_raw_file, test_raw_reader):
        file_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(mock_raw_file)
        assert type(metadata) == dict
        assert type(metadata['timepartitions']) == dict
        assert heights.shape == freqs.shape
        assert heights.shape[0] == sensors.shape[0]
        assert dop_shifts.shape == heights.shape