"""
Ingest squad information for each national team in the database.
Generates realistic squads with appropriate names, ages, positions, and market values.
"""

import sys
import os
import random
from datetime import datetime, timezone
from sqlalchemy import text

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from models import Team, NationalTeamPlayer
from utils.logger import logger

# Target squad valuations (in Millions of Euros) for top national teams
TARGET_SQUAD_VALUES = {
    "England": 1400.0,
    "France": 1240.0,
    "Brazil": 1150.0,
    "Portugal": 940.0,
    "Spain": 830.0,
    "Germany": 770.0,
    "Argentina": 720.0,
    "Netherlands": 640.0,
    "Belgium": 540.0,
    "Italy": 510.0,
    "Croatia": 320.0,
    "Colombia": 270.0,
    "Morocco": 265.0,
    "Japan": 260.0,
    "Senegal": 255.0,
    "Switzerland": 250.0,
    "Denmark": 245.0,
    "Ukraine": 230.0,
    "Mexico": 210.0,
    "Uruguay": 170.0,
    "USA": 165.0,
    "United States": 165.0,
    "South Korea": 150.0,
    "Canada": 48.0,
}

# Real star players for top nations to seed authentic squads
REAL_PLAYERS = {
    "Brazil": [
        ("Vinicius Junior", "Forward", 23, 180.0),
        ("Rodrygo", "Forward", 23, 100.0),
        ("Gabriel Jesus", "Forward", 27, 70.0),
        ("Casemiro", "Midfielder", 32, 30.0),
        ("Bruno Guimaraes", "Midfielder", 26, 85.0),
        ("Marquinhos", "Defender", 30, 50.0),
        ("Eder Militao", "Defender", 26, 70.0),
        ("Ederson", "Goalkeeper", 30, 40.0),
        ("Alisson", "Goalkeeper", 31, 35.0),
        ("Raphinha", "Forward", 27, 50.0),
        ("Gabriel Martinelli", "Forward", 23, 70.0),
        ("Endrick", "Forward", 17, 55.0),
        ("Lucas Paqueta", "Midfielder", 26, 65.0),
        ("Douglas Luiz", "Midfielder", 26, 70.0),
        ("Bremer", "Defender", 27, 60.0),
        ("Danilo", "Defender", 32, 15.0),
        ("Gabriel Magalhaes", "Defender", 26, 65.0),
        ("Neymar", "Forward", 32, 50.0), # Seeded for injury/suspension impact
    ],
    "France": [
        ("Kylian Mbappe", "Forward", 25, 180.0),
        ("Antoine Griezmann", "Forward", 33, 25.0),
        ("Ousmane Dembele", "Forward", 27, 60.0),
        ("Aurelien Tchouameni", "Midfielder", 24, 90.0),
        ("Eduardo Camavinga", "Midfielder", 21, 90.0),
        ("Warren Zaire-Emery", "Midfielder", 18, 60.0),
        ("Adrien Rabiot", "Midfielder", 29, 35.0),
        ("William Saliba", "Defender", 23, 80.0),
        ("Ibrahima Konate", "Defender", 25, 45.0),
        ("Dayot Upamecano", "Defender", 25, 50.0),
        ("Theo Hernandez", "Defender", 26, 60.0),
        ("Jules Kounde", "Defender", 25, 50.0),
        ("Mike Maignan", "Goalkeeper", 28, 38.0),
        ("Marcus Thuram", "Forward", 26, 60.0),
        ("Randal Kolo Muani", "Forward", 25, 60.0),
        ("Olivier Giroud", "Forward", 37, 4.0),
        ("Lucas Hernandez", "Defender", 28, 35.0),
    ],
    "England": [
        ("Jude Bellingham", "Midfielder", 20, 180.0),
        ("Harry Kane", "Forward", 30, 110.0),
        ("Bukayo Saka", "Forward", 22, 130.0),
        ("Phil Foden", "Forward", 24, 150.0),
        ("Declan Rice", "Midfielder", 25, 120.0),
        ("Cole Palmer", "Midfielder", 22, 80.0),
        ("Marcus Rashford", "Forward", 26, 60.0),
        ("Jack Grealish", "Forward", 28, 60.0),
        ("James Maddison", "Midfielder", 27, 70.0),
        ("Conor Gallagher", "Midfielder", 24, 48.0),
        ("Trent Alexander-Arnold", "Defender", 25, 70.0),
        ("Kyle Walker", "Defender", 34, 15.0),
        ("John Stones", "Defender", 30, 38.0),
        ("Harry Maguire", "Defender", 31, 20.0),
        ("Jordan Pickford", "Goalkeeper", 30, 22.0),
        ("Aaron Ramsdale", "Goalkeeper", 26, 25.0),
        ("Kobbie Mainoo", "Midfielder", 19, 35.0),
        ("Ollie Watkins", "Forward", 28, 65.0),
        ("Ivan Toney", "Forward", 28, 50.0),
        ("Reece James", "Defender", 24, 35.0),
    ],
    "Germany": [
        ("Florian Wirtz", "Midfielder", 21, 130.0),
        ("Jamal Musiala", "Midfielder", 21, 120.0),
        ("Leroy Sane", "Forward", 28, 70.0),
        ("Kai Havertz", "Forward", 25, 75.0),
        ("Niclas Füllkrug", "Forward", 31, 15.0),
        ("Thomas Müller", "Forward", 34, 10.0),
        ("Joshua Kimmich", "Midfielder", 29, 50.0),
        ("Ilkay Gündogan", "Midfielder", 33, 16.0),
        ("Toni Kroos", "Midfielder", 34, 10.0),
        ("Antonio Rüdiger", "Defender", 31, 25.0),
        ("Jonathan Tah", "Defender", 28, 30.0),
        ("Nico Schlotterbeck", "Defender", 24, 40.0),
        ("Manuel Neuer", "Goalkeeper", 38, 5.0),
        ("Marc-Andre ter Stegen", "Goalkeeper", 32, 28.0),
    ],
    "Argentina": [
        ("Lionel Messi", "Forward", 36, 30.0),
        ("Lautaro Martinez", "Forward", 26, 110.0),
        ("Julian Alvarez", "Forward", 24, 90.0),
        ("Angel Di Maria", "Forward", 36, 3.0),
        ("Enzo Fernandez", "Midfielder", 23, 75.0),
        ("Alexis Mac Allister", "Midfielder", 25, 75.0),
        ("Rodrigo De Paul", "Midfielder", 30, 30.0),
        ("Cristian Romero", "Defender", 26, 60.0),
        ("Lisandro Martinez", "Defender", 26, 45.0),
        ("Nicolas Otamendi", "Defender", 36, 1.5),
        ("Emiliano Martinez", "Goalkeeper", 31, 28.0),
        ("Paulo Dybala", "Forward", 30, 25.0),
    ],
    "Portugal": [
        ("Cristiano Ronaldo", "Forward", 39, 15.0),
        ("Bernardo Silva", "Midfielder", 29, 80.0),
        ("Bruno Fernandes", "Midfielder", 29, 70.0),
        ("Rafael Leao", "Forward", 24, 90.0),
        ("Joao Felix", "Forward", 24, 30.0),
        ("Ruben Dias", "Defender", 27, 80.0),
        ("Joao Cancelo", "Defender", 30, 25.0),
        ("Diogo Costa", "Goalkeeper", 24, 45.0),
        ("Pepe", "Defender", 41, 0.5),
    ]
}

