"""
Team Name Canonical Mapping — football-data.co.uk → PostgreSQL DB official names

Football-data.co.uk uses abbreviated team names (e.g. "Man City", "Nott'm Forest").
The DB stores official API-Football names (e.g. "Manchester City FC", "Nottingham Forest FC").

This mapping is used when ingesting historical football-data.co.uk CSV data.
It covers all 7 target competitions: PL, PD, SA, BL1, FL1, DED, and BSA.

IMPORTANT: Keep this file up to date when new teams are promoted/relegated.
"""

# Format: { "football-data short name": "DB official canonical name" }
TEAM_NAME_MAP: dict[str, str] = {

    # ==========================================
    # PREMIER LEAGUE (PL) — England
    # ==========================================
    "Arsenal": "Arsenal FC",
    "Aston Villa": "Aston Villa FC",
    "Bournemouth": "AFC Bournemouth",
    "Brentford": "Brentford FC",
    "Brighton": "Brighton & Hove Albion FC",
    "Brighton & HA": "Brighton & Hove Albion FC",
    "Burnley": "Burnley FC",
    "Chelsea": "Chelsea FC",
    "Crystal Palace": "Crystal Palace FC",
    "Everton": "Everton FC",
    "Fulham": "Fulham FC",
    "Ipswich": "Ipswich Town FC",
    "Leeds": "Leeds United FC",
    "Leicester": "Leicester City",
    "Liverpool": "Liverpool FC",
    "Luton": "Luton Town FC",
    "Man City": "Manchester City FC",
    "Man United": "Manchester United FC",
    "Middlesbrough": "Middlesbrough",
    "Newcastle": "Newcastle United FC",
    "Norwich": "Norwich City",
    "Nott'm Forest": "Nottingham Forest FC",
    "Sheffield United": "Sheffield United FC",
    "Sheffield Weds": "Sheffield Wednesday FC",
    "Southampton": "Southampton FC",
    "Stoke": "Stoke City FC",
    "Sunderland": "Sunderland AFC",
    "Swansea": "Swansea City FC",
    "Tottenham": "Tottenham Hotspur FC",
    "Watford": "Watford FC",
    "West Brom": "West Bromwich Albion FC",
    "West Ham": "West Ham United FC",
    "Wolves": "Wolverhampton Wanderers FC",
    "Blackburn": "Blackburn Rovers FC",
    "Bolton": "Bolton Wanderers FC",
    "Charlton": "Charlton Athletic FC",
    "Hull": "Hull City AFC",
    "Portsmouth": "Portsmouth FC",
    "Birmingham": "Birmingham City FC",
    "Derby": "Derby County FC",
    "Queens Park Rangers": "Queens Park Rangers FC",
    "QPR": "Queens Park Rangers FC",
    "Reading": "Reading FC",
    "Wigan": "Wigan Athletic FC",
    "Coventry": "Coventry City FC",
    "Middlesboro": "Middlesbrough",
    "Blackpool": "Blackpool FC",
    "Exeter": "Exeter City FC",

    # ==========================================
    # LA LIGA (PD) — Spain
    # ==========================================
    "Ath Bilbao": "Athletic Club de Bilbao",
    "Ath Madrid": "Club Atlético de Madrid",
    "Atletico Madrid": "Club Atlético de Madrid",
    "Atl Madrid": "Club Atlético de Madrid",
    "Barcelona": "FC Barcelona",
    "Betis": "Real Betis Balompié",
    "Cadiz": "Cádiz CF",
    "Celta": "RC Celta de Vigo",
    "Eibar": "SD Eibar",
    "Elche": "Elche CF",
    "Espanol": "RCD Espanyol de Barcelona",
    "Espanya": "RCD Espanyol de Barcelona",
    "Getafe": "Getafe CF",
    "Girona": "Girona FC",
    "Granada": "Granada CF",
    "Huesca": "SD Huesca",
    "Leganes": "CD Leganés",
    "Levante": "Levante UD",
    "Mallorca": "RCD Mallorca",
    "Osasuna": "CA Osasuna",
    "Rayo Vallecano": "Rayo Vallecano de Madrid",
    "Real Madrid": "Real Madrid CF",
    "Real Sociedad": "Real Sociedad de Fútbol",
    "Sevilla": "Sevilla FC",
    "Sociedad": "Real Sociedad de Fútbol",
    "Sp Gijon": "Sporting de Gijón",
    "Alaves": "Deportivo Alavés",
    "Dep Alaves": "Deportivo Alavés",
    "Valencia": "Valencia CF",
    "Valladolid": "Real Valladolid CF",
    "Villarreal": "Villarreal CF",
    "Las Palmas": "UD Las Palmas",
    "La Palmas": "UD Las Palmas",
    "Almeria": "UD Almería",

    # ==========================================
    # SERIE A (SA) — Italy
    # ==========================================
    "AC Milan": "AC Milan",
    "Atalanta": "Atalanta BC",
    "Benevento": "Benevento Calcio",
    "Bologna": "Bologna FC 1909",
    "Cagliari": "Cagliari Calcio",
    "Chievo": "AC ChievoVerona",
    "Como": "Como 1907",
    "Cremonese": "US Cremonese",
    "Empoli": "Empoli FC",
    "Fiorentina": "ACF Fiorentina",
    "Frosinone": "Frosinone Calcio",
    "Genoa": "Genoa CFC",
    "Hellas Verona": "Hellas Verona FC",
    "Inter": "FC Internazionale Milano",
    "Inter Milan": "FC Internazionale Milano",  # duplicate fix
    "Juventus": "Juventus FC",
    "Lazio": "SS Lazio",
    "Lecce": "US Lecce",
    "Milan": "AC Milan",
    "Monza": "AC Monza",
    "Napoli": "SSC Napoli",
    "Parma": "Parma Calcio 1913",
    "Roma": "AS Roma",
    "Salernitana": "US Salernitana 1919",
    "Sampdoria": "UC Sampdoria",
    "Sassuolo": "US Sassuolo Calcio",
    "Spezia": "Spezia Calcio",
    "Torino": "Torino FC",
    "Udinese": "Udinese Calcio",
    "Venezia": "Venezia FC",

    # ==========================================
    # BUNDESLIGA (BL1) — Germany
    # ==========================================
    "Augsburg": "FC Augsburg",
    "Bayern Munich": "FC Bayern München",  # duplicate fix
    "Bayer Leverkusen": "Bayer 04 Leverkusen",
    "Bochum": "VfL Bochum 1848",
    "Borussia Dortmund": "Borussia Dortmund",
    "Dortmund": "Borussia Dortmund",
    "Borussia Mgladbach": "Borussia Mönchengladbach",
    "Mgladbach": "Borussia Mönchengladbach",
    "Eint Frankfurt": "Eintracht Frankfurt",
    "Frankfurt": "Eintracht Frankfurt",
    "FC Cologne": "1. FC Köln",
    "Fortuna Dusseldorf": "Fortuna Düsseldorf",
    "Freiburg": "SC Freiburg",
    "Hamburg": "Hamburger SV",
    "Hannover": "Hannover 96",
    "Hertha": "Hertha BSC",
    "Hoffenheim": "TSG 1899 Hoffenheim",
    "Karlsruher": "Karlsruher SC",
    "Koln": "1. FC Köln",
    "Mainz": "1. FSV Mainz 05",
    "Nurnberg": "1. FC Nürnberg",
    "Paderborn": "SC Paderborn 07",
    "RB Leipzig": "RB Leipzig",
    "Schalke 04": "FC Schalke 04",
    "St Pauli": "FC St. Pauli",
    "Stuttgart": "VfB Stuttgart",
    "Union Berlin": "1. FC Union Berlin",
    "Werder Bremen": "SV Werder Bremen",
    "Wolfsburg": "VfL Wolfsburg",
    "Heidenheim": "1. FC Heidenheim 1846",
    "Darmstadt": "SV Darmstadt 98",
    "Holstein Kiel": "Holstein Kiel",
    "Greuther Furth": "SpVgg Greuther Fürth",

    # ==========================================
    # LIGUE 1 (FL1) — France
    # ==========================================
    "Ajaccio": "AC Ajaccio",
    "Amiens": "Amiens SC",
    "Angers": "SCO Angers",
    "Auxerre": "AJ Auxerre",
    "Bordeaux": "FC Girondins de Bordeaux",
    "Brest": "Stade Brestois 29",
    "Caen": "Stade Malherbe Caen",
    "Clermont Foot": "Clermont Foot 63",
    "Dijon": "Dijon FCO",
    "Guingamp": "En Avant Guingamp",
    "Lens": "RC Lens",
    "Lille": "LOSC Lille",
    "Lorient": "FC Lorient",
    "Lyon": "Olympique Lyonnais",
    "Marseille": "Olympique de Marseille",
    "Metz": "FC Metz",
    "Monaco": "AS Monaco FC",
    "Montpellier": "Montpellier HSC",
    "Nantes": "FC Nantes",
    "Nice": "OGC Nice",
    "Nimes": "Nîmes Olympique",
    "Paris SG": "Paris Saint-Germain FC",
    "PSG": "Paris Saint-Germain FC",
    "Reims": "Stade de Reims",
    "Rennes": "Stade Rennais FC 1901",
    "Rodez": "Rodez Aveyron Football",
    "Sainte-Étienne": "AS Saint-Étienne",
    "St Etienne": "AS Saint-Étienne",
    "Strasbourg": "RC Strasbourg Alsace",
    "Toulouse": "Toulouse FC",
    "Troyes": "ESTAC Troyes",
    "Valenciennes": "Valenciennes FC",
    "Havre": "Le Havre AC",
    "Le Havre": "Le Havre AC",

    # ==========================================
    # EREDIVISIE (DED) — Netherlands
    # ==========================================
    "Ajax": "AFC Ajax",
    "AZ": "AZ Alkmaar",
    "Excelsior": "Excelsior Rotterdam",
    "Feyenoord": "Feyenoord Rotterdam",
    "Fortuna Sittard": "Fortuna Sittard",
    "Go Ahead Eagles": "Go Ahead Eagles",
    "Groningen": "FC Groningen",
    "Heerenveen": "SC Heerenveen",
    "NEC": "NEC Nijmegen",
    "PEC Zwolle": "PEC Zwolle",
    "PSV": "PSV Eindhoven",
    "RKC Waalwijk": "RKC Waalwijk",
    "Sparta Rotterdam": "Sparta Rotterdam",
    "Twente": "FC Twente",
    "Utrecht": "FC Utrecht",
    "Vitesse": "Vitesse Arnhem",
    "Waalwijk": "RKC Waalwijk",
    "Volendam": "FC Volendam",
    "Almere City": "Almere City FC",
    "Heracles": "Heracles Almelo",
    "Den Haag": "ADO Den Haag",

    # ==========================================
    # BRASILEIRÃO (BSA) — Brazil
    # (football-data.co.uk does NOT cover BSA)
    # BSA team names from API-Football / football-data.org
    # These are used when ingesting from other sources
    # ==========================================
    "Atletico Mineiro": "Clube Atlético Mineiro",
    "Atlético Mineiro": "Clube Atlético Mineiro",
    "Atl Mineiro": "Clube Atlético Mineiro",
    "Athletico Paranaense": "Club Athletico Paranaense",
    "Athletico-PR": "Club Athletico Paranaense",
    "Bahia": "Esporte Clube Bahia",
    "Botafogo": "Botafogo de Futebol e Regatas",
    "Bragantino": "Red Bull Bragantino",
    "Corinthians": "Sport Club Corinthians Paulista",
    "Cruzeiro": "Cruzeiro Esporte Clube",
    "Cuiabá": "Cuiabá Esporte Clube",
    "Cuiaba": "Cuiabá Esporte Clube",
    "Flamengo": "CR Flamengo",
    "Fluminense": "Fluminense Football Club",
    "Fortaleza": "Fortaleza Esporte Clube",
    "Goiás": "Goiás Esporte Clube",
    "Goias": "Goiás Esporte Clube",
    "Grêmio": "Grêmio FBPA",
    "Gremio": "Grêmio FBPA",
    "Internacional": "Sport Club Internacional",
    "Juventude": "Esporte Clube Juventude",
    "Palmeiras": "SE Palmeiras",
    "Santos": "Santos FC",
    "São Paulo": "São Paulo FC",
    "Sao Paulo": "São Paulo FC",
    "Sport": "Sport Club do Recife",
    "Vasco": "CR Vasco da Gama",
    "Vitória": "Esporte Clube Vitória",
    "Vitoria": "Esporte Clube Vitória",
    "América MG": "América Futebol Clube (MG)",
    "America MG": "América Futebol Clube (MG)",
    "Coritiba": "Coritiba Football Club",
    "RB Bragantino": "Red Bull Bragantino",

    # ==========================================
    # DUPLICATES / ALTERNATE SPELLINGS
    # (already listed above but alias for safety)
    # ==========================================
    "FC Bayern München": "FC Bayern München",  # canonical self-reference
    "FC Internazionale Milano": "FC Internazionale Milano",  # canonical
    "Club Atlético de Madrid": "Club Atlético de Madrid",  # canonical
}


