import sys
import os

# Ensure the root of the project is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from services.model_service import model_service
from fastapi.testclient import TestClient
from api.main import app

def test_service_layer():
    print("--- Testing Python ModelService.predict Layer ---")
    db = SessionLocal()
    try:
        # Load models if not initialized
        if not model_service.is_ready:
            print("Loading models...")
            model_service.load_models()
            
        test_cases = [
            ("USA", "Brazil"),
            ("US", "Brazil"),
            ("United States", "Brazil"),
            ("United States of America", "Brazil")
        ]
        
        for home, away in test_cases:
            try:
                res = model_service.predict(db, home, away, competition_code="WC")
                print(f"  ✓ {home} vs {away}: SUCCESS! Resolved Home: '{res['home_team']}', Away: '{res['away_team']}'")
                assert res["home_team"] == "United States", f"Expected 'United States', got '{res['home_team']}'"
                assert res["away_team"] == "Brazil", f"Expected 'Brazil', got '{res['away_team']}'"
            except Exception as e:
                print(f"  ✗ {home} vs {away}: FAILED! Error: {e}")
                sys.exit(1)
    finally:
        db.close()

def test_api_layer():
    print("\n--- Testing FastAPI API Layer via TestClient ---")
    client = TestClient(app)
    
    # 1. Test Prediction endpoints for all aliases
    test_cases = [
        ("USA", "Brazil"),
        ("US", "Brazil"),
        ("United States", "Brazil"),
        ("United States of America", "Brazil")
    ]
    
    for home, away in test_cases:
        response = client.post("/api/predict", json={
            "home_team": home,
            "away_team": away,
            "competition_code": "WC"
        })
        print(f"  POST /api/predict ({home} vs {away}) status: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.json()}"
        data = response.json()
        assert data["status"] == "success"
        prediction = data["prediction"]
        assert prediction["home_team"] == "United States", f"Expected 'United States', got '{prediction['home_team']}'"
        assert prediction["away_team"] == "Brazil", f"Expected 'Brazil', got '{prediction['away_team']}'"
        print(f"    ✓ Resolved properly to {prediction['home_team']} vs {prediction['away_team']}")
        
    # 2. Test GET /api/teams search query
    print("\n--- Testing GET /api/teams?search=USA ---")
    response = client.get("/api/teams?search=USA")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    teams = data["teams"]
    print(f"  Search for 'USA' returned {len(teams)} teams.")
    found_us = False
    for t in teams:
        print(f"    • ID={t['id']} Name='{t['name']}' TLA='{t['tla']}' ShortName='{t['short_name']}'")
        if t["name"] == "United States":
            found_us = True
            assert t["tla"] == "USA", f"Expected TLA 'USA', got '{t['tla']}'"
            assert t["short_name"] == "USA", f"Expected short name 'USA', got '{t['short_name']}'"
    assert found_us, "United States team should be returned for search query 'USA'"
    print("  ✓ Search check passed!")

    # 3. Test GET /api/team/USA profile query
    print("\n--- Testing GET /api/team/USA ---")
    response = client.get("/api/team/USA")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    team = data["team"]
    print(f"  Profile lookup resolved to Name='{team['name']}' TLA='{team['tla']}'")
    assert team["name"] == "United States", f"Expected 'United States', got '{team['name']}'"
    assert team["tla"] == "USA", f"Expected TLA 'USA', got '{team['tla']}'"
    print("  ✓ Profile check passed!")

if __name__ == "__main__":
    test_service_layer()
    test_api_layer()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! ✓")
