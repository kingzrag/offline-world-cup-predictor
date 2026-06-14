/**
 * src/api.ts
 * ──────────────────────────────────────────────────────────────────────────────
 * Typed API service layer for all FastAPI prediction endpoints.
 *
 * URL resolution strategy:
 *
 *   Development  (npm run dev / Vite dev server):
 *     BASE = "/fastapi"
 *     Requests to /fastapi/* are caught by the Express proxy in server.ts and
 *     forwarded to the local FastAPI process, eliminating CORS issues.
 *
 *   Production   (npm run build → Vercel static hosting):
 *     BASE = import.meta.env.VITE_API_URL  (e.g. https://…railway.app/api)
 *     The browser calls the Railway backend directly — no proxy layer exists.
 *     Set VITE_API_URL in Vercel → Project Settings → Environment Variables.
 *
 * Endpoints (relative to BASE):
 *   POST /predict          → POST  /api/predict
 *   GET  /teams            → GET   /api/teams
 *   GET  /team/:name       → GET   /api/team/:name
 *   GET  /fixtures         → GET   /api/fixtures
 *   GET  /health           → GET   /api/health
 */

import type {
  MatchPrediction,
  OverUnderLine,
  BTTSMarket,
  ScorelineProbability,
  AsianHandicap,
  TeamGoalMarket,
} from "./types";
import { MOCK_MATCHES } from "./data";

// ── Base URL ──────────────────────────────────────────────────────────────────
// Development  → "/fastapi"  (Express proxy in server.ts rewrites to /api/*)
// Production   → VITE_API_URL  (direct Railway backend; set in Vercel env vars)
//
// import.meta.env.PROD is injected by Vite at build time:
//   true  when running `vite build`  (Vercel deploy)
//   false when running `vite dev`    (local Express proxy)
export const API_BASE: string = import.meta.env.PROD
  ? (import.meta.env.VITE_API_URL as string) ?? ""
  : "/fastapi";

// Log the resolved API base so it is visible in the browser console on first load.
console.info(
  `[api] Resolved API base: "${API_BASE}" ` +
  `(${import.meta.env.PROD ? "production → Railway" : "development → Express proxy"})`
);

/** @internal – used by every apiFetch call below */
const BASE = API_BASE;

// ── Backend response shapes ───────────────────────────────────────────────────

export interface BackendOutcome {
  home_win_probability: number;   // 0–1
  draw_probability: number;       // 0–1
  away_win_probability: number;   // 0–1
  predicted_result: "HOME_WIN" | "DRAW" | "AWAY_WIN";
  confidence: number;             // 0–1
}

export interface BackendGoals {
  expected_home_goals: number;
  expected_away_goals: number;
  total_expected_goals: number;
}

export interface BackendOverUnderLine {
  over: number;   // 0–1
  under: number;  // 0–1
}

export interface BackendBTTS {
  yes: number;   // 0–1
  no: number;    // 0–1
}

export interface BackendScoreline {
  score: string;
  probability: number;
}

export interface BackendAsianHandicap {
  label: string;
  lines: Record<string, number>;
  favored_team: string;
}

export interface BackendTeamGoals {
  home: { over_0_5: number; over_1_5: number; over_2_5: number };
  away: { over_0_5: number; over_1_5: number; over_2_5: number };
}

export interface BackendMarkets {
  over_under: {
    "1.5": BackendOverUnderLine;
    "2.5": BackendOverUnderLine;
    "3.5": BackendOverUnderLine;
  };
  btts: BackendBTTS;
  most_likely_score: string;
  top_5_scorelines: BackendScoreline[];
  asian_handicap: BackendAsianHandicap;
  team_goals: BackendTeamGoals;
  probability_matrix: Record<string, number>;
}

export interface BackendModelVersions {
  wc_model: string;
  goal_model: string;
}

export interface BackendPrediction {
  home_team: string;
  away_team: string;
  generated_at: string;
  outcome: BackendOutcome;
  goals: BackendGoals;
  markets: BackendMarkets;
  model_versions: BackendModelVersions;
}

export interface BackendPredictResponse {
  status: string;
  latency_ms: number;
  prediction: BackendPrediction;
}

export interface BackendTeam {
  id: number;
  name: string;
  short_name: string | null;
  tla: string | null;
  crest_url: string | null;
  founded: number | null;
  venue: string | null;
}

