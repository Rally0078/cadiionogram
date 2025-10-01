from dataclasses import dataclass

@dataclass
class SiteInfo():
    timezone: str
    FH: float
    dip: float
    short_site: str
#FH at 300 km altitude
ald_site = SiteInfo(timezone='LT', FH=1.119, dip=10.2, short_site='al')
tir_site = SiteInfo(timezone='UT', FH=0.951, dip=0.5, short_site='ti')
hyd_site = SiteInfo(timezone='LT', FH=1.007, dip=6.5, short_site='tf')

site_dict = {
    'TIR': tir_site,
    'KSKGRL-IIGM PRAYAGRAJ': ald_site,
    'ALD': ald_site,
    'TFR': hyd_site
}