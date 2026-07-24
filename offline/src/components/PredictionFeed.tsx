import React, { useState } from 'react';

// ─── Types for backend data structure ───────────────────────────────────────────
interface FavoriteClub {
  id: string;
  name: string;
  logo?: string;
}

interface Competition {
  id: string;
  name: string;
  logo?: string;
  country?: string;
}

interface Country {
  code: string;
  name: string;
  flag?: string;
}

interface SavedFilter {
  id: string;
  name: string;
  count?: number;
}

interface FilterItem {
  id: string;
  label: string;
  count?: number;
}

interface MatchData {
  id: string;
  competition: string;
  competitionLogo?: string;
  homeTeam: string;
  awayTeam: string;
  kickoffTime: string;
  prediction: string;
  confidence: string;
  probability: number;
  expectedGoals: number;
  modelSignals: string[];
  simulationCount: number;
  status: string;
}

interface Statistics {
  todayMatches: number;
  liveMatches: number;
  upcoming: number;
  completed: number;
  highestConfidence: number;
  averageConfidence: number;
  lastSync: string;
}

// ─── Skeleton Loading Components ───────────────────────────────────────────────
const Skeleton = ({ className }: { className?: string }) => (
  <div className={`animate-pulse bg-[#E8E6E1] rounded ${className}`} />
);

const SidebarSkeleton = () => (
  <div className="space-y-6">
    {[1, 2, 3, 4].map((i) => (
      <div key={i} className="space-y-3">
        <Skeleton className="h-4 w-24" />
        <div className="space-y-2 pl-4">
          {[1, 2, 3].map((j) => (
            <Skeleton key={j} className="h-3 w-full" />
          ))}
        </div>
      </div>
    ))}
  </div>
);

const FeaturedMatchSkeleton = () => (
  <div className="border border-[#D4D4D4] rounded-lg p-8 space-y-6">
    <Skeleton className="h-6 w-32" />
    <div className="space-y-4">
      <Skeleton className="h-12 w-1/2" />
      <Skeleton className="h-8 w-16" />
      <Skeleton className="h-12 w-1/2" />
    </div>
    <div className="grid grid-cols-2 gap-4">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <Skeleton key={i} className="h-4 w-full" />
      ))}
    </div>
    <Skeleton className="h-10 w-40" />
  </div>
);

const MatchCardSkeleton = () => (
  <div className="border border-[#D4D4D4] rounded-lg p-6 space-y-4">
    <Skeleton className="h-4 w-24" />
    <div className="space-y-3">
      <Skeleton className="h-8 w-3/4" />
      <Skeleton className="h-6 w-12" />
      <Skeleton className="h-8 w-3/4" />
    </div>
    <div className="space-y-2">
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-4 w-1/3" />
    </div>
    <Skeleton className="h-8 w-32" />
  </div>
);

const StatisticsSkeleton = () => (
  <div className="space-y-4">
    {[1, 2, 3, 4, 5, 6, 7].map((i) => (
      <div key={i} className="flex justify-between items-center">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-16" />
      </div>
    ))}
  </div>
);

// ─── Empty State Components ───────────────────────────────────────────────────
const EmptyState = ({ message }: { message: string }) => (
  <div className="flex flex-col items-center justify-center py-20 px-8 border border-dashed border-[#D4D4D4] rounded-lg">
    <div className="text-[#4A4A4A] text-sm font-serif italic mb-4">No predictions available.</div>
    <div className="text-[#6B6B6B] text-xs">{message}</div>
  </div>
);

const LoadingState = () => (
  <div className="flex flex-col items-center justify-center py-20">
    <div className="w-8 h-8 border-2 border-[#8B7355] border-t-transparent rounded-full animate-spin mb-4" />
    <div className="text-[#6B6B6B] text-xs font-mono uppercase tracking-wider">Loading predictions...</div>
  </div>
);

const APIUnavailableState = () => (
  <div className="flex flex-col items-center justify-center py-20 px-8 border border-dashed border-[#D4D4D4] rounded-lg">
    <div className="text-[#4A4A4A] text-sm font-serif italic mb-4">Prediction service temporarily unavailable.</div>
    <div className="text-[#6B6B6B] text-xs">Please check your connection and try again.</div>
  </div>
);

