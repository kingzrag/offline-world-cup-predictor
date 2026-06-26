
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from services.transfermarkt_service import TransfermarktService
from utils.logger import logger

print("="*80)
print("RUNNING FULL TRANSFERMARKT INJURY/SUSPENSION INGESTION")
print("="*80)

db = SessionLocal()
try:
    tm_service = TransfermarktService()

    inj_summary = tm_service.ingest_injuries(db, "WC")
    print(f"\n✅ Injuries: {inj_summary}")

    susp_summary = tm_service.ingest_suspensions(db, "WC")
    print(f"\n✅ Suspensions: {susp_summary}")

    db.commit()
    print("\n✅ Done!")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