export interface BackendFormEntry {
  date: string | null;
  opponent: string;
  home: boolean;
  score: string | null;
  result: "W" | "D" | "L";
}

export interface BackendTeamProfile {
  id: number;
  name: string;
  short_name: string | null;
  tla: string | null;
  crest_url: string | null;
  founded: number | null;
  venue: string | null;
  elo_rating: number | null;
  squad_size: number | null;
  recent_form: BackendFormEntry[];
}

export interface BackendFixtureTeam {
  id: number;
  name: string;
  short_name: string | null;
  tla: string | null;
  crest_url: string | null;
}

export interface BackendFixtureLiveScore {
  home: number;
  away: number;
  is_live: boolean;   // true when IN_PLAY or PAUSED, false when FINISHED
}

export interface BackendFixture {
  id: number;
  kickoff_time: string | null;         // ISO-8601 UTC
  status: string;                       // TIMED | SCHEDULED | IN_PLAY | PAUSED | FINISHED | POSTPONED
  stage: string | null;                 // GROUP_STAGE | ROUND_OF_16 | QUARTER_FINALS …
  group: string | null;                 // GROUP_A … GROUP_L, null for knockouts
  venue: string | null;                 // home team's stadium
  competition: string | null;
  home_team: BackendFixtureTeam | null;
  away_team: BackendFixtureTeam | null;
  live_score: BackendFixtureLiveScore | null;  // populated for IN_PLAY, PAUSED, FINISHED
  winner: "HOME_TEAM" | "AWAY_TEAM" | "DRAW" | null;
  prediction?: {
    predicted_outcome: "HOME_WIN" | "AWAY_WIN" | "DRAW";
    home_probability: number;
    away_probability: number;
    draw_probability: number;
  } | null;
}

export interface BackendHealth {
  status: "ready" | "loading";
  models_loaded: boolean;
  model_versions: BackendModelVersions;
  timestamp: number;
}

// ── Low-level fetch helper ────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
  timeoutMs = 30000
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${BASE}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers ?? {}),
      },
    });
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`API ${res.status}: ${body.slice(0, 300)}`);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

// ── Public API functions ──────────────────────────────────────────────────────

/**
 * POST /fastapi/predict
 * Full prediction: 1X2 + goals + all betting markets.
 */
export async function predictMatch(
  homeTeam: string,
  awayTeam: string,
  competitionCode = "WC",
  signal?: AbortSignal
): Promise<BackendPredictResponse> {
  console.log(`[api] predictMatch → ${homeTeam} vs ${awayTeam} (${competitionCode})`);
  const result = await apiFetch<BackendPredictResponse>("/predict", {
    method: "POST",
    signal,
    body: JSON.stringify({
      home_team: homeTeam,
      away_team: awayTeam,
      competition_code: competitionCode,
    }),
  }, 45000);  // 45s timeout — ML inference on Render can take 10–15s on cold start
  console.log(`[api] predictMatch ← ${homeTeam} vs ${awayTeam}:`, result.prediction?.outcome);
  return result;
}

/**
 * GET /fastapi/teams?search=&limit=
 */
export async function getTeams(
  search?: string,
  limit = 100
): Promise<{ status: string; count: number; teams: BackendTeam[] }> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (search) params.set("search", search);
  return apiFetch(`/teams?${params.toString()}`);
}

/**
 * GET /fastapi/team/{teamName}
 */
export async function getTeamProfile(
  teamName: string
): Promise<{ status: string; team: BackendTeamProfile }> {
  return apiFetch(`/team/${encodeURIComponent(teamName)}`);
}

/**
 * GET /fastapi/fixtures?status=&stage=&group=&date_from=&date_to=&limit=&competition_code=
 *
 * Defaults: competition_code=WC, limit=200
 * All parameters are optional.
 */
export async function getFixtures(
  params: {
    status?: string;
    stage?: string;
    group?: string;
    date_from?: string;       // YYYY-MM-DD
    date_to?: string;         // YYYY-MM-DD
    competition_code?: string;
    limit?: number;
    year?: number;
    show_historical?: boolean;
  } = {}
): Promise<{ status: string; competition: string; count: number; fixtures: BackendFixture[] }> {
  const qs = new URLSearchParams();
  if (params.status)           qs.set("status",           params.status);
  if (params.stage)            qs.set("stage",            params.stage);
  if (params.group)            qs.set("group",            params.group);
  if (params.date_from)        qs.set("date_from",        params.date_from);
  if (params.date_to)          qs.set("date_to",          params.date_to);
  if (params.competition_code) qs.set("competition_code", params.competition_code);
  if (params.limit != null)    qs.set("limit",            String(params.limit));
  if (params.year != null)     qs.set("year",             String(params.year));
  if (params.show_historical !== undefined) qs.set("show_historical", String(params.show_historical));
  return apiFetch(`/fixtures?${qs.toString()}`);
}

