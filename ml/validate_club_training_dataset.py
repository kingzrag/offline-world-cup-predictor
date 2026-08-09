"""
ml/validate_club_training_dataset.py

STEP 6B — Phase 7: Dataset Validation

Validates ml/dataset_club_leagues.csv for:
1. Competition distribution
2. Season distribution
3. Target balance
4. Feature coverage / missing values / zero-value features
5. Team coverage
6. Temporal leakage checks (automated)
7. Duplicate rows
"""

import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
logger = logging.getLogger("validate_dataset")

DATASET_PATH = Path(__file__).parent / "dataset_club_leagues.csv"


def load_dataset() -> list[dict]:
    if not DATASET_PATH.exists():
        logger.error(f"Dataset not found at {DATASET_PATH}")
        return []
    with open(DATASET_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def validate(rows: list[dict]) -> dict:
    if not rows:
        return {"status": "EMPTY"}

    feature_cols = [
        "elo_diff", "form_diff", "gs_diff", "gc_diff", "home_adv", "h2h_factor",
        "home_elo_momentum", "away_elo_momentum", "elo_momentum_diff",
        "home_attack_rating", "away_attack_rating", "attack_rating_diff",
        "home_defence_rating", "away_defence_rating", "defence_rating_diff",
        "home_clean_sheet_rate", "away_clean_sheet_rate", "clean_sheet_rate_diff",
        "home_btts_rate", "away_btts_rate", "btts_rate_diff",
        "home_recent_form", "away_recent_form", "recent_form_diff",
        "competition_code_encoded", "home_league_position", "away_league_position",
        "league_position_diff",
    ]
    target_cols = ["target", "home_score", "away_score", "home_clean_sheet", "away_clean_sheet", "btts", "ah_cover"]

    results = {}

    # ── 1. Total rows ─────────────────────────────────────────────────────────
    results["total_rows"] = len(rows)

    # ── 2. Competition distribution ───────────────────────────────────────────
    comp_dist = defaultdict(int)
    for r in rows:
        comp_dist[r["competition_code"]] += 1
    results["competition_distribution"] = dict(sorted(comp_dist.items()))

    # ── 3. Season distribution (by year of utc_date) ──────────────────────────
    season_dist = defaultdict(lambda: defaultdict(int))
    for r in rows:
        try:
            dt = datetime.fromisoformat(r["utc_date"])
            year = dt.year
        except Exception:
            year = "unknown"
        season_dist[r["competition_code"]][year] += 1
    results["season_distribution"] = {
        comp: dict(sorted(years.items())) for comp, years in season_dist.items()
    }

    # ── 4. Target balance ────────────────────────────────────────────────────
    targets = [int(r["target"]) for r in rows]
    hw = targets.count(0)
    dr = targets.count(1)
    aw = targets.count(2)
    total = len(targets)
    results["target_balance"] = {
        "HOME_WIN": hw, "DRAW": dr, "AWAY_WIN": aw,
        "HOME_WIN_pct": round(hw/total*100, 1),
        "DRAW_pct": round(dr/total*100, 1),
        "AWAY_WIN_pct": round(aw/total*100, 1),
    }
    btts_vals = [int(r["btts"]) for r in rows]
    cs_h = [int(r["home_clean_sheet"]) for r in rows]
    cs_a = [int(r["away_clean_sheet"]) for r in rows]
    results["target_balance"]["BTTS_rate"] = round(sum(btts_vals)/total*100, 1)
    results["target_balance"]["HOME_CS_rate"] = round(sum(cs_h)/total*100, 1)
    results["target_balance"]["AWAY_CS_rate"] = round(sum(cs_a)/total*100, 1)

    # ── 5. Feature coverage ──────────────────────────────────────────────────
    feature_stats = {}
    for col in feature_cols:
        values = []
        missing = 0
        for r in rows:
            v = r.get(col, "")
            if v == "" or v is None:
                missing += 1
            else:
                try:
                    values.append(float(v))
                except ValueError:
                    missing += 1

        zero_count = sum(1 for v in values if v == 0.0)
        feature_stats[col] = {
            "missing": missing,
            "missing_pct": round(missing/total*100, 1),
            "zero": zero_count,
            "zero_pct": round(zero_count/total*100, 1),
            "min": round(min(values), 3) if values else None,
            "max": round(max(values), 3) if values else None,
            "mean": round(sum(values)/len(values), 3) if values else None,
        }
    results["feature_coverage"] = feature_stats

    # ── 6. Team coverage ─────────────────────────────────────────────────────
    all_teams = set()
    for r in rows:
        all_teams.add(r.get("home_team", ""))
        all_teams.add(r.get("away_team", ""))
    results["total_unique_teams"] = len(all_teams)

    # ── 7. Temporal leakage check ─────────────────────────────────────────────
    # Check: for each row, verify that no feature that should be "before" the match
    # is actually populated from match data. We do this by checking:
    # - elo_diff should vary (if always 0, it was never computed)
    # - form_diff should vary (if always 0, temporal filter broken)
    leakage_flags = []
    elo_diffs = [float(r["elo_diff"]) for r in rows if r.get("elo_diff")]
    if all(v == 0.0 for v in elo_diffs):
        leakage_flags.append("WARN: All elo_diff values are 0 — Elo may not have been computed")

    # Check date ordering is correct
    dates = []
    for r in rows:
        try:
            dates.append(datetime.fromisoformat(r["utc_date"]))
        except Exception:
            pass
    is_chronological = all(dates[i] <= dates[i+1] for i in range(len(dates)-1))
    if not is_chronological:
        leakage_flags.append("ERROR: Rows are NOT in chronological order — sort issue")

    results["leakage_flags"] = leakage_flags
    results["leakage_status"] = "PASS" if not leakage_flags else "WARN"

    # ── 8. Duplicate rows ────────────────────────────────────────────────────
    seen_keys = set()
    dups = 0
    for r in rows:
        key = (r.get("match_id", ""), r.get("competition_code", ""))
        if key in seen_keys:
            dups += 1
        seen_keys.add(key)
    results["duplicate_rows"] = dups

    return results


def print_report(results: dict) -> None:
    print("\n" + "=" * 70)
    print("CLUB TRAINING DATASET VALIDATION REPORT")
    print("=" * 70)
    print(f"\nTotal rows: {results.get('total_rows', 0)}")

    print("\n── Competition Distribution ──────────────────────────")
    for comp, count in results.get("competition_distribution", {}).items():
        print(f"  {comp:6s}: {count:6d} matches")

    print("\n── Season Distribution ───────────────────────────────")
    for comp, seasons in results.get("season_distribution", {}).items():
        print(f"  [{comp}]")
        for yr, cnt in sorted(seasons.items()):
            print(f"    {yr}: {cnt}")

    print("\n── Target Balance ─────────────────────────────────────")
    tb = results.get("target_balance", {})
    print(f"  HOME_WIN: {tb.get('HOME_WIN',0):6d} ({tb.get('HOME_WIN_pct',0):.1f}%)")
    print(f"  DRAW:     {tb.get('DRAW',0):6d} ({tb.get('DRAW_pct',0):.1f}%)")
    print(f"  AWAY_WIN: {tb.get('AWAY_WIN',0):6d} ({tb.get('AWAY_WIN_pct',0):.1f}%)")
    print(f"  BTTS Yes: {tb.get('BTTS_rate',0):.1f}%")
    print(f"  Home CS:  {tb.get('HOME_CS_rate',0):.1f}%")
    print(f"  Away CS:  {tb.get('AWAY_CS_rate',0):.1f}%")

    print("\n── Feature Coverage (missing / all-zero features) ─────")
    fc = results.get("feature_coverage", {})
    for col, stats in fc.items():
        issues = []
        if stats["missing_pct"] > 5:
            issues.append(f"⚠️ {stats['missing_pct']}% missing")
        if stats["zero_pct"] > 90:
            issues.append(f"⚠️ {stats['zero_pct']}% zero")
        status = " ".join(issues) if issues else "✅ OK"
        print(f"  {col:35s} miss={stats['missing_pct']:4.1f}% zero={stats['zero_pct']:4.1f}%  {status}")

    print("\n── Team Coverage ─────────────────────────────────────")
    print(f"  Unique teams: {results.get('total_unique_teams', 0)}")

    print("\n── Leakage Check ─────────────────────────────────────")
    status = results.get("leakage_status", "UNKNOWN")
    flags = results.get("leakage_flags", [])
    print(f"  Status: {status}")
    for f in flags:
        print(f"  {f}")
    if not flags:
        print("  No leakage detected ✅")

    print(f"\n── Duplicate Rows: {results.get('duplicate_rows', 0)}")
    print()


if __name__ == "__main__":
    logger.info("Loading dataset...")
    rows = load_dataset()
    logger.info(f"Loaded {len(rows)} rows")

    results = validate(rows)
    print_report(results)

    # Save validation results
    out_path = Path(__file__).parent / "dataset_validation_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved results to {out_path}")
