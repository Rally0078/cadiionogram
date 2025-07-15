from dataclasses import dataclass

@dataclass
class SiteInfo():
    timezone: str
    FH: float
    dip: float
    short_site: str

ald_site = SiteInfo(timezone='LT', FH=1.38, dip=10.2, short_site='al')
tir_site = SiteInfo(timezone='UT', FH=1.38, dip=0.5, short_site='ti')
site_dict = {
    'TIR': tir_site,
    'KSKGRL-IIGM PRAYAGRAJ': ald_site,
    'ALD': ald_site
}