/**
 * GET /fastapi/health
 */
export async function checkHealth(): Promise<BackendHealth> {
  return apiFetch<BackendHealth>("/health");
}

// ── Mapping helper ────────────────────────────────────────────────────────────

/**
 * mapBackendPrediction
 * Maps a FastAPI BackendPrediction onto an existing MatchPrediction object.
 * Only overwrites fields the API provides; all supplementary mock fields
 * (venue, stage, date, tactical ratings, H2H, etc.) are preserved.
 */
export function mapBackendPrediction(
  base: MatchPrediction,
  api: BackendPrediction
): MatchPrediction {
  const o = api.outcome;
  const g = api.goals;
  const m = api.markets;

  // Convert 0–1 floats to integer percentages clamped to [1, 99]
  const clamp = (v: number) => Math.min(99, Math.max(1, Math.round(v * 100)));
  const probA = clamp(o.home_win_probability);
  const probD = clamp(o.draw_probability);
  const probB = clamp(o.away_win_probability);

  // Human-readable prediction label
  const predictionLabel =
    o.predicted_result === "HOME_WIN"
      ? `${base.teamA} Win`
      : o.predicted_result === "AWAY_WIN"
      ? `${base.teamB} Win`
      : "Draw";

  // Map numeric confidence to categorical tier
  const confidence: "High" | "Medium" | "Low" =
    o.confidence >= 0.60 ? "High" : o.confidence >= 0.45 ? "Medium" : "Low";

  return {
    ...base,
    // Core prediction
    probA,
    probD,
    probB,
    prediction: predictionLabel,
    confidence,
    // Goals / xG
    xGA: g.expected_home_goals,
    xGB: g.expected_away_goals,
    totalExpectedGoals: g.total_expected_goals,
    // Betting markets
    overUnder: m.over_under,
    bttsMarket: m.btts,
    mostLikelyScore: m.most_likely_score,
    top5Scorelines: m.top_5_scorelines,
    asianHandicap: m.asian_handicap,
    teamGoals: m.team_goals,
    // Badge for live-model indicator in UI
    isLiveData: true,
  };
}

// ── Primary consumer: load all predictions ────────────────────────────────────

function formatKickoffDate(isoStr: string | null): string {
  if (!isoStr) return "Unknown Date";
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "2-digit",
      year: "numeric"
    });
  } catch {
    return "Unknown Date";
  }
}

