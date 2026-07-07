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
  CleanSheetMarket,
} from "./types";
import { formatKickoffDateLocal } from "./dateTimeUtils";
import { MOCK_MATCHES } from "./data";

// ── Base URL ──────────────────────────────────────────────────────────────────
// Development  → "/fastapi"  (Express proxy in server.ts rewrites to /api/*)
// Production   → VITE_API_URL  (direct backend; set in Vercel env vars)
//
// import.meta.env.PROD is injected by Vite at build time:
//   true  when running `vite build`  (Vercel deploy)
//   false when running `vite dev'    (local Express proxy)
//
// IMPORTANT: All API paths should NOT include /api prefix. The BASE should include it.
// This ensures consistent routing regardless of environment.
let rawApiBase: string = (import.meta as any).env.PROD
  ? ((import.meta as any).env.VITE_API_URL as string) ?? ""
  : "/fastapi";

// Ensure BASE always ends with /api for production, or /fastapi for development
// If VITE_API_URL doesn't include /api, append it automatically
if ((import.meta as any).env.PROD && rawApiBase && !rawApiBase.endsWith('/api')) {
  if (rawApiBase.endsWith('/')) {
    rawApiBase = rawApiBase + 'api';
  } else {
    rawApiBase = rawApiBase + '/api';
  }
  console.warn(`[api] VITE_API_URL didn't include /api suffix. Auto-appended. New BASE: "${rawApiBase}"`);
}

export const API_BASE: string = rawApiBase;

// Log the resolved API base so it is visible in the browser console on first load.
console.info(
  `[api] Resolved API base: "${API_BASE}" ` +
  `(${(import.meta as any).env.PROD ? "production → direct backend" : "development → Express proxy"})`
);
if ((import.meta as any).env.PROD && !API_BASE) {
  console.error(
    "[api] VITE_API_URL is not set — prediction requests will fail. " +
    "Set it in Vercel → Environment Variables (e.g. https://your-backend.onrender.com/api)"
  );
}

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

export interface BackendDoubleChance {
  "1x": number;
  "12": number;
  "x2": number;
}

export interface BackendDrawNoBet {
  home: number;
  away: number;
}

export interface BackendWinToNil {
  home: number;
  away: number;
}

export interface BackendWinningMargin {
  home: {
    "1_goal": number;
    "2_goals": number;
    "3_plus": number;
  };
  away: {
    "1_goal": number;
    "2_goals": number;
    "3_plus": number;
  };
}

export interface BackendGoalRange {
  "0_goals": number;
  "1_goal": number;
  "2_goals": number;
  "3_goals": number;
  "4_goals": number;
  "5_plus": number;
}

export interface BackendMarkets {
  over_under: {
    "0.5"?: BackendOverUnderLine;
    "1.5": BackendOverUnderLine;
    "2.5": BackendOverUnderLine;
    "3.5": BackendOverUnderLine;
    "4.5"?: BackendOverUnderLine;
    "5.5"?: BackendOverUnderLine;
    "6.5"?: BackendOverUnderLine;
    "7.5"?: BackendOverUnderLine;
  };
  btts: BackendBTTS;
  most_likely_score: string;
  top_5_scorelines: BackendScoreline[];
  asian_handicap: BackendAsianHandicap;
  team_goals: BackendTeamGoals;
  probability_matrix: Record<string, number>;
  clean_sheet?: CleanSheetMarket;
  // New derived markets
  double_chance?: BackendDoubleChance;
  draw_no_bet?: BackendDrawNoBet;
  win_to_nil?: BackendWinToNil;
  winning_margin?: BackendWinningMargin;
  goal_range?: BackendGoalRange;
  correct_score_matrix?: BackendScoreline[];
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
  /** World ELO ranking position (1 = best) — returned by GET /team/:name */
  elo_rank: number | null;
  /** FIFA world ranking — returned by GET /team/:name */
  fifa_rank: number | null;
  squad_size: number | null;
  /** Human-readable squad market value string, e.g. "€1.18B" or "N/A" */
  squad_value: string | null;
  recent_form: BackendFormEntry[];
  /** Injury list: ["Player Name (description)", …] */
  injuries: string[];
  /** Suspension list: ["Player Name (reason)", …] */
  suspensions: string[];
  btts_rate?: number | null;
  clean_sheet_rate?: number | null;
}

export interface BackendFixtureTeam {
  id: number;
  name: string;
  short_name: string | null;
  tla: string | null;
  crest_url: string | null;
  injuries?: string[];
  suspensions?: string[];
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
  live_minute?: number | null;
  prediction?: {
    predicted_outcome: "HOME_WIN" | "AWAY_WIN" | "DRAW";
    home_probability: number;
    away_probability: number;
    draw_probability: number;
  } | null;
}

