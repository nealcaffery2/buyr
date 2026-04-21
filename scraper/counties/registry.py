from .base import CountyScraper
from .adapters.publicsearch import PublicSearchScraper
from .adapters.gsccca import GSCCCAScraper
from .adapters.landmark import LandmarkScraper
from .adapters.tyler import TylerScraper
from .adapters.fidlar import FidlarScraper
from .adapters.kofile import KofileScraper
from .adapters.acclaim import AcclaimScraper
from .adapters.spatialest import SpatialEstScraper
from .adapters.custom.harris_tx import HarrisTXScraper
from .adapters.custom.tarrant_tx import TarrantTXScraper
from .adapters.custom.travis_tx import TravisTXScraper
from .adapters.custom.collin_tx import CollinTXScraper
from .adapters.custom.denton_tx import DentonTXScraper
from .adapters.custom.maricopa_az import MaricopaAZScraper
from .adapters.custom.duval_fl import DuvalFLScraper
from .adapters.custom.orange_fl import OrangeFLScraper
from .adapters.custom.hillsborough_fl import HillsboroughFLScraper
from .adapters.custom.jackson_mo import JacksonMOScraper
from .adapters.custom.mecklenburg_nc import MecklenburgNCScraper
from .adapters.custom.wake_nc import WakeNCScraper
from .adapters.custom.franklin_oh import FranklinOHScraper
from .adapters.custom.oklahoma_ok import OklahomaOKScraper
from .adapters.custom.shelby_tn import ShelbyTNScraper
from .adapters.custom.jefferson_ky import JeffersonKYScraper


# Maps (county_lower, STATE_UPPER) → scraper class
REGISTRY: dict[tuple[str, str], type[CountyScraper]] = {
    # Alabama
    ("jefferson", "AL"): LandmarkScraper,
    ("madison", "AL"): LandmarkScraper,       # countygovservices = Landmark variant
    # Arizona
    ("maricopa", "AZ"): MaricopaAZScraper,
    ("pima", "AZ"): TylerScraper,
    # Colorado
    ("denver", "CO"): KofileScraper,
    ("el paso", "CO"): TylerScraper,
    # Florida
    ("duval", "FL"): DuvalFLScraper,
    ("lee", "FL"): LandmarkScraper,
    ("orange", "FL"): OrangeFLScraper,
    ("hillsborough", "FL"): HillsboroughFLScraper,
    # Georgia
    ("fulton", "GA"): GSCCCAScraper,
    ("chatham", "GA"): GSCCCAScraper,
    # Indiana
    ("marion", "IN"): FidlarScraper,
    # Kentucky
    ("jefferson", "KY"): JeffersonKYScraper,
    # Missouri
    ("jackson", "MO"): JacksonMOScraper,
    ("st. louis", "MO"): LandmarkScraper,
    ("st. charles", "MO"): LandmarkScraper,
    # North Carolina
    ("mecklenburg", "NC"): MecklenburgNCScraper,
    ("guilford", "NC"): MecklenburgNCScraper,  # same NC ROD platform
    ("wake", "NC"): WakeNCScraper,
    ("forsyth", "NC"): MecklenburgNCScraper,
    ("durham", "NC"): MecklenburgNCScraper,
    # Ohio
    ("franklin", "OH"): FranklinOHScraper,
    ("hamilton", "OH"): FranklinOHScraper,
    ("montgomery", "OH"): FranklinOHScraper,
    # Oklahoma
    ("oklahoma", "OK"): OklahomaOKScraper,
    ("tulsa", "OK"): AcclaimScraper,
    ("cleveland", "OK"): SpatialEstScraper,
    ("canadian", "OK"): SpatialEstScraper,
    # Tennessee
    ("knox", "TN"): TylerScraper,
    ("shelby", "TN"): ShelbyTNScraper,
    ("davidson", "TN"): TylerScraper,
    ("hamilton", "TN"): TylerScraper,
    # South Carolina
    ("richland", "SC"): LandmarkScraper,
    ("greenville", "SC"): LandmarkScraper,
    ("charleston", "SC"): LandmarkScraper,
    # Texas
    ("tarrant", "TX"): TarrantTXScraper,
    ("rockwall", "TX"): CollinTXScraper,     # same CAD platform
    ("collin", "TX"): CollinTXScraper,
    ("kaufman", "TX"): CollinTXScraper,
    ("denton", "TX"): DentonTXScraper,
    ("grayson", "TX"): CollinTXScraper,
    ("dallas", "TX"): PublicSearchScraper,
    ("travis", "TX"): TravisTXScraper,
    ("harris", "TX"): HarrisTXScraper,
    ("bexar", "TX"): PublicSearchScraper,
    # Arkansas
    ("pulaski", "AR"): LandmarkScraper,
    ("lonoke", "AR"): LandmarkScraper,
    # Kansas
    ("wyandotte", "KS"): LandmarkScraper,
}

