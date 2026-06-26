# Production Verification Report

Generated: 2026-06-26T13:10:49.834031Z

## Provider Verification

| Provider | Returns Real Data | Competitions | International Matches | Player Records | Statistics | Parsing Failures | Blocked Requests | Duplicate Prevention |
|---|---|---:|---:|---:|---:|---:|---:|---|
| FootballDataProvider | Yes | 13 | 127 | 0 | 0 | 0 | 0 | Yes |
| TransfermarktProvider | Yes | 0 | 0 | 9 | 0 | 24 | 0 | Yes |
| FBrefProvider | No | 10 | 0 | 0 | 0 | 0 | 7 | Yes |
| StatsBombProvider | Yes | 24 | 397 | 0 | 1 | 0 | 0 | Yes |
| APIFootballProvider | No | 0 | 0 | 0 | 0 | 0 | 1 | Yes |
| SofaScoreProvider | No | 0 | 0 | 0 | 0 | 0 | 1 | Yes |

## Database Rows Collected By Provider

| Provider | DB Competitions | DB International Matches | DB Player Records | DB Statistics | Total Rows |
|---|---:|---:|---:|---:|---:|
| FootballDataProvider | 14 | 7736 | 0 | 0 | 7736 |
| TransfermarktProvider | 0 | 0 | 7075 | 0 | 7131 |
| FBrefProvider | 0 | 0 | 0 | 0 | 0 |
| StatsBombProvider | 5 | 315 | 3821 | 19193 | 20384 |
| APIFootballProvider | 0 | 0 | 0 | 0 | 0 |
| SofaScoreProvider | 0 | 0 | 4 | 398 | 4 |

## Provider Notes

### FootballDataProvider
- Live probe: `{'WC': 76, 'EC': 51, 'CA': 0, 'UNL': 0, 'WWC': 0, 'OLY': 0, 'WCQ': 0}`
- Competition and match data verified via football-data.org API

### TransfermarktProvider
- Live probe: `{'teams_checked': 32, 'teams_with_records': 8}`
- Germany probe: injuries=0, suspensions=1, tables=2
- Transfermarkt is used here for injuries, suspensions, and squad data; competition/match/stat endpoints are not implemented in this provider.

### FBrefProvider
- Live probe: `{'WC': 0, 'EC': 0, 'CA': 0, 'UNL': 0, 'WWC': 0, 'OLY': 0, 'WCQ': 0}`
- FBref requests were blocked by Cloudflare in this runtime.

### StatsBombProvider
- Live probe: `{'WC': 147, 'EC': 102, 'CA': 32, 'WWC': 116, 'WCQ': 0, 'AFCON': 0}`
- AFCON currently maps to competition id 6, but StatsBomb Open Data returned no seasons for that id in this runtime.
- Sample match statistics verified on statsbomb_3943043

### APIFootballProvider
- Live probe: `{'WC': 0}`
- API key exists, but live responses returned account suspension / plan limitations.

### SofaScoreProvider
- Live probe: `{'live_matches': 0}`
- SofaScore is optional and primarily live-data oriented in this architecture.
- Current live probe returned no matches and the collector emitted challenge/403 behavior in this runtime.

## Final Summary

- **Providers returning real data**: FootballDataProvider, TransfermarktProvider, StatsBombProvider
- **Providers still needing work**: FBrefProvider, APIFootballProvider, SofaScoreProvider
- **International matches collected (DB)**: 7,974
- **Player statistics collected (DB)**: 18,800
- **Estimated pipeline completion**: 80.0%

## External Limitations

- FBref is blocked by Cloudflare from this runtime, preventing real-data scraping despite provider support code.
- API-Football is externally limited by account suspension / free-plan season restrictions in this environment.
- Transfermarkt delivery is inconsistent across national-team pages: some pages return parseable tables, others return app-shell/no-table HTML.