// ─── Left Sidebar Component ───────────────────────────────────────────────────
const LeftSidebar = ({
  favoriteClubs,
  favoriteCompetitions,
  countries,
  savedFilters,
  isLoading
}: {
  favoriteClubs?: FavoriteClub[];
  favoriteCompetitions?: Competition[];
  countries?: Country[];
  savedFilters?: SavedFilter[];
  isLoading?: boolean;
}) => {
  if (isLoading) {
    return (
      <aside className="w-64 border-r border-[#D4D4D4] p-6 space-y-8">
        <SidebarSkeleton />
      </aside>
    );
  }

  return (
    <aside className="w-64 border-r border-[#D4D4D4] p-6 space-y-8">
      {/* Favorites */}
      <div>
        <h3 className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] mb-4 pb-2 border-b border-[#D4D4D4]">
          Favorites
        </h3>
        <div className="space-y-2">
          {favoriteClubs && favoriteClubs.length > 0 ? (
            favoriteClubs.map((club) => (
              <div key={club.id} className="flex items-center gap-3 text-sm text-[#1C1B17] font-serif">
                {club.logo && <span className="text-lg">{club.logo}</span>}
                <span>{club.name}</span>
              </div>
            ))
          ) : (
            <div className="text-xs text-[#6B6B6B] italic">[Favorite Club]</div>
          )}
        </div>
      </div>

      {/* Favorite Competitions */}
      <div>
        <h3 className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] mb-4 pb-2 border-b border-[#D4D4D4]">
          Favorite Competitions
        </h3>
        <div className="space-y-2">
          {favoriteCompetitions && favoriteCompetitions.length > 0 ? (
            favoriteCompetitions.map((comp) => (
              <div key={comp.id} className="flex items-center gap-3 text-sm text-[#1C1B17] font-serif">
                {comp.logo && <span className="text-lg">{comp.logo}</span>}
                <span>{comp.name}</span>
              </div>
            ))
          ) : (
            <div className="text-xs text-[#6B6B6B] italic">[Competition]</div>
          )}
        </div>
      </div>

      {/* Countries */}
      <div>
        <h3 className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] mb-4 pb-2 border-b border-[#D4D4D4]">
          Countries
        </h3>
        <div className="space-y-2">
          {countries && countries.length > 0 ? (
            countries.map((country) => (
              <div key={country.code} className="flex items-center gap-3 text-sm text-[#1C1B17] font-serif">
                {country.flag && <span className="text-lg">{country.flag}</span>}
                <span>{country.name}</span>
              </div>
            ))
          ) : (
            <div className="text-xs text-[#6B6B6B] italic">[Country]</div>
          )}
        </div>
      </div>

      {/* Saved Filters */}
      <div>
        <h3 className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] mb-4 pb-2 border-b border-[#D4D4D4]">
          Saved Filters
        </h3>
        <div className="space-y-2">
          {savedFilters && savedFilters.length > 0 ? (
            savedFilters.map((filter) => (
              <div key={filter.id} className="flex items-center justify-between text-sm text-[#1C1B17] font-serif">
                <span>{filter.name}</span>
                {filter.count !== undefined && (
                  <span className="text-xs text-[#6B6B6B] font-mono">({filter.count})</span>
                )}
              </div>
            ))
          ) : (
            <div className="text-xs text-[#6B6B6B] italic">[Saved Filter]</div>
          )}
        </div>
      </div>
    </aside>
  );
};

