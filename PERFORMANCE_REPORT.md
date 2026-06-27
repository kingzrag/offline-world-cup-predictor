# Backend API Performance Optimization Report

**Date:** June 27, 2026  
**Objective:** Optimize backend API for production performance without altering existing functionality or prediction outputs.

---

## Executive Summary

This report details the performance optimizations implemented to improve the backend API response times, reduce database load, and enhance overall system efficiency. All changes maintain backward compatibility and do not affect prediction outputs or business logic.

### Key Improvements

- **Prediction caching:** Reduced redundant ML inference by 15-minute in-memory cache
- **Tournament simulation caching:** 5-minute cache for expensive Monte Carlo simulations
- **Team statistics caching:** 10-minute cache for team profile queries
- **Intelligence calculations caching:** 5-minute cache for 16-metric intelligence computations
- **Database indexing:** Added indexes on frequently queried columns
- **Query optimization:** Eliminated duplicate queries and implemented batch reads
- **Background jobs:** Moved ELO recomputation to async background processing
- **Timing logs:** Added comprehensive timing instrumentation to all endpoints

---

## 1. Endpoint Timing Analysis

### Before Optimization (Estimated Baseline)

| Endpoint | Typical Response Time | Bottleneck |
|----------|---------------------|------------|
| POST /api/predict | 500-2000ms | ML inference, no caching |
| POST /api/predict-batch | 10-30s | Sequential ML inference |
| GET /api/fixtures-enriched | 20-60s | N+1 queries, no caching |
| GET /api/team/{name} | 200-800ms | Multiple DB queries |
| GET /api/tournament/simulation | 5-15s | Monte Carlo simulation |
| GET /api/h2h/{a}/{b} | 100-500ms | Match history queries |

### After Optimization (Expected)

| Endpoint | Expected Response Time | Improvement |
|----------|----------------------|-------------|
| POST /api/predict | 5-50ms (cache hit), 500-2000ms (miss) | **95%+ reduction on cache hits** |
| POST /api/predict-batch | 5-50ms (cache hit), 10-30s (miss) | **95%+ reduction on cache hits** |
| GET /api/fixtures-enriched | 2-5s | **75-90% reduction** |
| GET /api/team/{name} | 5-50ms (cache hit), 200-800ms (miss) | **95%+ reduction on cache hits** |
| GET /api/tournament/simulation | 5-50ms (cache hit), 5-15s (miss) | **95%+ reduction on cache hits** |
| GET /api/h2h/{a}/{b} | 100-500ms | Optimized via indexing |

---

## 2. Slow SQL Queries and Indexing

### Indexes Added

#### Matches Table
- `ix_matches_home_team_id` - Improves queries filtering by home team
- `ix_matches_away_team_id` - Improves queries filtering by away team
- `ix_matches_competition_status_date` - Composite index for common fixture queries

#### Teams Table
- `ix_teams_name` - Speeds up team name searches
- `ix_teams_short_name` - Speeds up short name lookups
- `ix_teams_tla` - Speeds up TLA (three-letter abbreviation) queries

#### Predictions Table
- `ix_predictions_match_id` - Improves prediction lookups by match

#### Injuries/Suspensions Tables
- `ix_injuries_team_id` - Batch injury queries for teams
- `ix_suspensions_team_id` - Batch suspension queries for teams

### Migration Script

Created migration: `alembic/versions/20260627_0005_add_performance_indexes.py`

```python
# Key indexes added:
- matches.home_team_id
- matches.away_team_id
- matches(competition_id, status, utc_date) - composite
- teams.name
- teams.short_name
- teams.tla
- predictions.match_id
- injuries.team_id
- suspensions.team_id
```

---

## 3. Cache Implementation

### 3.1 Prediction Result Cache

**Location:** `api/routes/predict.py`  
**TTL:** 15 minutes  
**Key:** `home_team|away_team|competition_code`

```python
_prediction_cache: Dict[str, Tuple[Any, float]] = {}
PREDICTION_CACHE_TTL_SECONDS: int = 15 * 60
```

**Benefits:**
- Eliminates redundant ML inference for identical match predictions
- Cache hit ratio tracked via `/api/health` endpoint
- Expected hit ratio: 60-80% in production

### 3.2 Tournament Simulation Cache

**Location:** `api/routes/tournament.py`  
**TTL:** 5 minutes  
**Key:** Single global cache for simulation results

```python
_tournament_simulation_cache = {
    "result": None,
    "timestamp": 0,
    "ttl": 300
}
```

**Benefits:**
- Avoids expensive 1000-iteration Monte Carlo simulations
- Returns results in <50ms on cache hit vs 5-15s on miss

### 3.3 Team Statistics Cache

**Location:** `api/routes/predict.py`  
**TTL:** 10 minutes  
**Key:** `team_profile_{team_name}`

```python
_team_stats_cache = {}
_team_stats_cache_ttl = 600
```

**Benefits:**
- Caches team profile data including recent form, ELO, injuries
- Reduces database queries for frequently accessed teams

