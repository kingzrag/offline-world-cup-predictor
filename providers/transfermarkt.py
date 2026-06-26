import hashlib
import json
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup, Tag

from providers.base import (
    BaseProvider,
    CompetitionData,
    InjuryData,
    MatchData,
    MatchEventData,
    MatchLineupData,
    MatchStatisticsData,
    PlayerData,
    StandingData,
    SuspensionData,
    TeamData,
)
from utils.logger import logger

SUPPORTED_TRANSFERMARKT_COMPETITIONS = {
    "WC": "FIFA World Cup",
    "EC": "UEFA Euro",
    "EU": "UEFA Euro",
    "CA": "Copa America",
    "AFCON": "Africa Cup of Nations",
    "UNL": "UEFA Nations League",
    "CNL": "CONCACAF Nations League",
    "WCQ": "FIFA World Cup Qualifiers",
    "WCQA": "FIFA World Cup Qualifiers (Asia)",
    "WCQC": "FIFA World Cup Qualifiers (CONCACAF)",
    "WCQE": "FIFA World Cup Qualifiers (Europe)",
    "ASIAN": "AFC Asian Cup",
    "ASIANQ": "AFC Asian Cup Qualifiers",
    "GC": "Gold Cup",
    "WWC": "Women's World Cup",
    "FRI": "International Friendlies",
    "OLY": "Olympic Football",
}

