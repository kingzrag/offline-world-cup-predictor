import { MatchPrediction, TrophyProbability, IntelligenceInsight } from "./types";

export const MOCK_MATCHES: MatchPrediction[] = [];

export const MOCK_TROPHY_PROBABILITIES: TrophyProbability[] = [
  {
    rank: 1,
    name: "Argentina",
    code: "ARG",
    winProbabilityPercent: 18.4,
    confidence: "High",
    recentForm: ["W", "W", "W", "W", "D"],
    tournamentStrength: 96,
    attackRating: 92,
    defenceRating: 91,
    midfieldRating: 93,
    gkRating: 89,
    squadDepth: 93,
    avgAge: 27.6,
    marketValue: "€950M",
    coach: "Lionel Scaloni",
    coachRating: 97,
    last10Wins: 8,
    last10Draws: 1,
    last10Losses: 1,
    last10GoalsScored: 24,
    last10GoalsConceded: 6,
    likelyPath: {
      groupStage: "Group C Winner",
      roundOf32: "vs Denmark (Group D Runner-up)",
      roundOf16: "vs Belgium (Group K Winner)",
      quarterFinal: "vs England (QF)",
      semiFinal: "vs Spain (SF)",
      final: "vs Brazil (Final)"
    }
  },
  {
    rank: 2,
    name: "Brazil",
    code: "BRA",
    winProbabilityPercent: 16.1,
    confidence: "High",
    recentForm: ["W", "W", "W", "D", "W"],
    tournamentStrength: 94,
    attackRating: 94,
    defenceRating: 89,
    midfieldRating: 91,
    gkRating: 92,
    squadDepth: 95,
    avgAge: 26.4,
    marketValue: "€1.25B",
    coach: "Dorival Júnior",
    coachRating: 88,
    last10Wins: 7,
    last10Draws: 2,
    last10Losses: 1,
    last10GoalsScored: 26,
    last10GoalsConceded: 8,
    likelyPath: {
      groupStage: "Group A Winner",
      roundOf32: "vs Sweden (Group B Runner-up)",
      roundOf16: "vs Germany (Round of 16)",
      quarterFinal: "vs Portugal (Quarter Final)",
      semiFinal: "vs France (Semi Final)",
      final: "vs Argentina (Final)"
    }
  },
  {
    rank: 3,
    name: "France",
    code: "FRA",
    winProbabilityPercent: 14.8,
    confidence: "High",
    recentForm: ["W", "D", "W", "L", "W"],
    tournamentStrength: 93,
    attackRating: 95,
    defenceRating: 90,
    midfieldRating: 89,
    gkRating: 88,
    squadDepth: 97,
    avgAge: 25.8,
    marketValue: "€1.35B",
    coach: "Didier Deschamps",
    coachRating: 92,
    last10Wins: 6,
    last10Draws: 2,
    last10Losses: 2,
    last10GoalsScored: 22,
    last10GoalsConceded: 9,
    likelyPath: {
      groupStage: "Group B Winner",
      roundOf32: "vs Ukraine (Group A Runner-up)",
      roundOf16: "vs Italy (Round of 16)",
      quarterFinal: "vs Netherlands (Quarter Final)",
      semiFinal: "vs Brazil (Semi Final)",
      final: "vs Argentina (Final)"
    }
  },
  {
    rank: 4,
    name: "Spain",
    code: "ESP",
    winProbabilityPercent: 12.2,
    confidence: "High",
    recentForm: ["W", "D", "W", "W", "W"],
    tournamentStrength: 92,
    attackRating: 90,
    defenceRating: 88,
    midfieldRating: 95,
    gkRating: 86,
    squadDepth: 90,
    avgAge: 24.8,
    marketValue: "€1.10B",
    coach: "Luis de la Fuente",
    coachRating: 94,
    last10Wins: 8,
    last10Draws: 1,
    last10Losses: 1,
    last10GoalsScored: 25,
    last10GoalsConceded: 7,
    likelyPath: {
      groupStage: "Group F Winner",
      roundOf32: "vs Chile (Group E Runner-up)",
      roundOf16: "vs Uruguay (Round of 16)",
      quarterFinal: "vs USA (Quarter Final)",
      semiFinal: "vs Argentina (Semi Final)",
      final: "vs Brazil (Final)"
    }
  },
  {
    rank: 5,
    name: "England",
    code: "ENG",
    winProbabilityPercent: 9.8,
    confidence: "Medium",
    recentForm: ["L", "W", "W", "D", "W"],
    tournamentStrength: 89,
    attackRating: 89,
    defenceRating: 85,
    midfieldRating: 92,
    gkRating: 84,
    squadDepth: 96,
    avgAge: 26.2,
    marketValue: "€1.42B",
    coach: "Thomas Tuchel",
    coachRating: 91,
    last10Wins: 5,
    last10Draws: 3,
    last10Losses: 2,
    last10GoalsScored: 18,
    last10GoalsConceded: 10,
    likelyPath: {
      groupStage: "Group E Winner",
      roundOf32: "vs Austria (Group F Runner-up)",
      roundOf16: "vs Switzerland (Round of 16)",
      quarterFinal: "vs Argentina (Quarter Final)",
      semiFinal: "vs Spain (Semi Final)",
      final: "vs Brazil (Final)"
    }
  },
  {
    rank: 6,
    name: "Portugal",
    code: "POR",
    winProbabilityPercent: 8.5,
    confidence: "High",
    recentForm: ["W", "W", "W", "W", "W"],
    tournamentStrength: 90,
    attackRating: 93,
    defenceRating: 88,
    midfieldRating: 91,
    gkRating: 87,
    squadDepth: 94,
    avgAge: 26.9,
    marketValue: "€1.05B",
    coach: "Roberto Martínez",
    coachRating: 85,
    last10Wins: 8,
    last10Draws: 1,
    last10Losses: 1,
    last10GoalsScored: 27,
    last10GoalsConceded: 8,
    likelyPath: {
      groupStage: "Group L Winner",
      roundOf32: "vs South Korea (Group K Runner-up)",
      roundOf16: "vs Croatia (Round of 16)",
      quarterFinal: "vs Brazil (Quarter Final)",
      semiFinal: "vs France (Semi Final)",
      final: "vs Argentina (Final)"
    }
  }
];

