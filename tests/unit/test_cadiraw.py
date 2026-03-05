class TestCADIRaw:
    def test_read_rawmd4(self, mock_raw_file, test_raw_reader):
        file_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(mock_raw_file)
        assert type(metadata) == dict
        assert type(metadata['timepartitions']) == dict
        assert heights.shape == freqs.shape
        assert heights.shape[0] == sensors.shape[0]
        assert dop_shifts.shape == heights.shape
    
    def test_read_rawmd4_incomplete_header(self, mock_raw_file_incomplete_header, test_raw_reader):
        file_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(mock_raw_file_incomplete_header)

        assert type(metadata) == dict
        assert type(metadata['timepartitions']) == dict
        assert len(freq_list) == 0
        assert metadata['incompleteheader'] == True

    def test_read_rawmd4_incomplete_data(self, mock_raw_file_incomplete_data, test_raw_reader):
        file_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(mock_raw_file_incomplete_data)

        assert type(metadata) == dict
        assert type(metadata['timepartitions']) == dict
        assert metadata['incompletedata'] == True
    
    def test_read_rawmd4_incomplete_data_2(self, mock_raw_file_incomplete_data_2, test_raw_reader):
        file_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(mock_raw_file_incomplete_data_2)

        assert type(metadata) == dict
        assert type(metadata['timepartitions']) == dict
        assert metadata['incompletedata'] == True

    def test_read_rawmd4_incomplete_data_3(self, mock_raw_file_incomplete_data_3, test_raw_reader):
        file_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(mock_raw_file_incomplete_data_3)

        assert type(metadata) == dict
        assert type(metadata['timepartitions']) == dict
        assert metadata['incompletedata'] == True