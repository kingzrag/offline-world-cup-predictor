#!/usr/bin/env python3
"""
Database connectivity diagnostic & initialization script.

Usage:
    python3 test_db.py

This script will:
  1. Detect the current OS user and PostgreSQL configuration
  2. List available PostgreSQL roles and databases
  3. Create the prediction_db database if it doesn't exist
  4. Verify SQLAlchemy connectivity
  5. Create all tables from the ORM models
  6. Print a summary report
"""
import subprocess
import sys
import getpass
import os


def run_psql(sql: str, db: str = "postgres") -> str:
    """Execute a psql command and return its output."""
    try:
        result = subprocess.run(
            ["psql", "-d", db, "-t", "-A", "-c", sql],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return f"[ERROR] {result.stderr.strip()}"
        return result.stdout.strip()
    except FileNotFoundError:
        return "[ERROR] psql not found — is PostgreSQL installed?"
    except subprocess.TimeoutExpired:
        return "[ERROR] psql command timed out"


def main():
    print("=" * 60)
    print("  Football Prediction Platform — Database Diagnostics")
    print("=" * 60)

    # 1. Current user
    current_user = getpass.getuser()
    print(f"\n[1] Current OS user:  {current_user}")
    print(f"    Running in Docker: {os.path.exists('/.dockerenv')}")

    # 2. Available roles
    print("\n[2] PostgreSQL Roles:")
    roles = run_psql("SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg_%';")
    if roles.startswith("[ERROR]"):
        print(f"    {roles}")
        print("\n    → Make sure PostgreSQL is running:")
        print("      brew services start postgresql@15")
        sys.exit(1)
    for role in roles.split("\n"):
        if role.strip():
            marker = " ← (you)" if role.strip() == current_user else ""
            print(f"    • {role.strip()}{marker}")

    # 3. Available databases
    print("\n[3] PostgreSQL Databases:")
    databases = run_psql("SELECT datname FROM pg_database WHERE datistemplate = false;")
    for db in databases.split("\n"):
        if db.strip():
            print(f"    • {db.strip()}")

    # 4. Create prediction_db if missing
    db_name = "prediction_db"
    exists = run_psql(f"SELECT 1 FROM pg_database WHERE datname='{db_name}';")
    if exists.strip() == "1":
        print(f"\n[4] Database '{db_name}' already exists. ✓")
    else:
        print(f"\n[4] Database '{db_name}' not found. Creating...")
        create_result = run_psql(f"CREATE DATABASE {db_name};")
        if "[ERROR]" in create_result:
            print(f"    {create_result}")
            sys.exit(1)
        print(f"    Database '{db_name}' created successfully. ✓")

    # 5. Build DATABASE_URL and verify SQLAlchemy connectivity
    print("\n[5] SQLAlchemy Connectivity Test:")
    # Import settings — this also validates the .env and config
    try:
        from utils.config import settings
        db_url = settings.DATABASE_URL
        # Mask password for display
        display_url = db_url
        if settings.DATABASE_PASSWORD:
            display_url = db_url.replace(settings.DATABASE_PASSWORD, "****")
        print(f"    DATABASE_URL = {display_url}")
    except Exception as e:
        print(f"    [ERROR] Failed to load settings: {e}")
        sys.exit(1)

    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"    Connected successfully. ✓")
            print(f"    PostgreSQL version: {version}")
    except Exception as e:
        print(f"    [ERROR] SQLAlchemy connection failed: {e}")
        print(f"\n    → Suggested fix:")
        print(f"      Ensure your .env or environment has the correct DATABASE_USER.")
        print(f"      For macOS local dev, your user is: {current_user}")
        sys.exit(1)

    # 6. Create all ORM tables
    print("\n[6] Creating ORM tables (if they don't exist)...")
    try:
        from database.base import Base
        # Import all models so Base.metadata has them registered
        import models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        
        # List the tables
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
            ))
            tables = [row[0] for row in result]
        print(f"    Tables in prediction_db ({len(tables)}):")
        for t in tables:
            print(f"      • {t}")
        print("    Schema sync completed. ✓")
    except Exception as e:
        print(f"    [ERROR] Table creation failed: {e}")
        sys.exit(1)

    # 7. Summary
    print("\n" + "=" * 60)
    print("  ✅  All checks passed. Database is ready for use.")
    print("=" * 60)
    print(f"\n  To start the server:")
    print(f"    uvicorn api.main:app --reload")
    print(f"\n  To collect data:")
    print(f"    python3 collect_odds.py")
    print(f"    python3 collect_elo.py")
    print()


if __name__ == "__main__":
    main()
