"""
FBref Provider — scrapes publicly available football statistics from fbref.com.

Supports international competitions:
  - FIFA World Cup (WC)
  - UEFA Euro (EC)
  - Copa América (CA)
  - UEFA Nations League (UNL)
  - Women's World Cup (WWC)
  - Olympic Football (OLY)
  - World Cup Qualifiers (WCQ / WCQE / WCQA / WCQC)

FBref exposes HTML tables — we parse them with BeautifulSoup.
If a competition is unavailable (404, blocked, no table found) we fail gracefully.
"""

import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

try:
    from curl_cffi import requests as curl_requests
except Exception:  # pragma: no cover - optional runtime dependency
    curl_requests = None

from providers.base import (
    BaseProvider,
    CompetitionData,
    InjuryData,
    MatchData,
    MatchEventData,
    MatchLineupData,
    MatchStatisticsData,
    PlayerData,
    PlayerMatchPerformanceData,
    StandingData,
    SuspensionData,
    TeamData,
)
from utils.logger import logger

# ---------------------------------------------------------------------------
# Competition map: our internal code → FBref URL slug
# ---------------------------------------------------------------------------
FBREF_COMPETITION_MAP: Dict[str, Dict[str, str]] = {
    "WC": {
        "name": "FIFA World Cup",
        "area": "World",
        "schedule_url": "https://fbref.com/en/comps/1/schedule/World-Cup-Scores-and-Fixtures",
        "stats_url": "https://fbref.com/en/comps/1/World-Cup-Stats",
    },
    "EC": {
        "name": "UEFA Euro",
        "area": "Europe",
        "schedule_url": "https://fbref.com/en/comps/676/schedule/European-Championship-Scores-and-Fixtures",
        "stats_url": "https://fbref.com/en/comps/676/European-Championship-Stats",
    },
    "CA": {
        "name": "Copa América",
        "area": "South America",
        "schedule_url": "https://fbref.com/en/comps/685/schedule/Copa-America-Scores-and-Fixtures",
        "stats_url": "https://fbref.com/en/comps/685/Copa-America-Stats",
    },
    "UNL": {
        "name": "UEFA Nations League",
        "area": "Europe",
        "schedule_url": "https://fbref.com/en/comps/703/schedule/UEFA-Nations-League-Scores-and-Fixtures",
        "stats_url": "https://fbref.com/en/comps/703/UEFA-Nations-League-Stats",
    },
    "WWC": {
        "name": "Women's World Cup",
        "area": "World",
        "schedule_url": "https://fbref.com/en/comps/106/schedule/Womens-World-Cup-Scores-and-Fixtures",
        "stats_url": "https://fbref.com/en/comps/106/Womens-World-Cup-Stats",
    },
    "OLY": {
        "name": "Olympic Football",
        "area": "World",
        "schedule_url": "https://fbref.com/en/comps/708/schedule/Olympic-Games-Scores-and-Fixtures",
        "stats_url": "https://fbref.com/en/comps/708/Olympic-Games-Stats",
    },
    "WCQ": {
        "name": "FIFA World Cup Qualifying",
        "area": "World",
        "schedule_url": "https://fbref.com/en/comps/30/schedule/World-Cup-Qualifying-UEFA-Scores-and-Fixtures",
        "stats_url": "https://fbref.com/en/comps/30/World-Cup-Qualifying-UEFA-Stats",
    },
    "WCQA": {
        "name": "World Cup Qualifying – CONMEBOL",
        "area": "South America",
        "schedule_url": "https://fbref.com/en/comps/26/schedule/World-Cup-Qualifying-CONMEBOL-Scores-and-Fixtures",
        "stats_url": "https://fbref.com/en/comps/26/World-Cup-Qualifying-CONMEBOL-Stats",
    },
    "WCQC": {
        "name": "World Cup Qualifying – CONCACAF",
        "area": "CONCACAF",
        "schedule_url": "https://fbref.com/en/comps/28/schedule/World-Cup-Qualifying-CONCACAF-Scores-and-Fixtures",
        "stats_url": "https://fbref.com/en/comps/28/World-Cup-Qualifying-CONCACAF-Stats",
    },
    "AFCON": {
        "name": "Africa Cup of Nations",
        "area": "Africa",
        "schedule_url": "https://fbref.com/en/comps/656/schedule/African-Cup-of-Nations-Scores-and-Fixtures",
        "stats_url": "https://fbref.com/en/comps/656/African-Cup-of-Nations-Stats",
    },
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://fbref.com/",
}