export interface BackendFixtureEnriched extends BackendFixture {
  enrichment?: {
    goals: {
      home_xg: number;
      away_xg: number;
      total_xg: number;
    };
    markets: {
      btts: BTTSMarket;
      over_under: {
        "0.5"?: OverUnderLine;
        "1.5": OverUnderLine;
        "2.5": OverUnderLine;
        "3.5": OverUnderLine;
        "4.5"?: OverUnderLine;
        "5.5"?: OverUnderLine;
        "6.5"?: OverUnderLine;
        "7.5"?: OverUnderLine;
      };
      clean_sheet: CleanSheetMarket;
      most_likely_score: string;
      top_5_scorelines: ScorelineProbability[];
      team_goals: TeamGoalMarket;
      asian_handicap?: AsianHandicap;
      // New derived markets
      double_chance?: BackendDoubleChance;
      draw_no_bet?: BackendDrawNoBet;
      win_to_nil?: BackendWinToNil;
      winning_margin?: BackendWinningMargin;
      goal_range?: BackendGoalRange;
      correct_score_matrix?: BackendScoreline[];
    };
  } | null;
}

export interface BackendHealth {
  status: "ready" | "loading";
  models_loaded: boolean;
  model_versions: BackendModelVersions;
  timestamp: number;
}

// ── Low-level fetch helper ────────────────────────────────────────────────────

/** Combine caller abort signal with a request timeout. */
function mergeAbortSignals(
  external: AbortSignal | undefined,
  timeoutMs: number
): { signal: AbortSignal; cleanup: () => void } {
  const timeoutController = new AbortController();
  const timer = setTimeout(() => timeoutController.abort(), timeoutMs);

  if (!external) {
    return {
      signal: timeoutController.signal,
      cleanup: () => clearTimeout(timer),
    };
  }

  if (external.aborted) {
    clearTimeout(timer);
    return { signal: external, cleanup: () => clearTimeout(timer) };
  }

  const merged = new AbortController();
  const onAbort = () => merged.abort();
  external.addEventListener("abort", onAbort);
  timeoutController.signal.addEventListener("abort", onAbort);

  return {
    signal: merged.signal,
    cleanup: () => {
      clearTimeout(timer);
      external.removeEventListener("abort", onAbort);
    },
  };
}

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
  timeoutMs = 30000,
  maxRetries = 3
): Promise<T> {
  const url = `${BASE}${path}`;
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const { signal, cleanup } = mergeAbortSignals(options?.signal ?? undefined, timeoutMs);
    const tStart = performance.now();
    
    try {
      console.log(`[api] → ${options?.method ?? "GET"} ${url}${attempt > 0 ? ` (retry ${attempt}/${maxRetries})` : ''}`);
      const res = await fetch(url, {
        ...options,
        signal,
        headers: {
          "Content-Type": "application/json",
          ...(options?.headers ?? {}),
        },
      });
      const tEnd = performance.now();
      const duration = (tEnd - tStart).toFixed(0);
      
      if (!res.ok) {
        const body = await res.text();
        console.error(`[api] ✗ ${res.status} ${url} in ${duration}ms: ${body.slice(0, 300)}`);
        lastError = new Error(`API ${res.status}: ${body.slice(0, 300)}`);
        
        // Don't retry on 4xx errors (client errors)
        if (res.status >= 400 && res.status < 500) {
          throw lastError;
        }
        
        // Retry on 5xx errors and network errors
        if (attempt < maxRetries) {
          const delayMs = Math.min(1000 * Math.pow(2, attempt), 10000); // Exponential backoff, max 10s
          console.log(`[api] Retrying in ${delayMs}ms...`);
          await new Promise(resolve => setTimeout(resolve, delayMs));
          continue;
        }
        
        throw lastError;
      }
      
      console.log(`[api] ← ${res.status} ${url} in ${duration}ms`);
      return (await res.json()) as T;
    } catch (err) {
      const tEnd = performance.now();
      const duration = (tEnd - tStart).toFixed(0);
      lastError = err as Error;
      
      // Don't retry if aborted
      if (err instanceof Error && err.name === 'AbortError') {
        console.error(`[api] ✗ Request aborted for ${url} in ${duration}ms`);
        throw err;
      }
      
      console.error(`[api] ✗ Request failed for ${url} in ${duration}ms:`, err);
      
      // Retry on network errors
      if (attempt < maxRetries) {
        const delayMs = Math.min(1000 * Math.pow(2, attempt), 10000); // Exponential backoff, max 10s
        console.log(`[api] Retrying in ${delayMs}ms...`);
        await new Promise(resolve => setTimeout(resolve, delayMs));
        continue;
      }
      
      throw lastError;
    } finally {
      cleanup();
    }
  }
  
  throw lastError || new Error('Max retries exceeded');
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
  const cacheKey = getCacheKey(`/team/${encodeURIComponent(teamName)}`);
  const cached = getCachedData<{ status: string; team: BackendTeamProfile }>(cacheKey);
  if (cached) {
    console.log(`[cache] HIT: ${cacheKey}`);
    return cached;
  }

  const result = await withDeduplication<{ status: string; team: BackendTeamProfile }>(
    cacheKey,
    () => apiFetch<{ status: string; team: BackendTeamProfile }>(`/team/${encodeURIComponent(teamName)}`)
  );
  setCachedData(cacheKey, result, 10 * 60 * 1000); // 10 minute cache for team profiles
  return result;
}

// ── H2H response shape ────────────────────────────────────────────────────────

