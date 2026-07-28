"""
config/competitions.py
──────────────────────
Centralized single source of truth for all supported football competitions
across the OFFLINE platform backend.

Adding a new competition requires only adding an entry to SUPPORTED_COMPETITIONS here.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CompetitionDef:
    code: str                  # Standard internal competition code (e.g. "PL", "PD", "CL")
    name: str                  # Full official display name
    short_name: str            # Concise label for UI and logs
    type: str                  # "League", "Cup", "International"
    country: str               # Host country or region (e.g., "England", "Europe", "International")
    is_tournament: bool = False # True for knockout/group tournaments (World Cup, Euro, Copa America)
    
    # Provider mapping codes (if provider uses a different key/id)
    football_data_code: Optional[str] = None
    sofascore_id: Optional[int] = None
    transfermarkt_id: Optional[str] = None
    api_football_id: Optional[int] = None
    statsbomb_id: Optional[int] = None


# ── SINGLE SOURCE OF TRUTH FOR ALL SUPPORTED COMPETITIONS ──────────────────────
SUPPORTED_COMPETITIONS: List[CompetitionDef] = [
    # ── DOMESTIC LEAGUES ───────────────────────────────────────────────────────
    CompetitionDef(
        code="PL",
        name="Premier League",
        short_name="EPL",
        type="League",
        country="England",
        football_data_code="PL",
        sofascore_id=17,
        transfermarkt_id="GB1",
        api_football_id=39,
    ),
    CompetitionDef(
        code="PD",
        name="La Liga",
        short_name="La Liga",
        type="League",
        country="Spain",
        football_data_code="PD",
        sofascore_id=8,
        transfermarkt_id="ES1",
        api_football_id=140,
    ),
    CompetitionDef(
        code="SA",
        name="Serie A",
        short_name="Serie A",
        type="League",
        country="Italy",
        football_data_code="SA",
        sofascore_id=23,
        transfermarkt_id="IT1",
        api_football_id=135,
    ),
    CompetitionDef(
        code="BL1",
        name="Bundesliga",
        short_name="Bundesliga",
        type="League",
        country="Germany",
        football_data_code="BL1",
        sofascore_id=35,
        transfermarkt_id="L1",
        api_football_id=78,
    ),
    CompetitionDef(
        code="FL1",
        name="Ligue 1",
        short_name="Ligue 1",
        type="League",
        country="France",
        football_data_code="FL1",
        sofascore_id=34,
        transfermarkt_id="FR1",
        api_football_id=61,
    ),
    CompetitionDef(
        code="MLS",
        name="Major League Soccer",
        short_name="MLS",
        type="League",
        country="United States",
        football_data_code="MLS",
        sofascore_id=242,
        transfermarkt_id="MLS1",
        api_football_id=253,
    ),
    CompetitionDef(
        code="BSA",
        name="Brasileirão Série A",
        short_name="Brasileirão",
        type="League",
        country="Brazil",
        football_data_code="BSA",
        sofascore_id=325,
        transfermarkt_id="BRA1",
        api_football_id=71,
    ),
    CompetitionDef(
        code="DED",
        name="Eredivisie",
        short_name="Eredivisie",
        type="League",
        country="Netherlands",
        football_data_code="DED",
        sofascore_id=37,
        transfermarkt_id="NL1",
        api_football_id=88,
    ),

    # ── EUROPEAN COMPETITIONS ─────────────────────────────────────────────────
    CompetitionDef(
        code="CL",
        name="UEFA Champions League",
        short_name="UCL",
        type="Cup",
        country="Europe",
        is_tournament=True,
        football_data_code="CL",
        sofascore_id=7,
        transfermarkt_id="CL",
        api_football_id=2,
    ),
    CompetitionDef(
        code="EL",
        name="UEFA Europa League",
        short_name="UEL",
        type="Cup",
        country="Europe",
        is_tournament=True,
        football_data_code="EL",
        sofascore_id=679,
        transfermarkt_id="EL",
        api_football_id=3,
    ),
    CompetitionDef(
        code="ECL",
        name="UEFA Conference League",
        short_name="UECL",
        type="Cup",
        country="Europe",
        is_tournament=True,
        football_data_code="ECL",
        sofascore_id=17015,
        transfermarkt_id="UCOL",
        api_football_id=848,
    ),

    # ── DOMESTIC CUPS ──────────────────────────────────────────────────────────
    CompetitionDef(
        code="FAC",
        name="FA Cup",
        short_name="FA Cup",
        type="Cup",
        country="England",
        football_data_code="FAC",
        sofascore_id=19,
        transfermarkt_id="FAC",
        api_football_id=45,
    ),
    CompetitionDef(
        code="CDR",
        name="Copa del Rey",
        short_name="Copa del Rey",
        type="Cup",
        country="Spain",
        football_data_code="CDR",
        sofascore_id=32,
        transfermarkt_id="CDR",
        api_football_id=143,
    ),
    CompetitionDef(
        code="DFB",
        name="DFB-Pokal",
        short_name="DFB Pokal",
        type="Cup",
        country="Germany",
        football_data_code="DFB",
        sofascore_id=209,
        transfermarkt_id="DFB",
        api_football_id=81,
    ),
    CompetitionDef(
        code="CIT",
        name="Coppa Italia",
        short_name="Coppa Italia",
        type="Cup",
        country="Italy",
        football_data_code="CIT",
        sofascore_id=327,
        transfermarkt_id="CIT",
        api_football_id=137,
    ),

    # ── INTERNATIONAL COMPETITIONS ────────────────────────────────────────────
    CompetitionDef(
        code="WC",
        name="FIFA World Cup",
        short_name="World Cup",
        type="International",
        country="International",
        is_tournament=True,
        football_data_code="WC",
        sofascore_id=16,
        transfermarkt_id="WM26",
        api_football_id=1,
    ),
    CompetitionDef(
        code="EC",
        name="UEFA Euro",
        short_name="UEFA Euro",
        type="International",
        country="Europe",
        is_tournament=True,
        football_data_code="EC",
        sofascore_id=1,
        transfermarkt_id="EM24",
        api_football_id=4,
    ),
    CompetitionDef(
        code="CA",
        name="Copa América",
        short_name="Copa América",
        type="International",
        country="South America",
        is_tournament=True,
        football_data_code="CA",
        sofascore_id=134,
        transfermarkt_id="CLI4",
        api_football_id=9,
    ),
    CompetitionDef(
        code="UNL",
        name="UEFA Nations League",
        short_name="Nations League",
        type="International",
        country="Europe",
        is_tournament=True,
        football_data_code="UNL",
        sofascore_id=10783,
        transfermarkt_id="UNL",
        api_football_id=5,
    ),
    CompetitionDef(
        code="WCQ",
        name="FIFA World Cup Qualifiers",
        short_name="WC Qualifiers",
        type="International",
        country="International",
        football_data_code="WCQ",
        sofascore_id=10,
        transfermarkt_id="WCQ",
        api_football_id=10,
    ),
]


# ── HELPER UTILITY FUNCTIONS ──────────────────────────────────────────────────
COMPETITIONS_BY_CODE: Dict[str, CompetitionDef] = {
    c.code.upper(): c for c in SUPPORTED_COMPETITIONS
}


def get_all_supported_competitions() -> List[CompetitionDef]:
    """Returns list of all supported competition definitions."""
    return SUPPORTED_COMPETITIONS


def get_supported_codes() -> List[str]:
    """Returns list of internal competition codes (e.g. ['PL', 'PD', 'SA', ...])."""
    return [c.code for c in SUPPORTED_COMPETITIONS]


def get_competition_by_code(code: str) -> Optional[CompetitionDef]:
    """Retrieves competition definition by code (case-insensitive)."""
    if not code:
        return None
    return COMPETITIONS_BY_CODE.get(code.upper())