export const MOCK_INTELLIGENCE: IntelligenceInsight[] = [
  {
    id: "int1",
    type: "Most Improved Team",
    team: "USA",
    details: "Expected goals conceded dropped by 34% inside the last six months, paired with extreme vertical speed outliers under Thomas Tuchel's structural lessons.",
    secondaryMetric: "-34% xGA Decline",
    analyst: "Tactical Desk, London",
    explanation: "Under the latest technical refinements, the US squad has drastically improved its rest-defense. High athletic capacity allows them to retreat and compact spaces within seconds, limiting central shot creation channels. This quantitative adjustment converts a historically unstable, high-variance squad into a robust defensive organization capable of deep bracket runs."
  },
  {
    id: "int2",
    type: "Best Attack",
    team: "France",
    details: "Averaging 2.65 Expected Goals (xG) per 90, driven by the most progressive acceleration metrics in deep half-spaces.",
    secondaryMetric: "2.65 xG / 90 min",
    analyst: "Data Operations, Paris",
    explanation: "France's structural attacking efficiency relies on explosive isolation patterns on both wings. Progressive ball carry metrics reveal that they bypass defensive blocks faster than any other team in Europe. With deep squad options allowing constant athletic rotation, France maintains high output throughout 90 minutes with zero degradation."
  },
  {
    id: "int3",
    type: "Best Defence",
    team: "Argentina",
    details: "Registry confirms only 4 professional goals conceded in their last 12 competitive matches. Opponents averaged an empty 0.62 xG per game.",
    secondaryMetric: "0.62 xG Allowed",
    analyst: "Analytical Director, Buenos Aires",
    explanation: "Argentina's success is rooted in aggressive rest-defense positioning. By compressing central space early in opponent build-ups, they deny passing lanes before transition risks materialize. High tactical discipline keeps their central center-backs shielded, minimizing high-quality chances against them."
  },
  {
    id: "int4",
    type: "Dark Horse",
    team: "Ecuador",
    details: "Unmatched high-altitude cardiovascular baseline metrics matching supreme central structural solidity in ELO ratings.",
    secondaryMetric: "+148 ELO points",
    analyst: "Global Scouting, Quito",
    explanation: "Ecuador possesses a unique high-intensity physical core that excels in double-pivot setups. The tactical data highlights high physical recovery rates, enabling them to sustain an intense high-press for full matches. If matched against possession-heavy European transition templates, Ecuador's pacing and physical disruptions present major tactical obstacles."
  },
  {
    id: "int5",
    type: "Biggest Upset Candidate",
    team: "Germany",
    details: "High squad fatigue indexes combined with severe spatial vulnerabilities in defensive response to rapid transitions.",
    secondaryMetric: "1.45 xGA Vulnerability",
    analyst: "Strategic Advisor, Berlin",
    explanation: "Germany's tactical setup is vulnerable to vertical transitions. When their fullbacks advance, spatial metrics show large gaps on the wings that are easily exploited. Aging center-backs lack recovery speed under counter-attacks, making them a prime candidate for early upsets against dynamic low-block transition sides."
  },
  {
    id: "int6",
    type: "Most Underrated Squad",
    team: "Denmark",
    details: "Consistent upper-decile rankings in set-piece expected goals (xG) and spatial midfield recycling rates.",
    secondaryMetric: "42% Set-piece xG Share",
    analyst: "Data Analyst, Copenhagen",
    explanation: "Denmark runs a highly sophisticated, deterministic strategy based on planned dead-ball operations. Their physical profile suits crowded box overloads, while their midfield recycling rates ensure constant territorial recovery. They are highly efficient at winning tight games without needing open-field brilliant plays."
  },
  {
    id: "int7",
    type: "Best Emerging Player",
    team: "Lamine Yamal (Spain)",
    details: " Outperforming all traditional age bracket progress curves in high-pressure creative metrics and progressive carries.",
    secondaryMetric: "6.8 Progressive Carries/90",
    analyst: "Director of Youth Scouting, Madrid",
    explanation: "Yamal's statistical profile shows extreme maturity in progressive carries and key passing decisions. Under pressure, his turnover index is exceptionally low, representing elite spatial awareness. He remains Spain's premium offensive creator, generating immediate territorial advantages."
  },
  {
    id: "int8",
    type: "Most Difficult Group",
    team: "Group L (Portugal, Italy, Senegal, Japan)",
    details: "The highest aggregate ELO concentration in World Cup history. Expect severe positional friction grids.",
    secondaryMetric: "1894 Avg Group ELO",
    analyst: "Tournament Design, Munich",
    explanation: "Group L represents an unprecedented tactical bottleneck. Senegal and Japan hold high physical and structural baselines that directly disrupt Portugal and Italy's offensive schemes. Every single point in this bracket is heavily contested, making fatigue management and structural discipline critical survival elements."
  }
];

export const MOCK_ACCURACY_STATS = {
  totalPredictions: 412,
  correctPredictions: 326,
  accuracyPercentage: 79.1,
  roi: 18.4,
  tournamentAccuracy: [
    { tournament: "Copa América 2024", accuracy: 82.4, size: 32 },
    { tournament: "Euro 2024", accuracy: 80.7, size: 51 },
    { tournament: "WC Qualifiers 2025", accuracy: 78.5, size: 218 },
    { tournament: "Nations League 2025", accuracy: 77.1, size: 111 }
  ],
  calibration: [
    { modelConfidenceRange: "90% - 100%", actualAccuracy: 92.4, volume: 53 },
    { modelConfidenceRange: "80% - 90%", actualAccuracy: 84.1, volume: 112 },
    { modelConfidenceRange: "70% - 80%", actualAccuracy: 74.8, volume: 145 },
    { modelConfidenceRange: "50% - 70%", actualAccuracy: 61.2, volume: 102 }
  ]
};