NATIONAL_TEAM_TRANSFERMARKT_URLS = {
    "Argentina": "https://www.transfermarkt.com/argentinien/sperrenundverletzungen/verein/3437",
    "Australia": "https://www.transfermarkt.com/australien/sperrenundverletzungen/verein/3433",
    "Austria": "https://www.transfermarkt.com/osterreich/sperrenundverletzungen/verein/3383",
    "Belgium": "https://www.transfermarkt.com/belgien/sperrenundverletzungen/verein/3382",
    "Bosnia and Herzegovina": "https://www.transfermarkt.com/bosnien-herzegowina/sperrenundverletzungen/verein/3618",
    "Bosnia-Herzegovina": "https://www.transfermarkt.com/bosnien-herzegowina/sperrenundverletzungen/verein/3618",
    "Brazil": "https://www.transfermarkt.com/brasilien/sperrenundverletzungen/verein/3439",
    "Cameroon": "https://www.transfermarkt.com/kamerun/sperrenundverletzungen/verein/3434",
    "Canada": "https://www.transfermarkt.com/kanada/sperrenundverletzungen/verein/3510",
    "Cape Verde": "https://www.transfermarkt.com/kap-verde/sperrenundverletzungen/verein/8574",
    "Cape Verde Islands": "https://www.transfermarkt.com/kap-verde/sperrenundverletzungen/verein/8574",
    "Colombia": "https://www.transfermarkt.com/kolumbien/sperrenundverletzungen/verein/3816",
    "Costa Rica": "https://www.transfermarkt.com/costa-rica/sperrenundverletzungen/verein/6306",
    "Croatia": "https://www.transfermarkt.com/kroatien/sperrenundverletzungen/verein/3556",
    "Curacao": "https://www.transfermarkt.com/curacao/sperrenundverletzungen/verein/19519",
    "Curaçao": "https://www.transfermarkt.com/curacao/sperrenundverletzungen/verein/19519",
    "Czech Republic": "https://www.transfermarkt.com/tschechien/sperrenundverletzungen/verein/3380",
    "Czechia": "https://www.transfermarkt.com/tschechien/sperrenundverletzungen/verein/3380",
    "DR Congo": "https://www.transfermarkt.com/demokratische-republik-kongo/sperrenundverletzungen/verein/4338",
    "Democratic Republic of Congo": "https://www.transfermarkt.com/demokratische-republik-kongo/sperrenundverletzungen/verein/4338",
    "Denmark": "https://www.transfermarkt.com/danemark/sperrenundverletzungen/verein/3436",
    "Ecuador": "https://www.transfermarkt.com/ecuador/sperrenundverletzungen/verein/5750",
    "Egypt": "https://www.transfermarkt.com/agypten/sperrenundverletzungen/verein/3580",
    "England": "https://www.transfermarkt.com/england/sperrenundverletzungen/verein/3299",
    "Finland": "https://www.transfermarkt.com/finnland/sperrenundverletzungen/verein/3558",
    "France": "https://www.transfermarkt.com/frankreich/sperrenundverletzungen/verein/3377",
    "Germany": "https://www.transfermarkt.com/deutschland/sperrenundverletzungen/verein/3262",
    "Ghana": "https://www.transfermarkt.com/ghana/sperrenundverletzungen/verein/3703",
    "Greece": "https://www.transfermarkt.com/griechenland/sperrenundverletzungen/verein/3440",
    "Haiti": "https://www.transfermarkt.com/haiti/sperrenundverletzungen/verein/3820",
    "Hungary": "https://www.transfermarkt.com/ungarn/sperrenundverletzungen/verein/3385",
    "Iceland": "https://www.transfermarkt.com/island/sperrenundverletzungen/verein/3620",
    "Iran": "https://www.transfermarkt.com/iran/sperrenundverletzungen/verein/3573",
    "Iraq": "https://www.transfermarkt.com/irak/sperrenundverletzungen/verein/3685",
    "Ireland": "https://www.transfermarkt.com/irland/sperrenundverletzungen/verein/3441",
    "Italy": "https://www.transfermarkt.com/italien/sperrenundverletzungen/verein/3376",
    "Ivory Coast": "https://www.transfermarkt.com/elfenbeinkuste/sperrenundverletzungen/verein/3504",
    "Cote d'Ivoire": "https://www.transfermarkt.com/elfenbeinkuste/sperrenundverletzungen/verein/3504",
    "Japan": "https://www.transfermarkt.com/japan/sperrenundverletzungen/verein/3435",
    "Jordan": "https://www.transfermarkt.com/jordanien/sperrenundverletzungen/verein/9083",
    "Mexico": "https://www.transfermarkt.com/mexiko/sperrenundverletzungen/verein/6303",
    "Morocco": "https://www.transfermarkt.com/marokko/sperrenundverletzungen/verein/3575",
    "Netherlands": "https://www.transfermarkt.com/niederlande/sperrenundverletzungen/verein/3379",
    "New Zealand": "https://www.transfermarkt.com/neuseeland/sperrenundverletzungen/verein/3576",
    "Nigeria": "https://www.transfermarkt.com/nigeria/sperrenundverletzungen/verein/9450",
    "North Macedonia": "https://www.transfermarkt.com/nordmazedonien/sperrenundverletzungen/verein/6308",
    "Norway": "https://www.transfermarkt.com/norwegen/sperrenundverletzungen/verein/3559",
    "Panama": "https://www.transfermarkt.com/panama/sperrenundverletzungen/verein/3822",
    "Paraguay": "https://www.transfermarkt.com/paraguay/sperrenundverletzungen/verein/3802",
    "Peru": "https://www.transfermarkt.com/peru/sperrenundverletzungen/verein/3803",
    "Poland": "https://www.transfermarkt.com/polen/sperrenundverletzungen/verein/3442",
    "Portugal": "https://www.transfermarkt.com/portugal/sperrenundverletzungen/verein/3300",
    "Qatar": "https://www.transfermarkt.com/katar/sperrenundverletzungen/verein/14162",
    "Romania": "https://www.transfermarkt.com/rumanien/sperrenundverletzungen/verein/3443",
    "Russia": "https://www.transfermarkt.com/russland/sperrenundverletzungen/verein/3438",
    "Saudi Arabia": "https://www.transfermarkt.com/saudi-arabien/sperrenundverletzungen/verein/3807",
    "Scotland": "https://www.transfermarkt.com/schottland/sperrenundverletzungen/verein/3387",
    "Senegal": "https://www.transfermarkt.com/senegal/sperrenundverletzungen/verein/3495",
    "Serbia": "https://www.transfermarkt.com/serbien/sperrenundverletzungen/verein/3444",
    "Slovakia": "https://www.transfermarkt.com/slowakei/sperrenundverletzungen/verein/3445",
    "Slovenia": "https://www.transfermarkt.com/slowenien/sperrenundverletzungen/verein/3446",
    "South Africa": "https://www.transfermarkt.com/sudafrika/sperrenundverletzungen/verein/3624",
    "South Korea": "https://www.transfermarkt.com/sudkorea/sperrenundverletzungen/verein/3589",
    "Spain": "https://www.transfermarkt.com/spanien/sperrenundverletzungen/verein/3375",
    "Sweden": "https://www.transfermarkt.com/schweden/sperrenundverletzungen/verein/3557",
    "Switzerland": "https://www.transfermarkt.com/schweiz/sperrenundverletzungen/verein/3384",
    "Tunisia": "https://www.transfermarkt.com/tunesien/sperrenundverletzungen/verein/3581",
    "Turkey": "https://www.transfermarkt.com/turkei/sperrenundverletzungen/verein/3381",
    "Ukraine": "https://www.transfermarkt.com/ukraine/sperrenundverletzungen/verein/3699",
    "United Arab Emirates": "https://www.transfermarkt.com/vereinigte-arabische-emirate/sperrenundverletzungen/verein/3808",
    "United States": "https://www.transfermarkt.com/vereinigte-staaten/sperrenundverletzungen/verein/3505",
    "Uruguay": "https://www.transfermarkt.com/uruguay/sperrenundverletzungen/verein/3449",
    "Uzbekistan": "https://www.transfermarkt.com/usbekistan/sperrenundverletzungen/verein/8388",
    "Wales": "https://www.transfermarkt.com/wales/sperrenundverletzungen/verein/3447",
    "Algeria": "https://www.transfermarkt.com/algerien/sperrenundverletzungen/verein/3582",
    "Angola": "https://www.transfermarkt.com/angola/sperrenundverletzungen/verein/8575",
    "Benin": "https://www.transfermarkt.com/benin/sperrenundverletzungen/verein/8576",
    "Burkina Faso": "https://www.transfermarkt.com/burkina-faso/sperrenundverletzungen/verein/8577",
    "Chile": "https://www.transfermarkt.com/chile/sperrenundverletzungen/verein/3804",
    "China": "https://www.transfermarkt.com/china/sperrenundverletzungen/verein/3583",
    "China PR": "https://www.transfermarkt.com/china/sperrenundverletzungen/verein/3583",
    "Cuba": "https://www.transfermarkt.com/kuba/sperrenundverletzungen/verein/3823",
    "El Salvador": "https://www.transfermarkt.com/el-salvador/sperrenundverletzungen/verein/6309",
    "Ethiopia": "https://www.transfermarkt.com/athiopien/sperrenundverletzungen/verein/8578",
    "Gambia": "https://www.transfermarkt.com/gambia/sperrenundverletzungen/verein/8579",
    "Guinea": "https://www.transfermarkt.com/guinea/sperrenundverletzungen/verein/8580",
    "Honduras": "https://www.transfermarkt.com/honduras/sperrenundverletzungen/verein/6310",
    "Indonesia": "https://www.transfermarkt.com/indonesien/sperrenundverletzungen/verein/14163",
    "Jamaica": "https://www.transfermarkt.com/jamaika/sperrenundverletzungen/verein/6311",
    "Kenya": "https://www.transfermarkt.com/kenia/sperrenundverletzungen/verein/8581",
    "Kuwait": "https://www.transfermarkt.com/kuwait/sperrenundverletzungen/verein/9084",
    "Lebanon": "https://www.transfermarkt.com/libanon/sperrenundverletzungen/verein/9085",
    "Libya": "https://www.transfermarkt.com/libyen/sperrenundverletzungen/verein/3686",
    "Mali": "https://www.transfermarkt.com/mali/sperrenundverletzungen/verein/8582",
    "Mauritania": "https://www.transfermarkt.com/mauretanien/sperrenundverletzungen/verein/8583",
    "Montenegro": "https://www.transfermarkt.com/montenegro/sperrenundverletzungen/verein/6312",
    "Namibia": "https://www.transfermarkt.com/namibia/sperrenundverletzungen/verein/8584",
    "Oman": "https://www.transfermarkt.com/oman/sperrenundverletzungen/verein/9086",
    "Philippines": "https://www.transfermarkt.com/philippinen/sperrenundverletzungen/verein/14164",
    "Syria": "https://www.transfermarkt.com/syrien/sperrenundverletzungen/verein/3687",
    "Tajikistan": "https://www.transfermarkt.com/tadschikistan/sperrenundverletzungen/verein/8389",
    "Thailand": "https://www.transfermarkt.com/thailand/sperrenundverletzungen/verein/14165",
    "Trinidad and Tobago": "https://www.transfermarkt.com/trinidad-und-tobago/sperrenundverletzungen/verein/6313",
    "Venezuela": "https://www.transfermarkt.com/venezuela/sperrenundverletzungen/verein/3805",
    "Vietnam": "https://www.transfermarkt.com/vietnam/sperrenundverletzungen/verein/14166",
    "Zambia": "https://www.transfermarkt.com/sambia/sperrenundverletzungen/verein/8585",
    "Zimbabwe": "https://www.transfermarkt.com/simbabwe/sperrenundverletzungen/verein/8586",
}