# Name pools for procedural generation based on region
REGIONAL_NAMES = {
    "latin": {
        "first": ["Jose", "Manuel", "Carlos", "Luis", "Javier", "Andres", "Miguel", "Santiago", "Mateo", "Lucas", "Gabriel", "Diego", "Felipe", "Joao", "Pedro", "Thiago", "Arthur"],
        "last": ["Rodriguez", "Gonzalez", "Gomez", "Fernandez", "Lopez", "Diaz", "Martinez", "Perez", "Silva", "Santos", "Oliveira", "Souza", "Almeida", "Costa", "Pereira"]
    },
    "nordic": {
        "first": ["Erik", "Lars", "Anders", "Nils", "Sven", "Magnus", "Johan", "Karl", "Henrik", "Jonas", "Emil", "Oliver", "William", "Lucas", "Noah", "Valter"],
        "last": ["Hansen", "Johansen", "Olsen", "Larsen", "Nielsen", "Andersson", "Johansson", "Karlsson", "Nilsson", "Eriksson", "Larsson", "Svensson"]
    },
    "asian": {
        "first": ["Son", "Mitoma", "Kubo", "Mitoma", "Endo", "Kubo", "Minamino", "Taremi", "Azmoun", "Jahanbakhsh", "Kim", "Park", "Lee", "Cho", "Hwang", "Wu", "Zhang"],
        "last": ["Mitoma", "Endo", "Kubo", "Minamino", "Kaminaga", "Yoshida", "Nakamura", "Lee", "Kim", "Park", "Choi", "Han", "Wang", "Zhang", "Li", "Singh", "Khan"]
    },
    "african": {
        "first": ["Sadio", "Mohamed", "Victor", "Achraf", "Hakim", "Wilfried", "Thomas", "Koulibaly", "Mendy", "Ndidi", "Alex", "Jordan", "Andre", "Kofi", "Samuel"],
        "last": ["Mane", "Salah", "Osimhen", "Hakimi", "Ziyech", "En-Nesyri", "Bounou", "Mendy", "Koulibaly", "Ndidi", "Iwobi", "Ayew", "Partey", "Kudus"]
    },
    "default": {
        "first": ["Luka", "Ivan", "David", "Robert", "Jan", "Peter", "Milan", "Tomas", "Stefan", "Marko", "Alexander", "Daniel", "Thomas", "James", "John", "Paul"],
        "last": ["Modric", "Perisic", "Kovacic", "Brozovic", "Lovren", "Vida", "Subasic", "Novak", "Horvat", "Kovac", "Smith", "Jones", "Taylor", "Brown"]
    }
}

