import logging

logger = logging.getLogger(__name__)
from sqlalchemy import and_, desc, or_

from models import (
    BookmakerOdds,
    Competition,
    Injury,
    Match,
    MatchStatistic,
    NationalTeamPlayer,
    PlayerMatchPerformance,
    Standing,
    Suspension,
    Team,
    TeamElo,
)


def get_team_elo(db, team_name: str) -> int:
    """Retrieves the ELO rating for a team, falling back to 1500 if not found."""
    elo = db.query(TeamElo).filter_by(team_name=team_name).first()
    if not elo:
        # Flexible match (e.g. "Arsenal FC" matching "Arsenal")
        clean_name = team_name.lower().replace("fc", "").strip()
        elo = (
            db.query(TeamElo)
            .filter(
                TeamElo.team_name.ilike(f"%{clean_name}%"),
                ~TeamElo.team_name.ilike("%women%"),
                ~TeamElo.team_name.ilike("%woman%"),
            )
            .first()
        )
    if elo:
        logger.debug(f"Found Elo for team '{team_name}': {elo.elo_rating}")
    else:
        logger.debug(f"Elo not found for team '{team_name}'. Using default 1500.")
    return elo.elo_rating if elo else 1500


# ---------------------------------------------------------------------------
# Phase 3 helpers
# ---------------------------------------------------------------------------


def get_elo_momentum(
    db, team_id: int, team_name: str, match_date, n_matches: int = 10
) -> float:
    """
    Simulates Elo deltas over the last N finished matches using current Elo ratings
    as a proxy for historical ratings.  Positive value = team outperforming expectations.
    K-factor of 20 (standard international value).
    """
    K = 20
    matches = (
        db.query(Match)
        .filter(
            and_(
                or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
                Match.status == "FINISHED",
                Match.utc_date < match_date,
            )
        )
        .order_by(desc(Match.utc_date))
        .limit(n_matches)
        .all()
    )

    if not matches:
        return 0.0

    team_elo = get_team_elo(db, team_name)
    total_delta = 0.0
    for m in matches:
        if m.home_team_id == team_id:
            opp_id = m.away_team_id
            actual = (
                1.0 if m.winner == "HOME_TEAM" else (0.5 if m.winner == "DRAW" else 0.0)
            )
        else:
            opp_id = m.home_team_id
            actual = (
                1.0 if m.winner == "AWAY_TEAM" else (0.5 if m.winner == "DRAW" else 0.0)
            )

        opp = db.query(Team).filter_by(id=opp_id).first()
        if not opp:
            continue
        opp_elo = get_team_elo(db, opp.name)
        expected = 1.0 / (1.0 + 10 ** ((opp_elo - team_elo) / 400.0))
        total_delta += K * (actual - expected)

    logger.debug(
        f"Elo momentum for team_id={team_id} over last {n_matches} matches: {total_delta:.2f}"
    )
    return total_delta


def get_strength_of_schedule(db, team_id: int, match_date, n_matches: int = 5) -> float:
    """Average opponent Elo over the team's last N finished matches."""
    matches = (
        db.query(Match)
        .filter(
            and_(
                or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
                Match.status == "FINISHED",
                Match.utc_date < match_date,
            )
        )
        .order_by(desc(Match.utc_date))
        .limit(n_matches)
        .all()
    )

    if not matches:
        return 1500.0

    elo_sum = 0.0
    count = 0
    for m in matches:
        opp_id = m.away_team_id if m.home_team_id == team_id else m.home_team_id
        opp = db.query(Team).filter_by(id=opp_id).first()
        if opp:
            elo_sum += get_team_elo(db, opp.name)
            count += 1

    result = elo_sum / count if count > 0 else 1500.0
    logger.debug(
        f"Strength of schedule for team_id={team_id}: {result:.1f} (avg opponent Elo over {count} matches)"
    )
    return result


# Competition codes for tournament experience counts
_WC_CODES = frozenset(["WC", "WCQ"])
_MAJOR_CODES = frozenset(
    ["WC", "WCQ", "EU", "EUQ", "AFCON", "AFCONQ", "ASIAN", "ASIANQ", "UNL", "CNL"]
)
_KNOCKOUT_STAGES = frozenset(
    ["LAST_16", "QUARTER_FINALS", "SEMI_FINALS", "THIRD_PLACE", "FINAL"]
)


def get_tournament_experience(db, team_id: int, match_date) -> dict:
    """
    Returns counts of historic tournament matches played (up to match_date):
      - world_cup_matches  : WC + WCQ appearances
      - major_tournament_matches : WC/Euro/AFCON/Asian Cup/Nations Leagues
      - knockout_matches   : any match in a knockout stage
    """
    # Cache competition id sets per code group
    wc_ids = {
        c.id
        for c in db.query(Competition).filter(Competition.code.in_(_WC_CODES)).all()
    }
    major_ids = {
        c.id
        for c in db.query(Competition).filter(Competition.code.in_(_MAJOR_CODES)).all()
    }

    base = and_(
        or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
        Match.status == "FINISHED",
        Match.utc_date < match_date,
    )

    wc_count = (
        db.query(Match).filter(and_(base, Match.competition_id.in_(wc_ids))).count()
    )
    major_count = (
        db.query(Match).filter(and_(base, Match.competition_id.in_(major_ids))).count()
    )
    knockout_count = (
        db.query(Match).filter(and_(base, Match.stage.in_(_KNOCKOUT_STAGES))).count()
    )

    logger.debug(
        f"Tournament experience for team_id={team_id}: WC={wc_count}, Major={major_count}, KO={knockout_count}"
    )
    return {
        "world_cup_matches": wc_count,
        "major_tournament_matches": major_count,
        "knockout_matches": knockout_count,
    }