// ─── Filter Bar Component ───────────────────────────────────────────────────
const FilterBar = ({
  filters,
  activeFilter,
  onFilterChange,
  isLoading
}: {
  filters: FilterItem[];
  activeFilter: string;
  onFilterChange: (filterId: string) => void;
  isLoading?: boolean;
}) => {
  if (isLoading) {
    return (
      <div className="flex gap-3 pb-6 border-b border-[#D4D4D4]">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <Skeleton key={i} className="h-10 w-24 rounded" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex gap-3 pb-6 border-b border-[#D4D4D4] overflow-x-auto">
      {filters.map((filter) => (
        <button
          key={filter.id}
          onClick={() => onFilterChange(filter.id)}
          className={`px-4 py-2 text-xs font-mono uppercase tracking-wider rounded transition-all duration-200 whitespace-nowrap ${
            activeFilter === filter.id
              ? 'bg-[#1C1B17] text-[#F7F4EE]'
              : 'bg-transparent text-[#4A4A4A] hover:bg-[#E8E6E1]'
          }`}
        >
          {filter.label}
          {filter.count !== undefined && ` (${filter.count})`}
        </button>
      ))}
    </div>
  );
};

// ─── Featured Match Card Component ───────────────────────────────────────────
const FeaturedMatchCard = ({ match, isLoading }: { match?: MatchData; isLoading?: boolean }) => {
  if (isLoading) {
    return <FeaturedMatchSkeleton />;
  }

  if (!match) {
    return (
      <div className="border border-[#D4D4D4] rounded-lg p-8 space-y-6">
        <div className="text-xs text-[#6B6B6B] font-mono uppercase tracking-wider">[Competition]</div>
        <div className="space-y-4">
          <div className="text-2xl font-serif text-[#1C1B17]">[Home Team]</div>
          <div className="text-sm text-[#4A4A4A] font-mono uppercase">vs</div>
          <div className="text-2xl font-serif text-[#1C1B17]">[Away Team]</div>
        </div>
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Kickoff</div>
            <div className="text-[#1C1B17] font-serif">[Kickoff Time]</div>
          </div>
          <div>
            <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Status</div>
            <div className="text-[#1C1B17] font-serif">[Match Status]</div>
          </div>
          <div>
            <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Prediction</div>
            <div className="text-[#1C1B17] font-serif">[Prediction]</div>
          </div>
          <div>
            <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Confidence</div>
            <div className="text-[#8B7355] font-serif">[Confidence]</div>
          </div>
          <div>
            <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Probability</div>
            <div className="text-[#1C1B17] font-serif">[Probability]</div>
          </div>
          <div>
            <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Expected Goals</div>
            <div className="text-[#1C1B17] font-serif">[Expected Goals]</div>
          </div>
        </div>
        <div className="text-xs text-[#6B6B6B] font-mono uppercase tracking-wider">
          [Model Signals] • [Simulation Count] simulations
        </div>
        <button className="px-6 py-3 bg-[#1C1B17] text-[#F7F4EE] text-xs font-mono uppercase tracking-wider rounded hover:bg-[#4A4A4A] transition-colors">
          View Full Analysis →
        </button>
      </div>
    );
  }

  return (
    <div className="border border-[#D4D4D4] rounded-lg p-8 space-y-6">
      <div className="text-xs text-[#6B6B6B] font-mono uppercase tracking-wider">{match.competition}</div>
      <div className="space-y-4">
        <div className="text-2xl font-serif text-[#1C1B17]">{match.homeTeam}</div>
        <div className="text-sm text-[#4A4A4A] font-mono uppercase">vs</div>
        <div className="text-2xl font-serif text-[#1C1B17]">{match.awayTeam}</div>
      </div>
      <div className="grid grid-cols-2 gap-4 text-xs">
        <div>
          <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Kickoff</div>
          <div className="text-[#1C1B17] font-serif">{match.kickoffTime}</div>
        </div>
        <div>
          <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Status</div>
          <div className="text-[#1C1B17] font-serif">{match.status}</div>
        </div>
        <div>
          <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Prediction</div>
          <div className="text-[#1C1B17] font-serif">{match.prediction}</div>
        </div>
        <div>
          <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Confidence</div>
          <div className="text-[#8B7355] font-serif">{match.confidence}</div>
        </div>
        <div>
          <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Probability</div>
          <div className="text-[#1C1B17] font-serif">{match.probability}%</div>
        </div>
        <div>
          <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Expected Goals</div>
          <div className="text-[#1C1B17] font-serif">{match.expectedGoals}</div>
        </div>
      </div>
      <div className="text-xs text-[#6B6B6B] font-mono uppercase tracking-wider">
        {match.modelSignals.join(' • ')} • {match.simulationCount.toLocaleString()} simulations
      </div>
      <button className="px-6 py-3 bg-[#1C1B17] text-[#F7F4EE] text-xs font-mono uppercase tracking-wider rounded hover:bg-[#4A4A4A] transition-colors">
        View Full Analysis →
      </button>
    </div>
  );
};

// ─── Match Card Component ───────────────────────────────────────────────────
const MatchCard = ({ match, isLoading }: { match?: MatchData; isLoading?: boolean }) => {
  if (isLoading) {
    return <MatchCardSkeleton />;
  }

  if (!match) {
    return (
      <div className="border border-[#D4D4D4] rounded-lg p-6 space-y-4">
        <div className="text-xs text-[#6B6B6B] font-mono uppercase tracking-wider">[League]</div>
        <div className="space-y-3">
          <div className="text-lg font-serif text-[#1C1B17]">[Home Team]</div>
          <div className="text-xs text-[#4A4A4A] font-mono uppercase">vs</div>
          <div className="text-lg font-serif text-[#1C1B17]">[Away Team]</div>
        </div>
        <div className="space-y-2 text-xs">
          <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Prediction</div>
          <div className="text-[#1C1B17] font-serif">[Prediction]</div>
          <div className="text-[#8B7355] font-serif">[Confidence]</div>
          <div className="text-[#1C1B17] font-serif">[Probability]%</div>
        </div>
        <div className="text-xs text-[#6B6B6B] font-mono uppercase tracking-wider">
          [Expected Goals] • [Status]
        </div>
        <button className="px-4 py-2 bg-transparent border border-[#D4D4D4] text-[#1C1B17] text-xs font-mono uppercase tracking-wider rounded hover:bg-[#E8E6E1] transition-colors">
          View Analysis →
        </button>
      </div>
    );
  }

  return (
    <div className="border border-[#D4D4D4] rounded-lg p-6 space-y-4">
      <div className="text-xs text-[#6B6B6B] font-mono uppercase tracking-wider">{match.competition}</div>
      <div className="space-y-3">
        <div className="text-lg font-serif text-[#1C1B17]">{match.homeTeam}</div>
        <div className="text-xs text-[#4A4A4A] font-mono uppercase">vs</div>
        <div className="text-lg font-serif text-[#1C1B17]">{match.awayTeam}</div>
      </div>
      <div className="space-y-2 text-xs">
        <div className="text-[#6B6B6B] font-mono uppercase tracking-wider">Prediction</div>
        <div className="text-[#1C1B17] font-serif">{match.prediction}</div>
        <div className="text-[#8B7355] font-serif">{match.confidence}</div>
        <div className="text-[#1C1B17] font-serif">{match.probability}%</div>
      </div>
      <div className="text-xs text-[#6B6B6B] font-mono uppercase tracking-wider">
        {match.expectedGoals} xG • {match.status}
      </div>
      <button className="px-4 py-2 bg-transparent border border-[#D4D4D4] text-[#1C1B17] text-xs font-mono uppercase tracking-wider rounded hover:bg-[#E8E6E1] transition-colors">
        View Analysis →
      </button>
    </div>
  );
};

// ─── Right Information Panel Component ───────────────────────────────────────
const RightInfoPanel = ({ statistics, isLoading }: { statistics?: Statistics; isLoading?: boolean }) => {
  if (isLoading) {
    return (
      <aside className="w-64 border-l border-[#D4D4D4] p-6 space-y-8">
        <StatisticsSkeleton />
      </aside>
    );
  }

  if (!statistics) {
    return (
      <aside className="w-64 border-l border-[#D4D4D4] p-6 space-y-8">
        <div className="space-y-4">
          <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
            Today's Matches
          </div>
          <div className="text-2xl font-serif text-[#1C1B17]">[ ]</div>
        </div>
        <div className="space-y-4">
          <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
            Live Matches
          </div>
          <div className="text-2xl font-serif text-[#1C1B17]">[ ]</div>
        </div>
        <div className="space-y-4">
          <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
            Upcoming
          </div>
          <div className="text-2xl font-serif text-[#1C1B17]">[ ]</div>
        </div>
        <div className="space-y-4">
          <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
            Completed
          </div>
          <div className="text-2xl font-serif text-[#1C1B17]">[ ]</div>
        </div>
        <div className="space-y-4">
          <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
            Highest Confidence
          </div>
          <div className="text-2xl font-serif text-[#8B7355]">[ ]%</div>
        </div>
        <div className="space-y-4">
          <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
            Average Model Confidence
          </div>
          <div className="text-2xl font-serif text-[#1C1B17]">[ ]%</div>
        </div>
        <div className="space-y-4">
          <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
            Last Backend Sync
          </div>
          <div className="text-xs text-[#6B6B6B] font-mono">[Updated Time]</div>
        </div>
      </aside>
    );
  }

  return (
    <aside className="w-64 border-l border-[#D4D4D4] p-6 space-y-8">
      <div className="space-y-4">
        <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
          Today's Matches
        </div>
        <div className="text-2xl font-serif text-[#1C1B17]">{statistics.todayMatches}</div>
      </div>
      <div className="space-y-4">
        <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
          Live Matches
        </div>
        <div className="text-2xl font-serif text-[#8B7355]">{statistics.liveMatches}</div>
      </div>
      <div className="space-y-4">
        <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
          Upcoming
        </div>
        <div className="text-2xl font-serif text-[#1C1B17]">{statistics.upcoming}</div>
      </div>
      <div className="space-y-4">
        <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
          Completed
        </div>
        <div className="text-2xl font-serif text-[#1C1B17]">{statistics.completed}</div>
      </div>
      <div className="space-y-4">
        <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
          Highest Confidence
        </div>
        <div className="text-2xl font-serif text-[#8B7355]">{statistics.highestConfidence}%</div>
      </div>
      <div className="space-y-4">
        <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
          Average Model Confidence
        </div>
        <div className="text-2xl font-serif text-[#1C1B17]">{statistics.averageConfidence}%</div>
      </div>
      <div className="space-y-4">
        <div className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A] pb-2 border-b border-[#D4D4D4]">
          Last Backend Sync
        </div>
        <div className="text-xs text-[#6B6B6B] font-mono">{statistics.lastSync}</div>
      </div>
    </aside>
  );
};

// ─── Main Prediction Feed Component ───────────────────────────────────────────
const PredictionFeed = () => {
  const [activeFilter, setActiveFilter] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [apiUnavailable, setApiUnavailable] = useState(false);

  // Placeholder filter items - will be populated from backend
  const filters: FilterItem[] = [
    { id: 'all', label: 'All' },
    { id: 'live', label: 'Live', count: 0 },
    { id: 'today', label: 'Today', count: 0 },
    { id: 'tomorrow', label: 'Tomorrow', count: 0 },
    { id: 'this-week', label: 'This Week', count: 0 },
    { id: 'high-confidence', label: 'High Confidence', count: 0 },
    { id: 'favorites', label: 'Favorites', count: 0 },
    { id: 'bookmarks', label: 'Bookmarks', count: 0 },
  ];

  // Simulate loading state
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen bg-[#F7F4EE]">
      {/* Three-column layout */}
      <div className="flex">
        {/* Left Sidebar */}
        <LeftSidebar isLoading={isLoading} />

        {/* Main Content */}
        <main className="flex-1 p-8 space-y-8">
          {/* Editorial Title */}
          <div className="space-y-2">
            <h1 className="text-4xl font-serif text-[#1C1B17] tracking-tight">Prediction Feed</h1>
            <p className="text-sm text-[#4A4A4A] font-serif italic">
              Predictions updated continuously from live backend data.
            </p>
          </div>

          {/* Metadata Row */}
          <div className="flex gap-8 text-xs font-mono text-[#6B6B6B] uppercase tracking-wider">
            <div>
              <span className="text-[#4A4A4A]">Total Matches: </span>
              <span className="text-[#1C1B17]">[Total Matches]</span>
            </div>
            <div>
              <span className="text-[#4A4A4A]">Last Updated: </span>
              <span className="text-[#1C1B17]">[Last Updated]</span>
            </div>
            <div>
              <span className="text-[#4A4A4A]">Predictions Generated: </span>
              <span className="text-[#1C1B17]">[Predictions Generated]</span>
            </div>
          </div>

          {/* Filter Bar */}
          <FilterBar
            filters={filters}
            activeFilter={activeFilter}
            onFilterChange={setActiveFilter}
            isLoading={isLoading}
          />

          {/* Content based on state */}
          {isLoading ? (
            <LoadingState />
          ) : apiUnavailable ? (
            <APIUnavailableState />
          ) : (
            <>
              {/* Featured Match */}
              <div className="space-y-4">
                <h2 className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A]">
                  Featured Prediction
                </h2>
                <FeaturedMatchCard isLoading={isLoading} />
              </div>

              {/* Match Grid */}
              <div className="space-y-4">
                <h2 className="text-xs font-mono uppercase tracking-widest text-[#4A4A4A]">
                  All Predictions
                </h2>
                <div className="grid grid-cols-2 gap-6">
                  {[1, 2, 3, 4, 5, 6].map((i) => (
                    <MatchCard key={i} isLoading={isLoading} />
                  ))}
                </div>
              </div>
            </>
          )}
        </main>

        {/* Right Information Panel */}
        <RightInfoPanel isLoading={isLoading} />
      </div>
    </div>
  );
};

export default PredictionFeed;
