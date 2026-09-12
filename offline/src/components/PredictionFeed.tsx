import React, { useState, useEffect, useMemo } from 'react';
import { Heart, Star, Clock, TrendingUp, Activity, Zap } from 'lucide-react';
import { MatchPrediction } from '../types';
import { COMPETITION_FILTERS, PRIMARY_COMPETITIONS, getCompetitionById } from '../config/competitions';
import {
  formatSmartKickoffLocal,
  isKickoffToday,
  isKickoffTomorrow,
} from '../dateTimeUtils';
import { loadFixturesProgressive } from '../api';
import { TeamBadge } from '../teamAssetUtils';

// ─── Props ────────────────────────────────────────────────────────────────────
interface PredictionFeedProps {
  matches?: MatchPrediction[];
  isLoading?: boolean;
  favoriteMatchIds?: string[];
  onToggleFavorite?: (matchId: string) => void;
  onViewAnalysis?: (match: MatchPrediction) => void;
  initialFilter?: string;
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────
const Skeleton = ({ className }: { className?: string }) => (
  <div className={`animate-pulse bg-[#E8E6E1] rounded ${className}`} />
);

// ─── Confidence badge ─────────────────────────────────────────────────────────
const ConfidenceBadge = ({ confidence }: { confidence: 'High' | 'Medium' | 'Low' }) => {
  const styles = {
    High:   'bg-[#3a5c2d]/12 text-[#3a5c2d] border border-[#3a5c2d]/20',
    Medium: 'bg-[#8B7355]/12 text-[#8B7355] border border-[#8B7355]/20',
    Low:    'bg-[#9B9B9B]/12 text-[#6B6B6B] border border-[#9B9B9B]/20',
  };
  return (
    <span className={`text-[9px] font-mono uppercase tracking-[0.18em] px-1.5 py-0.5 rounded-sm ${styles[confidence]}`}>
      {confidence}
    </span>
  );
};

// ─── Live pill ────────────────────────────────────────────────────────────────
const LivePill = () => (
  <span className="inline-flex items-center gap-1 text-[9px] font-mono uppercase tracking-[0.18em] px-1.5 py-0.5 rounded-sm bg-red-500/10 text-red-500 border border-red-500/20">
    <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
    Live
  </span>
);

// ─── Probability bar ──────────────────────────────────────────────────────────
const ProbBar = ({ probA, probD, probB }: { probA: number; probD: number; probB: number }) => {
  const total = (probA || 0) + (probD || 0) + (probB || 0) || 100;
  const a = Math.round((probA / total) * 100);
  const d = Math.round((probD / total) * 100);
  const b = 100 - a - d;
  return (
    <div className="flex h-1 rounded-full overflow-hidden gap-px">
      <div className="bg-[#3a5c2d]" style={{ width: `${a}%` }} />
      <div className="bg-[#8B7355]" style={{ width: `${d}%` }} />
      <div className="bg-[#B44C2A]" style={{ width: `${b}%` }} />
    </div>
  );
};

// ─── Match Card ───────────────────────────────────────────────────────────────
const MatchCard = ({
  match,
  isFavorite,
  onToggleFavorite,
  onViewAnalysis,
}: {
  match: MatchPrediction;
  isFavorite: boolean;
  onToggleFavorite: (id: string) => void;
  onViewAnalysis: (m: MatchPrediction) => void;
}) => {
  return (
    <div className="bg-[#F7F4EE] border border-[#D4D4D4] rounded p-4 hover:border-[#1C1B17] transition-all duration-200 flex flex-col justify-between group">
      {/* Top bar */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-1.5 overflow-hidden">
          <span className="text-[9px] font-mono uppercase tracking-[0.18em] text-[#6B6B6B] truncate">
            {match.competition || match.stage}
          </span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {match.status === 'LIVE' ? (
            <LivePill />
          ) : (
            <ConfidenceBadge confidence={match.confidence} />
          )}
          <button
            onClick={e => { e.stopPropagation(); onToggleFavorite(match.id); }}
            className="text-[#9B9B9B] hover:text-[#1C1B17] transition-colors p-0.5"
            aria-label="Bookmark"
          >
            <Heart className={`w-3.5 h-3.5 ${isFavorite ? 'fill-[#1C1B17] text-[#1C1B17]' : ''}`} />
          </button>
        </div>
      </div>

      {/* Teams & Scores */}
      <div className="space-y-2.5 mb-4">
        <div className="flex items-center justify-between font-serif text-base text-[#1C1B17]">
          <div className="flex items-center gap-2 min-w-0 pr-2">
            <TeamBadge name={match.teamA} crestUrl={match.teamACrest} size="sm" />
            <span className="truncate">{match.teamA}</span>
          </div>
          {match.liveScore && match.status !== 'UPCOMING' && (
            <span className="font-mono text-sm font-bold ml-2 shrink-0">{match.liveScore.home}</span>
          )}
        </div>
        <div className="flex items-center justify-between font-serif text-base text-[#1C1B17]">
          <div className="flex items-center gap-2 min-w-0 pr-2">
            <TeamBadge name={match.teamB} crestUrl={match.teamBCrest} size="sm" />
            <span className="truncate">{match.teamB}</span>
          </div>
          {match.liveScore && match.status !== 'UPCOMING' && (
            <span className="font-mono text-sm font-bold ml-2 shrink-0">{match.liveScore.away}</span>
          )}
        </div>
      </div>

      {/* Probabilities */}
      <div className="space-y-1.5 mb-4">
        <ProbBar probA={match.probA} probD={match.probD} probB={match.probB} />
        <div className="flex justify-between text-[8.5px] font-mono text-[#6B6B6B] px-0.5">
          <span>{match.teamACode} {match.probA}%</span>
          <span>Draw {match.probD}%</span>
          <span>{match.teamBCode} {match.probB}%</span>
        </div>
      </div>

      {/* Footer */}
      <div className="pt-3 border-t border-[#EFEFEF] flex items-center justify-between text-[9px] font-mono text-[#6B6B6B]">
        <span className="truncate">
          {match.status === 'LIVE'
            ? `🔴 ${match.minute ? match.minute + "'" : 'Live'}`
            : formatSmartKickoffLocal(match.kickoffTime) || match.date}
        </span>
        <button
          onClick={() => onViewAnalysis(match)}
          className="text-[#1C1B17] font-bold tracking-wider hover:underline uppercase shrink-0 ml-2"
        >
          Analysis →
        </button>
      </div>
    </div>
  );
};

// ─── Sidebar ──────────────────────────────────────────────────────────────────
const Sidebar = ({
  matches,
  activeFilter,
  onFilterChange,
  favoriteCount,
  isLoading,
}: {
  matches: MatchPrediction[];
  activeFilter: string;
  onFilterChange: (id: string) => void;
  favoriteCount: number;
  isLoading: boolean;
}) => {
  const competitionCounts = useMemo(() => {
    const counts: Record<string, { total: number; live: number }> = {};
    for (const m of matches) {
      const cid = (m.competitionId ?? '').toUpperCase();
      if (!cid) continue;
      if (!counts[cid]) counts[cid] = { total: 0, live: 0 };
      counts[cid].total++;
      if (m.status === 'LIVE') counts[cid].live++;
    }
    return counts;
  }, [matches]);

  if (isLoading) {
    return (
      <aside className="hidden lg:block w-56 shrink-0 border-r border-[#D4D4D4] pt-8 px-5 space-y-6 min-h-screen">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-3 w-20" />
            {[1, 2, 3].map(j => <Skeleton key={j} className="h-3 w-full mt-1.5" />)}
          </div>
        ))}
      </aside>
    );
  }

  return (
    <aside className="hidden lg:block w-56 shrink-0 border-r border-[#D4D4D4] pt-8 px-5 space-y-6 min-h-screen sticky top-0 overflow-y-auto max-h-screen">
      {/* Quick filters */}
      <div>
        <h3 className="text-[8.5px] font-mono uppercase tracking-[0.28em] text-[#9B9B9B] mb-3">Quick Filters</h3>
        <div className="space-y-0.5">
          {[
            { id: 'all',       label: 'All Matches',      icon: <Activity className="w-2.5 h-2.5" /> },
            { id: 'live',      label: 'Live',             icon: <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse inline-block" /> },
            { id: 'today',     label: 'Today',            icon: <Clock className="w-2.5 h-2.5" /> },
            { id: 'tomorrow',  label: 'Tomorrow',         icon: <TrendingUp className="w-2.5 h-2.5" /> },
            { id: 'favorites', label: `Bookmarks (${favoriteCount})`, icon: <Heart className="w-2.5 h-2.5" /> },
          ].map(f => (
            <button
              key={f.id}
              onClick={() => onFilterChange(f.id)}
              className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded text-[9.5px] font-mono text-left transition-all duration-150
                ${activeFilter === f.id
                  ? 'bg-[#1C1B17] text-[#F7F4EE]'
                  : 'text-[#4A4A4A] hover:bg-[#F0EDE6]'
                }`}
            >
              <span className={activeFilter === f.id ? 'text-[#F7F4EE]' : 'text-[#8B8B8B]'}>{f.icon}</span>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Competitions */}
      <div>
        <h3 className="text-[8.5px] font-mono uppercase tracking-[0.28em] text-[#9B9B9B] mb-3">Competitions</h3>
        <div className="space-y-0.5">
          {PRIMARY_COMPETITIONS.map(comp => {
            const cnt = competitionCounts[comp.id] ?? { total: 0, live: 0 };
            return (
              <button
                key={comp.id}
                onClick={() => onFilterChange(comp.id)}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-[9.5px] font-mono text-left transition-all duration-150
                  ${activeFilter === comp.id
                    ? 'bg-[#1C1B17] text-[#F7F4EE]'
                    : 'text-[#4A4A4A] hover:bg-[#F0EDE6]'
                  }`}
              >
                <span className="truncate">{comp.name}</span>
                {cnt.total > 0 ? (
                  <span className={`ml-1 text-[8.5px] ${activeFilter === comp.id ? 'text-white/60' : 'text-[#9B9B9B]'}`}>
                    {cnt.live > 0 ? `🔴 ${cnt.live}` : cnt.total}
                  </span>
                ) : (
                  <span className={`ml-1 text-[7.5px] ${activeFilter === comp.id ? 'text-white/40' : 'text-[#BBB]'}`}>
                    0
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </aside>
  );
};

// ─── Right Panel ──────────────────────────────────────────────────────────────
const RightPanel = ({
  matches,
  isLoading,
}: {
  matches: MatchPrediction[];
  isLoading: boolean;
}) => {
  const stats = useMemo(() => {
    let live = 0, today = 0, upcoming = 0, completed = 0;
    let highest = 0, sum = 0;
    for (const m of matches) {
      if (m.status === 'LIVE') live++;
      else if (m.status === 'COMPLETED') completed++;
      else upcoming++;
      if (isKickoffToday(m.kickoffTime)) today++;
      const top = Math.max(m.probA, m.probD, m.probB);
      if (top > highest) highest = top;
      sum += top;
    }
    const avg = matches.length > 0 ? sum / matches.length : 0;
    return { live, today, upcoming, completed, highest, avg };
  }, [matches]);

  const row = (label: string, value: React.ReactNode) => (
    <div className="flex justify-between items-center py-2 border-b border-[#EFEFEF]">
      <span className="text-[9px] font-mono text-[#6B6B6B] uppercase tracking-wider">{label}</span>
      <span className="text-[9.5px] font-mono font-bold text-[#1C1B17]">{value}</span>
    </div>
  );

  if (isLoading) {
    return (
      <aside className="hidden xl:block w-52 shrink-0 border-l border-[#D4D4D4] pt-8 px-5 min-h-screen">
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} className="flex justify-between py-2 border-b border-[#EFEFEF]">
            <Skeleton className="h-2.5 w-20" />
            <Skeleton className="h-2.5 w-8" />
          </div>
        ))}
      </aside>
    );
  }

  return (
    <aside className="hidden xl:block w-52 shrink-0 border-l border-[#D4D4D4] pt-8 px-5 min-h-screen sticky top-0 max-h-screen overflow-y-auto">
      <h3 className="text-[8.5px] font-mono uppercase tracking-[0.28em] text-[#9B9B9B] mb-4">Live Stats</h3>
      {row('Live now', stats.live > 0 ? `🔴 ${stats.live}` : 0)}
      {row('Today', stats.today)}
      {row('Upcoming', stats.upcoming)}
      {row('Completed', stats.completed)}
      {row('Total', matches.length)}
      {row('Top confidence', `${stats.highest.toFixed(0)}%`)}
      {row('Avg confidence', `${stats.avg.toFixed(0)}%`)}

      <div className="mt-4 pt-4 border-t border-[#EFEFEF]">
        <h3 className="text-[8.5px] font-mono uppercase tracking-[0.28em] text-[#9B9B9B] mb-3">Supported Competitions</h3>
        <div className="space-y-1">
          {PRIMARY_COMPETITIONS.slice(0, 8).map(c => (
            <div key={c.id} className="text-[8.5px] font-mono text-[#4A4A4A] flex items-center justify-between">
              <span className="truncate">{c.name}</span>
              <span className="text-[8px] text-[#9B9B9B] shrink-0">{c.shortName}</span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
};

// ─── Filter bar ───────────────────────────────────────────────────────────────
const FilterBar = ({
  matches,
  activeFilter,
  onFilterChange,
}: {
  matches: MatchPrediction[];
  activeFilter: string;
  onFilterChange: (id: string) => void;
}) => {
  const compCounts = useMemo(() => {
    const m: Record<string, number> = {};
    for (const match of matches) {
      const cid = (match.competitionId ?? '').toUpperCase();
      m[cid] = (m[cid] ?? 0) + 1;
    }
    return m;
  }, [matches]);

  const liveCount = matches.filter(m => m.status === 'LIVE').length;
  const todayCount = matches.filter(m => isKickoffToday(m.kickoffTime)).length;
  const tomorrowCount = matches.filter(m => isKickoffTomorrow(m.kickoffTime)).length;

  const chips = [
    { id: 'all',       label: 'All',           count: matches.length },
    { id: 'live',      label: '🔴 Live',        count: liveCount },
    { id: 'today',     label: 'Today',          count: todayCount },
    { id: 'tomorrow',  label: 'Tomorrow',       count: tomorrowCount },
    { id: 'favorites', label: '♥ Bookmarks',    count: undefined },
    ...COMPETITION_FILTERS
      .filter(f => !['all','live','today','tomorrow'].includes(f.id))
      .map(f => ({ id: f.id, label: f.label, count: compCounts[(f.id ?? '').toUpperCase()] })),
  ];

  return (
    <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
      {chips.map(chip => (
        <button
          key={chip.id}
          onClick={() => onFilterChange(chip.id)}
          className={`shrink-0 px-3 py-1.5 text-[9px] font-mono uppercase tracking-[0.18em] rounded transition-all duration-150 whitespace-nowrap
            ${activeFilter === chip.id
              ? 'bg-[#1C1B17] text-[#F7F4EE]'
              : 'bg-[#F0EDE6] text-[#4A4A4A] hover:bg-[#E8E4DB]'
            }`}
        >
          {chip.label}
          {chip.count !== undefined && chip.count > 0 && (
            <span className={`ml-1 ${activeFilter === chip.id ? 'text-white/50' : 'text-[#9B9B9B]'}`}>
              ({chip.count})
            </span>
          )}
        </button>
      ))}
    </div>
  );
};

// ─── Main component ───────────────────────────────────────────────────────────
const PredictionFeed = ({
  matches = [],
  isLoading = false,
  favoriteMatchIds = [],
  onToggleFavorite = () => {},
  onViewAnalysis = () => {},
  initialFilter = 'all',
}: PredictionFeedProps) => {
  const [activeFilter, setActiveFilter] = useState(initialFilter);
  const [leagueMatches, setLeagueMatches] = useState<Record<string, MatchPrediction[]>>({});

  const handleFilterChange = (id: string) => {
    setActiveFilter(id);
    const isSpecialFilter = ['all', 'live', 'today', 'tomorrow', 'favorites'].includes(id);
    if (!isSpecialFilter) {
      console.log(`[PredictionFeed] League-specific tab selected: ${id}`);
      loadFixturesProgressive(id)
        .then(newMatches => {
          if (newMatches && newMatches.length > 0) {
            setLeagueMatches(prev => ({
              ...prev,
              [id.toUpperCase()]: newMatches,
            }));
          }
        })
        .catch(err =>
          console.warn(`[PredictionFeed] Failed loading league ${id}:`, err)
        );
    }
  };

  useEffect(() => {
    if (initialFilter) {
      setActiveFilter(initialFilter);
    }
  }, [initialFilter]);

  // Merge primary feed matches with any loaded league-specific fixtures
  const allCombinedMatches = useMemo(() => {
    const map = new Map<string, MatchPrediction>();
    for (const m of matches) map.set(m.id, m);
    for (const list of Object.values(leagueMatches)) {
      for (const m of list) map.set(m.id, m);
    }
    return Array.from(map.values());
  }, [matches, leagueMatches]);

  // Filter matches by active filter
  const displayMatches = useMemo(() => {
    let list = [...allCombinedMatches].filter(m => {
      // Always hide very old completed matches
      if (m.status === 'COMPLETED' && m.finished_at) {
        const age = Date.now() - new Date(m.finished_at).getTime();
        if (age > 12 * 60 * 60 * 1000) return false;
      }
      return true;
    });

    if (activeFilter === 'all') {
      // pass
    } else if (activeFilter === 'live') {
      list = list.filter(m => m.status === 'LIVE');
    } else if (activeFilter === 'today') {
      list = list.filter(m => isKickoffToday(m.kickoffTime));
    } else if (activeFilter === 'tomorrow') {
      list = list.filter(m => isKickoffTomorrow(m.kickoffTime));
    } else if (activeFilter === 'favorites') {
      list = list.filter(m => favoriteMatchIds.includes(m.id));
    } else {
      // Competition code
      const upper = activeFilter.toUpperCase();
      list = list.filter(m => {
        const cid = (m.competitionId ?? '').toUpperCase();
        return cid === upper || (upper === 'CL' && cid === 'UCL') || (upper === 'UCL' && cid === 'CL') ||
               (upper === 'EL' && cid === 'UEL') || (upper === 'UEL' && cid === 'EL');
      });
    }

    // Sort: Live → Upcoming (chronological) → Completed (newest first)
    return list.sort((a, b) => {
      const priority = (m: MatchPrediction) =>
        m.status === 'LIVE' ? 0 : m.status === 'UPCOMING' ? 1 : 2;
      const pa = priority(a), pb = priority(b);
      if (pa !== pb) return pa - pb;
      const ta = new Date(a.kickoffTime ?? a.date ?? 0).getTime();
      const tb = new Date(b.kickoffTime ?? b.date ?? 0).getTime();
      return pa === 2 ? tb - ta : ta - tb; // completed: newest first
    });
  }, [allCombinedMatches, activeFilter, favoriteMatchIds]);

  // Group by competition for section headers
  const grouped = useMemo(() => {
    const order: string[] = [];
    const map: Record<string, MatchPrediction[]> = {};
    for (const m of displayMatches) {
      const key = m.competition || 'Other';
      if (!map[key]) { order.push(key); map[key] = []; }
      map[key].push(m);
    }
    return order.map(k => ({ competition: k, matches: map[k] }));
  }, [displayMatches]);

  // Metadata for current active filter
  const currentCompConfig = getCompetitionById(activeFilter);
  const filterLabel = (() => {
    const chip = COMPETITION_FILTERS.find(f => f.id === activeFilter);
    return chip?.label ?? activeFilter;
  })();

  return (
    <div className="min-h-screen bg-[#F6F4EF] text-[#1C1B17] pt-20 px-4 sm:px-6 lg:px-8">
      {/* Header bar */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 mb-4">
          <h1 className="text-2xl sm:text-3xl font-serif tracking-tight">
            Prediction Feed
            <span className="ml-3 text-xs font-mono font-normal text-[#6B6B6B]">
              {displayMatches.length} {displayMatches.length === 1 ? 'match' : 'matches'}
            </span>
          </h1>
        </div>
        <FilterBar
          matches={allCombinedMatches}
          activeFilter={activeFilter}
          onFilterChange={handleFilterChange}
        />
      </div>

      {/* Main layout: Sidebar + Feed + Right Panel */}
      <div className="max-w-7xl mx-auto flex gap-6 pb-20">
        <Sidebar
          matches={allCombinedMatches}
          activeFilter={activeFilter}
          onFilterChange={handleFilterChange}
          favoriteCount={favoriteMatchIds.length}
          isLoading={isLoading}
        />

        {/* Center feed */}
        <main className="flex-1 min-w-0">
          {isLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className="bg-[#F7F4EE] border border-[#D4D4D4] rounded p-4 space-y-3">
                  <div className="flex justify-between">
                    <Skeleton className="h-3 w-24" />
                    <Skeleton className="h-3 w-12" />
                  </div>
                  <Skeleton className="h-5 w-3/4" />
                  <Skeleton className="h-5 w-2/3" />
                  <Skeleton className="h-1.5 w-full rounded-full" />
                  <Skeleton className="h-6 w-full" />
                </div>
              ))}
            </div>
          ) : displayMatches.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 px-6 text-center bg-[#F7F4EE] border border-[#D4D4D4] rounded-lg">
              <div className="text-3xl mb-3">🔍</div>
              <h3 className="text-lg font-serif text-[#1C1B17] mb-1">No matches found</h3>
              <p className="text-xs text-[#6B6B6B] font-mono max-w-sm mb-6">
                No active predictions available for <strong>{filterLabel}</strong> right now.
              </p>
              <button
                onClick={() => handleFilterChange('all')}
                className="px-5 py-2.5 text-[9px] font-mono uppercase tracking-[0.2em] bg-[#1C1B17] text-[#F7F4EE] rounded hover:bg-[#3a3a3a] transition-colors"
              >
                Show all matches
              </button>
            </div>
          ) : (
            <div className="space-y-8">
              {grouped.map(({ competition, matches: compMatches }) => (
                <section key={competition}>
                  {/* Section header */}
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-[9px] font-mono uppercase tracking-[0.28em] text-[#6B6B6B]">
                      {competition}
                    </span>
                    <span className="text-[8px] font-mono text-[#9B9B9B]">({compMatches.length})</span>
                    <div className="flex-1 h-px bg-[#D4D4D4]" />
                  </div>

                  {/* Card grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                    {compMatches.map(m => (
                      <MatchCard
                        key={m.id}
                        match={m}
                        isFavorite={favoriteMatchIds.includes(m.id)}
                        onToggleFavorite={onToggleFavorite}
                        onViewAnalysis={onViewAnalysis}
                      />
                    ))}
                  </div>
                </section>
              ))}
            </div>
          )}
        </main>

        {/* Right panel */}
        <RightPanel matches={matches} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default PredictionFeed;
