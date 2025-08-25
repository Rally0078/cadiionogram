import pytest
import struct
import os
from datetime import datetime
import numpy as np
import tempfile


@pytest.fixture
def mock_raw_file():
    mock_bytes = bytearray()
    nfreqs = 4
    noofreceivers = 4
    mock_bytes.extend('MOC'.encode('utf-8'))    #site
    mock_bytes.extend((b" Jan 20 12:34:56 2030" + b"\n"))   #Datetime
    mock_bytes.extend('H'.encode('utf-8'))  #filetype
    mock_bytes.extend(struct.pack('<H', nfreqs)) #nfreqs
    mock_bytes.extend(struct.pack('<B', 2)) #ndops
    mock_bytes.extend(struct.pack("<H", 90))    #minheight
    mock_bytes.extend(struct.pack("<H", 1024))  #maxheight
    mock_bytes.extend(struct.pack('<B', 8)) #pps
    mock_bytes.extend(struct.pack("<B", 3)) #npulses_avgd
    mock_bytes.extend(struct.pack("<H", 400))   #base_thr100
    mock_bytes.extend(struct.pack("<H", 135))   #noise_thr100
    mock_bytes.extend(struct.pack("<B", 1)) #min_dops_save
    mock_bytes.extend(struct.pack("<H", 60)) #dtime
    mock_bytes.extend('2'.encode('utf-8'))  #gain_control
    mock_bytes.extend('F'.encode('utf-8'))  #sig_process
    mock_bytes.extend(struct.pack('<B', noofreceivers)) #noofreceivers
    mock_bytes.extend('abcxyzdef32'.encode('utf-8'))  #Spares
    freq_list_mock = [3e6, 6e6, 9e6, 12e6]
    for n_freq in range(nfreqs):
        mock_bytes.extend(struct.pack("<f", freq_list_mock[n_freq]))
    minutes = np.sort(np.random.choice(np.arange(0, 60, 1, dtype=np.int32), size=10, replace=False))
    for minute in minutes:
        mock_bytes.extend(struct.pack('<B', minute))    #time_min
        mock_bytes.extend(struct.pack('<B', np.random.randint(0, 60, 1)[0]))    #time_sec
        mock_bytes.extend(struct.pack("<B", 226))   #gainflag
        #nfreqs is iterated through
        for nfreq in range(nfreqs):
            mock_bytes.extend(struct.pack("<B", 32))    #noise_flag
            mock_bytes.extend(struct.pack("<H", 384))   #noise_power10
            mock_bytes.extend(struct.pack("<B", np.random.randint(80, 160, 1)[0]))    #heightflag
            ndops_oneh = np.random.randint(1, 12, 1)[0]
            mock_bytes.extend(struct.pack("<B", ndops_oneh)) #ndops_oneh
            dop_flags = np.random.randint(1, 10, ndops_oneh)
            for dop_x in range(ndops_oneh):
                mock_bytes.extend(struct.pack("<B", dop_flags[dop_x])) #dop_flag
                for receiver in range(noofreceivers):
                    mock_bytes.extend(struct.pack("<B", np.random.randint(0, 256, 1)[0]))   #Re
                    mock_bytes.extend(struct.pack("<B", np.random.randint(0, 256, 1)[0]))   #Im
            mock_bytes.extend(struct.pack("<B", 226))   #hflag, stop if hflag > 224
    mock_bytes.extend(struct.pack("<B", 255))   #time_min, stop if time_min == 255

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(mock_bytes)
        f.flush()
        return f.name

@pytest.fixture
def mock_data():
    file_list = 'mockfile.md4'
    metadata = dict({
        "site": 'MOC',
        "datetime": datetime(year=2035, month=1, day=15, hour=12, minute=34, second=56),
        "source": 'mockfile.md4',
        "filetype": 'H',
        "ndops": 4,
        "nfreqs": 2,
        "nheights": 10,
        "minheight": 90,
        "maxheight": 1020,
        "dheight": 3,
        "pps": 10,
        "npulses_avgd": 3,
        "dtime": 60,
        "extension": 'md4',
        "noofreceivers": 4,
        "timepartitions": {'12:00:00': 100,
                '12:10:00': 150,
                '12:20:00': 250,
                '12:30:00': 450,
                '12:40:00': 500,
                '12:50:00': 578},
        })
    freq_list = [4e6, 6e6]
    heights = np.random.uniform(90, 800, 578)
    frequencies = np.random.choice(freq_list, replace=True, size=578)
    dop_shifts = np.random.choice(np.linspace(-5, 5, 4), size=578)
    sensors = np.random.uniform(0, 256, size=(578, 8))
    return file_list, metadata, heights, frequencies, freq_list, dop_shifts, sensors

@pytest.fixture
def expected_column_names():
    return ['freq (Hz)', 'height (km)', 'dopplershift']

@pytest.fixture
def mock_parquet_file(mock_data):
    file_list, metadata, heights, frequencies, freq_list, dop_shifts, sensors = mock_data
    

