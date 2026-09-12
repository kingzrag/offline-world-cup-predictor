// ─── Supported Competitions Configuration ───────────────────────────────────────
// Single source of truth for all football competitions supported by the platform.

export type CompetitionStatus = 'SUPPORTED' | 'NO_CURRENT_FIXTURES' | 'API_RESTRICTED' | 'HISTORICAL';
export type CompetitionCategory = 'Domestic' | 'European' | 'International';

export interface CompetitionConfig {
  id: string;
  name: string;
  shortName: string;
  logo: string;
  country: string;
  type: 'League' | 'Cup' | 'International';
  category: CompetitionCategory;
  status: CompetitionStatus;
  statusText?: string;
  season?: string;
}

export const SUPPORTED_COMPETITIONS: CompetitionConfig[] = [
  // ── Domestic Leagues (Primary Current Competitions) ─────────────────────────
  {
    id: 'PL',
    name: 'Premier League',
    shortName: 'EPL',
    logo: '/leagues/premier-league.svg',
    country: 'England',
    type: 'League',
    category: 'Domestic',
    status: 'SUPPORTED',
    season: '2026-27',
  },
  {
    id: 'PD',
    name: 'La Liga',
    shortName: 'La Liga',
    logo: '/leagues/la-liga-seeklogo.png',
    country: 'Spain',
    type: 'League',
    category: 'Domestic',
    status: 'SUPPORTED',
    season: '2026-27',
  },
  {
    id: 'SA',
    name: 'Serie A',
    shortName: 'Serie A',
    logo: '/leagues/serie-a.png',
    country: 'Italy',
    type: 'League',
    category: 'Domestic',
    status: 'SUPPORTED',
    season: '2026-27',
  },
  {
    id: 'BL1',
    name: 'Bundesliga',
    shortName: 'Bundesliga',
    logo: '/leagues/bundesliga.png',
    country: 'Germany',
    type: 'League',
    category: 'Domestic',
    status: 'SUPPORTED',
    season: '2026-27',
  },
  {
    id: 'FL1',
    name: 'Ligue 1',
    shortName: 'Ligue 1',
    logo: '/leagues/premier-league.svg',
    country: 'France',
    type: 'League',
    category: 'Domestic',
    status: 'SUPPORTED',
    season: '2026-27',
  },
  {
    id: 'DED',
    name: 'Eredivisie',
    shortName: 'Eredivisie',
    logo: '/leagues/premier-league.svg',
    country: 'Netherlands',
    type: 'League',
    category: 'Domestic',
    status: 'SUPPORTED',
    season: '2026-27',
  },
  {
    id: 'BSA',
    name: 'Brasileirão Série A',
    shortName: 'Brasileirão',
    logo: '/leagues/premier-league.svg',
    country: 'Brazil',
    type: 'League',
    category: 'Domestic',
    status: 'SUPPORTED',
    season: '2026',
  },
  {
    id: 'MLS',
    name: 'Major League Soccer',
    shortName: 'MLS',
    logo: '/leagues/premier-league.svg',
    country: 'United States',
    type: 'League',
    category: 'Domestic',
    status: 'SUPPORTED',
    season: '2026',
  },

  // ── European Club Competitions ──────────────────────────────────────────────
  {
    id: 'CL',
    name: 'UEFA Champions League',
    shortName: 'UCL',
    logo: '/leagues/champions-league.svg',
    country: 'Europe',
    type: 'Cup',
    category: 'European',
    status: 'SUPPORTED',
    season: '2026-27',
  },
  {
    id: 'EL',
    name: 'UEFA Europa League',
    shortName: 'UEL',
    logo: '/leagues/europa-league.svg',
    country: 'Europe',
    type: 'Cup',
    category: 'European',
    status: 'SUPPORTED',
    season: '2026-27',
  },

  // ── Historical / International Competitions (Hidden from main current sections) ──
  {
    id: 'WC',
    name: 'FIFA World Cup',
    shortName: 'World Cup',
    logo: '/leagues/world-cup.svg',
    country: 'International',
    type: 'International',
    category: 'International',
    status: 'HISTORICAL',
    statusText: 'Historical',
    season: '2026',
  },
  {
    id: 'EC',
    name: 'UEFA Euro',
    shortName: 'UEFA Euro',
    logo: '/leagues/champions-league.svg',
    country: 'Europe',
    type: 'International',
    category: 'International',
    status: 'HISTORICAL',
    statusText: 'Historical',
    season: '2024',
  },
  {
    id: 'CA',
    name: 'Copa América',
    shortName: 'Copa América',
    logo: '/leagues/world-cup.svg',
    country: 'South America',
    type: 'International',
    category: 'International',
    status: 'HISTORICAL',
    statusText: 'Historical',
    season: '2024',
  },
  {
    id: 'UNL',
    name: 'UEFA Nations League',
    shortName: 'Nations League',
    logo: '/leagues/champions-league.svg',
    country: 'Europe',
    type: 'International',
    category: 'International',
    status: 'HISTORICAL',
    statusText: 'Historical',
    season: '2024-25',
  },
  {
    id: 'WCQ',
    name: 'FIFA World Cup Qualifiers',
    shortName: 'WC Qualifiers',
    logo: '/leagues/world-cup.svg',
    country: 'International',
    type: 'International',
    category: 'International',
    status: 'HISTORICAL',
    statusText: 'Historical',
    season: '2024-26',
  },
];