export function mapFixtureToPrediction(f: BackendFixture): MatchPrediction {
  const teamA = f.home_team?.name ?? "Unknown";
  const teamB = f.away_team?.name ?? "Unknown";
  const teamACode = f.home_team?.tla || f.home_team?.short_name || teamA.substring(0, 3).toUpperCase();
  const teamBCode = f.away_team?.tla || f.away_team?.short_name || teamB.substring(0, 3).toUpperCase();

  let stageLabel = "";
  if (f.stage === "GROUP_STAGE" && f.group) {
    const groupName = f.group.replace("GROUP_", "Group ");
    stageLabel = `Group Stage • ${groupName}`;
  } else if (f.stage) {
    stageLabel = f.stage.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  } else {
    stageLabel = "Group Stage";
  }

  let statusMapped: "LIVE" | "UPCOMING" | "COMPLETED" = "UPCOMING";
  if (f.status === "IN_PLAY" || f.status === "PAUSED") {
    statusMapped = "LIVE";
  } else if (f.status === "FINISHED") {
    statusMapped = "COMPLETED";
  }

  // Baseline outcome fields
  let predictionLabel = "Draw / Even Lean";
  let confidence: "High" | "Medium" | "Low" = "Medium";
  let probA = 33;
  let probD = 34;
  let probB = 33;

  if (f.prediction) {
    const p = f.prediction;
    probA = Math.round(p.home_probability * 100);
    probD = Math.round(p.draw_probability * 100);
    probB = Math.round(p.away_probability * 100);
    predictionLabel = p.predicted_outcome === "HOME_WIN" ? `${teamA} Win` :
                      p.predicted_outcome === "AWAY_WIN" ? `${teamB} Win` : "Draw";
    confidence = (p.home_probability >= 0.60 || p.away_probability >= 0.60) ? "High" : 
                 (p.home_probability >= 0.45 || p.away_probability >= 0.45) ? "Medium" : "Low";
  } else if (statusMapped === "COMPLETED") {
    if (f.winner === "HOME_TEAM") {
      predictionLabel = `${teamA} Win`;
      probA = 100; probD = 0; probB = 0;
    } else if (f.winner === "AWAY_TEAM") {
      predictionLabel = `${teamB} Win`;
      probA = 0; probD = 0; probB = 100;
    } else {
      predictionLabel = "Draw";
      probA = 0; probD = 100; probB = 0;
    }
    confidence = "High";
  }

  return {
    id: String(f.id),
    teamA,
    teamB,
    teamACode,
    teamBCode,
    date: formatKickoffDate(f.kickoff_time),
    kickoffTime: f.kickoff_time,
    stage: stageLabel,
    status: statusMapped,
    prediction: predictionLabel,
    confidence,
    probA,
    probD,
    probB,
    venue: f.venue || "TBD Stadium",
    liveScore: f.live_score ?? null,
    winner: f.winner,

    // Default placeholders for tactical ratings that get loaded dynamically or mapped
    attackA: 80, attackB: 80,
    defenceA: 80, defenceB: 80,
    midfieldA: 80, midfieldB: 80,
    xGA: f.live_score?.home ?? 1.5, xGB: f.live_score?.away ?? 1.5,
    xGAA: 1.0, xGAB: 1.0,
    possessionA: 50, possessionB: 50,
    shotsA: 12.0, shotsB: 12.0,
    shotsAllowedA: 10.0, shotsAllowedB: 10.0,
    cleanSheetA: 30, cleanSheetB: 30,
    bttsRateA: 50, bttsRateB: 50,
    recentFormA: ["D", "D", "D", "D", "D"],
    recentFormB: ["D", "D", "D", "D", "D"],
    fifaRankA: 15, fifaRankB: 15,
    eloRankA: 15, eloRankB: 15,
    squadValueA: "€250M", squadValueB: "€250M",
    restDaysA: 4, restDaysB: 4,
    fatigueA: 20, fatigueB: 20,
    injuriesA: [], injuriesB: [],
    suspensionsA: [], suspensionsB: [],
    missingKeyPlayersA: [], missingKeyPlayersB: [],
    impactRatingA: "Minimal", impactRatingB: "Minimal",
    h2hPreviousMeetings: 5,
    h2hWinsA: 2, h2hWinsB: 2, h2hDraws: 1,
    h2hGoalsA: 7, h2hGoalsB: 7,
    aiSummary: "The ML analytical pipeline is ready to simulate transition profiles. Click 'View Full Report' to dynamically generate expected goal distributions and ELO metrics.",
    
    // If completed, add btts and correct scoreline indicators
    ...(statusMapped === "COMPLETED" && {
      overUnder: {
        "1.5": { over: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 1.5 ? 1 : 0, under: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 1.5 ? 0 : 1 },
        "2.5": { over: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 2.5 ? 1 : 0, under: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 2.5 ? 0 : 1 },
        "3.5": { over: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 3.5 ? 1 : 0, under: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 3.5 ? 0 : 1 },
      },
      bttsMarket: {
        yes: (f.live_score?.home ?? 0) > 0 && (f.live_score?.away ?? 0) > 0 ? 1 : 0,
        no: (f.live_score?.home ?? 0) > 0 && (f.live_score?.away ?? 0) > 0 ? 0 : 1
      },
      mostLikelyScore: `${f.live_score?.home ?? 0}-${f.live_score?.away ?? 0}`,
      top5Scorelines: [
        { score: `${f.live_score?.home ?? 0}-${f.live_score?.away ?? 0}`, probability: 1.0 }
      ]
    })
  };
}


// ── Client-side prediction cache (15 minutes) ─────────────────────────────────

const CACHE_TTL_MS = 15 * 60 * 1000; // 15 minutes

interface CacheEntry {
  prediction: BackendPrediction;
  expiresAt: number;
}

const _predictionCache = new Map<string, CacheEntry>();

function cacheKey(home: string, away: string): string {
  return `${home.trim().toLowerCase()}|${away.trim().toLowerCase()}`;
}

