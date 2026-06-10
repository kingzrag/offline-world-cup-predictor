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
  crest_url: string | null;
}

export interface BackendFixture {
  id: number;
  utc_date: string | null;
  status: string;
  competition: string | null;
  home_team: BackendFixtureTeam | null;
  away_team: BackendFixtureTeam | null;
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
  timeoutMs = 8000
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
  competitionCode = "WC"
): Promise<BackendPredictResponse> {
  return apiFetch<BackendPredictResponse>("/predict", {
    method: "POST",
    body: JSON.stringify({
      home_team: homeTeam,
      away_team: awayTeam,
      competition_code: competitionCode,
    }),
  });
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
 * GET /fastapi/fixtures?limit=&competition_id=
 */
export async function getFixtures(
  limit = 20,
  competitionId?: number
): Promise<{ status: string; count: number; fixtures: BackendFixture[] }> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (competitionId != null) params.set("competition_id", String(competitionId));
  return apiFetch(`/fixtures?${params.toString()}`);
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

/**
 * getPredictions()
 *
 * Strategy:
 *   1. Check health — if models not loaded, bail out early.
 *   2. Use the MOCK_MATCHES fixture list as the canonical schedule.
 *      For each match, fire POST /api/predict with the real team names.
 *   3. Merge the live prediction into the mock record via mapBackendPrediction.
 *   4. Return enriched records. Failures on individual matches are silent —
 *      that match keeps its mock values.
 *
 * This gives us real ML output for every match in the schedule without
 * needing a dedicated "list all predictions" endpoint on the backend.
 */
export async function getPredictions(): Promise<MatchPrediction[]> {
  // 1. Verify backend is reachable and models are loaded
  let health: BackendHealth;
  try {
    health = await checkHealth();
  } catch {
    throw new Error("FastAPI backend unreachable");
  }

  if (!health.models_loaded) {
    throw new Error("ML models are still loading on the backend");
  }

  // 2. Run predictions for every mock match in parallel (with concurrency cap)
  const CONCURRENCY = 4;
  const results: MatchPrediction[] = [...MOCK_MATCHES];

  // Process in batches to avoid hammering the server
  for (let i = 0; i < MOCK_MATCHES.length; i += CONCURRENCY) {
    const batch = MOCK_MATCHES.slice(i, i + CONCURRENCY);
    const settled = await Promise.allSettled(
      batch.map(async (mockMatch) => {
        const resp = await predictMatch(mockMatch.teamA, mockMatch.teamB, "WC");
        return { index: i + batch.indexOf(mockMatch), enriched: mapBackendPrediction(mockMatch, resp.prediction) };
      })
    );

    // Merge successful predictions back into results array
    for (const outcome of settled) {
      if (outcome.status === "fulfilled") {
        results[outcome.value.index] = outcome.value.enriched;
      }
      // On rejection: keep the mock value at that index (silent fallback)
    }
  }

  return results;
}