# Per-county base_url overrides for multi-county adapters
COUNTY_URLS: dict[tuple[str, str], str] = {
    # PublicSearch
    ("dallas", "TX"): "https://dallas.tx.publicsearch.us",
    ("bexar", "TX"): "https://bexar.tx.publicsearch.us",
    # Tyler
    ("pima", "AZ"): "https://pimacountyaz-web.tylerhost.net",
    ("el paso", "CO"): "https://publicrecordsearch.elpasoco.com",
    ("knox", "TN"): "https://propertyinfo.knoxcountytn.gov",
    ("davidson", "TN"): "https://portal.padctn.org",
    ("hamilton", "TN"): "https://assessor.hamiltontn.gov",
    # KoFile
    ("denver", "CO"): "https://countyfusion3.kofiletech.us",
    # Acclaim
    ("tulsa", "OK"): "https://acclaim.tulsacounty.org",
    # SpatialEst
    ("cleveland", "OK"): "https://personal.spatialest.com/ok/cleveland",
    ("canadian", "OK"): "https://property.spatialest.com/ok/canadian",
    # GSCCCA
    ("fulton", "GA"): "https://search.gsccca.org",
    ("chatham", "GA"): "https://www.chathamtax.org",
    # Fidlar
    ("marion", "IN"): "https://inmarion.fidlar.com",
    # Landmark — every county using LandmarkScraper must have a URL here
    ("jefferson", "AL"): "https://landmark.jeffersonprobate.com/LandMarkWeb",
    ("madison", "AL"): "https://madisonproperty.countygovservices.com/LandMarkWeb",
    ("lee", "FL"): "https://or.leeclerk.org/LandMarkWeb",
    ("st. louis", "MO"): "https://stlouiscounty.recorderofdeeds.com/LandMarkWeb",
    ("st. charles", "MO"): "https://stcharlescounty.recorderofdeeds.com/LandMarkWeb",
    ("richland", "SC"): "https://rod.richlandcountysc.gov/LandMarkWeb",
    ("greenville", "SC"): "https://www.greenvillecounty.org/rod/LandMarkWeb",
    ("charleston", "SC"): "https://www.charlestoncounty.org/departments/rod/LandMarkWeb",
    ("pulaski", "AR"): "https://www.pulaskiclerk.com/LandMarkWeb",
    ("lonoke", "AR"): "https://lonokeclerk.com/LandMarkWeb",
    ("wyandotte", "KS"): "https://www.wycokck.org/rod/LandMarkWeb",
    # Custom
    ("shelby", "TN"): "https://search.register.shelby.tn.us",
}


def get_scraper(county: str, state: str) -> CountyScraper | None:
    key = (county.lower(), state.upper())
    cls = REGISTRY.get(key)
    if not cls:
        return None
    instance = cls(county=county, state=state)
    url = COUNTY_URLS.get(key)
    if url:
        instance.base_url = url
    return instance