def normalize_team_name(raw_name: str) -> str:
    """
    Return the canonical DB team name for a football-data.co.uk raw name.
    Falls back to the raw name if no mapping is found.
    """
    if not raw_name:
        return raw_name
    raw_name = raw_name.strip()
    return TEAM_NAME_MAP.get(raw_name, raw_name)


# Competition code → football-data.co.uk division code + URL pattern
FDCO_LEAGUE_MAP = {
    "PL":  {"div": "E0",  "url_pattern": "https://www.football-data.co.uk/mmz4281/{season}/{div}.csv"},
    "PD":  {"div": "SP1", "url_pattern": "https://www.football-data.co.uk/mmz4281/{season}/{div}.csv"},
    "SA":  {"div": "I1",  "url_pattern": "https://www.football-data.co.uk/mmz4281/{season}/{div}.csv"},
    "BL1": {"div": "D1",  "url_pattern": "https://www.football-data.co.uk/mmz4281/{season}/{div}.csv"},
    "FL1": {"div": "F1",  "url_pattern": "https://www.football-data.co.uk/mmz4281/{season}/{div}.csv"},
    "DED": {"div": "N1",  "url_pattern": "https://www.football-data.co.uk/mmz4281/{season}/{div}.csv"},
    # BSA is NOT available on football-data.co.uk
}

# Target seasons to download (season code format: first 2 digits of start year + first 2 digits of end year)
# e.g. 2015-16 = "1516", 2023-24 = "2324", 2024-25 = "2425"
TARGET_SEASONS = [
    "1516",  # 2015-16
    "1617",  # 2016-17
    "1718",  # 2017-18
    "1819",  # 2018-19
    "1920",  # 2019-20
    "2021",  # 2020-21
    "2122",  # 2021-22
    "2223",  # 2022-23
    "2324",  # 2023-24
    "2425",  # 2024-25
]

# Human-readable season labels
SEASON_LABELS = {
    "1516": "2015-16",
    "1617": "2016-17",
    "1718": "2017-18",
    "1819": "2018-19",
    "1920": "2019-20",
    "2021": "2020-21",
    "2122": "2021-22",
    "2223": "2022-23",
    "2324": "2023-24",
    "2425": "2024-25",
}