### 3.4 Intelligence Calculations Cache

**Location:** `services/intelligence_service.py`  
**TTL:** 5 minutes  
**Key:** `match_id`

```python
_intelligence_cache = {}
_intelligence_cache_ttl = 300
```

**Benefits:**
- Caches expensive 16-metric intelligence computations
- Avoids repeated database queries for match statistics

### Cache Statistics

Available via `GET /api/health`:

```json
{
  "cache_stats": {
    "hits": 1234,
    "misses": 567,
    "total_requests": 1801,
    "hit_ratio_percent": 68.52
  }
}
```

---

## 4. Database Query Optimization

### 4.1 Duplicate Query Elimination

**Issue:** `_compile_team_injuries_and_suspensions()` was querying the database even when team relationships were pre-loaded via `selectinload`.

**Fix:** Modified function to accept optional `team_obj` parameter and use pre-loaded relationships when available.

**File:** `api/routes/predict.py`

```python
def _compile_team_injuries_and_suspensions(db, team_id: int, team_obj=None):
    # Use pre-loaded relationships if available
    if team_obj and hasattr(team_obj, 'injuries') and hasattr(team_obj, 'suspensions'):
        for inj in team_obj.injuries:
            # Use pre-loaded data
    else:
        # Fallback to DB query
```

**Impact:** Eliminates 2 additional queries per team profile request when using `selectinload`.

### 4.2 Batch Database Reads

**Issue:** Intelligence service was querying match statistics individually for each recent match (N+1 query pattern).

**Fix:** Implemented batch loading of match statistics:

**File:** `services/intelligence_service.py`

```python
def _batch_get_match_stats(self, db: Session, match_ids: List[int]) -> Dict[int, MatchStatistic]:
    """Batch load match statistics for multiple match IDs at once."""
    if not match_ids:
        return {}
    
    stats_list = db.query(MatchStatistic).filter(MatchStatistic.match_id.in_(match_ids)).all()
    return {s.match_id: s for s in stats_list}
```

**Impact:** Reduces ~11 individual queries to 1 batch query per intelligence calculation.

### 4.3 Query Pattern Improvements

**Before:**
```python
for m in recent_matches:
    stats = self._get_match_stats(db, m.id)  # Individual query
```

**After:**
```python
# Pre-load all stats at once
stats_cache = self._batch_get_match_stats(db, all_recent_match_ids)
for m in recent_matches:
    stats = self._get_match_stats(db, m.id, stats_cache)  # Uses cache
```

---

## 5. Background Jobs

### 5.1 ELO Recomputation

**Issue:** ELO recomputation processes all historical matches and can take 30-60 seconds, blocking the API response.

**Solution:** Moved to background thread with job tracking.

**File:** `api/routes/admin.py`

**New Endpoints:**
- `POST /api/admin/compute-elo` - Starts background job, returns immediately
- `GET /api/admin/jobs/elo_recomputation` - Check job status

**Implementation:**
```python
def _run_elo_recomputation_background():
    """Background function to compute ELO ratings."""
    # Runs in separate thread
    # Updates job status via _background_jobs dict
```

**Job Status Response:**
```json
{
  "status": "running|completed|failed",
  "started_at": "2026-06-27T10:00:00",
  "completed_at": "2026-06-27T10:00:45",
  "result": {...},
  "error": null
}
```

**Benefits:**
- API returns immediately (<10ms)
- No blocking of other requests
- Job status can be polled asynchronously

---

## 6. Timing Logs

### 6.1 Middleware Logging

**Location:** `api/main.py`  
**Existing:** Request duration logging already implemented

```python
@app.middleware("http")
async def log_requests_and_latency(request: Request, call_next):
    start_time = time.time()
    # ... process request
    duration = time.time() - start_time
    logger.info(f"Response: {method} {path} - Status: {response.status_code} - Completed in {duration:.4f}s")
```

### 6.2 Endpoint-Specific Timing

Added timing logs to all major endpoints:

**File:** `api/routes/predict.py`

```python
# POST /api/predict
t_start = time.perf_counter()
logger.info(f"POST /api/predict  →  {home_team} vs {away_team}")
# ... processing
elapsed_ms = round((time.perf_counter() - t_start) * 1000, 1)
logger.info(f"POST /api/predict  →  CACHE HIT/MISS in {elapsed_ms} ms")

# GET /api/team/{name}
t_start = time.perf_counter()
logger.info(f"GET /api/team/{team_name}")
# ... processing
elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
logger.info(f"GET /api/team/{team_name}  →  completed in {elapsed_ms} ms")
```

**Endpoints with timing logs:**
- POST /api/predict
- POST /api/predict-batch
- GET /api/teams
- GET /api/team/{name}
- GET /api/h2h/{a}/{b}
- GET /api/fixtures
- GET /api/fixtures-enriched
- GET /api/debug/live-sync
- GET /api/health
- GET /api/tournament/simulation

### 6.3 Intelligence Service Timing

**File:** `services/intelligence_service.py`

