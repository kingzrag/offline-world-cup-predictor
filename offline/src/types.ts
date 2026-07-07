// ── Market sub-types (mirror BackendMarkets from api.ts) ─────────────────────

export interface OverUnderLine {
  over: number;   // probability 0–1
  under: number;  // probability 0–1
}

export interface BTTSMarket {
  yes: number;  // probability 0–1
  no: number;   // probability 0–1
}

export interface CleanSheetMarket {
  home_clean_sheet: number;  // P(away scores 0) — 0–1
  away_clean_sheet: number;  // P(home scores 0) — 0–1
}

export interface ScorelineProbability {
  score: string;       // e.g. "1-0"
  probability: number; // 0–1
}

export interface AsianHandicap {
  label: string;
  lines: Record<string, number>; // e.g. { "-0.5": 0.54, "0.0": 0.50 }
  favored_team: string;
}

export interface TeamGoalMarket {
  over_0_5: number;
  over_1_5: number;
  over_2_5: number;
}

export interface DoubleChanceMarket {
  "1x": number;  // Home Win or Draw
  "12": number;  // Home Win or Away Win
  "x2": number;  // Draw or Away Win
}

export interface DrawNoBetMarket {
  home: number;  // Home DNB probability
  away: number;  // Away DNB probability
}

export interface WinToNilMarket {
  home: number;  // Home wins AND away scores 0
  away: number;  // Away wins AND home scores 0
}

export interface WinningMarginMarket {
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

export interface GoalRangeMarket {
  "0_goals": number;
  "1_goal": number;
  "2_goals": number;
  "3_goals": number;
  "4_goals": number;
  "5_plus": number;
}

// ── Core prediction interfaces ────────────────────────────────────────────────

export interface MatchPrediction {
  id: string;
  teamA: string;
  teamB: string;
  teamACode: string; // ISO 3-letter code
  teamBCode: string; // ISO 3-letter code
  date: string;
  stage: string;
  status: 'LIVE' | 'UPCOMING' | 'COMPLETED';
  prediction: string;
  confidence: 'High' | 'Medium' | 'Low';
  probA: number; // probability of teamA win (0-100)
  probD: number; // probability of draw (0-100)
  probB: number; // probability of teamB win (0-100)
  /** Home stadium — only present when verified in backend data */
  venue?: string | null;
  winner?: 'HOME_TEAM' | 'AWAY_TEAM' | 'DRAW' | null;

  // Tactical ratings (0-99 scale)
  attackA: number;
  attackB: number;
  defenceA: number;
  defenceB: number;
  midfieldA: number;
  midfieldB: number;

  // Statistical metrics
  xGA: number; // expected goals scored by A
  xGB: number; // expected goals scored by B
  xGAA: number; // expected goals allowed by A
  xGAB: number; // expected goals allowed by B
  possessionA: number;
  possessionB: number;
  shotsA: number;
  shotsB: number;
  shotsAllowedA: number;
  shotsAllowedB: number;
  cleanSheetA: number | null; // %
  cleanSheetB: number | null; // %
  bttsRateA: number | null;   // %
  bttsRateB: number | null;   // %

  // High-level details
  recentFormA: string[]; // e.g. ["W","W","D","W","L"]
  recentFormB: string[];
  fifaRankA: number;
  fifaRankB: number;
  eloRankA: number;
  eloRankB: number;
  squadValueA: string; // e.g. "€1.13B"
  squadValueB: string;
  restDaysA: number;
  restDaysB: number;
  fatigueA: number; // 0-100 (higher = more tired)
  fatigueB: number;

  // Player availability
  injuriesA: string[];
  injuriesB: string[];
  suspensionsA: string[];
  suspensionsB: string[];
  missingKeyPlayersA?: string[];
  missingKeyPlayersB?: string[];
  impactRatingA: 'Critical' | 'Moderate' | 'Minimal';
  impactRatingB: 'Critical' | 'Moderate' | 'Minimal';