TEAM_ALIASES = {
    "usa": "United States",
    "us": "United States",
    "united states of america": "United States",
    "united states": "United States",
    "america": "United States",
    "korea republic": "South Korea",
    "republic of korea": "South Korea",
    "south korea": "South Korea",
    "korea": "South Korea",
    "ivory coast": "Ivory Coast",
    "cote d ivoire": "Ivory Coast",
    "cote d'ivoire": "Ivory Coast",
    "czech republic": "Czech Republic",
    "czechia": "Czech Republic",
    "bosnia herzegovina": "Bosnia and Herzegovina",
    "bosnia and herzegovina": "Bosnia and Herzegovina",
    "bosnia-herzegovina": "Bosnia and Herzegovina",
    "dr congo": "DR Congo",
    "congo dr": "DR Congo",
    "democratic republic of congo": "DR Congo",
    "cape verde islands": "Cape Verde",
    "cape verde": "Cape Verde",
    "curacao": "Curacao",
    "curaçao": "Curacao",
    "england national team": "England",
    "germany national team": "Germany",
    "france national team": "France",
    "spain national team": "Spain",
    "italy national team": "Italy",
    "brazil national team": "Brazil",
    "argentina national team": "Argentina",
    "netherlands national team": "Netherlands",
    "holland": "Netherlands",
    "portugal national team": "Portugal",
    "belgium national team": "Belgium",
    "switzerland national team": "Switzerland",
    "sweden national team": "Sweden",
    "denmark national team": "Denmark",
    "norway national team": "Norway",
    "finland national team": "Finland",
    "greece national team": "Greece",
    "turkey national team": "Turkey",
    "türkiye": "Turkey",
    "poland national team": "Poland",
    "croatia national team": "Croatia",
    "serbia national team": "Serbia",
    "ukraine national team": "Ukraine",
    "russia national team": "Russia",
    "russian federation": "Russia",
    "mexico national team": "Mexico",
    "japan national team": "Japan",
    "south korea national team": "South Korea",
    "iran national team": "Iran",
    "saudi arabia national team": "Saudi Arabia",
    "australia national team": "Australia",
    "new zealand national team": "New Zealand",
    "morocco national team": "Morocco",
    "egypt national team": "Egypt",
    "senegal national team": "Senegal",
    "tunisia national team": "Tunisia",
    "nigeria national team": "Nigeria",
    "ghana national team": "Ghana",
    "cameroon national team": "Cameroon",
    "algeria national team": "Algeria",
    "ivory coast national team": "Ivory Coast",
    "costa rica national team": "Costa Rica",
    "panama national team": "Panama",
    "jamaica national team": "Jamaica",
    "honduras national team": "Honduras",
    "el salvador national team": "El Salvador",
    "trinidad and tobago national team": "Trinidad and Tobago",
    "china pr": "China",
    "china national team": "China",
    "thailand national team": "Thailand",
    "indonesia national team": "Indonesia",
    "philippines national team": "Philippines",
    "vietnam national team": "Vietnam",
    "uzbekistan national team": "Uzbekistan",
    "tajikistan national team": "Tajikistan",
    "iraq national team": "Iraq",
    "syria national team": "Syria",
    "jordan national team": "Jordan",
    "kuwait national team": "Kuwait",
    "oman national team": "Oman",
    "united arab emirates": "United Arab Emirates",
    "uae": "United Arab Emirates",
    "qatar national team": "Qatar",
    "lebanon national team": "Lebanon",
    "libya national team": "Libya",
    "ethiopia national team": "Ethiopia",
    "kenya national team": "Kenya",
    "zambia national team": "Zambia",
    "zimbabwe national team": "Zimbabwe",
    "mali national team": "Mali",
    "guinea national team": "Guinea",
    "burkina faso national team": "Burkina Faso",
    "benin national team": "Benin",
    "gambia national team": "Gambia",
    "mauritania national team": "Mauritania",
    "namibia national team": "Namibia",
    "angola national team": "Angola",
    "chile national team": "Chile",
    "peru national team": "Peru",
    "ecuador national team": "Ecuador",
    "colombia national team": "Colombia",
    "venezuela national team": "Venezuela",
    "paraguay national team": "Paraguay",
    "uruguay national team": "Uruguay",
    "bolivia national team": "Bolivia",
    "cuba national team": "Cuba",
    "haiti national team": "Haiti",
    "north macedonia": "North Macedonia",
    "macedonia": "North Macedonia",
    "montenegro national team": "Montenegro",
    "slovakia national team": "Slovakia",
    "slovenia national team": "Slovenia",
    "hungary national team": "Hungary",
    "romania national team": "Romania",
    "bulgaria national team": "Bulgaria",
    "iceland national team": "Iceland",
    "ireland national team": "Ireland",
    "republic of ireland": "Ireland",
    "wales national team": "Wales",
    "scotland national team": "Scotland",
    "northern ireland": "Northern Ireland",
}

