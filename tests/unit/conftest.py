import pytest
from pathlib import Path
import numpy as np
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from itertools import chain
from ionogramparser.mdxreader import MDreader
import struct
import os
import random
import tempfile
from utils.siteinfo import site_dict

@pytest.fixture
def date_site_dict():
    sitename = ['TIR', 'TIR', 'ALD', 'TFR']
    obs_dt = [datetime(year=2019,month=10,day=5, hour=0,minute=0,second=0), 
              datetime(year=2024,month=2,day=23, hour=0,minute=0,second=0), 
              datetime(year=2018,month=4,day=21, hour=0,minute=0,second=0), 
              datetime(year=2026,month=7,day=15, hour=0,minute=0,second=0), ]
    expected_tz = [ZoneInfo('Asia/Kolkata'), timezone.utc, ZoneInfo('Asia/Kolkata'), ZoneInfo('Asia/Kolkata'), ZoneInfo('Asia/Kolkata')]
    return sitename, obs_dt, expected_tz

@pytest.fixture
def test_site_dict():
    return site_dict

@pytest.fixture
def mock_raw_file_incomplete_header():
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
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(mock_bytes)
        f.flush()
        return f.name

@pytest.fixture
def mock_raw_file_incomplete_data():
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
            """mock_bytes.extend(struct.pack("<B", ndops_oneh)) #ndops_oneh
            dop_flags = np.random.randint(1, 10, ndops_oneh)
            for dop_x in range(ndops_oneh):
                mock_bytes.extend(struct.pack("<B", dop_flags[dop_x])) #dop_flag
                for receiver in range(noofreceivers):
                    mock_bytes.extend(struct.pack("<B", np.random.randint(0, 256, 1)[0]))   #Re
                    mock_bytes.extend(struct.pack("<B", np.random.randint(0, 256, 1)[0]))   #Im
            mock_bytes.extend(struct.pack("<B", 226))   #hflag, stop if hflag > 224
    mock_bytes.extend(struct.pack("<B", 255))   #time_min, stop if time_min == 255"""

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(mock_bytes)
        f.flush()
        return f.name

@pytest.fixture
def mock_raw_file_incomplete_data_2():
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
        """mock_bytes.extend(struct.pack('<B', np.random.randint(0, 60, 1)[0]))    #time_sec
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
    mock_bytes.extend(struct.pack("<B", 255))   #time_min, stop if time_min == 255"""

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(mock_bytes)
        f.flush()
        return f.name

@pytest.fixture
def mock_raw_file_incomplete_data_3():
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
            """mock_bytes.extend(struct.pack("<B", 226))   #hflag, stop if hflag > 224
    mock_bytes.extend(struct.pack("<B", 255))   #time_min, stop if time_min == 255"""

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(mock_bytes)
        f.flush()
        return f.name

@pytest.fixture
def mock_raw_file_TIR_LT():
    mock_bytes = bytearray()
    nfreqs = 4
    noofreceivers = 4
    mock_bytes.extend('TIR'.encode('utf-8'))    #site
    mock_bytes.extend((b" Jan 20 12:34:56 2010" + b"\n"))   #Datetime
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
def mock_raw_file_TIR_UT():
    mock_bytes = bytearray()
    nfreqs = 4
    noofreceivers = 4
    mock_bytes.extend('TIR'.encode('utf-8'))    #site
    mock_bytes.extend((b" Mar 20 12:34:56 2025" + b"\n"))   #Datetime
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