// Helper: Get primary current competitions (Domestic + European, excluding historical tournaments)
export const PRIMARY_COMPETITIONS = SUPPORTED_COMPETITIONS.filter(c => c.status !== 'HISTORICAL');

// Helper: Get domestic leagues
export const DOMESTIC_LEAGUES = PRIMARY_COMPETITIONS.filter(c => c.category === 'Domestic');

// Helper: Get European club competitions
export const EUROPEAN_COMPETITIONS = PRIMARY_COMPETITIONS.filter(c => c.category === 'European');

// Helper: Get historical competitions
export const HISTORICAL_COMPETITIONS = SUPPORTED_COMPETITIONS.filter(c => c.status === 'HISTORICAL');

const ID_ALIASES: Record<string, string> = {
  'UCL': 'CL',
  'UEL': 'EL',
  'EPL': 'PL',
  'LALIGA': 'PD',
  'SERIEA': 'SA',
  'BUNDESLIGA': 'BL1',
  'LIGUE1': 'FL1',
};

// Helper function to get competition by ID
export function getCompetitionById(id: string): CompetitionConfig | undefined {
  if (!id) return undefined;
  const upper = id.toUpperCase();
  const canonicalId = ID_ALIASES[upper] || upper;
  return SUPPORTED_COMPETITIONS.find(comp => comp.id.toUpperCase() === canonicalId);
}

// Helper function to get competition by name
export function getCompetitionByName(name: string): CompetitionConfig | undefined {
  if (!name) return undefined;
  return SUPPORTED_COMPETITIONS.find(comp => 
    comp.name.toLowerCase() === name.toLowerCase() ||
    comp.shortName.toLowerCase() === name.toLowerCase()
  );
}

// Dynamic Competition Filters builder (returns filters for current primary competitions)
export const COMPETITION_FILTERS = [
  { id: 'all', label: 'All Matches', icon: '🏆' },
  { id: 'live', label: 'LIVE', icon: '🔴' },
  { id: 'today', label: 'Today', icon: '📅' },
  { id: 'tomorrow', label: 'Tomorrow', icon: '📆' },
  ...PRIMARY_COMPETITIONS.map(c => ({
    id: c.id,
    label: c.name,
    icon: c.country === 'England' ? '🏴󠁧󠁢󠁥󠁮󠁧󠁿' : c.country === 'Spain' ? '🇪🇸' : c.country === 'Germany' ? '🇩🇪' : c.country === 'Italy' ? '🇮🇹' : c.country === 'France' ? '🇫🇷' : c.country === 'Netherlands' ? '🇳🇱' : c.country === 'Brazil' ? '🇧🇷' : c.country === 'Europe' ? '⭐' : '⚽',
  }))
];
