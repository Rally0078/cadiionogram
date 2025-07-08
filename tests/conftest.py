import pytest
from pathlib import Path
import numpy as np
from itertools import chain
from ionogramparser.mdxreader import MDreader
import struct
import os
import random

#from cadiparser.csvio import CSVtools

def pytest_collection_modifyitems(items):
    """Modifies test items in place to ensure test classes run in a given order."""
    CLASS_ORDER = ["TestCADIRaw", "TestPandasUtils", "TestParquetRaw", "TestCADIRawIntegration"]
    sorted_items = items.copy()
      # read the class names from default items
    class_mapping = {item: item.cls.__name__ for item in items}

    
    # Iteratively move tests of each class to the end of the test queue
    for class_ in CLASS_ORDER:
        sorted_items = [it for it in sorted_items if class_mapping[it] != class_] + [
            it for it in sorted_items if class_mapping[it] == class_
        ]
        
   
    items[:] = sorted_items


@pytest.fixture
def test_raw_reader():
    return MDreader
#@pytest.fixture
#def test_csvio():
#    return CSVtools()

@pytest.fixture
def test_files_md4():
    return Path("E:\\vimal\\data\\250409TI").glob('5D09*.md4')

@pytest.fixture
def test_files_md3():
    return Path("E:\\vimal\\data\\250409TI").glob('5D09*.md3')

@pytest.fixture
def test_files_single_folder():
    return Path("E:\\vimal\\data\\250409TI")

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

    folder_1 = Path("E:\\vimal\\data\\250409TI").glob('5D09*.md4')
    folder_2 = Path("E:\\vimal\\data\\250410TI").glob('5D10*.md4')

    return chain(folder_1, folder_2)

@pytest.fixture
def test_raw_files_day():
    return [Path("E:\\vimal\\data\\250409TI"), Path("E:\\vimal\\data\\250410TI")]

@pytest.fixture
def test_files_md3_day():
    return [Path("./outputsingle/09042025/metadata_daymd3.json"), 
            Path("./outputsingle/10042025/metadata_daymd3.json")]

@pytest.fixture
def test_files_md4_day():
    return [Path("./outputsingle/09042025/metadata_daymd4.json"), 
            Path("./outputsingle/10042025/metadata_daymd4.json")]