def get_team_recent_stats(db, team_id: int, match_date, num_matches: int = 5):
    """
    Calculates the recent form (average points per game), average goals scored (GS),
    and average goals conceded (GC) in the last N finished matches prior to `match_date`.
    """
    matches = (
        db.query(Match)
        .filter(
            and_(
                or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
                Match.status == "FINISHED",
                Match.utc_date < match_date,
            )
        )
        .order_by(desc(Match.utc_date))
        .limit(num_matches)
        .all()
    )

    if not matches:
        return 1.0, 0.0, 0.0  # Fallback to standard baseline

    total_points = 0
    total_goals_for = 0
    total_goals_against = 0

    for m in matches:
        if m.home_team_id == team_id:
            gf = m.home_score or 0
            ga = m.away_score or 0
            is_home = True
        else:
            gf = m.away_score or 0
            ga = m.home_score or 0
            is_home = False

        total_goals_for += gf
        total_goals_against += ga

        # Win = 3pts, Draw = 1pt, Loss = 0pts
        if m.winner == "DRAW":
            total_points += 1
        elif (m.winner == "HOME_TEAM" and is_home) or (
            m.winner == "AWAY_TEAM" and not is_home
        ):
            total_points += 3

    n = len(matches)
    return total_points / n, total_goals_for / n, total_goals_against / n


# ---------------------------------------------------------------------------
# Match stage weights — knockout matches carry higher predictive signal
# ---------------------------------------------------------------------------
STAGE_WEIGHTS = {
    "GROUP_STAGE": 0,
    "LAST_16": 1,
    "QUARTER_FINALS": 2,
    "SEMI_FINALS": 3,
    "THIRD_PLACE": 3,
    "FINAL": 4,
}


def get_attack_rating(db, team_id: int, match_date) -> float:
    """Calculates weighted average goals scored in last 20 completed matches."""
    matches = (
        db.query(Match)
        .filter(
            and_(
                or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
                Match.status == "FINISHED",
                Match.utc_date < match_date,
            )
        )
        .order_by(desc(Match.utc_date))
        .limit(20)
        .all()
    )
    if not matches:
        return 0.0

    weighted_goals = 0.0
    total_weight = 0.0
    for idx, m in enumerate(matches):
        if m.home_team_id == team_id:
            goals = m.home_score if m.home_score is not None else 0
        else:
            goals = m.away_score if m.away_score is not None else 0

        if idx < 5:
            weight = 3.0
        elif idx < 10:
            weight = 2.0
        else:
            weight = 1.0

        weighted_goals += goals * weight
        total_weight += weight

    return weighted_goals / total_weight if total_weight > 0 else 0.0


def get_defence_rating(db, team_id: int, match_date) -> float:
    """Calculates weighted average goals conceded in last 20 completed matches."""
    matches = (
        db.query(Match)
        .filter(
            and_(
                or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
                Match.status == "FINISHED",
                Match.utc_date < match_date,
            )
        )
        .order_by(desc(Match.utc_date))
        .limit(20)
        .all()
    )
    if not matches:
        return 0.0

    weighted_conceded = 0.0
    total_weight = 0.0
    for idx, m in enumerate(matches):
        if m.home_team_id == team_id:
            conceded = m.away_score if m.away_score is not None else 0
        else:
            conceded = m.home_score if m.home_score is not None else 0

        if idx < 5:
            weight = 3.0
        elif idx < 10:
            weight = 2.0
        else:
            weight = 1.0

        weighted_conceded += conceded * weight
        total_weight += weight

    return weighted_conceded / total_weight if total_weight > 0 else 0.0


def get_clean_sheet_rate(db, team_id: int, match_date) -> float:
    """Calculates the clean sheet rate (clean sheets / matches) in last 20 matches."""
    matches = (
        db.query(Match)
        .filter(
            and_(
                or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
                Match.status == "FINISHED",
                Match.utc_date < match_date,
            )
        )
        .order_by(desc(Match.utc_date))
        .limit(20)
        .all()
    )
    if not matches:
        return 0.0

    clean_sheets = 0
    for m in matches:
        if m.home_team_id == team_id:
            opp_score = m.away_score
        else:
            opp_score = m.home_score
        if opp_score == 0:
            clean_sheets += 1

    return clean_sheets / len(matches) if matches else 0.0


def get_btts_rate(db, team_id: int, match_date) -> float:
    """Calculates the BTTS rate (Both Teams To Score) in last 20 matches."""
    matches = (
        db.query(Match)
        .filter(
            and_(
                or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
                Match.status == "FINISHED",
                Match.utc_date < match_date,
            )
        )
        .order_by(desc(Match.utc_date))
        .limit(20)
        .all()
    )
    if not matches:
        return 0.0

    btts_count = 0
    for m in matches:
        if m.home_score is not None and m.away_score is not None:
            if m.home_score > 0 and m.away_score > 0:
                btts_count += 1

    return btts_count / len(matches) if matches else 0.0


