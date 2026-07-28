// ─── Supported Competitions Configuration ───────────────────────────────────────
// This configuration defines all competitions supported by the OFFLINE platform.
// Adding a new competition only requires adding an entry here.

export interface CompetitionConfig {
  id: string;
  name: string;
  shortName: string;
  logo: string;
  country: string;
  type: 'League' | 'Cup' | 'International';
  season?: string;
}

export const SUPPORTED_COMPETITIONS: CompetitionConfig[] = [
  {
    id: 'PL',
    name: 'Premier League',
    shortName: 'EPL',
    logo: '/leagues/premier-league.svg',
    country: 'England',
    type: 'League',
    season: '2024-25',
  },
  {
    id: 'LL',
    name: 'La Liga',
    shortName: 'LIGA',
    logo: '/leagues/la-liga-seeklogo.png',
    country: 'Spain',
    type: 'League',
    season: '2024-25',
  },
  {
    id: 'BL',
    name: 'Bundesliga',
    shortName: 'BL1',
    logo: '/leagues/bundesliga.png',
    country: 'Germany',
    type: 'League',
    season: '2024-25',
  },
  {
    id: 'SA',
    name: 'Serie A',
    shortName: 'SA',
    logo: '/leagues/serie-a.png',
    country: 'Italy',
    type: 'League',
    season: '2024-25',
  },
  {
    id: 'FL1',
    name: 'Ligue 1',
    shortName: 'L1',
    logo: '/leagues/premier-league.svg',
    country: 'France',
    type: 'League',
    season: '2024-25',
  },
  {
    id: 'CL',
    name: 'UEFA Champions League',
    shortName: 'UCL',
    logo: '/leagues/champions-league.svg',
    country: 'Europe',
    type: 'Cup',
    season: '2024-25',
  },
  {
    id: 'EL',
    name: 'UEFA Europa League',
    shortName: 'UEL',
    logo: '/leagues/europa-league.svg',
    country: 'Europe',
    type: 'Cup',
    season: '2024-25',
  },
  {
    id: 'WC',
    name: 'FIFA World Cup',
    shortName: 'WC',
    logo: '/leagues/world-cup.svg',
    country: 'International',
    type: 'International',
    season: '2026',
  },
  {
    id: 'EC',
    name: 'UEFA Euro',
    shortName: 'EURO',
    logo: '/leagues/champions-league.svg',
    country: 'Europe',
    type: 'International',
    season: '2024',
  },
  {
    id: 'UNL',
    name: 'UEFA Nations League',
    shortName: 'UNL',
    logo: '/leagues/champions-league.svg',
    country: 'Europe',
    type: 'International',
    season: '2024-25',
  },
  {
    id: 'CA',
    name: 'Copa América',
    shortName: 'CA',
    logo: '/leagues/world-cup.svg',
    country: 'South America',
    type: 'International',
    season: '2024',
  },
  {
    id: 'WCQ',
    name: 'FIFA World Cup Qualifiers',
    shortName: 'WCQ',
    logo: '/leagues/world-cup.svg',
    country: 'International',
    type: 'International',
    season: '2024-26',
  },
];

// Helper function to get competition by ID
export function getCompetitionById(id: string): CompetitionConfig | undefined {
  return SUPPORTED_COMPETITIONS.find(comp => comp.id === id);
}

// Helper function to get competition by name
export function getCompetitionByName(name: string): CompetitionConfig | undefined {
  return SUPPORTED_COMPETITIONS.find(comp => 
    comp.name.toLowerCase() === name.toLowerCase() ||
    comp.shortName.toLowerCase() === name.toLowerCase()
  );
}

// Competition filter options for UI
export const COMPETITION_FILTERS = [
  { id: 'all', label: 'All Matches', icon: '🏆' },
  { id: 'live', label: 'LIVE', icon: '🔴' },
  { id: 'today', label: 'Today', icon: '📅' },
  { id: 'tomorrow', label: 'Tomorrow', icon: '📆' },
  { id: 'PL', label: 'Premier League', icon: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
  { id: 'LL', label: 'La Liga', icon: '🇪🇸' },
  { id: 'BL', label: 'Bundesliga', icon: '🇩🇪' },
  { id: 'SA', label: 'Serie A', icon: '🇮🇹' },
  { id: 'FL1', label: 'Ligue 1', icon: '🇫🇷' },
  { id: 'CL', label: 'Champions League', icon: '⭐' },
  { id: 'EL', label: 'Europa League', icon: '🌟' },
  { id: 'WC', label: 'World Cup', icon: '🌍' },
  { id: 'EC', label: 'UEFA Euro', icon: '🇪🇺' },
  { id: 'UNL', label: 'Nations League', icon: '🏛️' },
  { id: 'CA', label: 'Copa América', icon: '🌎' },
  { id: 'WCQ', label: 'WC Qualifiers', icon: '✈️' },
];
