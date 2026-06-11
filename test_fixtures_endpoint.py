import sys
import os
from fastapi.testclient import TestClient
from api.main import app
from database.connection import SessionLocal
from models import Match, Competition

def test_fixtures_endpoint():
    client = TestClient(app)
    
    # 1. Test standard GET /api/fixtures (defaults to WC)
    response = client.get("/api/fixtures")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "fixtures" in data
    assert isinstance(data["fixtures"], list)
    print(f"✓ Found {len(data['fixtures'])} fixtures for default (WC)")
    
    if len(data["fixtures"]) > 0:
        fixture = data["fixtures"][0]
        # Verify required fields
        required_fields = {
            "id", "kickoff_time", "status", "stage", "group", 
            "venue", "competition", "home_team", "away_team", 
            "live_score", "winner"
        }
        for field in required_fields:
            assert field in fixture, f"Field '{field}' missing from fixture output"
        print("✓ All required fields present in fixture structure")
        
        # Verify team structure
        for team_key in ("home_team", "away_team"):
            team = fixture[team_key]
            if team:
                for subfield in ("id", "name", "short_name", "tla", "crest_url"):
                    assert subfield in team, f"Subfield '{subfield}' missing from team {team_key}"
        print("✓ Team structures validated")

    # 2. Test with invalid competition code
    response = client.get("/api/fixtures?competition_code=INVALID")
    assert response.status_code == 404
    print("✓ 404 returned for invalid competition code")

    # 3. Test filtering by status
    response = client.get("/api/fixtures?status=FINISHED")
    assert response.status_code == 200
    data = response.json()
    for f in data["fixtures"]:
        assert f["status"] == "FINISHED"
    print(f"✓ Succeeded querying by FINISHED status: {len(data['fixtures'])} fixtures")

    # 4. Test filtering by stage
    response = client.get("/api/fixtures?stage=GROUP_STAGE")
    assert response.status_code == 200
    data = response.json()
    for f in data["fixtures"]:
        assert f["stage"] == "GROUP_STAGE"
    print(f"✓ Succeeded querying by GROUP_STAGE stage: {len(data['fixtures'])} fixtures")

    print("✓ All GET /api/fixtures tests passed successfully!")

if __name__ == "__main__":
    test_fixtures_endpoint()