PLAYER_COLUMN_LABELS = {
    "player",
    "spieler",
    "name",
}
REASON_COLUMN_LABELS = {
    "reason",
    "grund",
    "description",
    "details",
}
RETURN_COLUMN_LABELS = {
    "expected return",
    "expectedreturn",
    "return",
    "back on",
    "bis voraussichtlich",
    "return expected",
}
SINCE_COLUMN_LABELS = {
    "since",
    "seit",
    "from",
    "out since",
}
MISSED_MATCH_COLUMN_LABELS = {
    "games missed",
    "missed matches",
    "matches missed",
    "verpasste spiele",
    "spiele verpasst",
    "match ban",
}
SUSPENSION_KEYWORDS = (
    "suspens",
    "sperr",
    "ban",
    "card",
    "yellow",
    "red",
)
BLOCKED_MARKERS = (
    "just a moment",
    "cf-browser-verification",
    "attention required",
    "cloudflare",
    "access denied",
    "checking your browser",
    "please wait",
    "ray id",
    "challenge platform",
    "cf_chl",
    "browser check",
    "security check",
    "human verification",
    "ddos protection",
    "error 403",
    "error 503",
    "service unavailable",
    "temporarily unavailable",
)
EMPTY_MARKERS = (
    "no injuries",
    "no suspensions",
    "derzeit keine verletzten spieler",
    "keine verletzten",
    "keine gesperrten",
    "no players",
    "keine spieler",
    "currently no",
    "zurzeit keine",
    "no data available",
    "keine daten",
    "empty",
    "no entries",
    "keine einträge",
)


