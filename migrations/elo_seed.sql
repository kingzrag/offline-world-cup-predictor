-- Computing ELO from data/international/results.csv ...
-- Computed ELO for 336 teams.
-- Exporting 100 teams.

-- =================================================================
-- ELO Seed: generated from international results CSV
-- Generated at: 2026-06-13 08:48:11 UTC
-- =================================================================

BEGIN;

INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Abkhazia', 1638, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Albania', 1703, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Algeria', 1866, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Andalusia', 1620, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Argentina', 2154, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Australia', 1904, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Austria', 1900, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Basque Country', 1826, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Belgium', 1941, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Bolivia', 1729, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Bosnia and Herzegovina', 1656, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Brazil', 2039, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Burkina Faso', 1637, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Cameroon', 1725, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Canada', 1903, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Cape Verde', 1669, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Catalonia', 1705, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Chile', 1774, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Colombia', 2028, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Costa Rica', 1730, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Croatia', 1964, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Czech Republic', 1804, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Czechoslovakia', 1787, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('DR Congo', 1760, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Denmark', 1919, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Ecuador', 1997, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Egypt', 1809, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('England', 2088, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('France', 2134, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Georgia', 1716, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('German DR', 1709, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Germany', 2031, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Ghana', 1617, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Greece', 1817, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Guatemala', 1650, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Guernsey', 1747, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Haiti', 1684, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Honduras', 1696, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Hungary', 1778, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Iceland', 1616, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Iran', 1893, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Iraq', 1746, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Iraqi Kurdistan', 1653, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Isle of Man', 1700, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Isle of Wight', 1669, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Israel', 1666, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Italy', 1929, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Ivory Coast', 1801, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Jamaica', 1677, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Japan', 2010, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Jersey', 1802, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Jordan', 1777, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Kernow', 1609, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Kosovo', 1778, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Kárpátalja', 1607, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Mali', 1700, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Mexico', 1947, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Morocco', 2017, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Netherlands', 2022, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('New Zealand', 1732, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Nigeria', 1877, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('North Macedonia', 1635, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Northern Cyprus', 1703, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Northern Ireland', 1660, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Norway', 1982, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Occitania', 1690, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Oman', 1616, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Padania', 1684, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Panama', 1821, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Paraguay', 1892, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Peru', 1748, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Poland', 1787, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Portugal', 2032, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Qatar', 1616, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Republic of Ireland', 1767, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Rhodes', 1600, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Romania', 1689, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Russia', 1844, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Saudi Arabia', 1706, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Scotland', 1851, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Senegal', 1898, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Serbia', 1816, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Slovakia', 1744, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Slovenia', 1751, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('South Africa', 1670, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('South Korea', 1888, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Spain', 2217, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Sweden', 1780, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Switzerland', 1962, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Tunisia', 1733, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Turkey', 1964, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Ukraine', 1804, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('United Arab Emirates', 1687, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('United States', 1906, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Uruguay', 1950, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Uzbekistan', 1841, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Venezuela', 1786, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Wales', 1779, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Ynys Môn', 1648, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();
INSERT INTO team_elo (team_name, elo_rating, last_updated) VALUES ('Yugoslavia', 1851, NOW()) ON CONFLICT (team_name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();

COMMIT;

-- Done. 100 ELO ratings upserted.
