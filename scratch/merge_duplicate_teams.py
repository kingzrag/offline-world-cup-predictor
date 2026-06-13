import sys
import os
import datetime

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from models import Team, Match, Player, Standing, Prediction, Injury, Suspension, NationalTeamPlayer, NationalTeamInjury, NationalTeamSuspension
from utils.logger import logger

def clean_name(name):
    n = name.lower().strip()
    n = n.replace("-", " ")
    n = n.replace("&", "and")
    # Handle specific aliases
    aliases = {
        "usa": "united states",
        "us": "united states",
        "united states of america": "united states",
        "czechia": "czech republic",
        "congo dr": "dr congo",
        "republic of ireland": "ireland",
        "côte d'ivoire": "ivory coast",
        "cote d'ivoire": "ivory coast",
    }
    return aliases.get(n, n)

def merge_teams():
    db = SessionLocal()
    try:
        logger.info("Starting team merge and database cleanup...")
        teams = db.query(Team).all()
        
        # Group by cleaned name
        grouped = {}
        for t in teams:
            c_name = clean_name(t.name)
            grouped.setdefault(c_name, []).append(t)
            
        merge_count = 0
        
        for c_name, t_list in grouped.items():
            if len(t_list) <= 1:
                continue
                
            # We have duplicates!
            # Let's find the master team and the duplicate teams.
            # The master team should be the one that:
            # 1. Has historical matches (has the old ID, usually smaller ID)
            # 2. Or has the most players, injuries, etc.
            match_counts = []
            for t in t_list:
                cnt = db.query(Match).filter(
                    (Match.home_team_id == t.id) | (Match.away_team_id == t.id)
                ).count()
                match_counts.append((cnt, t))
                
            # Sort by match count descending, so the one with the most matches is the master
            match_counts.sort(key=lambda x: x[0], reverse=True)
            master_cnt, master_team = match_counts[0]
            duplicates = [t for cnt, t in match_counts[1:]]
            
            logger.info(f"Merging duplicates for team '{master_team.name}' (Master ID: {master_team.id}, match count: {master_cnt}):")
            for dup in duplicates:
                dup_cnt = db.query(Match).filter(
                    (Match.home_team_id == dup.id) | (Match.away_team_id == dup.id)
                ).count()
                logger.info(f"  -> Duplicate ID: {dup.id} ('{dup.name}', match count: {dup_cnt})")
                
                # Capture values to copy
                dup_api_id = dup.api_id
                dup_short_name = dup.short_name
                dup_tla = dup.tla
                dup_crest_url = dup.crest_url
                dup_transfermarkt_url = dup.transfermarkt_url
                dup_fifa_ranking = dup.fifa_ranking
                dup_squad_mv = dup.squad_market_value
                dup_mv = dup.market_value
                
                # Null out unique constraints on duplicate to avoid IntegrityError
                dup.api_id = None
                db.flush()
                
                # 1. Transfer api_id, short_name, tla, crest_url, transfermarkt_url to master if master doesn't have it
                if not master_team.api_id and dup_api_id:
                    master_team.api_id = dup_api_id
                if not master_team.short_name and dup_short_name:
                    master_team.short_name = dup_short_name
                if not master_team.tla and dup_tla:
                    master_team.tla = dup_tla
                if not master_team.crest_url and dup_crest_url:
                    master_team.crest_url = dup_crest_url
                if not master_team.transfermarkt_url and dup_transfermarkt_url:
                    master_team.transfermarkt_url = dup_transfermarkt_url
                if master_team.fifa_ranking is None and dup_fifa_ranking is not None:
                    master_team.fifa_ranking = dup_fifa_ranking
                if (master_team.squad_market_value is None or master_team.squad_market_value == 0) and dup_squad_mv:
                    master_team.squad_market_value = dup_squad_mv
                if (master_team.market_value is None or master_team.market_value == 0) and dup_mv:
                    master_team.market_value = dup_mv

                # 2. Update Match home_team_id / away_team_id references
                matches_home = db.query(Match).filter(Match.home_team_id == dup.id).all()
                for m in matches_home:
                    m.home_team_id = master_team.id
                matches_away = db.query(Match).filter(Match.away_team_id == dup.id).all()
                for m in matches_away:
                    m.away_team_id = master_team.id
                    
                # 3. Update Standing references
                standings = db.query(Standing).filter(Standing.team_id == dup.id).all()
                for s in standings:
                    # Check if master already has standing for this competition
                    existing_standing = db.query(Standing).filter_by(competition_id=s.competition_id, team_id=master_team.id).first()
                    if existing_standing:
                        # Delete the duplicate standing row
                        db.delete(s)
                    else:
                        s.team_id = master_team.id
                        
                # 4. Update Prediction references
                predictions = db.query(Prediction).filter(Prediction.predicted_winner_id == dup.id).all()
                for p in predictions:
                    p.predicted_winner_id = master_team.id
                    
                # 5. Update Player / NationalTeamPlayer references
                players = db.query(Player).filter(Player.team_id == dup.id).all()
                for p in players:
                    p.team_id = master_team.id
                nt_players = db.query(NationalTeamPlayer).filter(NationalTeamPlayer.team_id == dup.id).all()
                for p in nt_players:
                    p.team_id = master_team.id
                    
                # 6. Update Injury / NationalTeamInjury references
                injuries = db.query(Injury).filter(Injury.team_id == dup.id).all()
                for i in injuries:
                    i.team_id = master_team.id
                nt_injuries = db.query(NationalTeamInjury).filter(NationalTeamInjury.team_id == dup.id).all()
                for i in nt_injuries:
                    i.team_id = master_team.id
                    
                # 7. Update Suspension / NationalTeamSuspension references
                suspensions = db.query(Suspension).filter(Suspension.team_id == dup.id).all()
                for s in suspensions:
                    s.team_id = master_team.id
                nt_suspensions = db.query(NationalTeamSuspension).filter(NationalTeamSuspension.team_id == dup.id).all()
                for s in nt_suspensions:
                    s.team_id = master_team.id
                    
                # Flush updates
                db.flush()
                
                # Delete duplicate team
                db.delete(dup)
                merge_count += 1
                
        db.commit()
        logger.info(f"Database cleanup complete! Merged and deleted {merge_count} duplicate team entries.")
    except Exception as e:
        db.rollback()
        logger.error(f"Merge failed: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    merge_teams()