_REQUEST_DELAY = 3.0  # seconds between requests — be respectful to FBref


def _safe_int(val: str) -> Optional[int]:
    try:
        return int(val.strip())
    except Exception:
        return None


def _safe_float(val: str) -> Optional[float]:
    try:
        return float(val.strip())
    except Exception:
        return None


def _parse_date(date_str: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except Exception:
            continue
    return None


class FBrefProvider(BaseProvider):
    """
    FBref Provider — HTML-scraping provider for international football statistics.

    Collects per-match and per-player:
      player ratings (not native to FBref — SofaScore domain)
      goalkeeper saves, passing accuracy, tackles, interceptions,
      aerial duels, successful passes, substitutions, formations,
      lineups, shots, shots on target, possession, cards.

    Gracefully degrades if a competition page is unavailable.
    """

    name = "FBref"

    def __init__(self):
        super().__init__()
        self._session = requests.Session()
        self._session.headers.update(_HEADERS)
        self._blocked_by_cloudflare = False
        logger.info(f"{self.name} provider initialized (HTML scraping mode)")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a URL and return parsed HTML, or None on failure."""
        try:
            time.sleep(_REQUEST_DELAY)
            resp = self._session.get(url, timeout=30)
            if resp.status_code in (403, 429) and curl_requests is not None:
                try:
                    resp = curl_requests.get(
                        url,
                        impersonate="chrome124",
                        headers=_HEADERS,
                        timeout=30,
                    )
                except Exception as impersonation_error:
                    logger.debug(
                        f"{self.name}: curl_cffi fallback failed for {url}: {impersonation_error}"
                    )
            if resp.status_code == 429:
                logger.warning(
                    f"{self.name}: Rate-limited by FBref (429), backing off 30s"
                )
                time.sleep(30)
                resp = self._session.get(url, timeout=30)
            if resp.status_code != 200:
                body = (resp.text or "")[:300]
                if (
                    "Just a moment" in body
                    or "cf-browser-verification" in body
                    or resp.status_code == 403
                ):
                    self._blocked_by_cloudflare = True
                    logger.warning(
                        f"{self.name}: Request blocked by Cloudflare for {url}"
                    )
                else:
                    logger.warning(f"{self.name}: HTTP {resp.status_code} for {url}")
                return None
            self._blocked_by_cloudflare = False
            return BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            logger.warning(f"{self.name}: Request failed for {url}: {e}")
            return None

    def _find_table(self, soup: BeautifulSoup, table_id: str) -> Optional[Any]:
        """Find a specific table by ID (handles commented-out HTML that FBref uses)."""
        # FBref wraps some tables in HTML comments — extract them
        table = soup.find("table", {"id": table_id})
        if table:
            return table
        # Try searching in comments
        from bs4 import Comment

        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment_soup = BeautifulSoup(str(comment), "lxml")
            table = comment_soup.find("table", {"id": table_id})
            if table:
                return table
        return None

    # ------------------------------------------------------------------
    # BaseProvider interface
    # ------------------------------------------------------------------

    async def get_competitions(self) -> List[CompetitionData]:
        competitions = []
        for code, info in FBREF_COMPETITION_MAP.items():
            competitions.append(
                CompetitionData(
                    id=f"fbref_{code}",
                    name=info["name"],
                    code=code,
                    area=info["area"],
                    source=self.name,
                )
            )
        logger.info(
            f"{self.name}: Returning {len(competitions)} supported competitions"
        )
        return competitions

    async def get_competition_standings(
        self, competition_code: str
    ) -> List[StandingData]:
        """FBref doesn't expose standings tables in a consistent format — return empty."""
        return []

    async def get_competition_matches(self, competition_code: str) -> List[MatchData]:
        """Scrape the fixtures/results schedule page for a competition."""
        comp = FBREF_COMPETITION_MAP.get(competition_code)
        if not comp:
            logger.warning(
                f"{self.name}: Unsupported competition code: {competition_code}"
            )
            return []

        logger.info(f"{self.name}: Scraping matches for {comp['name']}")
        soup = self._get(comp["schedule_url"])
        if not soup:
            logger.warning(
                f"{self.name}: Could not fetch schedule for {competition_code}"
            )
            return []

        # FBref schedule tables use id="sched_..."
        table = (
            self._find_table(soup, "sched_all")
            or self._find_table(soup, f"sched_{competition_code}_all")
            or soup.find("table", class_=re.compile(r"stats_table"))
        )
        if not table:
            logger.warning(
                f"{self.name}: No schedule table found for {competition_code}"
            )
            return []

        matches = []
        rows = table.find("tbody").find_all("tr") if table.find("tbody") else []
        for row in rows:
            if row.get("class") and "spacer" in " ".join(row.get("class", [])):
                continue
            cells = row.find_all(["td", "th"])
            if not cells:
                continue

            try:
                cell_map = {td.get("data-stat", ""): td for td in cells}

                date_td = cell_map.get("date") or cell_map.get("gameday")
                home_td = cell_map.get("home_team") or cell_map.get("squad_a")
                away_td = cell_map.get("away_team") or cell_map.get("squad_b")
                score_td = cell_map.get("score") or cell_map.get("result")

                if not home_td or not away_td:
                    continue

                home_name = home_td.get_text(strip=True)
                away_name = away_td.get_text(strip=True)
                if not home_name or not away_name:
                    continue

                date_str = date_td.get_text(strip=True) if date_td else ""
                match_date = _parse_date(date_str)

                home_score, away_score = None, None
                score_str = score_td.get_text(strip=True) if score_td else ""
                if "–" in score_str or "-" in score_str:
                    sep = "–" if "–" in score_str else "-"
                    parts = score_str.split(sep)
                    if len(parts) == 2:
                        home_score = _safe_int(parts[0])
                        away_score = _safe_int(parts[1])

                status = "FINISHED" if home_score is not None else "SCHEDULED"

                # Extract match report link to use as our ID
                match_link = score_td.find("a") if score_td else None
                match_id = None
                if match_link and match_link.get("href"):
                    href = match_link["href"]
                    # e.g. /en/matches/abc123/...
                    m = re.search(r"/matches/([a-f0-9]+)/", href)
                    if m:
                        match_id = f"fbref_{m.group(1)}"

                if not match_id:
                    # Fallback: build ID from teams + date
                    match_id = f"fbref_{home_name}_{away_name}_{date_str}".replace(
                        " ", "_"
                    )

                home_team = TeamData(name=home_name, source=self.name)
                away_team = TeamData(name=away_name, source=self.name)

                matches.append(
                    MatchData(
                        id=match_id,
                        competition_id=competition_code,
                        home_team=home_team,
                        away_team=away_team,
                        utc_date=match_date,
                        status=status,
                        home_score=home_score,
                        away_score=away_score,
                        provider_ids={self.name: match_id},
                        source=self.name,
                    )
                )
            except Exception as e:
                logger.debug(f"{self.name}: Error parsing row: {e}")
                continue

        logger.info(
            f"{self.name}: Scraped {len(matches)} matches for {competition_code}"
        )
        return matches

    async def get_live_matches(self) -> List[MatchData]:
        """FBref does not provide live match data."""
        return []

    async def get_match_statistics(
        self, match_id: str
    ) -> Optional[MatchStatisticsData]:
        """
        Scrape a match report page on FBref to get detailed statistics.
        match_id should be the FBref match ID (e.g. 'abc123def456...')
        """
        # Extract the raw FBref match hash from our composite ID
        fbref_id = match_id.replace("fbref_", "").split("_")[0]
        if len(fbref_id) < 8:
            logger.debug(
                f"{self.name}: Cannot build match report URL from ID: {match_id}"
            )
            return None

        url = f"https://fbref.com/en/matches/{fbref_id}/"
        logger.info(f"{self.name}: Scraping match stats from {url}")
        soup = self._get(url)
        if not soup:
            return None

        try:
            stats = MatchStatisticsData(match_id=match_id, source=self.name)

            # --- Possession ---
            for div in soup.find_all("div", class_=re.compile(r"possession")):
                text = div.get_text(strip=True)
                nums = re.findall(r"\d+\.?\d*", text)
                if len(nums) >= 2:
                    stats.home_possession = float(nums[0])
                    stats.away_possession = float(nums[1])
                    break

            # --- Team stats table (shots, passes, tackles etc.) ---
            # FBref uses two stat tables: one for each team
            for side, attr in [("home", "home"), ("away", "away")]:
                table_id_candidates = [
                    f"stats_{side}_summary",
                    "stats_a_summary",
                    "stats_b_summary",
                ]
                for tid in table_id_candidates:
                    tbl = self._find_table(soup, tid)
                    if tbl:
                        self._parse_team_stats_from_table(tbl, stats, side)
                        break

            # --- Shot summary tables ---
            self._parse_shot_summary(soup, stats)

            return (
                stats
                if (stats.home_shots is not None or stats.home_possession is not None)
                else None
            )
        except Exception as e:
            logger.warning(
                f"{self.name}: Error parsing match stats for {match_id}: {e}"
            )
            return None

    def _parse_team_stats_from_table(
        self, table: Any, stats: MatchStatisticsData, side: str
    ):
        """Parse a team summary stats table and fill MatchStatisticsData."""
        try:
            rows = table.find("tfoot")
            if not rows:
                rows = table
            totals = rows.find_all("tr")
            for row in totals:
                cells = {
                    td.get("data-stat", ""): td.get_text(strip=True)
                    for td in row.find_all(["td", "th"])
                }
                shots = _safe_int(cells.get("shots", "") or cells.get("sh", ""))
                shots_ot = _safe_int(
                    cells.get("shots_on_target", "") or cells.get("sot", "")
                )
                passes = _safe_int(
                    cells.get("passes", "") or cells.get("passes_total", "")
                )
                pass_pct = _safe_float(
                    cells.get("passes_pct", "") or cells.get("pass_pct", "")
                )
                tackles = _safe_int(
                    cells.get("tackles", "") or cells.get("tackles_won", "")
                )
                interceptions = _safe_int(cells.get("interceptions", ""))
                aerials_won = _safe_int(
                    cells.get("aerials_won", "") or cells.get("won_aerial", "")
                )

                if side == "home":
                    if shots is not None:
                        stats.home_shots = shots
                    if shots_ot is not None:
                        stats.home_shots_on_target = shots_ot
                    if passes is not None:
                        stats.home_passes = passes
                    if pass_pct is not None:
                        stats.home_pass_accuracy = pass_pct
                    if tackles is not None:
                        stats.home_tackles = tackles
                    if interceptions is not None:
                        stats.home_interceptions = interceptions
                    if aerials_won is not None:
                        stats.home_aerial_duels = aerials_won
                else:
                    if shots is not None:
                        stats.away_shots = shots
                    if shots_ot is not None:
                        stats.away_shots_on_target = shots_ot
                    if passes is not None:
                        stats.away_passes = passes
                    if pass_pct is not None:
                        stats.away_pass_accuracy = pass_pct
                    if tackles is not None:
                        stats.away_tackles = tackles
                    if interceptions is not None:
                        stats.away_interceptions = interceptions
                    if aerials_won is not None:
                        stats.away_aerial_duels = aerials_won
        except Exception as e:
            logger.debug(f"{self.name}: Error parsing team stats table: {e}")

    def _parse_shot_summary(self, soup: BeautifulSoup, stats: MatchStatisticsData):
        """Parse shot summary stats from the shots table."""
        try:
            shots_table = self._find_table(soup, "shots_all")
            if not shots_table:
                return
            home_shots, away_shots, home_sot, away_sot = 0, 0, 0, 0
            for row in shots_table.find("tbody").find_all("tr"):
                cells = {
                    td.get("data-stat", ""): td.get_text(strip=True)
                    for td in row.find_all("td")
                }
                team_cell = cells.get("team", "")
                outcome = cells.get("outcome", "")
                if not team_cell:
                    continue
                is_home = "home" in team_cell.lower()
                if is_home:
                    home_shots += 1
                    if outcome.lower() in ("goal", "saved", "on target"):
                        home_sot += 1
                else:
                    away_shots += 1
                    if outcome.lower() in ("goal", "saved", "on target"):
                        away_sot += 1

            if home_shots > 0 and stats.home_shots is None:
                stats.home_shots = home_shots
                stats.away_shots = away_shots
            if home_sot > 0 and stats.home_shots_on_target is None:
                stats.home_shots_on_target = home_sot
                stats.away_shots_on_target = away_sot
        except Exception as e:
            logger.debug(f"{self.name}: Error parsing shot summary: {e}")

    async def get_match_lineups(
        self, match_id: str
    ) -> Optional[Dict[str, MatchLineupData]]:
        """Scrape lineups from the match report page."""
        fbref_id = match_id.replace("fbref_", "").split("_")[0]
        if len(fbref_id) < 8:
            return None

        url = f"https://fbref.com/en/matches/{fbref_id}/"
        soup = self._get(url)
        if not soup:
            return None

        try:
            lineups: Dict[str, MatchLineupData] = {}

            # FBref lineup sections are divs with class "lineup"
            lineup_divs = soup.find_all("div", id=re.compile(r"div_lineup"))
            if not lineup_divs:
                lineup_divs = soup.find_all("div", class_="lineup")

            for i, div in enumerate(lineup_divs[:2]):
                side = "home" if i == 0 else "away"
                players = []
                formation = None

                # Formation is often in the header
                header = div.find(["h2", "h3", "p"])
                if header:
                    text = header.get_text()
                    m = re.search(r"\d-\d(-\d)+|\d-\d", text)
                    if m:
                        formation = m.group()

                # Players list
                for li in div.find_all("li"):
                    name = li.get_text(strip=True)
                    if name:
                        link = li.find("a")
                        player_id = None
                        if link and link.get("href"):
                            pm = re.search(r"/players/([a-f0-9]+)/", link["href"])
                            if pm:
                                player_id = f"fbref_{pm.group(1)}"
                        players.append(
                            PlayerMatchPerformanceData(
                                player=PlayerData(
                                    id=player_id, name=name, source=self.name
                                ),
                                is_starter=True,
                                source=self.name,
                            )
                        )

                team = TeamData(source=self.name)
                lineups[side] = MatchLineupData(
                    match_id=match_id,
                    team=team,
                    formation=formation,
                    starting_xi=players,
                    substitutes=[],
                    source=self.name,
                )

            return lineups if lineups else None
        except Exception as e:
            logger.warning(f"{self.name}: Error parsing lineups for {match_id}: {e}")
            return None

    async def get_match_events(self, match_id: str) -> List[MatchEventData]:
        """
        Parse match events (goals, cards, substitutions) from the match report.
        """
        fbref_id = match_id.replace("fbref_", "").split("_")[0]
        if len(fbref_id) < 8:
            return []

        url = f"https://fbref.com/en/matches/{fbref_id}/"
        soup = self._get(url)
        if not soup:
            return []

        events = []
        try:
            # Events div
            events_div = soup.find("div", id="events_wrap")
            if not events_div:
                return []

            for event_div in events_div.find_all("div", class_=re.compile(r"event")):
                try:
                    text = event_div.get_text(" ", strip=True)

                    # Determine minute
                    minute = None
                    m = re.search(r"(\d+)(?:\+\d+)?'", text)
                    if m:
                        minute = int(m.group(1))

                    # Determine event type
                    event_type = "UNKNOWN"
                    classes = " ".join(event_div.get("class", []))
                    if "goal" in classes.lower() or "⚽" in text:
                        event_type = "GOAL"
                    elif "yellow_card" in classes.lower() or "🟨" in text:
                        event_type = "YELLOW_CARD"
                    elif "red_card" in classes.lower() or "🟥" in text:
                        event_type = "RED_CARD"
                    elif (
                        "substitution" in classes.lower() or "↑" in text or "↓" in text
                    ):
                        event_type = "SUBSTITUTION"

                    # Player name
                    player_link = event_div.find("a")
                    player_name = (
                        player_link.get_text(strip=True) if player_link else None
                    )

                    # Home/away
                    is_home = "a_" not in classes  # rough heuristic

                    events.append(
                        MatchEventData(
                            id=f"fbref_{match_id}_{minute}_{event_type}_{player_name}",
                            match_id=match_id,
                            type=event_type,
                            minute=minute,
                            player_name=player_name,
                            is_home=is_home,
                            source=self.name,
                        )
                    )
                except Exception as e:
                    logger.debug(f"{self.name}: Error parsing event: {e}")
                    continue
        except Exception as e:
            logger.warning(f"{self.name}: Error parsing events for {match_id}: {e}")

        return events

    async def get_team_injuries(self, team_id: str) -> List[InjuryData]:
        """FBref does not expose injury data — use Transfermarkt instead."""
        return []

    async def get_team_suspensions(self, team_id: str) -> List[SuspensionData]:
        """FBref does not expose suspension data — use Transfermarkt instead."""
        return []

    # ------------------------------------------------------------------
    # FBref-specific: scrape player stats for a competition
    # ------------------------------------------------------------------

    async def get_player_stats_for_competition(
        self, competition_code: str
    ) -> List[PlayerMatchPerformanceData]:
        """
        Scrape player-level statistics for a competition.
        Returns a list of PlayerMatchPerformanceData objects.
        """
        comp = FBREF_COMPETITION_MAP.get(competition_code)
        if not comp:
            logger.warning(
                f"{self.name}: No player stats available for {competition_code}"
            )
            return []

        logger.info(f"{self.name}: Scraping player stats for {comp['name']}")
        soup = self._get(comp["stats_url"])
        if not soup:
            return []

        # Standard player stats table
        table = self._find_table(soup, "stats_standard") or self._find_table(
            soup, "stats_standard_combined"
        )
        if not table:
            logger.warning(
                f"{self.name}: No player stats table found for {competition_code}"
            )
            return []

        performances = []
        try:
            tbody = table.find("tbody")
            if not tbody:
                return []
            for row in tbody.find_all("tr"):
                if row.get("class") and any(
                    c in row.get("class", []) for c in ["thead", "spacer"]
                ):
                    continue
                cells = {
                    td.get("data-stat", ""): td.get_text(strip=True)
                    for td in row.find_all(["td", "th"])
                }

                player_name = cells.get("player", "")
                if not player_name:
                    continue

                team_name = cells.get("team", "") or cells.get("squad", "")
                position = cells.get("position", "") or cells.get("pos", "")

                # Player link for ID
                player_id = None
                player_td = row.find("td", {"data-stat": "player"}) or row.find(
                    "th", {"data-stat": "player"}
                )
                if player_td:
                    link = player_td.find("a")
                    if link and link.get("href"):
                        pm = re.search(r"/players/([a-f0-9]+)/", link["href"])
                        if pm:
                            player_id = f"fbref_{pm.group(1)}"

                perf = PlayerMatchPerformanceData(
                    player=PlayerData(
                        id=player_id,
                        name=player_name,
                        position=position,
                        source=self.name,
                    ),
                    team=TeamData(name=team_name, source=self.name),
                    position=position,
                    goals=_safe_int(cells.get("goals", "")),
                    assists=_safe_int(cells.get("assists", "")),
                    shots=_safe_int(cells.get("shots", "") or cells.get("sh", "")),
                    shots_on_target=_safe_int(
                        cells.get("shots_on_target", "") or cells.get("sot", "")
                    ),
                    passes=_safe_int(
                        cells.get("passes", "") or cells.get("passes_total", "")
                    ),
                    pass_accuracy=_safe_float(
                        cells.get("passes_pct", "") or cells.get("pass_pct", "")
                    ),
                    tackles=_safe_int(
                        cells.get("tackles", "") or cells.get("tackles_won", "")
                    ),
                    interceptions=_safe_int(cells.get("interceptions", "")),
                    saves=_safe_int(
                        cells.get("gk_saves", "") or cells.get("saves", "")
                    ),
                    source=self.name,
                )
                performances.append(perf)
        except Exception as e:
            logger.warning(f"{self.name}: Error parsing player stats: {e}")

        logger.info(
            f"{self.name}: Scraped {len(performances)} player records for {competition_code}"
        )
        return performances
