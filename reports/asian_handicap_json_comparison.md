# Asian Handicap JSON Before/After Comparison

## Problem
The Asian Handicap section was displaying "No Asian Handicap predictions available" because the API response structure did not match what the frontend expected.

## Root Cause
The Poisson engine returns handicap data with field names `favored_team_prefix` and `suggested_lines`, but the frontend expects `label`, `lines`, and `favored_team`.

## JSON Structure Comparison

### BEFORE FIX (from `/api/fixtures-enriched`)

```json
{
    "markets": {
        "btts": {...},
        "over_under": {...},
        "clean_sheet": {...},
        "most_likely_score": "1-1",
        "top_5_scorelines": [...],
        "team_goals": {...},
        "asian_handicap": {
            "favored_team_prefix": "Home",
            "suggested_lines": {
                "Home -0.25": 0.4257,
                "Home -0.5": 0.4257,
                "Home -0.75": 0.3254,
                "Home -1.0": 0.225
            }
        }
    }
}
```

**Frontend expectation** (from `offline/src/App.tsx`):
```typescript
{match.asianHandicap && Object.keys(match.asianHandicap.lines).length > 0 ? (
  // Render cards
) : (
  // Show "No Asian Handicap predictions available."
)}
```

**Problem**: 
- Frontend looks for `match.asianHandicap.lines`
- API returns `asian_handicap.suggested_lines`
- Frontend sees `lines` as undefined → displays fallback message

### AFTER FIX (from `/api/fixtures-enriched`)

```json
{
    "markets": {
        "btts": {...},
        "over_under": {...},
        "clean_sheet": {...},
        "most_likely_score": "1-1",
        "top_5_scorelines": [...],
        "team_goals": {...},
        "asian_handicap": {
            "label": "Home -0.5",
            "lines": {
                "Home -0.25": 0.4257,
                "Home -0.5": 0.4257,
                "Home -0.75": 0.3254,
                "Home -1.0": 0.225
            },
            "favored_team": "Home"
        }
    }
}
```

**Fix applied** in `api/routes/predict.py`:
```python
def _build_enrichment_from_xg(...):
    poisson = evaluate_poisson_engine(max(h_xg, 0.01), max(a_xg, 0.01))
    
    # Transform Poisson handicap structure to match frontend expectations
    poisson_handicap = poisson["asian_handicap"]
    asian_handicap = {
        "label": poisson_handicap.get("favored_team_prefix", "Home") + " -0.5",
        "lines": poisson_handicap.get("suggested_lines", {}),
        "favored_team": poisson_handicap.get("favored_team_prefix", "Home"),
    }
    
    return {
        "markets": {
            ...
            "asian_handicap": asian_handicap,
        },
    }
```

## Field Mapping

| Poisson Engine Field | Frontend Expected Field | Transformation |
|---------------------|------------------------|----------------|
| `favored_team_prefix` | `favored_team` | Direct copy |
| `suggested_lines` | `lines` | Direct copy |
| (none) | `label` | Generated as `{favored_team} -0.5` |

## Additional Safeguards

1. **ML Model Fallback**: If ML model returns empty lines, generate from Poisson
2. **Comprehensive Logging**: Added logging at each stage to trace data flow
3. **Structure Validation**: Check for empty lines and regenerate if needed

## Verification

After the fix:
- ✅ API returns `asian_handicap.lines` with handicap probabilities
- ✅ Frontend receives non-empty lines object
- ✅ Section 5 displays handicap cards instead of fallback message
- ✅ All handicap lines (-0.25, -0.5, -0.75, -1.0) are present with probabilities

## Test Case: Argentina vs France

**API Response** (after fix):
```json
{
    "enrichment": {
        "markets": {
            "asian_handicap": {
                "label": "Home -0.5",
                "lines": {
                    "Home -0.25": 0.4257,
                    "Home -0.5": 0.4257,
                    "Home -0.75": 0.3254,
                    "Home -1.0": 0.225
                },
                "favored_team": "Home"
            }
        }
    }
}
```

**Frontend Rendering**:
- Section 5 displays 4 handicap cards
- Each card shows: Handicap line, Probability %, Progress bar, Strength label
- AI PICK badge shows for probabilities ≥ 90%