class TransfermarktProvider(BaseProvider):
    """
    Transfermarkt Provider
    - Injuries, suspensions, squad values, player availability
    - Resilient scraping across multiple HTML layouts
    """

    name = "Transfermarkt"

    def __init__(self):
        super().__init__()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        self.session = requests.Session()
        self.cache_dir = (
            Path(__file__).resolve().parent.parent / ".cache" / "transfermarkt"
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl_seconds = 60 * 60 * 12
        self.last_scrape_report: Dict[str, Any] = {}

    def _normalize_team_name(self, team_name: str) -> str:
        normalized = re.sub(r"[^a-z0-9 ]+", " ", team_name.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        normalized = normalized.replace("women s", "women")
        return TEAM_ALIASES.get(normalized, normalized)

    def resolve_team_key(self, team_name: str) -> Optional[str]:
        exact_alias = TEAM_ALIASES.get(self._normalize_team_name(team_name))
        if exact_alias and exact_alias in NATIONAL_TEAM_TRANSFERMARKT_URLS:
            return exact_alias
        if team_name in NATIONAL_TEAM_TRANSFERMARKT_URLS:
            return team_name

        normalized_target = self._normalize_team_name(team_name)
        for candidate in NATIONAL_TEAM_TRANSFERMARKT_URLS:
            normalized_candidate = self._normalize_team_name(candidate)
            if normalized_target == normalized_candidate:
                return candidate
        for candidate in NATIONAL_TEAM_TRANSFERMARKT_URLS:
            normalized_candidate = self._normalize_team_name(candidate)
            if (
                normalized_target in normalized_candidate
                or normalized_candidate in normalized_target
            ):
                return candidate
        return None

    def get_team_url(self, team_name: str) -> Optional[str]:
        team_key = self.resolve_team_key(team_name)
        return NATIONAL_TEAM_TRANSFERMARKT_URLS.get(team_key) if team_key else None

    def _cache_paths(self, url: str) -> Tuple[Path, Path]:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.html", self.cache_dir / f"{digest}.json"

    def _read_cache(self, url: str) -> Optional[Dict[str, Any]]:
        html_path, meta_path = self._cache_paths(url)
        if not html_path.exists() or not meta_path.exists():
            return None
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            fetched_at = meta.get("fetched_at")
            if not fetched_at:
                return None
            age = time.time() - fetched_at
            if age > self.cache_ttl_seconds:
                return None
            return {
                "html": html_path.read_text(encoding="utf-8", errors="ignore"),
                "status_code": meta.get("status_code", 200),
                "from_cache": True,
                "url": url,
                "error": None,
            }
        except Exception as exc:
            logger.debug(f"{self.name}: cache read failed for {url}: {exc}")
            return None

    def _write_cache(self, url: str, html: str, status_code: int) -> None:
        html_path, meta_path = self._cache_paths(url)
        try:
            html_path.write_text(html, encoding="utf-8")
            meta_path.write_text(
                json.dumps(
                    {"url": url, "status_code": status_code, "fetched_at": time.time()}
                ),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.debug(f"{self.name}: cache write failed for {url}: {exc}")

    def _fetch_page(
        self, url: str, retries: int = 5, base_delay: float = 2.0
    ) -> Dict[str, Any]:
        cached = self._read_cache(url)
        if cached:
            logger.debug(f"{self.name}: cache hit for {url}")
            return cached

        last_error = None
        last_status = None
        import random

        for attempt in range(retries):
            try:
                response = self.session.get(url, headers=self.headers, timeout=25)
                last_status = response.status_code
                
                # Success cases
                if response.status_code == 200 and response.text:
                    self._write_cache(url, response.text, response.status_code)
                    return {
                        "html": response.text,
                        "status_code": response.status_code,
                        "from_cache": False,
                        "url": url,
                        "error": None,
                    }
                
                # Handle specific status codes
                if response.status_code == 429:
                    last_error = f"Rate limited (HTTP 429)"
                    logger.warning(
                        f"{self.name}: rate limited for {url} (attempt {attempt + 1}/{retries})"
                    )
                elif response.status_code >= 500:
                    last_error = f"Server error (HTTP {response.status_code})"
                    logger.warning(
                        f"{self.name}: server error {response.status_code} for {url} (attempt {attempt + 1}/{retries})"
                    )
                elif response.status_code == 403:
                    last_error = f"Forbidden (HTTP 403) - possible block"
                    logger.warning(
                        f"{self.name}: access forbidden for {url} (attempt {attempt + 1}/{retries})"
                    )
                else:
                    last_error = f"HTTP {response.status_code}"
                    logger.warning(
                        f"{self.name}: request returned {response.status_code} for {url} (attempt {attempt + 1}/{retries})"
                    )
            except requests.exceptions.Timeout as exc:
                last_error = f"Timeout: {exc}"
                logger.warning(
                    f"{self.name}: request timeout for {url} (attempt {attempt + 1}/{retries})"
                )
            except requests.exceptions.ConnectionError as exc:
                last_error = f"Connection error: {exc}"
                logger.warning(
                    f"{self.name}: connection error for {url} (attempt {attempt + 1}/{retries})"
                )
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    f"{self.name}: request failed for {url} with {exc} (attempt {attempt + 1}/{retries})"
                )
            
            # Exponential backoff with jitter to avoid thundering herd
            if attempt < retries - 1:
                # Add jitter: random value between 0.5x and 1.5x of the base delay
                jitter = random.uniform(0.5, 1.5)
                sleep_seconds = base_delay * (2**attempt) * jitter
                logger.debug(f"{self.name}: retrying after {sleep_seconds:.2f}s")
                time.sleep(sleep_seconds)
        
        logger.error(f"{self.name}: all retries exhausted for {url}: {last_error}")
        return {
            "html": None,
            "status_code": last_status,
            "from_cache": False,
            "url": url,
            "error": last_error,
        }

    def _parse_date(self, date_str: str) -> Optional[date]:
        if not date_str:
            return None
        cleaned = re.sub(r"\s+", " ", date_str.strip())
        if cleaned.lower() in {"?", "-", "unknown", "", "n/a"}:
            return None
        cleaned = cleaned.replace(".", "/")
        candidates = [
            "%d/%m/%Y",
            "%d/%m/%y",
            "%Y-%m-%d",
            "%b %d, %Y",
            "%d %b %Y",
            "%d %B %Y",
        ]
        for fmt in candidates:
            try:
                return datetime.strptime(cleaned, fmt).date()
            except Exception:
                continue
        return None

    def _parse_int(self, val_str: str) -> Optional[int]:
        if not val_str:
            return None
        val_clean = "".join(c for c in str(val_str) if c.isdigit())
        return int(val_clean) if val_clean else None

    def _normalize_label(self, label: str) -> str:
        label = re.sub(r"\s+", " ", label.lower().strip())
        label = label.replace(":", "")
        return label

    def _text(self, node: Optional[Tag]) -> str:
        return node.get_text(" ", strip=True) if node else ""

    def _detect_blocked_or_empty(self, html: str) -> Tuple[bool, bool, str]:
        lower = html.lower()
        if any(marker in lower for marker in BLOCKED_MARKERS):
            return True, False, "blocked-marker"
        if "challenge-platform" in lower or "cf_chl" in lower:
            return True, False, "cloudflare-challenge"
        if any(marker in lower for marker in EMPTY_MARKERS):
            return False, True, "empty-marker"
        return False, False, ""

    def _candidate_tables(self, soup: BeautifulSoup) -> List[Tuple[Optional[str], Tag]]:
        candidates: List[Tuple[Optional[str], Tag]] = []
        for table in soup.select("table"):
            heading = None
            for previous in table.find_all_previous(
                ["h1", "h2", "h3", "h4", "div"], limit=4
            ):
                text = self._text(previous)
                if text and len(text) < 120:
                    heading = text
                    break
            candidates.append((heading, table))
        return candidates

    def _header_map(self, table: Tag) -> Dict[int, str]:
        headers: Dict[int, str] = {}
        header_row = None
        thead = table.find("thead")
        if thead:
            header_row = thead.find("tr")
        if not header_row:
            header_row = table.find("tr")
        if not header_row:
            return headers
        for index, th in enumerate(header_row.find_all(["th", "td"], recursive=False)):
            headers[index] = self._normalize_label(self._text(th))
        return headers

    def _is_relevant_table(
        self, heading: Optional[str], table: Tag, header_map: Dict[int, str]
    ) -> bool:
        header_values = set(header_map.values())
        
        # Primary check: table has player and reason/description columns
        if PLAYER_COLUMN_LABELS & header_values and (
            REASON_COLUMN_LABELS & header_values or RETURN_COLUMN_LABELS & header_values
        ):
            return True
        
        # Secondary check: table has player column and any injury/suspension-related keywords
        if PLAYER_COLUMN_LABELS & header_values:
            heading_text = (
                (heading or "") + " " + self._text(table.find_previous(["h2", "h3", "h4"]))
            )
            heading_lower = heading_text.lower()
            if any(
                token in heading_lower
                for token in ("injur", "verletz", "suspens", "sperr", "ban", "absence", "unavailable")
            ):
                return True
        
        # Tertiary check: table structure suggests injury/suspension data
        heading_text = (
            (heading or "") + " " + self._text(table.find_previous(["h2", "h3", "h4", "h5"]))
        )
        heading_lower = heading_text.lower()
        if any(
            token in heading_lower
            for token in ("injur", "verletz", "suspens", "sperr", "ban", "absence", "unavailable", "verletzung", "sperre")
        ):
            return True
        
        # Fallback: check table HTML content for German/English injury/suspension markers
        lower = str(table).lower()
        return any(
            token in lower 
            for token in ("sperrenundverletzungen", "verletz", "suspens", "injury", "ban", "absence")
        )

    def _classify_section(self, section_hint: str, reason: str) -> str:
        blob = f"{section_hint} {reason}".lower()
        return (
            "suspensions"
            if any(keyword in blob for keyword in SUSPENSION_KEYWORDS)
            else "injuries"
        )

    def _extract_player_name(
        self, row: Tag, cells: List[Tag], player_index: Optional[int]
    ) -> Optional[str]:
        search_nodes = []
        if player_index is not None and player_index < len(cells):
            search_nodes.append(cells[player_index])
        search_nodes.extend(cells[:3])  # Check first 3 cells for player name
        search_nodes.append(row)  # Fallback to row itself
        
        for node in search_nodes:
            # Expanded selector list with fallbacks
            for selector in [
                "td.hauptlink a",
                "a.spielprofil_tooltip",
                "a[title]",
                "td a[href*='profil']",
                "td a[href*='spieler']",
                "td a",
                "a",
                "img[alt]",
                ".player-name",
                "[class*='player']",
                "[class*='name']",
            ]:
                found = node.select_one(selector)
                if found:
                    if found.name == "img":
                        name = found.get("alt", "").strip()
                    else:
                        name = self._text(found)
                    if name and name.lower() not in {"details", "profil", "view", "show"}:
                        return name
            text = self._text(node)
            if text and len(text) > 2:  # Avoid single characters
                return text.split("\n")[0].strip()
        
        # Final fallback: extract from row text
        text = self._text(row)
        if text:
            # Try to extract first meaningful word sequence
            parts = text.split()
            if len(parts) >= 2:
                return " ".join(parts[:2])
            return parts[0] if parts else None
        return None

    def _extract_value(
        self,
        cells: List[Tag],
        header_map: Dict[int, str],
        labels: set[str],
        fallback_indexes: List[int],
    ) -> str:
        for index, label in header_map.items():
            if label in labels and index < len(cells):
                return self._text(cells[index])
        for index in fallback_indexes:
            if index < len(cells):
                return self._text(cells[index])
        return ""

    def _parse_table_rows(
        self,
        heading: Optional[str],
        table: Tag,
        report: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        injuries: List[Dict[str, Any]] = []
        suspensions: List[Dict[str, Any]] = []
        header_map = self._header_map(table)
        body = table.find("tbody") or table
        rows = body.find_all("tr", recursive=False)
        current_section = heading or "Injuries"
        player_index = next(
            (
                index
                for index, label in header_map.items()
                if label in PLAYER_COLUMN_LABELS
            ),
            0,
        )

        for row in rows:
            cells = row.find_all("td", recursive=False)
            if not cells:
                continue
            if len(cells) == 1:
                current_section = self._text(cells[0]) or current_section
                continue

            player_name = self._extract_player_name(row, cells, player_index)
            if not player_name:
                report["skipped_rows"] += 1
                continue

            reason = self._extract_value(
                cells, header_map, REASON_COLUMN_LABELS, [2, 1]
            )
            since_str = self._extract_value(cells, header_map, SINCE_COLUMN_LABELS, [3])
            return_str = self._extract_value(
                cells, header_map, RETURN_COLUMN_LABELS, [4]
            )
            missed_str = self._extract_value(
                cells, header_map, MISSED_MATCH_COLUMN_LABELS, [5, 4]
            )
            section_type = self._classify_section(current_section, reason)

            if section_type == "suspensions":
                suspensions.append(
                    {
                        "player_name": player_name,
                        "suspension_reason": reason or current_section or "Suspension",
                        "matches_remaining": self._parse_int(missed_str),
                    }
                )
            else:
                since_date = self._parse_date(since_str)
                expected_return_date = self._parse_date(return_str)
                days_out = None
                if since_date and expected_return_date:
                    days_out = (expected_return_date - since_date).days
                elif expected_return_date:
                    days_out = max(0, (expected_return_date - date.today()).days)
                injuries.append(
                    {
                        "player_name": player_name,
                        "injury_type": reason or current_section or "Unknown Injury",
                        "expected_return_date": expected_return_date,
                        "days_out": days_out,
                    }
                )
        return injuries, suspensions

    def _dedupe_rows(
        self, rows: List[Dict[str, Any]], keys: List[str]
    ) -> List[Dict[str, Any]]:
        seen = set()
        deduped = []
        for row in rows:
            fingerprint = tuple((row.get(key) or "") for key in keys)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            deduped.append(row)
        return deduped

    def _scrape_team_data(
        self, url: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        report: Dict[str, Any] = {
            "url": url,
            "page_visited": True,
            "from_cache": False,
            "status_code": None,
            "blocked": False,
            "empty_page": False,
            "parse_failures": 0,
            "skipped_rows": 0,
            "tables_seen": 0,
            "candidate_tables": 0,
            "players_extracted": 0,
            "injuries_found": 0,
            "suspensions_found": 0,
            "error": None,
        }
        page = self._fetch_page(url)
        report["status_code"] = page.get("status_code")
        report["from_cache"] = page.get("from_cache", False)
        html_content = page.get("html")
        if not html_content:
            report["error"] = page.get("error") or "empty-response"
            self.last_scrape_report = report
            logger.error(
                f"{self.name}: Could not retrieve content for {url} ({report['error']})"
            )
            return [], []

        blocked, empty_page, reason = self._detect_blocked_or_empty(html_content)
        if blocked:
            report["blocked"] = True
            report["error"] = reason
            self.last_scrape_report = report
            logger.warning(f"{self.name}: blocked page detected for {url} ({reason})")
            return [], []

        soup = BeautifulSoup(html_content, "lxml")
        candidates = self._candidate_tables(soup)
        report["tables_seen"] = len(candidates)

        injuries: List[Dict[str, Any]] = []
        suspensions: List[Dict[str, Any]] = []
        for heading, table in candidates:
            header_map = self._header_map(table)
            if not self._is_relevant_table(heading, table, header_map):
                continue
            report["candidate_tables"] += 1
            parsed_injuries, parsed_suspensions = self._parse_table_rows(
                heading, table, report
            )
            injuries.extend(parsed_injuries)
            suspensions.extend(parsed_suspensions)

        injuries = self._dedupe_rows(
            injuries, ["player_name", "injury_type", "expected_return_date"]
        )
        suspensions = self._dedupe_rows(
            suspensions, ["player_name", "suspension_reason", "matches_remaining"]
        )
        report["players_extracted"] = len(
            {
                row["player_name"]
                for row in injuries + suspensions
                if row.get("player_name")
            }
        )
        report["injuries_found"] = len(injuries)
        report["suspensions_found"] = len(suspensions)

        if not injuries and not suspensions:
            report["empty_page"] = empty_page or report["candidate_tables"] == 0
            report["parse_failures"] += 1
            if report["empty_page"]:
                logger.info(f"{self.name}: empty injury/suspension page for {url}")
            else:
                logger.warning(
                    f"{self.name}: no parseable injury/suspension rows found at {url}"
                )

        self.last_scrape_report = report
        logger.info(
            f"{self.name}: page={url} cache={report['from_cache']} status={report['status_code']} "
            f"tables={report['tables_seen']} candidates={report['candidate_tables']} players={report['players_extracted']} "
            f"injuries={report['injuries_found']} suspensions={report['suspensions_found']} skipped={report['skipped_rows']} "
            f"parse_failures={report['parse_failures']} blocked={report['blocked']} empty={report['empty_page']}"
        )
        
        # Log individual players extracted for debugging
        if report['players_extracted'] > 0:
            player_names = [
                row.get('player_name') for row in injuries + suspensions if row.get('player_name')
            ]
            logger.debug(f"{self.name}: extracted players: {player_names[:10]}")  # Log first 10
        
        # Log individual injuries found
        if report['injuries_found'] > 0:
            injury_details = [
                f"{inj.get('player_name')}: {inj.get('injury_type')}" 
                for inj in injuries[:5]
            ]
            logger.debug(f"{self.name}: injuries: {injury_details}")
        
        # Log individual suspensions found
        if report['suspensions_found'] > 0:
            suspension_details = [
                f"{susp.get('player_name')}: {susp.get('suspension_reason')}" 
                for susp in suspensions[:5]
            ]
            logger.debug(f"{self.name}: suspensions: {suspension_details}")
        
        return injuries, suspensions

    async def get_competitions(self) -> List[CompetitionData]:
        return [
            CompetitionData(
                code=code, name=name, area="International", source=self.name
            )
            for code, name in SUPPORTED_TRANSFERMARKT_COMPETITIONS.items()
        ]

    async def get_competition_standings(
        self, competition_code: str
    ) -> List[StandingData]:
        logger.debug(f"{self.name}: Competition standings not implemented")
        return []

    async def get_competition_matches(self, competition_code: str) -> List[MatchData]:
        logger.debug(f"{self.name}: Competition matches not implemented")
        return []

    async def get_live_matches(self) -> List[MatchData]:
        logger.debug(f"{self.name}: Live matches not implemented")
        return []

    async def get_match_statistics(
        self, match_id: str
    ) -> Optional[MatchStatisticsData]:
        logger.debug(f"{self.name}: Match statistics not implemented")
        return None

    async def get_match_lineups(
        self, match_id: str
    ) -> Optional[Dict[str, MatchLineupData]]:
        logger.debug(f"{self.name}: Match lineups not implemented")
        return None

    async def get_match_events(self, match_id: str) -> List[MatchEventData]:
        logger.debug(f"{self.name}: Match events not implemented")
        return []

    async def get_team_injuries(self, team_name: str) -> List[InjuryData]:
        logger.info(f"{self.name}: Fetching injuries for {team_name}")
        url = self.get_team_url(team_name)
        if not url:
            logger.warning(f"{self.name}: No URL found for team {team_name}")
            return []
        injuries_list, _ = self._scrape_team_data(url)
        return [
            InjuryData(
                player=PlayerData(name=inj["player_name"], source=self.name),
                team=TeamData(name=team_name, source=self.name),
                injury_type=inj["injury_type"],
                status="OUT" if (inj.get("days_out") or 0) > 0 else "DOUBTFUL",
                return_date=datetime.combine(
                    inj["expected_return_date"], datetime.min.time()
                )
                if inj.get("expected_return_date")
                else None,
                source=self.name,
            )
            for inj in injuries_list
        ]

    async def get_team_suspensions(self, team_name: str) -> List[SuspensionData]:
        logger.info(f"{self.name}: Fetching suspensions for {team_name}")
        url = self.get_team_url(team_name)
        if not url:
            logger.warning(f"{self.name}: No URL found for team {team_name}")
            return []
        _, suspensions_list = self._scrape_team_data(url)
        return [
            SuspensionData(
                player=PlayerData(name=susp["player_name"], source=self.name),
                team=TeamData(name=team_name, source=self.name),
                reason=susp["suspension_reason"],
                status="PENDING"
                if (susp.get("matches_remaining") or 0) > 0
                else "SERVED",
                matches_missed=susp.get("matches_remaining"),
                source=self.name,
            )
            for susp in suspensions_list
        ]