export interface BackendH2hMatch {
  date: string | null;
  home_team: string | null;
  away_team: string | null;
  score: string | null;
  winner: string | null;
  result_for_a: "W" | "D" | "L";
}

export interface BackendH2h {
  status: string;
  team_a: string;
  team_b: string;
  previous_meetings: number;
  team_a_wins: number;
  team_b_wins: number;
  draws: number;
  team_a_goals: number;
  team_b_goals: number;
  recent_matches: BackendH2hMatch[];
}

/**
 * GET /fastapi/h2h/{teamA}/{teamB}
 */
export async function getH2h(
  teamA: string,
  teamB: string
): Promise<BackendH2h> {
  const cacheKey = getCacheKey(`/h2h/${encodeURIComponent(teamA)}/${encodeURIComponent(teamB)}`);
  const cached = getCachedData<BackendH2h>(cacheKey);
  if (cached) {
    console.log(`[cache] HIT: ${cacheKey}`);
    return cached;
  }

  const result = await withDeduplication<BackendH2h>(
    cacheKey,
    () => apiFetch<BackendH2h>(`/h2h/${encodeURIComponent(teamA)}/${encodeURIComponent(teamB)}`)
  );
  setCachedData(cacheKey, result, 10 * 60 * 1000); // 10 minute cache for H2H
  return result;
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
  const cacheKey = getCacheKey('/fixtures', params);
  const cached = getCachedData<{ status: string; competition: string; count: number; fixtures: BackendFixture[] }>(cacheKey);
  if (cached) {
    console.log(`[cache] HIT: ${cacheKey}`);
    return cached;
  }

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
  
  const result = await withDeduplication<{ status: string; competition: string; count: number; fixtures: BackendFixture[] }>(
    cacheKey, 
    () => apiFetch<{ status: string; competition: string; count: number; fixtures: BackendFixture[] }>(`/fixtures?${qs.toString()}`)
  );
  setCachedData(cacheKey, result, 5 * 60 * 1000); // 5 minute cache for fixtures
  return result;
}

/**
 * GET /fastapi/fixtures-enriched?status=&stage=&group=&date_from=&date_to=&limit=&competition_code=
 *
 * Defaults: competition_code=WC, limit=200
 * All parameters are optional.
 */
export async function getFixturesEnriched(
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
): Promise<{ status: string; competition: string; count: number; fixtures: BackendFixtureEnriched[] }> {
  const cacheKey = getCacheKey('/fixtures-enriched', params);
  const cached = getCachedData<{ status: string; competition: string; count: number; fixtures: BackendFixtureEnriched[] }>(cacheKey);
  if (cached) {
    console.log(`[cache] HIT: ${cacheKey}`);
    return cached;
  }

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
  
  const result = await withDeduplication<{ status: string; competition: string; count: number; fixtures: BackendFixtureEnriched[] }>(
    cacheKey,
    () => apiFetch<{ status: string; competition: string; count: number; fixtures: BackendFixtureEnriched[] }>(`/fixtures-enriched?${qs.toString()}`)
  );
  setCachedData(cacheKey, result, 5 * 60 * 1000); // 5 minute cache
  return result;
}

/**
 * GET /fastapi/health
 */
export async function checkHealth(signal?: AbortSignal): Promise<BackendHealth> {
  return apiFetch<BackendHealth>("/health", { signal }, 15000);
}

/**
 * Wait until ML models are loaded (Render cold-start can take 30–60s).
 */
export async function waitForModelsReady(
  maxAttempts = 8,
  delayMs = 4000,
  signal?: AbortSignal
): Promise<BackendHealth> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
    try {
      const health = await checkHealth(signal);
      console.log(`[api] health attempt ${attempt}/${maxAttempts}:`, health);
      if (health.models_loaded) return health;
    } catch (err: any) {
      console.warn(`[api] health attempt ${attempt}/${maxAttempts} failed:`, err?.message);
    }
    if (attempt < maxAttempts) {
      await new Promise(r => setTimeout(r, delayMs));
    }
  }
  throw new Error("ML models are still loading on the backend — please reload in a moment.");
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

  // Only overwrite xG if the fresh call returns non-zero values.
  // The single /predict endpoint sometimes returns 0.0 for home goals when the
  // XGBoost goal model clips a negative prediction to 0.  If the base already
  // has real enrichment xG (from /fixtures-enriched), keep those values so the
  // drawer never shows "0.00" when the enriched data was good.
  const safeXGA = g.expected_home_goals > 0 ? g.expected_home_goals : (base.xGA ?? 0);
  const safeXGB = g.expected_away_goals > 0 ? g.expected_away_goals : (base.xGB ?? 0);
  const safeTotalXG = safeXGA + safeXGB;

  return {
    ...base,
    // Core prediction
    probA,
    probD,
    probB,
    prediction: predictionLabel,
    confidence,
    modelConfidence: o.confidence,
    // Goals / xG — guarded to never overwrite real enrichment data with 0
    xGA: safeXGA,
    xGB: safeXGB,
    totalExpectedGoals: g.total_expected_goals > 0 ? g.total_expected_goals : safeTotalXG,
    // Betting markets
    overUnder: m.over_under,
    bttsMarket: m.btts,
    cleanSheetMarket: m.clean_sheet || base.cleanSheetMarket,
    cleanSheetA: m.clean_sheet ? Math.round(m.clean_sheet.home_clean_sheet * 100) : base.cleanSheetA,
    cleanSheetB: m.clean_sheet ? Math.round(m.clean_sheet.away_clean_sheet * 100) : base.cleanSheetB,
    bttsRateA: m.btts ? Math.round(m.btts.yes * 100) : base.bttsRateA,
    bttsRateB: m.btts ? Math.round(m.btts.yes * 100) : base.bttsRateB,
    mostLikelyScore: m.most_likely_score,
    top5Scorelines: m.top_5_scorelines,
    asianHandicap: m.asian_handicap,
    teamGoals: m.team_goals,
    // New derived markets
    doubleChanceMarket: m.double_chance,
    drawNoBetMarket: m.draw_no_bet,
    winToNilMarket: m.win_to_nil,
    winningMarginMarket: m.winning_margin,
    goalRangeMarket: m.goal_range,
    correctScoreMatrix: m.correct_score_matrix,
    // Badge for live-model indicator in UI
    isLiveData: true,
  };
}

