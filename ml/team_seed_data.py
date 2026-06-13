"""
ml/team_seed_data.py
====================
Pre-computed team metadata for seeding a fresh database.
Includes FIFA rankings and squad market values (€M) for the 2026 World Cup.

These values are used by extract_ml_features() to produce meaningful features
when the full data pipeline hasn't been run yet.

Sources:
  - FIFA rankings: FIFA.com (June 2025 release)
  - Squad market values: Transfermarkt.com (June 2025 estimates, in €M)
"""

# fmt: off
# (fifa_ranking, squad_market_value_in_millions_eur)
TEAM_DATA: dict[str, tuple[int, float]] = {
    # Top 20
    "Argentina":            (1,   590.0),
    "France":               (2,   1280.0),
    "Spain":                (3,   1040.0),
    "England":              (4,   1520.0),
    "Brazil":               (5,   950.0),
    "Portugal":             (6,   820.0),
    "Netherlands":          (7,   640.0),
    "Belgium":              (8,   460.0),
    "Italy":                (9,   650.0),
    "Germany":              (10,  880.0),
    "Uruguay":              (11,  320.0),
    "Colombia":             (12,  340.0),
    "Croatia":              (13,  310.0),
    "Morocco":              (14,  340.0),
    "Japan":                (15,  280.0),
    "United States":        (16,  230.0),
    "Mexico":               (17,  140.0),
    "Switzerland":          (18,  310.0),
    "Denmark":              (19,  360.0),
    "Austria":              (20,  280.0),
    # 21-40
    "Senegal":              (21,  240.0),
    "Iran":                 (22,  80.0),
    "Turkey":               (23,  380.0),
    "Australia":            (24,  90.0),
    "Ecuador":              (25,  180.0),
    "Poland":               (26,  260.0),
    "South Korea":          (27,  180.0),
    "Sweden":               (28,  200.0),
    "Canada":               (29,  190.0),
    "Nigeria":              (30,  210.0),
    "Serbia":               (31,  280.0),
    "Hungary":              (32,  210.0),
    "Scotland":             (33,  180.0),
    "Norway":               (34,  330.0),
    "Chile":                (35,  120.0),
    "Egypt":                (36,  140.0),
    "Ghana":                (37,  100.0),
    "Algeria":              (38,  130.0),
    "Cameroon":             (39,  120.0),
    "Ivory Coast":          (40,  160.0),
    # 41-60 (potential qualifiers / group opponents)
    "Saudi Arabia":         (41,  30.0),
    "Tunisia":              (42,  70.0),
    "Peru":                 (43,  90.0),
    "Venezuela":            (44,  110.0),
    "Paraguay":             (45,  80.0),
    "Czech Republic":       (46,  200.0),
    "Panama":               (47,  25.0),
    "Jamaica":              (48,  50.0),
    "Bolivia":              (49,  20.0),
    "Honduras":             (50,  18.0),
    "Costa Rica":           (51,  35.0),
    "Qatar":                (52,  15.0),
    "New Zealand":          (53,  12.0),
    "Uzbekistan":           (54,  25.0),
    "DR Congo":             (55,  80.0),
    "Slovenia":             (56,  160.0),
    "Albania":              (57,  110.0),
    "Georgia":              (58,  120.0),
    "Bosnia and Herzegovina": (59, 80.0),
    "Ukraine":              (60,  200.0),
    # Common aliases
    "Bosnia & Herzegovina": (59,  80.0),
    "USA":                  (16,  230.0),
    "Republic of Ireland":  (62,  60.0),
    "Wales":                (61,  80.0),
    "Slovakia":             (63,  120.0),
}
# fmt: on
