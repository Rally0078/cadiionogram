from src.utils.pandasutils import PandasUtils
import copy
class TestPandasUtils:
    def test_create_pandas(self, mock_data, expected_column_names):
        file_list, metadata, heights, frequencies, freq_list, dop_shifts, sensors = mock_data
        df = PandasUtils.create_pandas_from_arrays(metadata, freqs=frequencies, heights=heights, dop_shifts=dop_shifts, sensors=sensors)

        expected_columns = copy.deepcopy(expected_column_names)
        for i in range(metadata['noofreceivers']):
            expected_columns.append(f"sensor{i+1} real")
            expected_columns.append(f"sensor{i+1} imag")
        assert (df.columns == expected_columns).all()
        assert len(df) == len(heights)