// ── Primary consumer: load all predictions ────────────────────────────────────

export function mapFixtureToPrediction(f: BackendFixture | BackendFixtureEnriched): MatchPrediction {
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
  let modelConfidence = 0.50;
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
    modelConfidence = p.predicted_outcome === "HOME_WIN" ? p.home_probability :
                      p.predicted_outcome === "AWAY_WIN" ? p.away_probability :
                      p.draw_probability;
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
    modelConfidence = 1.0;
  }

  const enrichment = (f as any).enrichment;

  const predictionObj: MatchPrediction = {
    id: String(f.id),
    teamA,
    teamB,
    teamACode,
    teamBCode,
    date: formatKickoffDateLocal(f.kickoff_time),
    kickoffTime: f.kickoff_time,
    stage: stageLabel,
    status: statusMapped,
    prediction: predictionLabel,
    confidence,
    modelConfidence,
    probA,
    probD,
    probB,
    venue: f.venue?.trim() || null,
    liveScore: f.live_score ?? null,
    winner: f.winner,
    minute: f.live_minute ?? null,
    ...(f.prediction || enrichment ? { isLiveData: true } : {}),

    // Default neutral placeholders for stats loaded dynamically in the match drawer
    attackA: 80, attackB: 80,
    defenceA: 80, defenceB: 80,
    midfieldA: 80, midfieldB: 80,
    xGA: enrichment ? enrichment.goals.home_xg : (f.live_score?.home ?? 0),
    xGB: enrichment ? enrichment.goals.away_xg : (f.live_score?.away ?? 0),
    xGAA: 1.0, xGAB: 1.0,
    possessionA: 50, possessionB: 50,
    shotsA: 12.0, shotsB: 12.0,
    shotsAllowedA: 10.0, shotsAllowedB: 10.0,
    cleanSheetA: enrichment && enrichment.markets?.clean_sheet ? Math.round(enrichment.markets.clean_sheet.home_clean_sheet * 100) : null,
    cleanSheetB: enrichment && enrichment.markets?.clean_sheet ? Math.round(enrichment.markets.clean_sheet.away_clean_sheet * 100) : null,
    bttsRateA: enrichment && enrichment.markets?.btts ? Math.round(enrichment.markets.btts.yes * 100) : null,
    bttsRateB: enrichment && enrichment.markets?.btts ? Math.round(enrichment.markets.btts.yes * 100) : null,
    // ── These are now loaded dynamically via getTeamProfile + getH2h ──────────
    recentFormA: [],
    recentFormB: [],
    fifaRankA: 0,
    fifaRankB: 0,
    eloRankA: 0,
    eloRankB: 0,
    squadValueA: "Loading...",
    squadValueB: "Loading...",
    // ─────────────────────────────────────────────────────────────────────────
    restDaysA: 4, restDaysB: 4,
    fatigueA: 20, fatigueB: 20,
    injuriesA: f.home_team?.injuries || [],
    injuriesB: f.away_team?.injuries || [],
    suspensionsA: f.home_team?.suspensions || [],
    suspensionsB: f.away_team?.suspensions || [],
    missingKeyPlayersA: [], missingKeyPlayersB: [],
    impactRatingA: "Minimal", impactRatingB: "Minimal",
    h2hPreviousMeetings: 0,
    h2hWinsA: 0, h2hWinsB: 0, h2hDraws: 0,
    h2hGoalsA: 0, h2hGoalsB: 0,
    aiSummary: "",
    
    // If completed, add btts and correct scoreline indicators
    ...(statusMapped === "COMPLETED" && {
      overUnder: {
        "0.5": { over: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 0.5 ? 1 : 0, under: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 0.5 ? 0 : 1 },
        "1.5": { over: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 1.5 ? 1 : 0, under: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 1.5 ? 0 : 1 },
        "2.5": { over: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 2.5 ? 1 : 0, under: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 2.5 ? 0 : 1 },
        "3.5": { over: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 3.5 ? 1 : 0, under: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 3.5 ? 0 : 1 },
        "4.5": { over: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 4.5 ? 1 : 0, under: (f.live_score?.home ?? 0) + (f.live_score?.away ?? 0) > 4.5 ? 0 : 1 },
      },
      bttsMarket: {
        yes: (f.live_score?.home ?? 0) > 0 && (f.live_score?.away ?? 0) > 0 ? 1 : 0,
        no: (f.live_score?.home ?? 0) > 0 && (f.live_score?.away ?? 0) > 0 ? 0 : 1
      },
      mostLikelyScore: `${f.live_score?.home ?? 0}-${f.live_score?.away ?? 0}`,
      top5Scorelines: [
        { score: `${f.live_score?.home ?? 0}-${f.live_score?.away ?? 0}`, probability: 1.0 }
      ],
      teamGoals: {
        home: {
          over_0_5: (f.live_score?.home ?? 0) > 0 ? 1 : 0,
          over_1_5: (f.live_score?.home ?? 0) > 1 ? 1 : 0,
          over_2_5: (f.live_score?.home ?? 0) > 2 ? 1 : 0,
        },
        away: {
          over_0_5: (f.live_score?.away ?? 0) > 0 ? 1 : 0,
          over_1_5: (f.live_score?.away ?? 0) > 1 ? 1 : 0,
          over_2_5: (f.live_score?.away ?? 0) > 2 ? 1 : 0,
        }
      }
    })
  };

  if (enrichment) {
    predictionObj.totalExpectedGoals = enrichment.goals.total_xg;
    predictionObj.overUnder = enrichment.markets.over_under;
    predictionObj.bttsMarket = enrichment.markets.btts;
    predictionObj.mostLikelyScore = enrichment.markets.most_likely_score;
    predictionObj.top5Scorelines = enrichment.markets.top_5_scorelines;
    predictionObj.cleanSheetMarket = enrichment.markets.clean_sheet;
    predictionObj.teamGoals = enrichment.markets.team_goals;
    predictionObj.asianHandicap = enrichment.markets.asian_handicap;
    // New derived markets
    predictionObj.doubleChanceMarket = enrichment.markets.double_chance;
    predictionObj.drawNoBetMarket = enrichment.markets.draw_no_bet;
    predictionObj.winToNilMarket = enrichment.markets.win_to_nil;
    predictionObj.winningMarginMarket = enrichment.markets.winning_margin;
    predictionObj.goalRangeMarket = enrichment.markets.goal_range;
    predictionObj.correctScoreMatrix = enrichment.markets.correct_score_matrix;
  }

  return predictionObj;
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

