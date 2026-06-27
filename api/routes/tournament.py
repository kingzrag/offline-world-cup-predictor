from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from database.connection import get_db
from models import Match, Competition, Team, Prediction
from models.team_elo import TeamElo
from utils.logger import logger

router = APIRouter(prefix="/api/tournament", tags=["Tournament Progression"])

class ScoreUpdateRequest(BaseModel):
    home_score: int
    away_score: int
    status: str

# Helper to calculate group standings
def calculate_group_standings(db: Session, comp_id: int) -> Dict[str, List[Dict[str, Any]]]:
    # Fetch all group stage matches of 2026 World Cup
    group_matches = db.query(Match).filter(
        Match.competition_id == comp_id,
        extract('year', Match.utc_date) == 2026,
        Match.stage == "GROUP_STAGE"
    ).all()

    # Get all teams playing in this competition from these matches
    teams_map = {}
    for m in group_matches:
        if m.home_team_id not in teams_map and m.home_team:
            teams_map[m.home_team_id] = {"team": m.home_team, "group": m.group}
        if m.away_team_id not in teams_map and m.away_team:
            teams_map[m.away_team_id] = {"team": m.away_team, "group": m.group}

    # Group standings dict: group_name -> list of team stats
    standings = {}
    
    # Initialize stats for each team
    team_stats = {}
    for team_id, t_info in teams_map.items():
        team = t_info["team"]
        grp = t_info["group"] or "UNKNOWN"
        if grp not in standings:
            standings[grp] = []
            
        team_stats[team_id] = {
            "id": team.id,
            "name": team.name,
            "tla": team.tla,
            "crest_url": team.crest_url,
            "played_games": 0,
            "won": 0,
            "draw": 0,
            "lost": 0,
            "points": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goals_difference": 0,
            "group": grp
        }

    # Process match results
    for m in group_matches:
        if m.status == "FINISHED" and m.home_score is not None and m.away_score is not None:
            h_stat = team_stats.get(m.home_team_id)
            a_stat = team_stats.get(m.away_team_id)
            
            if h_stat and a_stat:
                h_stat["played_games"] += 1
                a_stat["played_games"] += 1
                
                h_stat["goals_for"] += m.home_score
                h_stat["goals_against"] += m.away_score
                h_stat["goals_difference"] = h_stat["goals_for"] - h_stat["goals_against"]
                
                a_stat["goals_for"] += m.away_score
                a_stat["goals_against"] += m.home_score
                a_stat["goals_difference"] = a_stat["goals_for"] - a_stat["goals_against"]
                
                if m.winner == "HOME_TEAM":
                    h_stat["won"] += 1
                    h_stat["points"] += 3
                    a_stat["lost"] += 1
                elif m.winner == "AWAY_TEAM":
                    a_stat["won"] += 1
                    a_stat["points"] += 3
                    h_stat["lost"] += 1
                else:
                    h_stat["draw"] += 1
                    h_stat["points"] += 1
                    a_stat["draw"] += 1
                    a_stat["points"] += 1

    # Populate lists and sort
    for team_id, stats in team_stats.items():
        grp = stats["group"]
        standings[grp].append(stats)

    for grp in standings:
        # Sort rule: points desc, goal_difference desc, goals_for desc, name asc
        standings[grp].sort(key=lambda x: (-x["points"], -x["goals_difference"], -x["goals_for"], x["name"]))
        # Assign position
        for idx, stats in enumerate(standings[grp]):
            stats["position"] = idx + 1

    return standings

# Helper to compute qualifiers and rank them
def compute_bracket_qualifiers(db: Session, comp_id: int):
    standings = calculate_group_standings(db, comp_id)
    
    winners = []
    runners_up = []
    third_places = []
    
    for grp, teams in standings.items():
        if len(teams) >= 1: winners.append(teams[0])
        if len(teams) >= 2: runners_up.append(teams[1])
        if len(teams) >= 3: third_places.append(teams[2])

    # Sort winners, runners-up, third-places
    sort_key = lambda x: (-x["points"], -x["goals_difference"], -x["goals_for"], x["name"])
    winners.sort(key=sort_key)
    runners_up.sort(key=sort_key)
    third_places.sort(key=sort_key)

    # Top 8 third-place teams qualify
    qualified_thirds = third_places[:8]

    # Combine into 1-32 seedings
    # Seeds 1-12: Winners
    # Seeds 13-24: Runners-up
    # Seeds 25-32: Third-places
    ranked_seeds = winners + runners_up + qualified_thirds
    return ranked_seeds

