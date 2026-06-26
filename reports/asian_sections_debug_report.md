# Debug Report: Asian Total and Asian Handicap Sections Not Appearing

## Executive Summary
The Asian Total and Asian Handicap sections were not appearing in the Match Analysis modal because the backend API endpoint `/api/fixtures-enriched` was not including `asian_handicap` data in the enrichment response. This has been fixed by updating the enrichment mapping functions in `api/routes/predict.py`.

## Data Flow Analysis

### 1. Backend Response Structure

**Source**: `services/model_service.py` (lines 302-306)

The `predict_goals` method correctly returns `asian_handicap` in the markets object:

```python
"asian_handicap": {
    "label":        asian_handicap_label,
    "lines":        poisson["asian_handicap"]["suggested_lines"],
    "favored_team": poisson["asian_handicap"]["favored_team_prefix"],
},
```

**Source**: `services/poisson_engine.py` (lines 156-159)

The Poisson engine generates handicap lines:

```python
return {
    "favored_team_prefix": prefix,  # "Home" or "Away"
    "suggested_lines": results      # {"Home -0.25": 0.72, "Home -0.5": 0.68, ...}
}
```

### 2. API Endpoint Response

**Source**: `api/routes/predict.py` (lines 101-146)

**BEFORE FIX** - `_build_enrichment_from_xg` function was missing `asian_handicap`:

```python
return {
    "goals": {...},
    "markets": {
        "btts":              poisson["btts"],
        "over_under":        poisson["over_under"],
        "clean_sheet":       poisson["clean_sheet"],
        "most_likely_score": most_likely_score or poisson["most_likely_score"],
        "top_5_scorelines":  poisson["top_5_scorelines"],
        "team_goals":        poisson["team_goals"],
        # ❌ MISSING: "asian_handicap"
    },
}
```

**BEFORE FIX** - `_build_enrichment_from_prediction` function was missing `asian_handicap`:

```python
return {
    "goals": {...},
    "markets": {
        "btts":              markets["btts"],
        "over_under":        markets["over_under"],
        "clean_sheet":       markets.get("clean_sheet"),
        "most_likely_score": markets["most_likely_score"],
        "top_5_scorelines":  markets["top_5_scorelines"],
        "team_goals":        markets["team_goals"],
        # ❌ MISSING: "asian_handicap"
    },
}
```

### 3. Frontend Data Mapping

**Source**: `offline/src/api.ts` (line 570)

Frontend correctly maps the backend field:

```typescript
asianHandicap: m.asian_handicap,
```

### 4. Frontend Conditional Rendering

**Source**: `offline/src/App.tsx` (line 4584)

Asian Handicap section checks for data existence:

```typescript
{match.asianHandicap && Object.keys(match.asianHandicap.lines).length > 0 ? (
  // Render cards
) : (
  // Show "No Asian Handicap predictions available."
)}
```

Asian Total section (Section 4) uses computed values from `overUnder` data, which IS present in the backend response.

## Root Cause

The `/api/fixtures-enriched` endpoint uses `_build_enrichment_from_xg` and `_build_enrichment_from_prediction` to construct the enrichment response. Both functions were missing the `asian_handicap` field, so the frontend never received this data even though:

1. The Poisson engine correctly generates handicap probabilities
2. The model service correctly includes handicap data in full predictions
3. The frontend correctly expects and handles handicap data

## Fix Applied

**File**: `api/routes/predict.py`

**Change 1** - Added to `_build_enrichment_from_xg` (line 124):
```python
"asian_handicap":    poisson["asian_handicap"],
```

**Change 2** - Added to `_build_enrichment_from_prediction` (line 146):
```python
"asian_handicap":    markets.get("asian_handicap"),
```

## Verification

After the fix:
- `/api/fixtures-enriched` will return `asian_handicap` in the `markets.enrichment` object
- Frontend will receive `match.asianHandicap` with structure:
  ```typescript
  {
    label: "Home -0.5",
    lines: {"Home -0.25": 0.72, "Home -0.5": 0.68, ...},
    favored_team: "Home"
  }
  ```
- Asian Handicap section (Section 5) will render with handicap cards
- Asian Total section (Section 4) will continue to render using existing `overUnder` data

## Notes

- **Asian Total section**: Uses `overUnder` data (already present in backend), so it should render correctly once the enrichment is populated
- **Asian Handicap section**: Requires the fix to receive handicap data from the backend
- **No frontend changes needed**: The frontend code was correct; only the backend enrichment mapping needed to be fixed
- **No UI redesign needed**: The sections will render with the existing design once data is available