// ── Generic API response cache ─────────────────────────────────────────────────

interface GenericCacheEntry<T> {
  data: T;
  expiresAt: number;
}

const _genericCache = new Map<string, GenericCacheEntry<any>>();
const _pendingRequests = new Map<string, Promise<any>>();

function getCacheKey(endpoint: string, params?: Record<string, any>): string {
  const paramString = params ? JSON.stringify(params) : '';
  return `${endpoint}:${paramString}`;
}

function getCachedData<T>(key: string): T | null {
  const entry = _genericCache.get(key);
  if (!entry) return null;
  if (Date.now() > entry.expiresAt) {
    _genericCache.delete(key);
    return null;
  }
  return entry.data as T;
}

function setCachedData<T>(key: string, data: T, ttlMs: number = CACHE_TTL_MS): void {
  _genericCache.set(key, {
    data,
    expiresAt: Date.now() + ttlMs,
  });
}

// ── Request deduplication ─────────────────────────────────────────────────────

async function withDeduplication<T>(
  key: string,
  fetcher: () => Promise<T>
): Promise<T> {
  // Check if request is already in flight
  const existing = _pendingRequests.get(key);
  if (existing) {
    console.log(`[cache] Request deduped: ${key}`);
    return existing as Promise<T>;
  }

  // Create new request
  const promise = fetcher().finally(() => {
    _pendingRequests.delete(key);
  });

  _pendingRequests.set(key, promise);
  return promise;
}

// ── Batch predict API call ──────────────────────────────────────────────────

interface BatchMatchInput {
  home_team: string;
  away_team: string;
  competition_code?: string;
  match_id?: string;
}

interface BatchResultItem {
  home_team: string;
  away_team: string;
  match_id?: string;
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
  success_count?: number;
  error_count?: number;
  results: BatchResultItem[];
}

const BATCH_CHUNK_SIZE = 10;
const BATCH_CHUNK_TIMEOUT_MS = 90000;

function normalizeTeamName(name: string): string {
  return name.trim().toLowerCase().normalize("NFD").replace(/\p{M}/gu, "");
}

function findMatchForBatchResult(
  matches: MatchPrediction[],
  item: BatchResultItem
): MatchPrediction | undefined {
  if (item.match_id) {
    const byId = matches.find(m => m.id === item.match_id);
    if (byId) return byId;
  }
  const home = normalizeTeamName(item.home_team);
  const away = normalizeTeamName(item.away_team);
  return matches.find(
    m => normalizeTeamName(m.teamA) === home && normalizeTeamName(m.teamB) === away
  );
}