function getCached(home: string, away: string): BackendPrediction | null {
  const entry = _predictionCache.get(cacheKey(home, away));
  if (!entry) return null;
  if (Date.now() > entry.expiresAt) {
    _predictionCache.delete(cacheKey(home, away));
    return null;
  }
  return entry.prediction;
}

function setCached(home: string, away: string, prediction: BackendPrediction): void {
  _predictionCache.set(cacheKey(home, away), {
    prediction,
    expiresAt: Date.now() + CACHE_TTL_MS,
  });
}

// ── Batch predict API call ──────────────────────────────────────────────────

interface BatchMatchInput {
  home_team: string;
  away_team: string;
  competition_code?: string;
}

interface BatchResultItem {
  home_team: string;
  away_team: string;
  status: "success" | "error";
  prediction?: BackendPrediction;
  cached: boolean;
  latency_ms: number;
  error?: string;
}

interface BatchPredictResponse {
  status: string;
  total_ms: number;
  count: number;
  results: BatchResultItem[];
}

export async function predictBatch(
  matches: BatchMatchInput[],
  signal?: AbortSignal
): Promise<BatchPredictResponse> {
  return apiFetch<BatchPredictResponse>("/predict-batch", {
    method: "POST",
    signal,
    body: JSON.stringify({ matches }),
  }, 120000); // 2-min timeout for large batches
}

// ── Instant fixture load (Phase 1 — renders immediately) ──────────────────────

/**
 * loadFixturesInstant()
 *
 * Phase 1 of the optimised loading pipeline.
 * Fetches /fixtures only (no ML inference) and returns mapped MatchPrediction[].
 * The caller can render the full page immediately with fixture-level data,
 * then call enrichPredictionsInBackground() to hydrate ML values progressively.
 *
 * Timing logs:
 *   [perf] fixtures fetch time
 *   [perf] fixture map time
 *   [perf] total instant render time
 */
export async function loadFixturesInstant(
  year?: number,
  showHistorical?: boolean,
  signal?: AbortSignal
): Promise<MatchPrediction[]> {
  const t0 = performance.now();

  console.log("[perf] ► fixtures fetch start");
  const fixturesResponse = await getFixtures({
    competition_code: "WC",
    limit: 500,
    year,
    show_historical: showHistorical,
  });
  const fixtures = fixturesResponse.fixtures || [];
  const t1 = performance.now();
  console.log(`[perf] fixtures fetch time: ${(t1 - t0).toFixed(0)} ms  (${fixtures.length} fixtures)`);

  const mapped = fixtures.map(mapFixtureToPrediction);
  const t2 = performance.now();
  console.log(`[perf] fixture map time: ${(t2 - t1).toFixed(0)} ms`);
  console.log(`[perf] total instant render time: ${(t2 - t0).toFixed(0)} ms`);

  return mapped;
}

// ── Background enrichment (Phase 2 — progressive ML hydration) ───────────────

/**
 * enrichPredictionsInBackground()
 *
 * Phase 2 of the optimised loading pipeline.
 * Runs AFTER the page is already rendered with fixture data.
 *
 * Strategy:
 *   1. Check client-side cache — skip already-cached matches.
 *   2. Try POST /predict-batch for all cache-miss matches in ONE request.
 *   3. If batch endpoint fails, fall back to 10-concurrent individual /predict calls.
 *   4. For each match whose prediction arrives, call onMatchUpdated(matchId, enriched).
 *   5. Respects AbortSignal so stale tab-switch requests are cancelled.
 *
 * Timing logs:
 *   [perf] prediction fetch time
 *   [perf] total page render time (cumulative from t0Page)
 *
 * @param matches       The full match list returned by loadFixturesInstant.
 * @param onMatchUpdated  Callback invoked per-match as predictions arrive.
 * @param signal          AbortSignal from the calling component's AbortController.
 * @param t0Page          performance.now() timestamp of initial page render start.
 */
