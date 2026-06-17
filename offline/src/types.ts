// ── Market sub-types (mirror BackendMarkets from api.ts) ─────────────────────

export interface OverUnderLine {
  over: number;   // probability 0–1
  under: number;  // probability 0–1
}

export interface BTTSMarket {
  yes: number;  // probability 0–1
  no: number;   // probability 0–1
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
  venue: string;
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
  cleanSheetA: number; // %
  cleanSheetB: number; // %
  bttsRateA: number;   // %
  bttsRateB: number;   // %

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
    "1.5": OverUnderLine;
    "2.5": OverUnderLine;
    "3.5": OverUnderLine;
  };
  bttsMarket?: BTTSMarket;
  mostLikelyScore?: string;
  top5Scorelines?: ScorelineProbability[];
  asianHandicap?: AsianHandicap;
  teamGoals?: {
    home: TeamGoalMarket;
    away: TeamGoalMarket;
  };
  totalExpectedGoals?: number;
  modelConfidence?: number;

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