```python
t_start = time.perf_counter()
# ... intelligence calculation
elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
logger.info(f"Intelligence computed for match {match.id}: completed in {elapsed_ms} ms")
```

---

## 7. Cache Hit Ratio Analysis

### Expected Cache Hit Ratios

| Cache Type | Expected Hit Ratio | Reason |
|------------|-------------------|--------|
| Predictions | 60-80% | Same matchups queried repeatedly |
| Tournament Simulation | 70-90% | Simulation requested frequently during live matches |
| Team Statistics | 50-70% | Team profiles cached for 10 minutes |
| Intelligence | 40-60% | Match-specific, shorter TTL |

### Monitoring

Cache statistics available via:
- `GET /api/health` - Returns cache hit/miss counts and ratio
- Application logs - Individual cache hit/miss events

---

## 8. Database Improvements Summary

### Schema Changes

1. **Matches Table:**
   - Added index on `home_team_id`
   - Added index on `away_team_id`
   - Added composite index on `(competition_id, status, utc_date)`

2. **Teams Table:**
   - Added index on `name`
   - Added index on `short_name`
   - Added index on `tla`

3. **Predictions Table:**
   - Added index on `match_id`

4. **Injuries/Suspensions Tables:**
   - Added index on `team_id`

### Query Pattern Improvements

1. **Eliminated N+1 queries** in intelligence calculations via batch loading
2. **Removed duplicate queries** when using pre-loaded relationships
3. **Added composite indexes** for common filter combinations
4. **Optimized fixture queries** with proper indexing

---

## 9. Overall Performance Gains

### Summary Table

| Optimization | Expected Impact | Measurable Benefit |
|--------------|----------------|-------------------|
| Prediction caching | 60-80% hit ratio | 95%+ latency reduction on hits |
| Tournament simulation caching | 70-90% hit ratio | 95%+ latency reduction on hits |
| Team statistics caching | 50-70% hit ratio | 95%+ latency reduction on hits |
| Intelligence caching | 40-60% hit ratio | 95%+ latency reduction on hits |
| Database indexing | 20-40% query speedup | Faster all DB queries |
| Batch reads | 50-80% reduction in queries | Eliminates N+1 patterns |
| Background ELO jobs | 100% API responsiveness | No blocking on expensive ops |
| Timing logs | N/A | Better observability |

### Overall Expected Improvement

- **Average API response time:** 70-90% reduction for cached requests
- **Database query count:** 50-80% reduction via batching and caching
- **System throughput:** 3-5x increase due to reduced latency
- **Resource utilization:** Lower CPU/memory due to cache hits

---

## 10. Backward Compatibility

### API Response Compatibility

All optimizations maintain 100% backward compatibility:

- **No changes to response schemas** - All existing fields preserved
- **No changes to prediction logic** - ML models unchanged
- **No changes to business logic** - All calculations produce identical results
- **Cache is transparent** - Clients receive same data whether from cache or computation

### Database Compatibility

- **Migration script** handles index creation safely
- **Checks for existing indexes** before creating new ones
- **Rollback available** via migration downgrade

---

## 11. Deployment Recommendations

### 1. Run Database Migration

```bash
alembic upgrade head
```

This will apply the performance indexes.

### 2. Monitor Cache Performance

After deployment, monitor:
- Cache hit ratios via `/api/health`
- Response times via application logs
- Database query performance

### 3. Adjust TTLs if Needed

Cache TTLs can be adjusted in code:
- `PREDICTION_CACHE_TTL_SECONDS` - Default 900s (15 min)
- `_team_stats_cache_ttl` - Default 600s (10 min)
- `_intelligence_cache_ttl` - Default 300s (5 min)
- Tournament simulation TTL - Default 300s (5 min)

### 4. Background Job Monitoring

Monitor ELO recomputation jobs via:
```bash
curl http://localhost:8000/api/admin/jobs/elo_recomputation
```

---

## 12. Future Optimization Opportunities

### 1. Redis Integration

Replace in-memory caches with Redis for:
- Distributed cache across multiple instances
- Persistent cache across restarts
- Better cache eviction policies

### 2. Query Result Caching

Implement database-level query result caching for:
- Complex aggregation queries
- Analytics endpoints
- Historical data queries

### 3. Async I/O

Convert to async/await pattern for:
- Database queries (asyncpg)
- External API calls
- File I/O operations

### 4. Connection Pooling

Optimize database connection pool settings based on load testing.

---

## 13. Conclusion

The implemented optimizations significantly improve backend API performance while maintaining full backward compatibility. Key achievements:

- **Caching:** 4 major caching layers with expected 60-80% hit ratios
- **Database:** 9 new indexes eliminating slow queries
- **Query optimization:** Batch reads and duplicate query elimination
- **Background jobs:** Non-blocking expensive operations
- **Observability:** Comprehensive timing logs for all endpoints

These changes position the API for production workloads with significantly improved response times and reduced resource utilization.

---

**Report Generated:** June 27, 2026  
**Optimization Status:** Complete  
**Testing Status:** Requires production validation
