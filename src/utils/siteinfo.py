from dataclasses import dataclass, fields
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Optional
import json
import sys
import platform
from pathlib import Path
from functools import lru_cache

DEFAULT_SITES = {
    "TIR": {
        "FH": 0.951,
        "dip": 0.5,
        "site": "TIR",
        "short_site": "ti",
        "ph_corr": [8.8906, -29.5086],
        "polarity": [1, -1, 1, -1],
        "site_separation": [30.1, 30.1]
    },
    "KSKGRL-IIGM PRAYAGRAJ": {
        "FH": 1.119,
        "dip": 10.2,
        "site": "ALD",
        "short_site": "al",
        "ph_corr": [0.0, 0.0],
        "polarity": [1, -1, 1, -1],
        "site_separation": [20.1, 20.1]
    },
    "ALD": {
        "FH": 1.119,
        "dip": 10.2,
        "site": "ALD",
        "short_site": "al",
        "ph_corr": [0.0, 0.0],
        "polarity": [1, -1, 1, -1],
        "site_separation": [20.1, 20.1]
  },
  "TFR": {
    "FH": 1.007,
    "dip": 6.5,
    "site": "TFR",
    "short_site": "tf",
    "ph_corr": [0.0, 0.0],
    "polarity": [1, -1, 1, -1],
    "site_separation": [30.1, 30.1]
  },
  "MOC": {
    "FH": 0.0,
    "dip": 0.0,
    "site": "MOC",
    "short_site": "ut",
    "ph_corr": [0.0, 0.0],
    "polarity": [1, -1, 1, -1],
    "site_separation": [15.0, 15.0]
  }
}

def get_sites_json_path() -> Path:
    os_name = platform.system()
    if os_name == "Windows":
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent / "sites.json"
        else:
            return Path("./sites.json")
    else:
        return Path.home() / ".config" / "egrliono" / "sites.json"

@lru_cache(maxsize=None)
def load_sites_file() -> dict:
    json_path = get_sites_json_path()
    if not json_path.exists():
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SITES, f, indent=4)
        return DEFAULT_SITES
    
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

@dataclass
class SiteInfo():
    FH: float
    dip: float
    site: str
    short_site: str
    ph_corr: List[float]
    polarity: List[float]
    site_separation: List[float]

    def get_tzinfo(self, dtime: datetime) -> ZoneInfo:
        if self.site == 'TIR':
            tir_threshold = datetime(year=2020, month=1, day=1)
            if dtime.tzinfo is not None:
                tir_threshold = tir_threshold.replace(tzinfo=dtime.tzinfo)
            if dtime < tir_threshold:
                return ZoneInfo('Asia/Kolkata')
            else:
                return ZoneInfo(key='UTC')
        else:
            return ZoneInfo('Asia/Kolkata')
    
    def get_tzstr(self, dtime: datetime) -> str:
        tz = self.get_tzinfo(dtime)
        if tz == ZoneInfo(key='UTC'):
            return 'UT'
        return 'LT'

    @classmethod
    def from_file(cls, site_name: str) -> "SiteInfo":
        data = load_sites_file()
        if site_name not in data:
            raise KeyError(f"Site {site_name} not found in sites.json")
        site_data = data[site_name]
        class_fields = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in site_data.items() if k in class_fields}
        return cls(**filtered_data)

    @classmethod
    def get_from_file(cls, site_name: str, default=None) -> Optional["SiteInfo"]:
        try:
            return cls.from_file(site_name)
        except KeyError:
            return default