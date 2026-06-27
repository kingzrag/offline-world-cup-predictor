# Frontend Prediction UI Mapping Audit Report

**Date:** June 27, 2026  
**Objective:** Audit the prediction UI for probability-to-team mapping issues

---

## Executive Summary

**Verdict:** ✅ **NO FRONTEND MAPPING BUGS FOUND**

The frontend correctly maps probabilities to team names in all components. The perceived issue is caused by a **data source discrepancy** between the CSV audit file and the database, not a frontend mapping bug.

---

## Data Flow Trace

### Step 1: Backend API Response

**File:** `api/routes/predict.py`  
**Endpoint:** `/api/fixtures-enriched`

Backend returns:
```json
{
  "home_team": { "name": "England" },
  "away_team": { "name": "Panama" },
  "prediction": {
    "home_probability": 0.8559,
    "draw_probability": 0.1227,
    "away_probability": 0.0214
  }
}
```

### Step 2: API Layer Mapping

**File:** `offline/src/api.ts`  
**Function:** `mapFixtureToPrediction()` (Lines 687-729)

```typescript
const teamA = f.home_team?.name ?? "Unknown";  // "England"
const teamB = f.away_team?.name ?? "Unknown";  // "Panama"

probA = Math.round(p.home_probability * 100);  // 86 (England)
probD = Math.round(p.draw_probability * 100);   // 12
probB = Math.round(p.away_probability * 100);  // 2 (Panama)
```

**✅ CORRECT MAPPING:**
- `home_probability` → `probA` (teamA = home_team)
- `away_probability` → `probB` (teamB = away_team)

### Step 3: UI Components - All Verified CORRECT

#### Component 1: BestPredictionsCarousel.tsx

**Location:** Lines 192-197

```typescript
<span>{match.teamACode} {match.probA}%</span>  // ENG 86%
<span>Draw {match.probD}%</span>               // Draw 12%
<span>{match.teamBCode} {match.probB}%</span>  // PAN 2%
```

**✅ CORRECT:** teamA (England) with probA (86%), teamB (Panama) with probB (2%)

#### Component 2: App.tsx - Match Cards

**Location:** Lines 2200-2202

```typescript
<span>{match.teamACode} {match.probA}%</span>
<span>Draw {match.probD}%</span>
<span>{match.teamBCode} {match.probB}%</span>
```

**✅ CORRECT:** Same mapping as above

#### Component 3: App.tsx - Hero Section

**Location:** Lines 2318-2320

```typescript
<span>{match.teamACode} Win: {match.probA}%</span>
<span>Draw: {match.probD}%</span>
<span>{match.teamBCode} Win: {match.probB}%</span>
```

**✅ CORRECT:** Same mapping with "Win" label added

#### Component 4: App.tsx - Match Detail Modal

**Location:** Lines 4703-4712

```typescript
<div>
  <span>{match.teamA} Win</span>
  <span>{match.teamA} Win: {probA}%</span>
</div>
<div>
  <span>Draw</span>
  <span>Draw: {probD}%</span>
</div>
<div>
  <span>{match.teamB} Win</span>
  <span>{match.teamB} Win: {probB}%</span>
</div>
```

**✅ CORRECT:** teamA (England) with probA, teamB (Panama) with probB

#### Component 5: App.tsx - Dynamic Probabilities Bar

**Location:** Lines 4577-4584

```typescript
<div style={{ width: `${match.probA}%` }}></div>  // Green bar for teamA
<div style={{ width: `${match.probD}%` }}></div>  // Gray bar for draw
<div style={{ width: `${match.probB}%` }}></div>  // Dark bar for teamB
```

**✅ CORRECT:** Visual bars match probability values

---

## Search Results

### Searched Terms
- `home_probability` - Found only in `api.ts` (backend mapping layer)
- `away_probability` - Found only in `api.ts` (backend mapping layer)
- `teamA` - Found in all components, always mapped to `probA`
- `teamB` - Found in all components, always mapped to `probB`
- `probA` - Always associated with teamA/home_team
- `probB` - Always associated with teamB/away_team

### Team Name Labels
All instances where team names replaced "Home Win"/"Away Win":
- Lines 2318, 2320: `{match.teamACode} Win: {match.probA}%`
- Lines 4703, 4711: `{match.teamA} Win`, `{match.teamB} Win`

**✅ ALL CORRECT:** Team names are used as labels, but the underlying probability mapping remains correct.

---

## Root Cause Analysis

### The Real Issue

The perceived mapping issue is caused by a **data source discrepancy**, not a frontend bug:

**CSV Audit Data (`next_fixtures_audit_data.csv`):**
```
Panama,England,0.4513,1.8366  # Panama home, England away
```

**Database:**
```
England vs Panama (England home, Panama away)
```

**Backend Raw Model (England home):**
```
Home Win: 85.59% (England)
Draw: 12.27%
Away Win: 2.14% (Panama)
```

**CSV xG values (Panama home):**
```
Panama xG: 0.45
England xG: 1.84
```

This explains why the CSV data appears to show "wrong" probabilities - it's using a different home/away assignment than the database.

---

## Verification for All 4 Matches

### England vs Panama
- **Database:** England home, Panama away
- **Frontend Display:** England 86%, Draw 12%, Panama 2%
- **✅ CORRECT:** Matches backend `home_probability` for England

### Colombia vs Portugal
- **Database:** Colombia home, Portugal away
- **Frontend Display:** Colombia 51%, Draw 31%, Portugal 18%
- **✅ CORRECT:** Matches backend `home_probability` for Colombia

### Jordan vs Argentina
- **Database:** Jordan home, Argentina away
- **Frontend Display:** Jordan 3%, Draw 1%, Argentina 96%
- **✅ CORRECT:** Matches backend `away_probability` for Argentina

### Croatia vs Ghana
- **Database:** Croatia home, Ghana away
- **Frontend Display:** Croatia 48%, Draw 24%, Ghana 28%
- **✅ CORRECT:** Matches backend `home_probability` for Croatia

---

## Files Modified

**NONE** - No frontend code changes required.

---

## Why the Bug Happened

The bug did NOT happen in the frontend. The confusion arose from:

1. **CSV audit file** was generated with different home/away assignments than the database
2. **User compared CSV data** (which had Panama as home) to frontend display (which shows England as home)
3. **Different home/away assignments** result in different probability distributions

---

## How It Was Fixed

**No fix needed** - The frontend is working correctly. The issue is in the CSV audit data generation process, which should be investigated separately.

---

## Confirmation

Every prediction page and modal uses the correct team-to-probability mapping:

- ✅ Match Cards: `teamA` ↔ `probA`, `teamB` ↔ `probB`
- ✅ Best Predictions Carousel: `teamA` ↔ `probA`, `teamB` ↔ `probB`
- ✅ Hero Section: `teamA` ↔ `probA`, `teamB` ↔ `probB`
- ✅ Match Detail Modal: `teamA` ↔ `probA`, `teamB` ↔ `probB`
- ✅ Dynamic Probabilities Bar: `probA` bar for teamA, `probB` bar for teamB

**The UI is preserving the improved team-name labels while maintaining correct probability mapping.**

---

## Recommendation

Investigate the CSV audit data generation process to ensure it uses the same home/away assignments as the database. The frontend code is working correctly and requires no changes.

---

**Report Generated:** June 27, 2026  
**Audit Status:** Complete  
**Frontend Status:** ✅ No bugs found
