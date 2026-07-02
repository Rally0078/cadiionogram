from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List
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

    
#FH at 300 km altitude
ald_site = SiteInfo(FH=1.119, dip=10.2, site='ALD',short_site='al',
                ph_corr=[0,0],polarity=[1,-1,1,-1], site_separation=[20.1, 20.1])
tir_site = SiteInfo(FH=0.951, dip=0.5, site='TIR', short_site='ti',
                ph_corr=[8.8906,-29.5086],polarity=[1,-1,1,-1], site_separation=[30.1, 30.1])
hyd_site = SiteInfo(FH=1.007, dip=6.5, site='TFR', short_site='tf',
                ph_corr=[0,0],polarity=[1,-1,1,-1], site_separation=[30.1, 30.1])
moc_site = SiteInfo(FH=0, dip=0, site='MOC', short_site='ut',
                ph_corr=[0,0],polarity=[1,-1,1,-1], site_separation=[15,15])
site_dict = {
    'TIR': tir_site,
    'KSKGRL-IIGM PRAYAGRAJ': ald_site,
    'ALD': ald_site,
    'TFR': hyd_site,
    'MOC': moc_site
}