  // Head-to-head history
  h2hPreviousMeetings: number;
  h2hWinsA: number;
  h2hWinsB: number;
  h2hDraws: number;
  h2hGoalsA: number;
  h2hGoalsB: number;

  // Dynamic AI summary
  aiSummary?: string;

  // ── Live backend market fields (populated when FastAPI responds) ─────────────
  overUnder?: {
    "0.5"?: OverUnderLine;
    "1.5": OverUnderLine;
    "2.5": OverUnderLine;
    "3.5": OverUnderLine;
    "4.5"?: OverUnderLine;
    "5.5"?: OverUnderLine;
    "6.5"?: OverUnderLine;
    "7.5"?: OverUnderLine;
  };
  bttsMarket?: BTTSMarket;
  cleanSheetMarket?: CleanSheetMarket;  // Poisson-derived clean sheet probabilities
  mostLikelyScore?: string;
  top5Scorelines?: ScorelineProbability[];
  asianHandicap?: AsianHandicap;
  teamGoals?: {
    home: TeamGoalMarket;
    away: TeamGoalMarket;
  };
  totalExpectedGoals?: number;
  modelConfidence?: number;
  // New derived markets
  doubleChanceMarket?: DoubleChanceMarket;
  drawNoBetMarket?: DrawNoBetMarket;
  winToNilMarket?: WinToNilMarket;
  winningMarginMarket?: WinningMarginMarket;
  goalRangeMarket?: GoalRangeMarket;
  correctScoreMatrix?: ScorelineProbability[];

  // Monte Carlo qualification & advancement (from /tournament/simulation)
  qualifyProbA?: number;  // 0–100 probability teamA qualifies from group
  qualifyProbB?: number;  // 0–100 probability teamB qualifies from group
  advancementA?: {
    r32: number; r16: number; qf: number; sf: number; final: number; champion: number;
  };
  advancementB?: {
    r32: number; r16: number; qf: number; sf: number; final: number; champion: number;
  };

  /** Set to true when this record was enriched by the live FastAPI model */
  isLiveData?: boolean;

  /** Raw ISO-8601 UTC kickoff time — always UTC; format for display via dateTimeUtils */
  kickoffTime?: string | null;

  /**
   * Current or final score from football-data.org.
   * Populated for IN_PLAY, PAUSED, and FINISHED matches.
   * null for SCHEDULED / TIMED matches.
   */
  liveScore?: { home: number; away: number; is_live: boolean } | null;

  /** Match minute from football-data.org (IN_PLAY / PAUSED only) */
  minute?: number | null;
}

export interface TrophyProbability {
  rank: number;
  name: string;
  code: string;
  winProbabilityPercent: number;
  confidence: 'High' | 'Medium' | 'Low';
  recentForm: string[];
  tournamentStrength: number;

  // Team analysis details
  attackRating: number;
  defenceRating: number;
  midfieldRating: number;
  gkRating: number;
  squadDepth: number;
  avgAge: number;
  marketValue: string;
  coach: string;
  coachRating: number;

  // Last 10 matches
  last10Wins: number;
  last10Draws: number;
  last10Losses: number;
  last10GoalsScored: number;
  last10GoalsConceded: number;

  // Projected path
  likelyPath: {
    groupStage: string;
    roundOf32: string;
    roundOf16: string;
    quarterFinal: string;
    semiFinal: string;
    final: string;
  };
}

export interface IntelligenceInsight {
  id: string;
  type:
    | 'Most Improved Team'
    | 'Best Attack'
    | 'Best Defence'
    | 'Dark Horse'
    | 'Biggest Upset Candidate'
    | 'Most Underrated Squad'
    | 'Best Emerging Player'
    | 'Most Difficult Group';
  team: string;
  details: string;
  secondaryMetric?: string;
  analyst: string;
  explanation?: string;
}
