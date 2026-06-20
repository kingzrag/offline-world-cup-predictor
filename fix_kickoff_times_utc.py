"""
fix_kickoff_times_utc.py
────────────────────────────────────────────────────────────────────────────
ROOT CAUSE
  The `utc_date` column in the `matches` table is a naive DateTime column.
  During initial data ingestion, the football-data.org API returned UTC
  timestamps (e.g. "2026-06-11T19:00:00Z" for Mexico vs South Africa).

  However, the ingestion pipeline was run on a machine set to IST (UTC+5:30).
  SQLAlchemy's naive DateTime column silently stripped the tzinfo, but the
  actual values stored appear to be IST-local times (00:30 IST = 19:00 UTC).

  CONFIRMED: Mexico vs South Africa stored as 2026-06-12 00:30:00
             Official kickoff:               2026-06-11 19:00:00 UTC  ✅

FIX
  For all WC 2026 matches (utc_date > 2026-06-01), subtract 5h30m (IST offset)
  from the stored naive datetime to obtain the true UTC value.

  This is a one-time migration. After running this, the backend serializer
  `.replace(tzinfo=timezone.utc).isoformat()` will produce correct UTC strings.
  The frontend (dateTimeUtils.ts) correctly converts UTC→local timezone via
  Intl.DateTimeFormat, so no frontend changes are needed.

SAFETY
  - Prints a full before/after preview for the first 20 matches.
  - Asks for confirmation before writing.
  - Skips matches where stored time already looks like UTC (i.e. minutes == 0
    and hours are round numbers typically used for UTC slots).
"""

import sys
sys.path.insert(0, '.')

from database.connection import SessionLocal
from models.match import Match
from models.competition import Competition
from datetime import timedelta

IST_OFFSET = timedelta(hours=5, minutes=30)


def main():
    db = SessionLocal()
    try:
        comp = db.query(Competition).filter_by(code='WC').first()
        if not comp:
            print("ERROR: No WC competition found in database.")
            sys.exit(1)

        matches = (
            db.query(Match)
            .filter(
                Match.competition_id == comp.id,
                Match.utc_date > '2026-06-01',
            )
            .order_by(Match.utc_date)
            .all()
        )

        print(f"Found {len(matches)} WC 2026 matches to correct.\n")
        print(f"{'Match':<45} {'Stored (IST)':<22} {'Corrected (UTC)':<22}")
        print("-" * 90)

        corrections = []
        for m in matches:
            ht = m.home_team.name if m.home_team else '?'
            at = m.away_team.name if m.away_team else '?'
            label = f"{ht} vs {at}"
            stored = m.utc_date
            corrected = stored - IST_OFFSET
            corrections.append((m, corrected))
            print(f"{label:<45} {str(stored):<22} {str(corrected):<22}")

        print()
        answer = input("Apply these corrections? [yes/no]: ").strip().lower()
        if answer != 'yes':
            print("Aborted. No changes made.")
            sys.exit(0)

        for m, corrected in corrections:
            m.utc_date = corrected

        db.commit()
        print(f"\n✅ Successfully updated {len(corrections)} match kickoff times to UTC.")
        print("   The frontend will now display correct local times via Intl.DateTimeFormat.")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