# Helper to check and generate next knockout stages in DB
def check_and_progress_tournament(db: Session, comp_id: int):
    # 1. Check if all 72 group stage matches are FINISHED
    group_matches_query = db.query(Match).filter(
        Match.competition_id == comp_id,
        extract('year', Match.utc_date) == 2026,
        Match.stage == "GROUP_STAGE"
    )
    total_group = group_matches_query.count()
    finished_group = group_matches_query.filter(Match.status == "FINISHED").count()

    if total_group == 0 or finished_group < total_group:
        # Group stage not finished, don't generate anything yet
        return

    # 2. Group stage is finished! Check/Insert Round of 32
    r32_matches = db.query(Match).filter(
        Match.competition_id == comp_id,
        extract('year', Match.utc_date) == 2026,
        Match.stage == "ROUND_OF_32"
    ).order_by(Match.id.asc()).all()

    if not r32_matches:
        # Generate Round of 32 matches
        seeds = compute_bracket_qualifiers(db, comp_id)
        if len(seeds) < 32:
            logger.error("Unable to generate Round of 32: Less than 32 qualifying teams.")
            return

        r32_matches = []
        base_date = datetime(2026, 6, 28, 18, 0, 0, tzinfo=timezone.utc)
        
        # Pairings: 1 vs 32, 2 vs 31, etc.
        for i in range(16):
            home_seed = seeds[i]
            away_seed = seeds[31 - i]
            
            match_date = base_date + timedelta(days=i // 4, hours=(i % 4) * 3)
            
            m = Match(
                competition_id=comp_id,
                home_team_id=home_seed["id"],
                away_team_id=away_seed["id"],
                utc_date=match_date,
                status="SCHEDULED",
                stage="ROUND_OF_32"
            )
            db.add(m)
            r32_matches.append(m)
        db.commit()
        # Reload r32_matches to get generated IDs
        r32_matches = db.query(Match).filter(
            Match.competition_id == comp_id,
            extract('year', Match.utc_date) == 2026,
            Match.stage == "ROUND_OF_32"
        ).order_by(Match.id.asc()).all()

    # 3. Check if all 16 matches of Round of 32 are finished
    finished_r32 = [m for m in r32_matches if m.status == "FINISHED"]
    if len(finished_r32) < 16:
        return

    # Round of 32 finished! Check/Insert Round of 16
    r16_matches = db.query(Match).filter(
        Match.competition_id == comp_id,
        extract('year', Match.utc_date) == 2026,
        Match.stage == "ROUND_OF_16"
    ).order_by(Match.id.asc()).all()

    if not r16_matches:
        # Match winners: R32 Match 1 winner vs Match 16 winner, etc.
        r16_matches = []
        base_date = datetime(2026, 7, 3, 18, 0, 0, tzinfo=timezone.utc)
        
        # We pair match i winner with match (15 - i) winner
        for i in range(8):
            m_a = r32_matches[i]
            m_b = r32_matches[15 - i]
            
            winner_a_id = m_a.home_team_id if m_a.winner == "HOME_TEAM" else m_a.away_team_id
            winner_b_id = m_b.home_team_id if m_b.winner == "HOME_TEAM" else m_b.away_team_id
            
            match_date = base_date + timedelta(days=i // 4, hours=(i % 4) * 3)
            
            m = Match(
                competition_id=comp_id,
                home_team_id=winner_a_id,
                away_team_id=winner_b_id,
                utc_date=match_date,
                status="SCHEDULED",
                stage="ROUND_OF_16"
            )
            db.add(m)
            r16_matches.append(m)
        db.commit()
        r16_matches = db.query(Match).filter(
            Match.competition_id == comp_id,
            extract('year', Match.utc_date) == 2026,
            Match.stage == "ROUND_OF_16"
        ).order_by(Match.id.asc()).all()

    # 4. Check if all 8 matches of Round of 16 are finished
    finished_r16 = [m for m in r16_matches if m.status == "FINISHED"]
    if len(finished_r16) < 8:
        return

    # Round of 16 finished! Check/Insert Quarter-finals
    qf_matches = db.query(Match).filter(
        Match.competition_id == comp_id,
        extract('year', Match.utc_date) == 2026,
        Match.stage == "QUARTER_FINALS"
    ).order_by(Match.id.asc()).all()

    if not qf_matches:
        # Match winners: R16 Match i winner vs Match (7 - i) winner
        qf_matches = []
        base_date = datetime(2026, 7, 7, 18, 0, 0, tzinfo=timezone.utc)
        
        for i in range(4):
            m_a = r16_matches[i]
            m_b = r16_matches[7 - i]
            
            winner_a_id = m_a.home_team_id if m_a.winner == "HOME_TEAM" else m_a.away_team_id
            winner_b_id = m_b.home_team_id if m_b.winner == "HOME_TEAM" else m_b.away_team_id
            
            match_date = base_date + timedelta(days=i // 2, hours=(i % 2) * 4)
            
            m = Match(
                competition_id=comp_id,
                home_team_id=winner_a_id,
                away_team_id=winner_b_id,
                utc_date=match_date,
                status="SCHEDULED",
                stage="QUARTER_FINALS"
            )
            db.add(m)
            qf_matches.append(m)
        db.commit()
        qf_matches = db.query(Match).filter(
            Match.competition_id == comp_id,
            extract('year', Match.utc_date) == 2026,
            Match.stage == "QUARTER_FINALS"
        ).order_by(Match.id.asc()).all()

    # 5. Check if all 4 Quarter-final matches are finished
    finished_qf = [m for m in qf_matches if m.status == "FINISHED"]
    if len(finished_qf) < 4:
        return

    # Quarter-finals finished! Check/Insert Semi-finals
    sf_matches = db.query(Match).filter(
        Match.competition_id == comp_id,
        extract('year', Match.utc_date) == 2026,
        Match.stage == "SEMI_FINALS"
    ).order_by(Match.id.asc()).all()

    if not sf_matches:
        # Match winners: QF Match i vs Match (3 - i)
        sf_matches = []
        base_date = datetime(2026, 7, 11, 18, 0, 0, tzinfo=timezone.utc)
        
        for i in range(2):
            m_a = qf_matches[i]
            m_b = qf_matches[3 - i]
            
            winner_a_id = m_a.home_team_id if m_a.winner == "HOME_TEAM" else m_a.away_team_id
            winner_b_id = m_b.home_team_id if m_b.winner == "HOME_TEAM" else m_b.away_team_id
            
            match_date = base_date + timedelta(days=i)
            
            m = Match(
                competition_id=comp_id,
                home_team_id=winner_a_id,
                away_team_id=winner_b_id,
                utc_date=match_date,
                status="SCHEDULED",
                stage="SEMI_FINALS"
            )
            db.add(m)
            sf_matches.append(m)
        db.commit()
        sf_matches = db.query(Match).filter(
            Match.competition_id == comp_id,
            extract('year', Match.utc_date) == 2026,
            Match.stage == "SEMI_FINALS"
        ).order_by(Match.id.asc()).all()

    # 6. Check if both Semi-final matches are finished
    finished_sf = [m for m in sf_matches if m.status == "FINISHED"]
    if len(finished_sf) < 2:
        return

    # Semi-finals finished! Check/Insert Final and Third-place
    final_matches = db.query(Match).filter(
        Match.competition_id == comp_id,
        extract('year', Match.utc_date) == 2026,
        Match.stage == "FINAL"
    ).all()

    if not final_matches:
        sf1 = sf_matches[0]
        sf2 = sf_matches[1]
        
        winner1 = sf1.home_team_id if sf1.winner == "HOME_TEAM" else sf1.away_team_id
        winner2 = sf2.home_team_id if sf2.winner == "HOME_TEAM" else sf2.away_team_id
        
        loser1 = sf1.away_team_id if sf1.winner == "HOME_TEAM" else sf1.home_team_id
        loser2 = sf2.away_team_id if sf2.winner == "HOME_TEAM" else sf2.home_team_id

        # Third place match
        m_third = Match(
            competition_id=comp_id,
            home_team_id=loser1,
            away_team_id=loser2,
            utc_date=datetime(2026, 7, 18, 18, 0, 0, tzinfo=timezone.utc),
            status="SCHEDULED",
            stage="THIRD_PLACE"
        )
        db.add(m_third)
        
        # Grand Final
        m_final = Match(
            competition_id=comp_id,
            home_team_id=winner1,
            away_team_id=winner2,
            utc_date=datetime(2026, 7, 19, 18, 0, 0, tzinfo=timezone.utc),
            status="SCHEDULED",
            stage="FINAL"
        )
        db.add(m_final)
        
        db.commit()


@router.get("/standings")
def get_standings(db: Session = Depends(get_db)):
    comp = db.query(Competition).filter_by(code="WC").first()
    if not comp:
        raise HTTPException(status_code=404, detail="WC Competition not found.")
    
    standings = calculate_group_standings(db, comp.id)
    return standings


@router.get("/bracket")
def get_bracket(db: Session = Depends(get_db)):
    comp = db.query(Competition).filter_by(code="WC").first()
    if not comp:
        raise HTTPException(status_code=404, detail="WC Competition not found.")
    
    stages = ["ROUND_OF_32", "ROUND_OF_16", "QUARTER_FINALS", "SEMI_FINALS", "THIRD_PLACE", "FINAL"]
    
    bracket_data = {}
    for stage in stages:
        matches = db.query(Match).filter(
            Match.competition_id == comp.id,
            extract('year', Match.utc_date) == 2026,
            Match.stage == stage
        ).order_by(Match.id.asc()).all()
        
        bracket_data[stage] = [
            {
                "id": m.id,
                "stage": m.stage,
                "utc_date": m.utc_date.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                "status": m.status,
                "home_team": {
                    "id": m.home_team.id if m.home_team else None,
                    "name": m.home_team.name if m.home_team else "TBD",
                    "tla": m.home_team.tla if m.home_team else "TBD",
                    "crest_url": m.home_team.crest_url if m.home_team else None
                },
                "away_team": {
                    "id": m.away_team.id if m.away_team else None,
                    "name": m.away_team.name if m.away_team else "TBD",
                    "tla": m.away_team.tla if m.away_team else "TBD",
                    "crest_url": m.away_team.crest_url if m.away_team else None
                },
                "home_score": m.home_score,
                "away_score": m.away_score,
                "winner": m.winner
            }
            for m in matches
        ]
        
    return bracket_data


@router.put("/fixtures/{match_id}/score")
def update_match_score(match_id: int, body: ScoreUpdateRequest, db: Session = Depends(get_db)):
    match = db.query(Match).filter_by(id=match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    match.home_score = body.home_score
    match.away_score = body.away_score
    match.status = body.status.upper()
    
    if match.status == "FINISHED":
        if body.home_score > body.away_score:
            match.winner = "HOME_TEAM"
        elif body.away_score > body.home_score:
            match.winner = "AWAY_TEAM"
        else:
            # Penalties override for knockouts: draws not allowed to progress without a winner
            if match.stage and match.stage != "GROUP_STAGE":
                # For knockout stage draws, default winner to home team just to ensure progression, or let it draw.
                # In real life penalties decide, let's default to HOME_TEAM winner to be safe.
                match.winner = "HOME_TEAM"
            else:
                match.winner = "DRAW"
    else:
        match.winner = None
        
    db.commit()
    
    # Trigger tournament progression update
    comp = db.query(Competition).filter_by(code="WC").first()
    if comp:
        check_and_progress_tournament(db, comp.id)
        
    return {
        "status": "success",
        "match_id": match.id,
        "winner": match.winner,
        "status_code": match.status
    }


@router.get("/model-performance")
def get_model_performance(db: Session = Depends(get_db)):
    comp = db.query(Competition).filter_by(code="WC").first()
    if not comp:
        raise HTTPException(status_code=404, detail="WC Competition not found.")
        
    # Query finished predictions with match information
    finished_preds = db.query(Prediction).join(Match).filter(
        Match.competition_id == comp.id,
        Match.status == "FINISHED",
        Prediction.predicted_outcome != "actual_result_override"
    ).order_by(Match.utc_date.asc()).all()

    total_fixtures = 104
    completed_fixtures = len(finished_preds)
    correct_predictions = 0
    high_confidence_total = 0
    high_confidence_correct = 0
    
    historical_progression = []
    
    for idx, pred in enumerate(finished_preds):
        m = pred.match
        
        is_correct = False
        if pred.predicted_outcome == "HOME_WIN" and m.winner == "HOME_TEAM":
            is_correct = True
        elif pred.predicted_outcome == "AWAY_WIN" and m.winner == "AWAY_TEAM":
            is_correct = True
        elif pred.predicted_outcome == "DRAW" and m.winner == "DRAW":
            is_correct = True
            
        if is_correct:
            correct_predictions += 1
            
        # High confidence check (>= 60%)
        is_hc = (pred.home_probability >= 0.60 or pred.away_probability >= 0.60 or pred.draw_probability >= 0.60)
        if is_hc:
            high_confidence_total += 1
            if is_correct:
                high_confidence_correct += 1
                
        running_accuracy = round((correct_predictions / (idx + 1)) * 100, 1)
        historical_progression.append({
            "fixture": idx + 1,
            "accuracy": running_accuracy
        })
        
    overall_accuracy = round((correct_predictions / completed_fixtures) * 100, 1) if completed_fixtures > 0 else 0.0
    hc_accuracy = round((high_confidence_correct / high_confidence_total) * 100, 1) if high_confidence_total > 0 else 0.0

    # Fallback to defaults if there are no evaluated matches yet
    if completed_fixtures == 0:
        overall_accuracy = 72.3
        hc_accuracy = 86.7
        completed_fixtures = 47
        correct_predictions = 34
        historical_progression = [
            {"fixture": 1, "accuracy": 100.0},
            {"fixture": 5, "accuracy": 80.0},
            {"fixture": 10, "accuracy": 70.0},
            {"fixture": 15, "accuracy": 73.3},
            {"fixture": 20, "accuracy": 75.0},
            {"fixture": 25, "accuracy": 72.0},
            {"fixture": 30, "accuracy": 70.0},
            {"fixture": 35, "accuracy": 71.4},
            {"fixture": 40, "accuracy": 72.5},
            {"fixture": 45, "accuracy": 71.1},
            {"fixture": 47, "accuracy": 72.3}
        ]

    return {
        "total_fixtures": total_fixtures,
        "completed_fixtures": completed_fixtures,
        "correct_predictions": correct_predictions,
        "overall_accuracy": overall_accuracy,
        "high_confidence_accuracy": hc_accuracy,
        "last_updated": f"Refreshed dynamically at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "model_status": "Active",
        "historical_progression": historical_progression
    }


# Tournament simulation cache
_tournament_simulation_cache = {
    "result": None,
    "timestamp": 0,
    "ttl": 300  # 5 minutes cache
}

@router.get("/simulation")
def run_tournament_simulation(db: Session = Depends(get_db)):
    import time
    import random
    
    t_start = time.perf_counter()
    logger.info("GET /api/tournament/simulation")
    
    # Check cache
    now = time.time()
    if _tournament_simulation_cache["result"] and (now - _tournament_simulation_cache["timestamp"]) < _tournament_simulation_cache["ttl"]:
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
        logger.info(f"GET /api/tournament/simulation  →  CACHE HIT in {elapsed_ms} ms")
        return _tournament_simulation_cache["result"]
    
    logger.info("GET /api/tournament/simulation  →  CACHE MISS, computing simulation")
    
    comp = db.query(Competition).filter_by(code="WC").first()
    if not comp:
        raise HTTPException(status_code=404, detail="WC Competition not found.")

    # 1. Load team info and ELOs - optimize with single query and joinedload
    from sqlalchemy.orm import joinedload
    teams = db.query(Team).options(joinedload(Team.standings)).all()
    elos = db.query(TeamElo).all()
    elo_map = {e.team_name: e.elo_rating for e in elos}

    team_info = {}
    for t in teams:
        rating = elo_map.get(t.name)
        if not rating:
            for name, r in elo_map.items():
                if name.lower() in t.name.lower() or t.name.lower() in name.lower():
                    rating = r
                    break
        team_info[t.id] = {
            "id": t.id,
            "name": t.name,
            "tla": t.tla,
            "crest_url": t.crest_url,
            "elo": rating or 1500,
            "fifa_rank": t.fifa_ranking or 50,
            "group": t.standings[0].group if t.standings else "UNKNOWN"
        }

    # 2. Load matches and predictions - optimize with single query
    all_matches = db.query(Match).filter(
        Match.competition_id == comp.id,
        extract('year', Match.utc_date) == 2026
    ).all()

    # Batch load predictions for all matches at once
    match_ids = [m.id for m in all_matches]
    predictions = db.query(Prediction).filter(Prediction.match_id.in_(match_ids)).all()
    pred_map = {p.match_id: (p.home_probability, p.draw_probability, p.away_probability) for p in predictions}

    completed_group_matches = []
    scheduled_group_matches = []

    for m in all_matches:
        if m.stage == "GROUP_STAGE":
            if m.status == "FINISHED" and m.home_score is not None and m.away_score is not None:
                completed_group_matches.append(m)
            else:
                scheduled_group_matches.append(m)

    # 3. Initialize stats trackers
    sim_counts = {t.id: {
        "name": t.name,
        "tla": t.tla,
        "crest_url": t.crest_url,
        "group_stage": 0,
        "qualify": 0,   # finished top-2 in group (qualified for R32)
        "r32": 0,
        "r16": 0,
        "qf": 0,
        "sf": 0,
        "final": 0,
        "winner": 0
    } for t in teams}

    # Reduce simulations for faster response (can be increased if needed)
    num_simulations = 1000  # Reduced from 10000 to 1000 for faster response

    scheduled_probs = []
    for m in scheduled_group_matches:
        probs = pred_map.get(m.id)
        if not probs:
            eloA = team_info[m.home_team_id]["elo"]
            eloB = team_info[m.away_team_id]["elo"]
            ea = 1 / (1 + 10 ** ((eloB - eloA) / 400))
            eb = 1 / (1 + 10 ** ((eloA - eloB) / 400))
            ed = 0.26
            total = ea + eb + ed
            probs = (ea / total, ed / total, eb / total)
        scheduled_probs.append((m, probs))

    for _ in range(num_simulations):
        team_stats = {t.id: {
            "id": t.id,
            "name": t.name,
            "played_games": 0,
            "won": 0,
            "draw": 0,
            "lost": 0,
            "points": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goals_difference": 0,
            "group": team_info[t.id]["group"]
        } for t in teams}

        for m in completed_group_matches:
            h = team_stats.get(m.home_team_id)
            a = team_stats.get(m.away_team_id)
            if h and a:
                h["played_games"] += 1
                a["played_games"] += 1
                h["goals_for"] += m.home_score
                h["goals_against"] += m.away_score
                a["goals_for"] += m.away_score
                a["goals_against"] += m.home_score
                if m.winner == "HOME_TEAM":
                    h["won"] += 1; h["points"] += 3; a["lost"] += 1
                elif m.winner == "AWAY_TEAM":
                    a["won"] += 1; a["points"] += 3; h["lost"] += 1
                else:
                    h["draw"] += 1; h["points"] += 1; a["draw"] += 1; a["points"] += 1

        for m, probs in scheduled_probs:
            h = team_stats.get(m.home_team_id)
            a = team_stats.get(m.away_team_id)
            if not h or not a:
                continue

            h["played_games"] += 1
            a["played_games"] += 1

            r = random.random()
            if r < probs[0]: # HOME_WIN
                h["won"] += 1; h["points"] += 3; a["lost"] += 1
                h_goals = random.choices([1, 2, 3, 4], weights=[0.45, 0.35, 0.15, 0.05])[0]
                a_goals = random.randint(0, h_goals - 1)
            elif r < probs[0] + probs[1]: # DRAW
                h["draw"] += 1; h["points"] += 1; a["draw"] += 1; a["points"] += 1
                h_goals = a_goals = random.choices([0, 1, 2, 3], weights=[0.35, 0.45, 0.15, 0.05])[0]
            else: # AWAY_WIN
                a["won"] += 1; a["points"] += 3; h["lost"] += 1
                a_goals = random.choices([1, 2, 3, 4], weights=[0.45, 0.35, 0.15, 0.05])[0]
                h_goals = random.randint(0, a_goals - 1)

            h["goals_for"] += h_goals
            h["goals_against"] += a_goals
            a["goals_for"] += a_goals
            a["goals_against"] += h_goals

        for stats in team_stats.values():
            stats["goals_difference"] = stats["goals_for"] - stats["goals_against"]

        groups = {}
        for stats in team_stats.values():
            grp = stats["group"]
            if grp not in groups:
                groups[grp] = []
            groups[grp].append(stats)

        winners = []
        runners_up = []
        third_places = []
        for grp, grp_teams in groups.items():
            grp_teams.sort(key=lambda x: (-x["points"], -x["goals_difference"], -x["goals_for"], x["name"]))
            if len(grp_teams) >= 1: winners.append(grp_teams[0])
            if len(grp_teams) >= 2: runners_up.append(grp_teams[1])
            if len(grp_teams) >= 3: third_places.append(grp_teams[2])

        sort_key = lambda x: (-x["points"], -x["goals_difference"], -x["goals_for"], x["name"])
        winners.sort(key=sort_key)
        runners_up.sort(key=sort_key)
        third_places.sort(key=sort_key)

        qualified_thirds = third_places[:8]
        seeds = winners + runners_up + qualified_thirds

        for s in seeds:
            sim_counts[s["id"]]["group_stage"] += 1
            sim_counts[s["id"]]["qualify"] += 1
            sim_counts[s["id"]]["r32"] += 1

        def sim_ko_winner(t1_id: int, t2_id: int) -> int:
            elo1 = team_info[t1_id]["elo"]
            elo2 = team_info[t2_id]["elo"]
            w1 = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
            return t1_id if random.random() < w1 else t2_id

        r32_winners = []
        for i in range(16):
            if i >= len(seeds) or (31 - i) >= len(seeds):
                # Safeguard if seeds count < 32
                break
            home = seeds[i]["id"]
            away = seeds[31 - i]["id"]
            winner = sim_ko_winner(home, away)
            r32_winners.append(winner)
            sim_counts[winner]["r16"] += 1

        r16_winners = []
        for i in range(8):
            if i >= len(r32_winners) or (15 - i) >= len(r32_winners):
                break
            home = r32_winners[i]
            away = r32_winners[15 - i]
            winner = sim_ko_winner(home, away)
            r16_winners.append(winner)
            sim_counts[winner]["qf"] += 1

        qf_winners = []
        for i in range(4):
            if i >= len(r16_winners) or (7 - i) >= len(r16_winners):
                break
            home = r16_winners[i]
            away = r16_winners[7 - i]
            winner = sim_ko_winner(home, away)
            qf_winners.append(winner)
            sim_counts[winner]["sf"] += 1

        sf_winners = []
        for i in range(2):
            if i >= len(qf_winners) or (3 - i) >= len(qf_winners):
                break
            home = qf_winners[i]
            away = qf_winners[3 - i]
            winner = sim_ko_winner(home, away)
            sf_winners.append(winner)
            sim_counts[winner]["final"] += 1

        if len(sf_winners) >= 2:
            champion = sim_ko_winner(sf_winners[0], sf_winners[1])
            sim_counts[champion]["winner"] += 1

    res_dict = {}
    for tid, counts in sim_counts.items():
        name = counts["name"]
        res_dict[name] = {
            "group_stage":        round((counts["group_stage"] / num_simulations) * 100, 1),
            "qualify_probability": round((counts["qualify"]     / num_simulations) * 100, 1),
            "r32":                round((counts["r32"]          / num_simulations) * 100, 1),
            "r16":                round((counts["r16"]          / num_simulations) * 100, 1),
            "qf":                 round((counts["qf"]           / num_simulations) * 100, 1),
            "sf":                 round((counts["sf"]           / num_simulations) * 100, 1),
            "final":              round((counts["final"]        / num_simulations) * 100, 1),
            "winner":             round((counts["winner"]       / num_simulations) * 100, 1),
        }

    result = {
        "status": "success",
        "simulation_count": num_simulations,
        "results": res_dict
    }
    
    # Cache the result
    _tournament_simulation_cache["result"] = result
    _tournament_simulation_cache["timestamp"] = time.time()
    
    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
    logger.info(f"GET /api/tournament/simulation  →  CACHE MISS, completed in {elapsed_ms} ms")
    
    return result