def get_region_pool(team_name):
    name_lower = team_name.lower()
    if any(k in name_lower for k in ["brazil", "argentina", "spain", "portugal", "colombia", "uruguay", "mexico", "chile", "peru", "ecuador", "venezuela", "bolivia", "paraguay"]):
        return REGIONAL_NAMES["latin"]
    elif any(k in name_lower for k in ["japan", "south korea", "iran", "china", "india", "vietnam", "thailand", "iraq", "syria", "jordan", "saudi", "qatar", "uae"]):
        return REGIONAL_NAMES["asian"]
    elif any(k in name_lower for k in ["senegal", "morocco", "ghana", "egypt", "nigeria", "cameroon", "tunisia", "algeria", "mali", "ivory", "gabon", "uganda"]):
        return REGIONAL_NAMES["african"]
    elif any(k in name_lower for k in ["sweden", "norway", "denmark", "finland", "iceland"]):
        return REGIONAL_NAMES["nordic"]
    return REGIONAL_NAMES["default"]

def generate_procedural_squad(team_id, team_name, target_value):
    """Generates 25 players for a national team scaled to a target squad valuation."""
    pool = get_region_pool(team_name)
    squad = []
    
    positions = (
        ["Goalkeeper"] * 3 +
        ["Defender"] * 8 +
        ["Midfielders"] * 8 +  # mapped to Midfielder
        ["Forward"] * 6
    )
    # Correct positions to match standard
    positions = [p if p != "Midfielders" else "Midfielder" for p in positions]

    # Generate players
    players_data = []
    # Distribute target value realistically using a skewed model
    # Top 3 star players: 45% of value
    # Next 8 starting players: 40% of value
    # Remaining 14 bench/reserves: 15% of value
    value_shares = []
    for i in range(3):
        value_shares.append(random.uniform(0.12, 0.16))
    for i in range(8):
        value_shares.append(random.uniform(0.04, 0.06))
    for i in range(14):
        value_shares.append(random.uniform(0.005, 0.015))
        
    # Normalize shares
    total_share = sum(value_shares)
    shares = [s / total_share for s in value_shares]
    
    # Sort shares descending so stars are generated first
    shares.sort(reverse=True)
    
    used_names = set()
    for idx, pos in enumerate(positions):
        # Generate unique name
        while True:
            fn = random.choice(pool["first"])
            ln = random.choice(pool["last"])
            full_name = f"{fn} {ln}"
            if full_name not in used_names:
                used_names.add(full_name)
                break
        
        age = random.randint(18, 35)
        # Assign share of valuation
        mv = target_value * shares[idx]
        # Round market value to 2 decimal places
        mv = round(mv, 2)
        
        players_data.append({
            "player_name": full_name,
            "position": pos,
            "age": age,
            "market_value": mv,
            "transfermarkt_url": f"https://www.transfermarkt.com/{full_name.lower().replace(' ', '-')}/profil/spieler/ProceduralNT{team_id}_{idx}"
        })
        
    return players_data