function applyBatchResults(
  batchResp: BatchPredictResponse,
  toFetch: MatchPrediction[],
  enrichedIds: Set<string>,
  onMatchUpdated: (matchId: string, enriched: MatchPrediction) => void
): { success: number; failed: number } {
  let success = 0;
  let failed = 0;

  for (const item of batchResp.results) {
    if (item.status !== "success" || !item.prediction) {
      failed += 1;
      console.warn(`[batch] ✗ ${item.home_team} vs ${item.away_team}: ${item.error ?? "no prediction"}`);
      continue;
    }

    const pred = item.prediction;
    setCached(item.home_team, item.away_team, pred);

    const base = findMatchForBatchResult(toFetch, item);
    if (!base) {
      failed += 1;
      console.warn(
        `[batch] ✗ could not match result to fixture: ${item.home_team} vs ${item.away_team}`
      );
      continue;
    }

    if (enrichedIds.has(base.id)) continue;

    const enriched = mapBackendPrediction(base, pred);
    enrichedIds.add(base.id);
    onMatchUpdated(base.id, enriched);
    success += 1;

    console.log(
      `[batch] ✓ ${enriched.teamA} vs ${enriched.teamB} → ` +
      `H ${enriched.probA}% D ${enriched.probD}% A ${enriched.probB}%` +
      (item.cached ? " (server cache)" : "")
    );
  }

  return { success, failed };
}

async function enrichMatchesIndividually(
  matches: MatchPrediction[],
  enrichedIds: Set<string>,
  onMatchUpdated: (matchId: string, enriched: MatchPrediction) => void,
  signal?: AbortSignal,
  concurrency = 5
): Promise<void> {
  const pending = matches.filter(m => !enrichedIds.has(m.id));
  if (pending.length === 0) return;

  console.log(`[api] individual /predict fallback for ${pending.length} match(es)`);

  for (let i = 0; i < pending.length; i += concurrency) {
    if (signal?.aborted) break;
    const chunk = pending.slice(i, i + concurrency);
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
        if (enrichedIds.has(id)) continue;
        setCached(base.teamA, base.teamB, prediction);
        const enriched = mapBackendPrediction(base, prediction);
        enrichedIds.add(id);
        onMatchUpdated(id, enriched);
        console.log(
          `[predict] ✓ ${enriched.teamA} vs ${enriched.teamB} → ` +
          `H ${enriched.probA}% D ${enriched.probD}% A ${enriched.probB}%`
        );
      } else {
        console.warn("[api] Individual prediction failed (skipped):", outcome.reason?.message);
      }
    }
  }
}