export async function enrichPredictionsInBackground(
  matches: MatchPrediction[],
  onMatchUpdated: (matchId: string, enriched: MatchPrediction) => void,
  signal?: AbortSignal,
  t0Page = 0
): Promise<void> {
  const activeMatches = matches.filter(m => m.status === "LIVE" || m.status === "UPCOMING");
  if (activeMatches.length === 0) return;

  // Separate already-cached from cache-misses
  const cached: MatchPrediction[] = [];
  const toFetch: MatchPrediction[] = [];

  for (const m of activeMatches) {
    const hit = getCached(m.teamA, m.teamB);
    if (hit) {
      cached.push(m);
      const enriched = mapBackendPrediction(m, hit);
      onMatchUpdated(m.id, enriched);
      console.log(
        `[cache HIT] ${m.teamA} vs ${m.teamB}  →  Home ${Math.round(hit.outcome.home_win_probability * 100)}%  ` +
        `Draw ${Math.round(hit.outcome.draw_probability * 100)}%  ` +
        `Away ${Math.round(hit.outcome.away_win_probability * 100)}%`
      );
    } else {
      toFetch.push(m);
    }
  }

  console.log(
    `[perf] ► prediction enrichment start: ${toFetch.length} cache-miss matches ` +
    `(${cached.length} served from cache)`
  );

  if (toFetch.length === 0) return;

  const tPredStart = performance.now();

  // ─────────────────────────────────────────────────────────────────────
  // Attempt 1: single batch request
  // ─────────────────────────────────────────────────────────────────────
  let usedBatch = false;
  try {
    if (signal?.aborted) return;

    const batchPayload = toFetch.map(m => ({
      home_team: m.teamA,
      away_team: m.teamB,
      competition_code: "WC",
    }));

    const batchResp = await predictBatch(batchPayload, signal);
    usedBatch = true;

    for (const item of batchResp.results) {
      if (signal?.aborted) break;
      if (item.status !== "success" || !item.prediction) {
        console.warn(`[batch] ✗ ${item.home_team} vs ${item.away_team}: ${item.error}`);
        continue;
      }

      const pred = item.prediction as unknown as BackendPrediction;
      setCached(item.home_team, item.away_team, pred);

      const base = toFetch.find(
        m => m.teamA === item.home_team && m.teamB === item.away_team
      );
      if (!base) continue;

      const enriched = mapBackendPrediction(base, pred);
      onMatchUpdated(base.id, enriched);

      console.log(
        `\nMATCH:\n${enriched.teamA} vs ${enriched.teamB}\n\nRESULT:\n` +
        `Home ${enriched.probA}%\nDraw ${enriched.probD}%\nAway ${enriched.probB}%\n` +
        `[cached by server: ${item.cached}]`
      );
    }
  } catch (batchErr: any) {
    if (signal?.aborted) return;
    console.warn("[api] Batch endpoint failed, falling back to individual requests:", batchErr?.message);
  }

  // ─────────────────────────────────────────────────────────────────────
  // Fallback: 10-concurrent individual /predict requests
  // Only runs for matches still missing predictions after batch attempt
  // ─────────────────────────────────────────────────────────────────────
  if (!usedBatch) {
    const CONCURRENCY = 10;
    for (let i = 0; i < toFetch.length; i += CONCURRENCY) {
      if (signal?.aborted) break;
      const chunk = toFetch.slice(i, i + CONCURRENCY);
      const settled = await Promise.allSettled(
        chunk.map(async (match) => {
          const resp = await predictMatch(match.teamA, match.teamB, "WC", signal);
          return { id: match.id, base: match, prediction: resp.prediction };
        })
      );

      for (const outcome of settled) {
        if (signal?.aborted) break;
        if (outcome.status === "fulfilled") {
          const { id, base, prediction } = outcome.value;
          setCached(base.teamA, base.teamB, prediction);
          const enriched = mapBackendPrediction(base, prediction);
          onMatchUpdated(id, enriched);
          console.log(
            `\nMATCH:\n${enriched.teamA} vs ${enriched.teamB}\n\nRESULT:\n` +
            `Home ${enriched.probA}%\nDraw ${enriched.probD}%\nAway ${enriched.probB}%\n`
          );
        } else {
          console.warn("[api] Individual prediction failed (skipped):", outcome.reason?.message);
        }
      }
    }
  }

  if (!signal?.aborted) {
    const tPredEnd = performance.now();
    const totalElapsed = t0Page > 0 ? tPredEnd - t0Page : tPredEnd - tPredStart;
    console.log(`[perf] prediction fetch time: ${(tPredEnd - tPredStart).toFixed(0)} ms`);
    console.log(`[perf] total page render time (fixtures + enrichment): ${totalElapsed.toFixed(0)} ms`);
  }
}

