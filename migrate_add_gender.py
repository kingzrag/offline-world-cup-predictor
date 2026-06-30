#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/Users/anuragsaikia/prediction')

from database.connection import SessionLocal, engine
from sqlalchemy import text
from models import Team

with engine.connect() as conn:
    trans = conn.begin()
    try:
        print("Adding gender column to teams table...")
        # Use VARCHAR first for simplicity and compatibility, then we can map
        conn.execute(text("ALTER TABLE teams ADD COLUMN IF NOT EXISTS gender VARCHAR(10) DEFAULT 'MEN'"))
        
        # Set index
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_teams_gender ON teams(gender)"))
        
        trans.commit()
        print("✅ Column and index added successfully!")
    except Exception as e:
        trans.rollback()
        print(f"❌ Adding column failed: {str(e)}")
        raise

# Now update using orm
db = SessionLocal()
try:
    teams = db.query(Team).all()
    updated = 0
    for t in teams:
        if any(sub in t.name.lower() for sub in ["women", "women's", "woman"]):
            t.gender = "WOMEN"
            updated +=1
    db.commit()
    print(f"✅ Updated {updated} women's teams!")
except Exception as e:
    db.rollback()
    print(f"❌ Updating genders failed: {str(e)}")
    raise
finally:
    db.close()

