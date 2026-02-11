from dataclasses import dataclass
from datetime import timezone, tzinfo, datetime
from zoneinfo import ZoneInfo
@dataclass
class SiteInfo():
    FH: float
    dip: float
    site: str
    short_site: str

    def get_tzinfo(self, dtime: datetime) -> timezone | ZoneInfo:
        if self.site == 'TIR':
            tir_threshold = datetime(year=2020, month=1, day=1)
            if dtime.tzinfo is not None:
                tir_threshold = tir_threshold.replace(tzinfo=dtime.tzinfo)
            if dtime < tir_threshold:
                return ZoneInfo('Asia/Kolkata')
            else:
                return timezone.utc
        else:
            return ZoneInfo('Asia/Kolkata')
    
    def get_tzstr(self, dtime: datetime) -> str:
        tz = self.get_tzinfo(dtime)
        if tz == timezone.utc:
            return 'UT'
        return 'LT'

    
#FH at 300 km altitude
ald_site = SiteInfo(FH=1.119, dip=10.2, site='ALD',short_site='al')
tir_site = SiteInfo(FH=0.951, dip=0.5, site='TIR', short_site='ti')
hyd_site = SiteInfo(FH=1.007, dip=6.5, site='TFR', short_site='tf')

site_dict = {
    'TIR': tir_site,
    'KSKGRL-IIGM PRAYAGRAJ': ald_site,
    'ALD': ald_site,
    'TFR': hyd_site
}