export async function predictBatch(
  matches: BatchMatchInput[],
  signal?: AbortSignal
): Promise<BatchPredictResponse> {
  console.log(`[api] predictBatch → ${matches.length} match(es)`);
  const resp = await apiFetch<BatchPredictResponse>("/predict-batch", {
    method: "POST",
    signal,
    body: JSON.stringify({ matches }),
  }, BATCH_CHUNK_TIMEOUT_MS);
  console.log(
    `[api] predictBatch ← ${resp.count} results in ${resp.total_ms?.toFixed?.(0) ?? "?"} ms ` +
    `(success: ${resp.success_count ?? "?"}, errors: ${resp.error_count ?? "?"})`
  );
  return resp;
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
  signal?: AbortSignal,
  limit: number = 30
): Promise<MatchPrediction[]> {
  const t0 = performance.now();

  console.log("[perf] ► fixtures fetch start");
  let fixtures: (BackendFixture | BackendFixtureEnriched)[] = [];
  try {
    const fixturesResponse = await getFixturesEnriched({
      competition_code: "WC",
      limit,
      year,
      show_historical: showHistorical,
    });
    fixtures = fixturesResponse.fixtures || [];
  } catch (err: any) {
    console.warn("[api] getFixturesEnriched failed, falling back to standard getFixtures:", err?.message);
    if (signal?.aborted) throw err;
    const fixturesResponse = await getFixtures({
      competition_code: "WC",
      limit,
      year,
      show_historical: showHistorical,
    });
    fixtures = fixturesResponse.fixtures || [];
  }
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
  if (activeMatches.length === 0) {
    console.log("[api] enrichment skipped — no LIVE/UPCOMING matches");
    return;
  }

  // Ensure ML models are loaded before firing batch requests (avoids 503 on cold start)
  try {
    await waitForModelsReady(8, 4000, signal);
  } catch (err: any) {
    if (signal?.aborted) return;
    console.error("[api] Models not ready — skipping prediction enrichment:", err?.message);
    return;
  }

  const enrichedIds = new Set<string>();
  const cached: MatchPrediction[] = [];
  const toFetch: MatchPrediction[] = [];

  for (const m of activeMatches) {
    if (m.isLiveData) {
      enrichedIds.add(m.id);
      continue;
    }
    const hit = getCached(m.teamA, m.teamB);
    if (hit) {
      cached.push(m);
      const enriched = mapBackendPrediction(m, hit);
      enrichedIds.add(m.id);
      onMatchUpdated(m.id, enriched);
      console.log(
        `[cache HIT] ${m.teamA} vs ${m.teamB} → H ${enriched.probA}% D ${enriched.probD}% A ${enriched.probB}%`
      );
    } else {
      toFetch.push(m);
    }
  }

  console.log(
    `[perf] ► prediction enrichment start: ${toFetch.length} cache-miss, ` +
    `${cached.length} client-cache hits, ${enrichedIds.size - cached.length} already enriched`
  );

  if (toFetch.length === 0) return;

  const tPredStart = performance.now();

  // Chunked batch requests — avoids 120s timeout when 40+ matches hit cold Render
  for (let i = 0; i < toFetch.length; i += BATCH_CHUNK_SIZE) {
    if (signal?.aborted) break;

    const chunk = toFetch.slice(i, i + BATCH_CHUNK_SIZE);
    const batchPayload = chunk.map(m => ({
      home_team: m.teamA,
      away_team: m.teamB,
      competition_code: "WC",
      match_id: m.id,
    }));

    console.log(
      `[batch] chunk ${Math.floor(i / BATCH_CHUNK_SIZE) + 1}/` +
      `${Math.ceil(toFetch.length / BATCH_CHUNK_SIZE)} → ${chunk.length} match(es)`
    );

    try {
      const batchResp = await predictBatch(batchPayload, signal);
      const { success, failed } = applyBatchResults(batchResp, chunk, enrichedIds, onMatchUpdated);
      console.log(`[batch] chunk done: ${success} success, ${failed} failed`);
    } catch (batchErr: any) {
      if (signal?.aborted) return;
      console.warn(
        `[api] Batch chunk failed (${chunk.length} matches), will retry individually:`,
        batchErr?.message
      );
    }
  }

  // Always retry any still-missing matches individually (fixes partial batch failure bug)
  const stillMissing = toFetch.filter(m => !enrichedIds.has(m.id));
  if (stillMissing.length > 0 && !signal?.aborted) {
    console.log(`[api] ${stillMissing.length} match(es) still need predictions after batch`);
    await enrichMatchesIndividually(stillMissing, enrichedIds, onMatchUpdated, signal);
  }

  const finalMissing = toFetch.filter(m => !enrichedIds.has(m.id)).length;
  if (!signal?.aborted) {
    const tPredEnd = performance.now();
    const totalElapsed = t0Page > 0 ? tPredEnd - t0Page : tPredEnd - tPredStart;
    console.log(
      `[perf] prediction enrichment complete: ${enrichedIds.size}/${activeMatches.length} enriched, ` +
      `${finalMissing} still missing, fetch time ${(tPredEnd - tPredStart).toFixed(0)} ms`
    );
    console.log(`[perf] total page render time (fixtures + enrichment): ${totalElapsed.toFixed(0)} ms`);
    if (finalMissing > 0) {
      console.warn(`[api] ${finalMissing} match(es) could not be enriched — check team names or backend logs`);
    }
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
 * mergeFixturesWithEnrichment
 * Re-applies ML enrichment from a previous render when refreshing fixture scores/status.
 */
export function mergeFixturesWithEnrichment(
  fresh: MatchPrediction[],
  existing: MatchPrediction[]
): MatchPrediction[] {
  const existingById = new Map(existing.map(m => [m.id, m]));

  return fresh.map(freshMatch => {
    const prev = existingById.get(freshMatch.id);
    if (!prev) return freshMatch;

    // Completed matches: use fresh result-derived probabilities from the API.
    if (freshMatch.status === "COMPLETED") {
      return { ...freshMatch, isLiveData: prev.isLiveData ?? freshMatch.isLiveData };
    }

    if (!prev.isLiveData) return freshMatch;

    return {
      ...freshMatch,
      probA: prev.probA,
      probD: prev.probD,
      probB: prev.probB,
      prediction: prev.prediction,
      confidence: prev.confidence,
      modelConfidence: prev.modelConfidence,
      isLiveData: true,
      overUnder: prev.overUnder,
      bttsMarket: prev.bttsMarket,
      mostLikelyScore: prev.mostLikelyScore,
      top5Scorelines: prev.top5Scorelines,
      asianHandicap: prev.asianHandicap,
      teamGoals: prev.teamGoals,
      totalExpectedGoals: prev.totalExpectedGoals,
      xGA: prev.xGA,
      xGB: prev.xGB,
      aiSummary: prev.aiSummary,
    };
  });
}

/**
 * mergeLiveScoreUpdate
 * Applies score/status/minute from a fresh fixture onto an existing enriched match.
 */
export function mergeLiveScoreUpdate(
  existing: MatchPrediction,
  fresh: MatchPrediction
): MatchPrediction {
  const merged = mergeFixturesWithEnrichment([fresh], [existing])[0];
  return merged;
}

/**
 * refreshLiveScoresInto()
 * Lightweight poll — fetches only IN_PLAY/PAUSED fixtures and merges into existing state.
 * Used by the 30-second live refresh interval.
 */
export async function refreshLiveScoresInto(
  existing: MatchPrediction[]
): Promise<MatchPrediction[]> {
  const previouslyLiveIds = new Set(
    existing.filter(m => m.status === "LIVE").map(m => m.id)
  );

  const liveFixtures = await getLiveFixtures();

  if (previouslyLiveIds.size > 0) {
    const stillLiveIds = new Set(liveFixtures.map(f => f.id));
    const endedCount = [...previouslyLiveIds].filter(id => !stillLiveIds.has(id)).length;
    if (endedCount > 0) {
      console.info(
        `[api] ${endedCount} previously-live match(es) no longer IN_PLAY — running full fixture refresh`
      );
      return refreshFixturesFromApi(existing);
    }
  }

  if (liveFixtures.length === 0) {
    console.info("[api] refreshLiveScoresInto — no live fixtures in DB");
    return existing;
  }

  const liveById = new Map(liveFixtures.map(m => [m.id, m]));
  let changeCount = 0;

  const updated = existing.map(match => {
    const fresh = liveById.get(match.id);
    if (!fresh) return match;

    const scoreChanged =
      match.liveScore?.home !== fresh.liveScore?.home ||
      match.liveScore?.away !== fresh.liveScore?.away ||
      match.status !== fresh.status ||
      match.minute !== fresh.minute;

    if (scoreChanged) {
      changeCount += 1;
      console.info(
        `[api] Live score update: ${match.teamA} vs ${match.teamB} ` +
        `${match.liveScore?.home ?? "?"}-${match.liveScore?.away ?? "?"} → ` +
        `${fresh.liveScore?.home ?? "?"}-${fresh.liveScore?.away ?? "?"} ` +
        `(min ${fresh.minute ?? "?"})`
      );
    }

    return mergeLiveScoreUpdate(match, fresh);
  });

  console.info(
    `[api] refreshLiveScoresInto — ${liveFixtures.length} live fixture(s), ${changeCount} score change(s)`
  );
  return updated;
}

/**
 * refreshFixturesFromApi()
 * Lightweight poll — fetches all fixtures and merges with existing ML enrichment.
 * Used by the 30s (live) and 5min (upcoming) frontend refresh intervals.
 */
export async function refreshFixturesFromApi(
  existing: MatchPrediction[],
  showHistorical?: boolean,
  limit: number = 30
): Promise<MatchPrediction[]> {
  const fixturesResponse = await getFixtures({
    competition_code: "WC",
    limit,
    show_historical: showHistorical,
  });
  const fresh = (fixturesResponse.fixtures || []).map(mapFixtureToPrediction);
  return mergeFixturesWithEnrichment(fresh, existing);
}

/**
 * getLiveFixtures()
 *
 * Lightweight poll — fetches only IN_PLAY and PAUSED fixtures from the DB.
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
 * GET /tournament/standings
 */
export async function getStandings(): Promise<GroupStandings> {
  const cacheKey = getCacheKey('/tournament/standings');
  const cached = getCachedData<GroupStandings>(cacheKey);
  if (cached) {
    console.log(`[cache] HIT: ${cacheKey}`);
    return cached;
  }

  const result = await withDeduplication<GroupStandings>(
    cacheKey,
    () => apiFetch<GroupStandings>("/tournament/standings")
  );
  setCachedData(cacheKey, result, 5 * 60 * 1000); // 5 minute cache
  return result;
}

/**
 * GET /tournament/bracket
 */
export async function getBracket(): Promise<BracketData> {
  const cacheKey = getCacheKey('/tournament/bracket');
  const cached = getCachedData<BracketData>(cacheKey);
  if (cached) {
    console.log(`[cache] HIT: ${cacheKey}`);
    return cached;
  }

  const result = await withDeduplication<BracketData>(
    cacheKey,
    () => apiFetch<BracketData>("/tournament/bracket")
  );
  setCachedData(cacheKey, result, 5 * 60 * 1000); // 5 minute cache
  return result;
}


/**
 * GET /tournament/model-performance
 */
export async function getModelPerformance(): Promise<ModelPerformanceStats> {
  const cacheKey = getCacheKey('/tournament/model-performance');
  const cached = getCachedData<ModelPerformanceStats>(cacheKey);
  if (cached) {
    console.log(`[cache] HIT: ${cacheKey}`);
    return cached;
  }

  const result = await withDeduplication<ModelPerformanceStats>(
    cacheKey,
    () => apiFetch<ModelPerformanceStats>("/tournament/model-performance")
  );
  setCachedData(cacheKey, result, 10 * 60 * 1000); // 10 minute cache
  return result;
}

export interface TeamSimulationResult {
  group_stage: number;
  qualify_probability?: number;
  r32: number;
  r16: number;
  qf: number;
  sf: number;
  final: number;
  winner: number;
}

export interface TournamentSimulationResponse {
  status: string;
  simulation_count: number;
  results: Record<string, TeamSimulationResult>;
}

/**
 * GET /tournament/simulation
 */
export async function getTournamentSimulation(): Promise<TournamentSimulationResponse> {
  const cacheKey = getCacheKey('/tournament/simulation');
  const cached = getCachedData<TournamentSimulationResponse>(cacheKey);
  if (cached) {
    console.log(`[cache] HIT: ${cacheKey}`);
    return cached;
  }

  const result = await withDeduplication<TournamentSimulationResponse>(
    cacheKey,
    () => apiFetch<TournamentSimulationResponse>("/tournament/simulation")
  );
  setCachedData(cacheKey, result, 5 * 60 * 1000); // 5 minute cache
  return result;
}