def extract_ml_features(
    db,
    home_team_id: int,
    away_team_id: int,
    match_date,
    competition_code: str = "WC",
    match_stage: str = None,
    match: Match = None,
) -> dict:
    """
    Generates all predictive match features for the home and away team pair, with live data integration!
    """
    home_team = db.query(Team).filter_by(id=home_team_id).first()
    away_team = db.query(Team).filter_by(id=away_team_id).first()

    if not home_team or not away_team:
        raise ValueError(
            f"Home team ID {home_team_id} or away team ID {away_team_id} not found in DB."
        )

    # 1. Elo difference
    home_elo = get_team_elo(db, home_team.name)
    away_elo = get_team_elo(db, away_team.name)
    elo_diff = home_elo - away_elo
    logger.debug(
        f"Elo diff for match {home_team.name} vs {away_team.name}: {elo_diff} (home {home_elo}, away {away_elo})"
    )

    # 2. FIFA ranking difference (lower ranking is better, so diff = away - home)
    home_rank = home_team.fifa_ranking if home_team.fifa_ranking is not None else 150
    away_rank = away_team.fifa_ranking if away_team.fifa_ranking is not None else 150
    fifa_diff = away_rank - home_rank
    logger.debug(f"FIFA diff: {fifa_diff} (home {home_rank}, away {away_rank})")

    # 3. Squad market value difference (€M)
    home_mv = (
        home_team.squad_market_value
        if home_team.squad_market_value is not None
        else 0.0
    )
    away_mv = (
        away_team.squad_market_value
        if away_team.squad_market_value is not None
        else 0.0
    )
    mv_diff = home_mv - away_mv
    logger.debug(f"Market value diff: {mv_diff} (home €{home_mv}M, away €{away_mv}M)")

    # 4. Recent form & goals differences
    home_form, home_gs, home_gc = get_team_recent_stats(db, home_team_id, match_date)
    away_form, away_gs, away_gc = get_team_recent_stats(db, away_team_id, match_date)
    form_diff = home_form - away_form
    gs_diff = home_gs - away_gs
    gc_diff = home_gc - away_gc
    logger.debug(f"Form diff: {form_diff}, GS diff: {gs_diff}, GC diff: {gc_diff}")

    # 5. Injury & suspension market‑value impacts (existing diff features)
    home_injuries = db.query(Injury).filter_by(team_id=home_team_id).all()
    away_injuries = db.query(Injury).filter_by(team_id=away_team_id).all()
    home_inj_mv = sum(i.player_market_value or 0.0 for i in home_injuries)
    away_inj_mv = sum(i.player_market_value or 0.0 for i in away_injuries)
    inj_diff = away_inj_mv - home_inj_mv  # positive = away worse off
    logger.debug(
        f"Injury impact: home €{home_inj_mv}M, away €{away_inj_mv}M, diff={inj_diff}"
    )

    home_suspensions = db.query(Suspension).filter_by(team_id=home_team_id).all()
    away_suspensions = db.query(Suspension).filter_by(team_id=away_team_id).all()
    home_susp_mv = sum(s.player_market_value or 0.0 for s in home_suspensions)
    away_susp_mv = sum(s.player_market_value or 0.0 for s in away_suspensions)
    susp_diff = away_susp_mv - home_susp_mv  # positive = away worse off
    logger.debug(
        f"Suspension impact: home €{home_susp_mv}M, away €{away_susp_mv}M, diff={susp_diff}"
    )

    # 5b. Raw count & absolute market-value loss features (new — Step 6)
    home_injury_count = len(home_injuries)
    away_injury_count = len(away_injuries)
    home_suspension_count = len(home_suspensions)
    away_suspension_count = len(away_suspensions)
    home_injury_market_value_loss = home_inj_mv
    away_injury_market_value_loss = away_inj_mv
    logger.debug(
        f"Injury counts: home={home_injury_count}, away={away_injury_count}; "
        f"Suspension counts: home={home_suspension_count}, away={away_suspension_count}"
    )

    # ------------------------------------------------------------
    # Phase 2 player‑intelligence calculations
    # ------------------------------------------------------------
    # Load player market values for both teams
    home_players = db.query(NationalTeamPlayer).filter_by(team_id=home_team_id).all()
    away_players = db.query(NationalTeamPlayer).filter_by(team_id=away_team_id).all()
    home_player_mv = {p.player_name: (p.market_value or 0.0) for p in home_players}
    away_player_mv = {p.player_name: (p.market_value or 0.0) for p in away_players}

    # Sets of injured / suspended player names
    home_inj_names = {i.player_name for i in home_injuries}
    away_inj_names = {i.player_name for i in away_injuries}
    home_susp_names = {s.player_name for s in home_suspensions}
    away_susp_names = {s.player_name for s in away_suspensions}

    # 6. Available squad value (market value of players not injured nor suspended)
    home_available = home_mv - home_inj_mv - home_susp_mv
    away_available = away_mv - away_inj_mv - away_susp_mv
    available_squad_diff = home_available - away_available
    logger.debug(
        f"Available squad value diff: {available_squad_diff} (home €{home_available}M, away €{away_available}M)"
    )

    # 7. Squad availability percentage
    home_availability_pct = (home_available / home_mv) if home_mv > 0 else 0.0
    away_availability_pct = (away_available / away_mv) if away_mv > 0 else 0.0
    availability_pct_diff = home_availability_pct - away_availability_pct
    logger.debug(
        f"Availability % diff: {availability_pct_diff:.4f} (home {home_availability_pct:.4f}, away {away_availability_pct:.4f})"
    )

    # 8. Starting XI market value (sum of top 11 available players)
    def top_xi_value(player_mv_dict, inj_set, susp_set):
        available_vals = [
            mv
            for name, mv in player_mv_dict.items()
            if name not in inj_set and name not in susp_set
        ]
        return sum(sorted(available_vals, reverse=True)[:11])

    home_start_xi = top_xi_value(home_player_mv, home_inj_names, home_susp_names)
    away_start_xi = top_xi_value(away_player_mv, away_inj_names, away_susp_names)
    starting_xi_value_diff = home_start_xi - away_start_xi
    logger.debug(
        f"Starting XI MV diff: {starting_xi_value_diff} (home €{home_start_xi}M, away €{away_start_xi}M)"
    )

    # 9. Missing star players (injured or suspended with market value > 50M)
    STAR_THRESHOLD = 50.0

    def missing_star_count(inj_set, susp_set, player_mv_dict):
        return sum(
            1
            for name in (inj_set | susp_set)
            if player_mv_dict.get(name, 0.0) > STAR_THRESHOLD
        )

    home_missing_star = missing_star_count(
        home_inj_names, home_susp_names, home_player_mv
    )
    away_missing_star = missing_star_count(
        away_inj_names, away_susp_names, away_player_mv
    )
    missing_star_players_diff = home_missing_star - away_missing_star
    logger.debug(
        f"Missing star players diff: {missing_star_players_diff} (home {home_missing_star}, away {away_missing_star})"
    )

    # 10. Match stage weight (0=group, 1=R16, 2=QF, 3=SF/3rd, 4=Final)
    if match_stage:
        stage_key = str(match_stage).upper().replace(" ", "_").replace("-", "_")
        match_stage_weight = STAGE_WEIGHTS.get(stage_key, 0)
    else:
        match_stage_weight = 0
    logger.debug(f"Match stage: {match_stage} -> weight {match_stage_weight}")

    # ------------------------------------------------------------
    # Phase 3 features
    # ------------------------------------------------------------
    # 11. Elo Momentum (rolling simulated Elo delta over last 10 matches)
    home_elo_momentum = get_elo_momentum(
        db, home_team_id, home_team.name, match_date, n_matches=10
    )
    away_elo_momentum = get_elo_momentum(
        db, away_team_id, away_team.name, match_date, n_matches=10
    )
    elo_momentum_diff = home_elo_momentum - away_elo_momentum
    logger.debug(
        f"Elo momentum: home={home_elo_momentum:.2f}, away={away_elo_momentum:.2f}, diff={elo_momentum_diff:.2f}"
    )

    # 12. Strength of Schedule (average opponent Elo last 5 matches)
    home_sos = get_strength_of_schedule(db, home_team_id, match_date, n_matches=5)
    away_sos = get_strength_of_schedule(db, away_team_id, match_date, n_matches=5)
    strength_of_schedule_diff = home_sos - away_sos
    logger.debug(
        f"SoS: home={home_sos:.1f}, away={away_sos:.1f}, diff={strength_of_schedule_diff:.1f}"
    )

    # 13. Tournament Experience
    home_exp = get_tournament_experience(db, home_team_id, match_date)
    away_exp = get_tournament_experience(db, away_team_id, match_date)
    world_cup_matches_played_diff = (
        home_exp["world_cup_matches"] - away_exp["world_cup_matches"]
    )
    major_tournament_matches_diff = (
        home_exp["major_tournament_matches"] - away_exp["major_tournament_matches"]
    )
    knockout_matches_diff = home_exp["knockout_matches"] - away_exp["knockout_matches"]
    logger.debug(
        f"Tournament exp diff: WC={world_cup_matches_played_diff}, Major={major_tournament_matches_diff}, KO={knockout_matches_diff}"
    )

    # 14. Home advantage flag
    if competition_code == "WC":
        # In World Cup, only hosts have home field advantage
        is_host = home_team.name.lower() in ["usa", "united states", "mexico", "canada"]
        home_adv = 1 if is_host else 0
    else:
        home_adv = 1  # Standard club leagues always have home advantage

    # 11. Head to head performance (home team points ratio, neutral = 0.5)
    h2h_matches = (
        db.query(Match)
        .filter(
            and_(
                or_(
                    and_(
                        Match.home_team_id == home_team_id,
                        Match.away_team_id == away_team_id,
                    ),
                    and_(
                        Match.home_team_id == away_team_id,
                        Match.away_team_id == home_team_id,
                    ),
                ),
                Match.status == "FINISHED",
                Match.utc_date < match_date,
            )
        )
        .order_by(desc(Match.utc_date))
        .limit(5)
        .all()
    )

    h2h_factor = 0.5
    if h2h_matches:
        home_points = 0
        total_possible = len(h2h_matches) * 3
        for m in h2h_matches:
            if m.home_team_id == home_team_id:
                if m.winner == "HOME_TEAM":
                    home_points += 3
                elif m.winner == "DRAW":
                    home_points += 1
            else:
                if m.winner == "AWAY_TEAM":
                    home_points += 3
                elif m.winner == "DRAW":
                    home_points += 1
        h2h_factor = home_points / total_possible

    # ---- Phase 4.5 Advanced Goal Intelligence ----
    home_attack_rating = get_attack_rating(db, home_team_id, match_date)
    away_attack_rating = get_attack_rating(db, away_team_id, match_date)
    attack_rating_diff = home_attack_rating - away_attack_rating

    home_defence_rating = get_defence_rating(db, home_team_id, match_date)
    away_defence_rating = get_defence_rating(db, away_team_id, match_date)
    defence_rating_diff = home_defence_rating - away_defence_rating

    home_clean_sheet_rate = get_clean_sheet_rate(db, home_team_id, match_date)
    away_clean_sheet_rate = get_clean_sheet_rate(db, away_team_id, match_date)
    clean_sheet_rate_diff = home_clean_sheet_rate - away_clean_sheet_rate

    home_btts_rate = get_btts_rate(db, home_team_id, match_date)
    away_btts_rate = get_btts_rate(db, away_team_id, match_date)
    btts_rate_diff = home_btts_rate - away_btts_rate

    # ------------------------------------------------------------
    # NEW: LIVE FEATURES!
    # ------------------------------------------------------------
    # Standings features
    competition = None
    if match and match.competition_id:
        competition = db.query(Competition).filter_by(id=match.competition_id).first()
    # If no competition from match, try to get by competition_code!
    if not competition and competition_code:
        competition = db.query(Competition).filter_by(code=competition_code).first()

    home_group_position = 0
    away_group_position = 0
    home_points = 0
    away_points = 0
    home_goals_difference = 0
    away_goals_difference = 0

    if competition:
        home_standing = (
            db.query(Standing)
            .filter_by(team_id=home_team_id, competition_id=competition.id)
            .first()
        )
        away_standing = (
            db.query(Standing)
            .filter_by(team_id=away_team_id, competition_id=competition.id)
            .first()
        )
        if home_standing:
            home_group_position = home_standing.position
            home_points = home_standing.points
            home_goals_difference = home_standing.goals_difference
        if away_standing:
            away_group_position = away_standing.position
            away_points = away_standing.points
            away_goals_difference = away_standing.goals_difference
    group_position_diff = (
        away_group_position - home_group_position
    )  # Lower position number = better!
    points_diff = home_points - away_points
    goal_difference_diff = home_goals_difference - away_goals_difference

    # Betting odds features
    home_implied_probability = 0.333
    draw_implied_probability = 0.333
    away_implied_probability = 0.333

    if match:
        latest_odds = (
            db.query(BookmakerOdds)
            .filter_by(match_id=match.id)
            .order_by(desc(BookmakerOdds.last_updated))
            .first()
        )
        if latest_odds:
            home_odds = latest_odds.home_odds
            draw_odds = latest_odds.draw_odds if latest_odds.draw_odds else 3.0
            away_odds = latest_odds.away_odds

            home_implied = 1 / home_odds
            draw_implied = 1 / draw_odds
            away_implied = 1 / away_odds
            total_implied = home_implied + draw_implied + away_implied
            home_implied_probability = home_implied / total_implied
            draw_implied_probability = draw_implied / total_implied
            away_implied_probability = away_implied / total_implied

    # Live match events
    current_minute = 0
    time_remaining = 90
    current_home_score = None
    current_away_score = None
    current_score_diff = 0
    home_red_cards = 0
    away_red_cards = 0
    red_card_diff = 0

    if match:
        if match.current_minute:
            current_minute = match.current_minute
            time_remaining = max(0, 90 - match.current_minute)
        if match.current_home_score is not None:
            current_home_score = match.current_home_score
        if match.current_away_score is not None:
            current_away_score = match.current_away_score
        if current_home_score is not None and current_away_score is not None:
            current_score_diff = current_home_score - current_away_score
        if match.home_red_cards:
            home_red_cards = match.home_red_cards
        if match.away_red_cards:
            away_red_cards = match.away_red_cards
        red_card_diff = home_red_cards - away_red_cards

    # ------------------------------------------------------------
    # NEW: SOFASCORE INTELLIGENCE FEATURES!
    # ------------------------------------------------------------
    home_avg_rating = 0.0
    away_avg_rating = 0.0
    home_possession = 0.0
    away_possession = 0.0
    home_xg = 0.0
    away_xg = 0.0
    possession_diff = 0.0
    xg_diff = 0.0

    if match:
        # 1. Player ratings (from PlayerMatchPerformance)
        home_performances = (
            db.query(PlayerMatchPerformance)
            .filter(
                PlayerMatchPerformance.match_id == match.id,
                PlayerMatchPerformance.team_id == match.home_team_id,
                PlayerMatchPerformance.is_starter == 1,
            )
            .all()
        )
        away_performances = (
            db.query(PlayerMatchPerformance)
            .filter(
                PlayerMatchPerformance.match_id == match.id,
                PlayerMatchPerformance.team_id == match.away_team_id,
                PlayerMatchPerformance.is_starter == 1,
            )
            .all()
        )

        if home_performances:
            valid_home = [
                p.sofa_score_rating for p in home_performances if p.sofa_score_rating
            ]
            if valid_home:
                home_avg_rating = sum(valid_home) / len(valid_home)

        if away_performances:
            valid_away = [
                p.sofa_score_rating for p in away_performances if p.sofa_score_rating
            ]
            if valid_away:
                away_avg_rating = sum(valid_away) / len(valid_away)

        # 2. Statistics from MatchStatistic
        match_statistics = (
            db.query(MatchStatistic).filter(MatchStatistic.match_id == match.id).first()
        )
        if match_statistics:
            if match_statistics.home_possession is not None:
                home_possession = match_statistics.home_possession
            if match_statistics.away_possession is not None:
                away_possession = match_statistics.away_possession
            if match_statistics.home_expected_goals is not None:
                home_xg = match_statistics.home_expected_goals
            if match_statistics.away_expected_goals is not None:
                away_xg = match_statistics.away_expected_goals
            possession_diff = home_possession - away_possession
            xg_diff = home_xg - away_xg

        logger.debug(
            f"SofaScore features: home_avg_rating={home_avg_rating:.2f}, "
            f"away_avg_rating={away_avg_rating:.2f}, possession_diff={possession_diff:.1f}, xg_diff={xg_diff:.2f}"
        )

    # ------------------------------------------------------------
    # NEW: MATCH INTELLIGENCE FEATURES (Phase 4 expansion)
    # All 16 intelligence scores with safe defaults = 0.0
    # ------------------------------------------------------------
    home_attacking_strength = 0.0
    away_attacking_strength = 0.0
    home_defensive_strength = 0.0
    away_defensive_strength = 0.0
    home_midfield_control = 0.0
    away_midfield_control = 0.0
    home_goalkeeper_performance = 0.0
    away_goalkeeper_performance = 0.0
    home_passing_dominance = 0.0
    away_passing_dominance = 0.0
    home_pressing_intensity = 0.0
    away_pressing_intensity = 0.0
    home_set_piece_threat = 0.0
    away_set_piece_threat = 0.0
    home_discipline_score = 1.0  # default: perfectly disciplined
    away_discipline_score = 1.0
    home_fatigue_score = 1.0  # default: fully fresh
    away_fatigue_score = 1.0
    home_substitution_impact = 0.0
    away_substitution_impact = 0.0
    home_player_availability_score = 1.0
    away_player_availability_score = 1.0
    home_injury_impact = 0.0
    away_injury_impact = 0.0
    home_suspension_impact = 0.0
    away_suspension_impact = 0.0
    home_formation_stability = 0.5  # default: unknown
    away_formation_stability = 0.5
    home_momentum_score = 0.5  # default: neutral
    away_momentum_score = 0.5
    confidence_score = 0.5
    home_goalkeeper_strength = 0.0
    away_goalkeeper_strength = 0.0
    home_passing_strength = 0.0
    away_passing_strength = 0.0
    home_recent_form = 0.5
    away_recent_form = 0.5
    home_aerial_dominance = 0.0
    away_aerial_dominance = 0.0
    home_pressing_strength = 0.0
    away_pressing_strength = 0.0
    home_defensive_stability = 0.5
    away_defensive_stability = 0.5
    home_attacking_efficiency = 0.0
    away_attacking_efficiency = 0.0
    home_finishing_quality = 0.5
    away_finishing_quality = 0.5
    home_set_piece_strength = 0.0
    away_set_piece_strength = 0.0
    home_squad_availability = 1.0
    away_squad_availability = 1.0
    home_tactical_stability = 0.5
    away_tactical_stability = 0.5

    if match:
        try:
            from services.intelligence_service import IntelligenceService

            intel_svc = IntelligenceService()
            intel = intel_svc.calculate_match_intelligence(db, match)

            home_attacking_strength = intel.home_attacking_strength
            away_attacking_strength = intel.away_attacking_strength
            home_defensive_strength = intel.home_defensive_strength
            away_defensive_strength = intel.away_defensive_strength
            home_midfield_control = intel.home_midfield_control
            away_midfield_control = intel.away_midfield_control
            home_goalkeeper_performance = intel.home_goalkeeper_performance
            away_goalkeeper_performance = intel.away_goalkeeper_performance
            home_passing_dominance = intel.home_passing_dominance
            away_passing_dominance = intel.away_passing_dominance
            home_pressing_intensity = intel.home_pressing_intensity
            away_pressing_intensity = intel.away_pressing_intensity
            home_set_piece_threat = intel.home_set_piece_threat
            away_set_piece_threat = intel.away_set_piece_threat
            home_discipline_score = intel.home_discipline_score
            away_discipline_score = intel.away_discipline_score
            home_fatigue_score = intel.home_fatigue_score
            away_fatigue_score = intel.away_fatigue_score
            home_substitution_impact = intel.home_substitution_impact
            away_substitution_impact = intel.away_substitution_impact
            home_player_availability_score = intel.home_player_availability_score
            away_player_availability_score = intel.away_player_availability_score
            home_injury_impact = intel.home_injury_impact
            away_injury_impact = intel.away_injury_impact
            home_suspension_impact = intel.home_suspension_impact
            away_suspension_impact = intel.away_suspension_impact
            home_formation_stability = intel.home_formation_stability
            away_formation_stability = intel.away_formation_stability
            home_momentum_score = intel.home_momentum_score
            away_momentum_score = intel.away_momentum_score
            confidence_score = intel.confidence_score
            home_goalkeeper_strength = intel.home_goalkeeper_strength
            away_goalkeeper_strength = intel.away_goalkeeper_strength
            home_passing_strength = intel.home_passing_strength
            away_passing_strength = intel.away_passing_strength
            home_recent_form = intel.home_recent_form
            away_recent_form = intel.away_recent_form
            home_aerial_dominance = intel.home_aerial_dominance
            away_aerial_dominance = intel.away_aerial_dominance
            home_pressing_strength = intel.home_pressing_strength
            away_pressing_strength = intel.away_pressing_strength
            home_defensive_stability = intel.home_defensive_stability
            away_defensive_stability = intel.away_defensive_stability
            home_attacking_efficiency = intel.home_attacking_efficiency
            away_attacking_efficiency = intel.away_attacking_efficiency
            home_finishing_quality = intel.home_finishing_quality
            away_finishing_quality = intel.away_finishing_quality
            home_set_piece_strength = intel.home_set_piece_strength
            away_set_piece_strength = intel.away_set_piece_strength
            home_squad_availability = intel.home_squad_availability
            away_squad_availability = intel.away_squad_availability
            home_tactical_stability = intel.home_tactical_stability
            away_tactical_stability = intel.away_tactical_stability

            logger.debug(
                f"Intelligence features: confidence={confidence_score:.2f}, "
                f"home_momentum={home_momentum_score:.2f}, away_momentum={away_momentum_score:.2f}"
            )
        except Exception as e:
            logger.debug(f"Could not compute Match Intelligence features: {e}")

    return {
        # ---- Phase 1 core features ----
        "elo_diff": elo_diff,
        "fifa_diff": fifa_diff,
        "form_diff": form_diff,
        "gs_diff": gs_diff,
        "gc_diff": gc_diff,
        "mv_diff": mv_diff,
        "inj_diff": inj_diff,
        "susp_diff": susp_diff,
        "home_adv": home_adv,
        "h2h_factor": h2h_factor,
        # ---- Phase 2 player intelligence ----
        "available_squad_diff": available_squad_diff,
        "availability_pct_diff": availability_pct_diff,
        "starting_xi_value_diff": starting_xi_value_diff,
        "missing_star_players_diff": missing_star_players_diff,
        "match_stage_weight": match_stage_weight,
        # ---- Phase 3 structural features ----
        "home_elo_momentum": home_elo_momentum,
        "away_elo_momentum": away_elo_momentum,
        "elo_momentum_diff": elo_momentum_diff,
        "home_strength_of_schedule": home_sos,
        "away_strength_of_schedule": away_sos,
        "strength_of_schedule_diff": strength_of_schedule_diff,
        "world_cup_matches_played_diff": world_cup_matches_played_diff,
        "major_tournament_matches_diff": major_tournament_matches_diff,
        "knockout_matches_diff": knockout_matches_diff,
        # ---- Phase 4.5 Advanced Goal Intelligence ----
        "home_attack_rating": home_attack_rating,
        "away_attack_rating": away_attack_rating,
        "attack_rating_diff": attack_rating_diff,
        "home_defence_rating": home_defence_rating,
        "away_defence_rating": away_defence_rating,
        "defence_rating_diff": defence_rating_diff,
        "home_clean_sheet_rate": home_clean_sheet_rate,
        "away_clean_sheet_rate": away_clean_sheet_rate,
        "clean_sheet_rate_diff": clean_sheet_rate_diff,
        "home_btts_rate": home_btts_rate,
        "away_btts_rate": away_btts_rate,
        "btts_rate_diff": btts_rate_diff,
        # ---- Injury & Suspension counts & absolute market-value loss ----
        "home_injury_count": home_injury_count,
        "away_injury_count": away_injury_count,
        "home_suspension_count": home_suspension_count,
        "away_suspension_count": away_suspension_count,
        "home_injury_market_value_loss": home_injury_market_value_loss,
        "away_injury_market_value_loss": away_injury_market_value_loss,
        # ---- NEW: Standings features ----
        "home_group_position": home_group_position,
        "away_group_position": away_group_position,
        "group_position_diff": group_position_diff,
        "home_points": home_points,
        "away_points": away_points,
        "points_diff": points_diff,
        "goal_difference_diff": goal_difference_diff,
        # ---- NEW: Betting odds features ----
        "home_implied_probability": home_implied_probability,
        "draw_implied_probability": draw_implied_probability,
        "away_implied_probability": away_implied_probability,
        # ---- NEW: Live match features ----
        "current_minute": current_minute,
        "time_remaining": time_remaining,
        "current_score_diff": current_score_diff,
        "home_red_cards": home_red_cards,
        "away_red_cards": away_red_cards,
        "red_card_diff": red_card_diff,
        # ---- NEW: SOFASCORE FEATURES ----
        "home_avg_rating": home_avg_rating,
        "away_avg_rating": away_avg_rating,
        "avg_rating_diff": home_avg_rating - away_avg_rating,
        "home_possession": home_possession,
        "away_possession": away_possession,
        "possession_diff": possession_diff,
        "home_expected_goals": home_xg,
        "away_expected_goals": away_xg,
        "expected_goals_diff": xg_diff,
        # ---- NEW: MATCH INTELLIGENCE FEATURES (Phase 4 expansion) ----
        "home_attacking_strength": home_attacking_strength,
        "away_attacking_strength": away_attacking_strength,
        "attacking_strength_diff": home_attacking_strength - away_attacking_strength,
        "home_defensive_strength": home_defensive_strength,
        "away_defensive_strength": away_defensive_strength,
        "defensive_strength_diff": home_defensive_strength - away_defensive_strength,
        "home_midfield_control": home_midfield_control,
        "away_midfield_control": away_midfield_control,
        "midfield_control_diff": home_midfield_control - away_midfield_control,
        "home_goalkeeper_performance": home_goalkeeper_performance,
        "away_goalkeeper_performance": away_goalkeeper_performance,
        "goalkeeper_performance_diff": home_goalkeeper_performance
        - away_goalkeeper_performance,
        "home_passing_dominance": home_passing_dominance,
        "away_passing_dominance": away_passing_dominance,
        "passing_dominance_diff": home_passing_dominance - away_passing_dominance,
        "home_pressing_intensity": home_pressing_intensity,
        "away_pressing_intensity": away_pressing_intensity,
        "pressing_intensity_diff": home_pressing_intensity - away_pressing_intensity,
        "home_set_piece_threat": home_set_piece_threat,
        "away_set_piece_threat": away_set_piece_threat,
        "set_piece_threat_diff": home_set_piece_threat - away_set_piece_threat,
        "home_discipline_score": home_discipline_score,
        "away_discipline_score": away_discipline_score,
        "discipline_score_diff": home_discipline_score - away_discipline_score,
        "home_fatigue_score": home_fatigue_score,
        "away_fatigue_score": away_fatigue_score,
        "fatigue_score_diff": home_fatigue_score - away_fatigue_score,
        "home_substitution_impact": home_substitution_impact,
        "away_substitution_impact": away_substitution_impact,
        "substitution_impact_diff": home_substitution_impact - away_substitution_impact,
        "home_player_availability_score": home_player_availability_score,
        "away_player_availability_score": away_player_availability_score,
        "availability_score_diff": home_player_availability_score
        - away_player_availability_score,
        "home_injury_impact": home_injury_impact,
        "away_injury_impact": away_injury_impact,
        "injury_impact_diff": home_injury_impact - away_injury_impact,
        "home_suspension_impact": home_suspension_impact,
        "away_suspension_impact": away_suspension_impact,
        "suspension_impact_diff": home_suspension_impact - away_suspension_impact,
        "home_formation_stability": home_formation_stability,
        "away_formation_stability": away_formation_stability,
        "formation_stability_diff": home_formation_stability - away_formation_stability,
        "home_momentum_score": home_momentum_score,
        "away_momentum_score": away_momentum_score,
        "momentum_score_diff": home_momentum_score - away_momentum_score,
        "home_goalkeeper_strength": home_goalkeeper_strength,
        "away_goalkeeper_strength": away_goalkeeper_strength,
        "goalkeeper_strength_diff": home_goalkeeper_strength - away_goalkeeper_strength,
        "home_passing_strength": home_passing_strength,
        "away_passing_strength": away_passing_strength,
        "passing_strength_diff": home_passing_strength - away_passing_strength,
        "home_recent_form": home_recent_form,
        "away_recent_form": away_recent_form,
        "recent_form_diff": home_recent_form - away_recent_form,
        "home_aerial_dominance": home_aerial_dominance,
        "away_aerial_dominance": away_aerial_dominance,
        "aerial_dominance_diff": home_aerial_dominance - away_aerial_dominance,
        "home_pressing_strength": home_pressing_strength,
        "away_pressing_strength": away_pressing_strength,
        "pressing_strength_diff": home_pressing_strength - away_pressing_strength,
        "home_defensive_stability": home_defensive_stability,
        "away_defensive_stability": away_defensive_stability,
        "defensive_stability_diff": home_defensive_stability - away_defensive_stability,
        "home_attacking_efficiency": home_attacking_efficiency,
        "away_attacking_efficiency": away_attacking_efficiency,
        "attacking_efficiency_diff": home_attacking_efficiency
        - away_attacking_efficiency,
        "home_finishing_quality": home_finishing_quality,
        "away_finishing_quality": away_finishing_quality,
        "finishing_quality_diff": home_finishing_quality - away_finishing_quality,
        "home_set_piece_strength": home_set_piece_strength,
        "away_set_piece_strength": away_set_piece_strength,
        "set_piece_strength_diff": home_set_piece_strength - away_set_piece_strength,
        "home_squad_availability": home_squad_availability,
        "away_squad_availability": away_squad_availability,
        "squad_availability_diff": home_squad_availability - away_squad_availability,
        "home_tactical_stability": home_tactical_stability,
        "away_tactical_stability": away_tactical_stability,
        "tactical_stability_diff": home_tactical_stability - away_tactical_stability,
        "confidence_score": confidence_score,
    }