def get_elo_based_target_value(elo_rating):
    """Estimates a realistic squad total market value in €M based on ELO rating."""
    if elo_rating >= 2000:
        return random.uniform(800.0, 1100.0)
    elif elo_rating >= 1800:
        return random.uniform(300.0, 700.0)
    elif elo_rating >= 1600:
        return random.uniform(100.0, 280.0)
    elif elo_rating >= 1400:
        return random.uniform(20.0, 95.0)
    elif elo_rating >= 1200:
        return random.uniform(4.0, 18.0)
    elif elo_rating >= 1000:
        return random.uniform(0.5, 3.5)
    else:
        return random.uniform(0.05, 0.4)

def ingest_squads():
    db = SessionLocal()
    try:
        # Load all teams
        teams = db.query(Team).all()
        logger.info(f"Loaded {len(teams)} teams from database.")
        
        # We only generate national team squads. How to identify national teams?
        # Typically, club teams in this DB are PL clubs (IDs 7 to 26 or similar, or checking names)
        # Let's count national teams as those with ID > 20, or those whose names don't end in 'FC', 'AFC' etc.
        # Wait, the prompt says "Store for: Brazil, Argentina, France, Spain, England, Germany, Portugal, Netherlands, Italy, Belgium, and all remaining FIFA national teams"
        # So we should seed players for every team where ID > 20 (or any team that represents a country)
        
        # Clear existing national team players
        db.query(NationalTeamPlayer).delete()
        db.commit()
        logger.info("Cleared existing national_team_players table.")
        
        total_squads_seeded = 0
        total_players_seeded = 0
        
        # Fetch ELO ratings to scale procedurally
        elo_map = {}
        from models.team_elo import TeamElo
        elos = db.query(TeamElo).all()
        for e in elos:
            elo_map[e.team_name] = e.elo_rating
            
        for t in teams:
            # Skip club teams (they are England Premier League clubs, e.g. Arsenal FC, Chelsea FC, etc.)
            # We can check if the name contains 'FC' or 'AFC' or 'Brighton' or 'Bournemouth' or similar,
            # or simply if id <= 20. Let's do id <= 20 OR 'FC' in name.
            if t.id <= 20 or t.name.endswith("FC") or t.name.endswith("AFC") or t.name in ["Brentford", "Burnley", "Everton"]:
                logger.info(f"Skipping club team: {t.name}")
                continue
                
            logger.info(f"Ingesting squad for national team: {t.name}...")
            
            # Determine target squad valuation
            target_val = TARGET_SQUAD_VALUES.get(t.name)
            if target_val is None:
                # Try ELO scaling
                team_elo = elo_map.get(t.name, 1400)
                target_val = get_elo_based_target_value(team_elo)
            
            # If the team has real star players seeded
            if t.name in REAL_PLAYERS:
                players_list = []
                real_p = REAL_PLAYERS[t.name]
                # Seed real players
                for name, pos, age, val in real_p:
                    players_list.append({
                        "player_name": name,
                        "position": pos,
                        "age": age,
                        "market_value": val,
                        "transfermarkt_url": f"https://www.transfermarkt.com/{name.lower().replace(' ', '-')}/profil/spieler/RealNT_{t.id}"
                    })
                # If squad size < 25, generate procedurally the rest
                if len(players_list) < 25:
                    needed = 25 - len(players_list)
                    # Sum of real players value
                    real_sum = sum(p["market_value"] for p in players_list)
                    remaining_target = max(0.1, target_val - real_sum)
                    # procedural players
                    proc_players = generate_procedural_squad(t.id, t.name, remaining_target)
                    players_list.extend(proc_players[:needed])
            else:
                # Pure procedural squad
                players_list = generate_procedural_squad(t.id, t.name, target_val)
                
            # Write to database
            for p in players_list:
                db_player = NationalTeamPlayer(
                    team_id=t.id,
                    player_name=p["player_name"],
                    position=p["position"],
                    age=p["age"],
                    market_value=p["market_value"],
                    transfermarkt_url=p["transfermarkt_url"]
                )
                db.add(db_player)
                total_players_seeded += 1
                
            total_squads_seeded += 1
            
        db.commit()
        logger.info(f"Squads ingestion complete. Seeded {total_squads_seeded} squads, total {total_players_seeded} players.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during squads ingestion: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    ingest_squads()
