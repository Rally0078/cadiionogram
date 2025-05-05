import pytest
from pathlib import Path
import numpy as np
from itertools import chain
from cadiparser.readrawdata import MDreader
from cadiparser.csvio import CSVtools

@pytest.fixture
def test_raw_reader():
    return MDreader()

@pytest.fixture
def test_csvio():
    return CSVtools()

@pytest.fixture
def test_files_md4():
    return Path("D:\\250409TI").glob('5D09*.md4')

@pytest.fixture
def test_files_md3():
    return Path("D:\\250409TI").glob('5D09*.md3')

@pytest.fixture
def test_files_single_folder():
    return Path("D:\\250409TI")

@pytest.fixture
def test_get_types():
    return {"height (km)": np.int32,
        "frequency (MHz)": np.float64,
        'doppler shift': np.float64,
        "sensor0 (signal unit)": np.complex128,
        "sensor1 (signal unit)": np.complex128,
        "sensor2 (signal unit)": np.complex128,
        "sensor3 (signal unit)": np.complex128
        }

@pytest.fixture
def test_get_all_files():

    folder_1 = Path("D:\\250409TI").glob('5D09*.md4')
    folder_2 = Path("D:\\250410TI").glob('5D10*.md4')

    return chain(folder_1, folder_2)

@pytest.fixture
def test_raw_files_day():
    return [Path("D:\\250409TI"), Path("D:\\250410TI")]

@pytest.fixture
def test_files_md3_day():
    return [Path("./outputsingle/09042025/metadata_daymd3.json"), 
            Path("./outputsingle/10042025/metadata_daymd3.json")]

@pytest.fixture
def test_files_md4_day():
    return [Path("./outputsingle/09042025/metadata_daymd4.json"), 
            Path("./outputsingle/10042025/metadata_daymd4.json")]