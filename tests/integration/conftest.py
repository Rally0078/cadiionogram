import pytest
from pathlib import Path

@pytest.fixture
def test_real_md3():
    return Path(__file__).parent.parent / Path("rawfiles/250409TI/5D091100.md3")

@pytest.fixture
def test_real_md4():
    return Path(__file__).parent.parent / Path("rawfiles/250409TI/5D091200.md4")

@pytest.fixture
def test_raw_othersites():
    return (Path(__file__).parent.parent / Path("rawfiles/othersites")).glob("*.md*")

@pytest.fixture
def test_raw_badfile():
    return Path(__file__).parent.parent / Path("rawfiles/badfiles/6C040400.md4")