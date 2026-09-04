from datetime import timezone
from zoneinfo import ZoneInfo
class TestSiteInfo:
    def test_siteinfo(self, test_site_dict, date_site_dict):
        sitenames, obs_datetimes, expected_zones = date_site_dict
        for site, obs_dt, expected_zone in zip(sitenames, obs_datetimes, expected_zones):
            assert expected_zone == test_site_dict.from_file(site).get_tzinfo(obs_dt)
    
    def test_raw_md4_TIR_LT(self, mock_raw_file_TIR_LT, test_raw_reader):
        file_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(mock_raw_file_TIR_LT)

        assert type(metadata) == dict
        assert type(metadata['timepartitions']) == dict
        assert metadata['datetime'].tzinfo == ZoneInfo('Asia/Kolkata')

    def test_raw_md4_TIR_UT(self, mock_raw_file_TIR_UT, test_raw_reader):
        file_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = test_raw_reader.read_raw_data(mock_raw_file_TIR_UT)

        assert type(metadata) == dict
        assert type(metadata['timepartitions']) == dict
        assert metadata['datetime'].tzinfo == ZoneInfo(key='UTC')