/**
 * getPredictions()
 *
 * ⚠️  Legacy blocking entry-point kept for backward compatibility.
 *     For new call-sites use loadFixturesInstant() + enrichPredictionsInBackground().
 *
 * Fetches fixtures then enriches ALL active matches before returning,
 * which blocks the caller until every prediction is resolved.
 */
export async function getPredictions(year?: number, showHistorical?: boolean): Promise<MatchPrediction[]> {
  // 1. Verify backend is reachable and models are loaded
  let health: BackendHealth;
  try {
    console.log("[api] getPredictions → checking health...");
    health = await checkHealth();
    console.log("[api] Health Check Result:", health);
  } catch (err) {
    console.error("[api] Health check failed:", err);
    throw new Error("FastAPI backend unreachable");
  }

  if (!health.models_loaded) {
    throw new Error("ML models are still loading on the backend");
  }

  // 2. Load fixtures instantly
  const results = await loadFixturesInstant(year, showHistorical);

  // 3. Enrich synchronously (legacy behaviour) using the fast batch path
  await enrichPredictionsInBackground(
    results,
    (id, enriched) => {
      const idx = results.findIndex(r => r.id === id);
      if (idx !== -1) results[idx] = enriched;
    }
  );

  return results;
}

/**
 * getLiveFixtures()
 *
 * Lightweight poll — fetches only IN_PLAY and PAUSED fixtures from the DB.
 * Used by the 60-second frontend refresh interval.
 * Does NOT re-run ML batch predictions (score/status sync only).
 */
export async function getLiveFixtures(): Promise<MatchPrediction[]> {
  const [inPlay, paused] = await Promise.all([
    getFixtures({ status: "IN_PLAY",  competition_code: "WC", limit: 50 }),
    getFixtures({ status: "PAUSED",   competition_code: "WC", limit: 50 }),
  ]);
  const fixtures = [...(inPlay.fixtures || []), ...(paused.fixtures || [])];
  return fixtures.map(mapFixtureToPrediction);
}

// ── Tournament progression types & API functions ─────────────────────────────

export interface GroupStandingTeam {
  id: number;
  name: string;
  tla: string | null;
  crest_url: string | null;
  played_games: number;
  won: number;
  draw: number;
  lost: number;
  points: number;
  goals_for: number;
  goals_against: number;
  goals_difference: number;
  group: string;
  position: number;
}

export type GroupStandings = Record<string, GroupStandingTeam[]>;

export interface BracketTeam {
  id: number | null;
  name: string;
  tla: string;
  crest_url: string | null;
}

export interface BracketMatch {
  id: number;
  stage: string;
  utc_date: string;
  status: string;
  home_team: BracketTeam;
  away_team: BracketTeam;
  home_score: number | null;
  away_score: number | null;
  winner: "HOME_TEAM" | "AWAY_TEAM" | "DRAW" | null;
}

export type BracketData = Record<string, BracketMatch[]>;

export interface ScoreUpdateResponse {
  status: string;
  match_id: number;
  winner: "HOME_TEAM" | "AWAY_TEAM" | "DRAW" | null;
  status_code: string;
}

export interface HistoricalProgressionEntry {
  fixture: number;
  accuracy: number;
}

export interface ModelPerformanceStats {
  total_fixtures: number;
  completed_fixtures: number;
  correct_predictions: number;
  overall_accuracy: number;
  high_confidence_accuracy: number;
  last_updated: string;
  model_status: string;
  historical_progression: HistoricalProgressionEntry[];
}

/**
 * GET /fastapi/tournament/standings
 */
export async function getStandings(): Promise<GroupStandings> {
  return apiFetch<GroupStandings>("/tournament/standings");
}

/**
 * GET /fastapi/tournament/bracket
 */
export async function getBracket(): Promise<BracketData> {
  return apiFetch<BracketData>("/tournament/bracket");
}

/**
 * PUT /fastapi/tournament/fixtures/{matchId}/score
 */
export async function updateMatchScore(
  matchId: number,
  homeScore: number,
  awayScore: number,
  status: string
): Promise<ScoreUpdateResponse> {
  return apiFetch<ScoreUpdateResponse>(`/tournament/fixtures/${matchId}/score`, {
    method: "PUT",
    body: JSON.stringify({
      home_score: homeScore,
      away_score: awayScore,
      status: status,
    }),
  });
}

/**
 * GET /fastapi/tournament/model-performance
 */
export async function getModelPerformance(): Promise<ModelPerformanceStats> {
  return apiFetch<ModelPerformanceStats>("/tournament/model-performance");
}

