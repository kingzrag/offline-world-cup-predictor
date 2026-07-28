// ─── Supported Competitions Configuration ───────────────────────────────────────
// Single source of truth for all football competitions supported by the platform.
// Adding a new competition requires only adding an entry here.

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
  // Domestic Leagues
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
    id: 'PD',
    name: 'La Liga',
    shortName: 'La Liga',
    logo: '/leagues/la-liga-seeklogo.png',
    country: 'Spain',
    type: 'League',
    season: '2024-25',
  },
  {
    id: 'SA',
    name: 'Serie A',
    shortName: 'Serie A',
    logo: '/leagues/serie-a.png',
    country: 'Italy',
    type: 'League',
    season: '2024-25',
  },
  {
    id: 'BL1',
    name: 'Bundesliga',
    shortName: 'Bundesliga',
    logo: '/leagues/bundesliga.png',
    country: 'Germany',
    type: 'League',
    season: '2024-25',
  },
  {
    id: 'FL1',
    name: 'Ligue 1',
    shortName: 'Ligue 1',
    logo: '/leagues/premier-league.svg',
    country: 'France',
    type: 'League',
    season: '2024-25',
  },
  {
    id: 'MLS',
    name: 'Major League Soccer',
    shortName: 'MLS',
    logo: '/leagues/premier-league.svg',
    country: 'United States',
    type: 'League',
    season: '2024',
  },
  {
    id: 'BSA',
    name: 'Brasileirão Série A',
    shortName: 'Brasileirão',
    logo: '/leagues/premier-league.svg',
    country: 'Brazil',
    type: 'League',
    season: '2024',
  },
  {
    id: 'DED',
    name: 'Eredivisie',
    shortName: 'Eredivisie',
    logo: '/leagues/premier-league.svg',
    country: 'Netherlands',
    type: 'League',
    season: '2024-25',
  },

  // European Competitions
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
    id: 'ECL',
    name: 'UEFA Conference League',
    shortName: 'UECL',
    logo: '/leagues/europa-league.svg',
    country: 'Europe',
    type: 'Cup',
    season: '2024-25',
  },

  // Domestic Cups
  {
    id: 'FAC',
    name: 'FA Cup',
    shortName: 'FA Cup',
    logo: '/leagues/premier-league.svg',
    country: 'England',
    type: 'Cup',
    season: '2024-25',
  },
  {
    id: 'CDR',
    name: 'Copa del Rey',
    shortName: 'Copa del Rey',
    logo: '/leagues/la-liga-seeklogo.png',
    country: 'Spain',
    type: 'Cup',
    season: '2024-25',
  },
  {
    id: 'DFB',
    name: 'DFB-Pokal',
    shortName: 'DFB Pokal',
    logo: '/leagues/bundesliga.png',
    country: 'Germany',
    type: 'Cup',
    season: '2024-25',
  },
  {
    id: 'CIT',
    name: 'Coppa Italia',
    shortName: 'Coppa Italia',
    logo: '/leagues/serie-a.png',
    country: 'Italy',
    type: 'Cup',
    season: '2024-25',
  },

  // International Competitions
  {
    id: 'WC',
    name: 'FIFA World Cup',
    shortName: 'World Cup',
    logo: '/leagues/world-cup.svg',
    country: 'International',
    type: 'International',
    season: '2026',
  },
  {
    id: 'EC',
    name: 'UEFA Euro',
    shortName: 'UEFA Euro',
    logo: '/leagues/champions-league.svg',
    country: 'Europe',
    type: 'International',
    season: '2024',
  },
  {
    id: 'CA',
    name: 'Copa América',
    shortName: 'Copa América',
    logo: '/leagues/world-cup.svg',
    country: 'South America',
    type: 'International',
    season: '2024',
  },
  {
    id: 'UNL',
    name: 'UEFA Nations League',
    shortName: 'Nations League',
    logo: '/leagues/champions-league.svg',
    country: 'Europe',
    type: 'International',
    season: '2024-25',
  },
  {
    id: 'WCQ',
    name: 'FIFA World Cup Qualifiers',
    shortName: 'WC Qualifiers',
    logo: '/leagues/world-cup.svg',
    country: 'International',
    type: 'International',
    season: '2024-26',
  },
];

// Helper function to get competition by ID
export function getCompetitionById(id: string): CompetitionConfig | undefined {
  if (!id) return undefined;
  return SUPPORTED_COMPETITIONS.find(comp => comp.id.toUpperCase() === id.toUpperCase());
}

// Helper function to get competition by name
export function getCompetitionByName(name: string): CompetitionConfig | undefined {
  if (!name) return undefined;
  return SUPPORTED_COMPETITIONS.find(comp => 
    comp.name.toLowerCase() === name.toLowerCase() ||
    comp.shortName.toLowerCase() === name.toLowerCase()
  );
}

// Dynamic Competition Filters builder (returns filters for active competitions only)
export const COMPETITION_FILTERS = [
  { id: 'all', label: 'All Matches', icon: '🏆' },
  { id: 'live', label: 'LIVE', icon: '🔴' },
  { id: 'today', label: 'Today', icon: '📅' },
  { id: 'tomorrow', label: 'Tomorrow', icon: '📆' },
  ...SUPPORTED_COMPETITIONS.map(c => ({
    id: c.id,
    label: c.name,
    icon: c.country === 'England' ? '🏴󠁧󠁢󠁥󠁮󠁧󠁿' : c.country === 'Spain' ? '🇪🇸' : c.country === 'Germany' ? '🇩🇪' : c.country === 'Italy' ? '🇮🇹' : c.country === 'France' ? '🇫🇷' : c.country === 'Europe' ? '⭐' : '🌍',
  }))
];
