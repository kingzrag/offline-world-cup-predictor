
# Sample SofaScore responses based on API documentation
SAMPLE_LIVE_EVENTS = {
    "events": [
        {
            "id": 9620324,
            "homeTeam": {"name": "Moreirense", "id": 3014},
            "awayTeam": {"name": "FC Vizela", "id": 5136},
            "status": {"type": "inprogress", "code": 70},
            "homeScore": {"current": 2},
            "awayScore": {"current": 1},
            "time": {"currentPeriodStartTimestamp": 1719673200}
        }
    ]
}

SAMPLE_STATISTICS = {
    "statistics": [
        {
            "period": "ALL",
            "groups": [
                {
                    "groupName": "Ball possession",
                    "statisticsItems": [
                        {"name": "Ball possession", "home": "58", "away": "42", "compareCode": 0}
                    ]
                },
                {
                    "groupName": "Shots",
                    "statisticsItems": [
                        {"name": "Total shots", "home": "15", "away": "10", "compareCode": 1},
                        {"name": "Shots on target", "home": "8", "away": "4", "compareCode": 1},
                        {"name": "Blocked shots", "home": "2", "away": "3", "compareCode": -1},
                        {"name": "Shots off target", "home": "5", "away": "3", "compareCode": 1}
                    ]
                },
                {
                    "groupName": "Expected",
                    "statisticsItems": [
                        {"name": "Expected goals (xG)", "home": "1.8", "away": "0.7", "compareCode": 1}
                    ]
                },
                {
                    "groupName": "Goals",
                    "statisticsItems": [
                        {"name": "Corner kicks", "home": "6", "away": "3", "compareCode": 1}
                    ]
                },
                {
                    "groupName": "Fouls",
                    "statisticsItems": [
                        {"name": "Fouls", "home": "12", "away": "15", "compareCode": -1},
                        {"name": "Offsides", "home": "3", "away": "1", "compareCode": 1}
                    ]
                }
            ]
        }
    ]
}

SAMPLE_LINEUPS = {
    "home": {
        "team": {"name": "Moreirense", "id": 3014},
        "formation": "4-4-2",
        "players": [
            {
                "player": {"name": "Kewin", "id": 100001, "position": "G"},
                "substitute": False,
                "statistics": {"rating": 7.2}
            },
            {
                "player": {"name": "Pedro Amador", "id": 100002, "position": "D"},
                "substitute": False,
                "statistics": {"rating": 6.8}
            }
        ]
    },
    "away": {
        "team": {"name": "FC Vizela", "id": 5136},
        "formation": "4-3-3",
        "players": [
            {
                "player": {"name": "Ivanildo Fernandes", "id": 806515, "position": "D"},
                "substitute": False,
                "statistics": {"rating": 6.1}
            }
        ]
    }
}

SAMPLE_INCIDENTS = {
    "incidents": [
        {
            "id": 120319530,
            "time": 3,
            "isHome": False,
            "incidentClass": "red",
            "incidentType": "card",
            "playerName": "Ivanildo Fernandes",
            "reason": "Professional foul last man"
        },
        {
            "id": 120319531,
            "time": 15,
            "isHome": True,
            "incidentClass": "goal",
            "incidentType": "goal",
            "playerName": "André Claro",
            "reason": "Header from corner"
        },
        {
            "id": 120319532,
            "time": 30,
            "isHome": False,
            "incidentClass": "yellow",
            "incidentType": "card",
            "playerName": "Samu"
        }
    ]
}
