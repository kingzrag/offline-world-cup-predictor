import React, { useState, useMemo } from 'react';
import { Heart, Star, Clock, TrendingUp, Activity, Zap } from 'lucide-react';
import { MatchPrediction } from '../types';
import { COMPETITION_FILTERS, SUPPORTED_COMPETITIONS } from '../config/competitions';
import {
  formatSmartKickoffLocal,
  isKickoffToday,
  isKickoffTomorrow,
} from '../dateTimeUtils';

// ─── Props ────────────────────────────────────────────────────────────────────
interface PredictionFeedProps {
  matches?: MatchPrediction[];
  isLoading?: boolean;
  favoriteMatchIds?: string[];
  onToggleFavorite?: (matchId: string) => void;
  onViewAnalysis?: (match: MatchPrediction) => void;
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

// ─── Match card ───────────────────────────────────────────────────────────────
const MatchCard = ({
  match,
  isFavorite,
  onToggleFavorite,
  onViewAnalysis,
}: {
  match: MatchPrediction;
  isFavorite: boolean;
  onToggleFavorite: (id: string) => void;
  onViewAnalysis: (match: MatchPrediction) => void;
}) => {
  const isLive = match.status === 'LIVE';
  const maxProb = Math.max(match.probA ?? 0, match.probD ?? 0, match.probB ?? 0);
  const kickoff = match.kickoffTime
    ? formatSmartKickoffLocal(match.kickoffTime)
    : match.date;

  // Prediction label: humanise HOME_WIN / AWAY_WIN / DRAW
  const predLabel = (() => {
    const p = match.prediction?.toUpperCase();
    if (p === 'HOME_WIN') return match.teamA;
    if (p === 'AWAY_WIN') return match.teamB;
    if (p === 'DRAW') return 'Draw';
    return match.prediction;
  })();

  return (
    <div className="border border-[#D4D4D4] rounded bg-white hover:border-[#B8B4AC] transition-all duration-200 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-3 pb-2 border-b border-[#EFEFEF]">
        <span className="text-[9px] font-mono uppercase tracking-[0.22em] text-[#6B6B6B]">
          {match.competition || 'Match'}
        </span>
        <div className="flex items-center gap-2">
          {isLive ? <LivePill /> : <ConfidenceBadge confidence={match.confidence} />}
          <button
            onClick={() => onToggleFavorite(match.id)}
            className="text-[#B8B4AC] hover:text-[#3a5c2d] transition-colors duration-150"
            title={isFavorite ? 'Remove from bookmarks' : 'Add to bookmarks'}
          >
            <Heart
              className="w-3 h-3"
              fill={isFavorite ? '#3a5c2d' : 'none'}
              stroke={isFavorite ? '#3a5c2d' : 'currentColor'}
            />
          </button>
        </div>
      </div>

      {/* Teams */}
      <div className="px-4 py-3 flex-1">
        <div className="space-y-1 mb-3">
          <div className="text-sm font-serif text-[#1C1B17] leading-snug">{match.teamA}</div>
          <div className="text-[9px] font-mono uppercase tracking-widest text-[#9B9B9B]">vs</div>
          <div className="text-sm font-serif text-[#1C1B17] leading-snug">{match.teamB}</div>
        </div>

        {/* Prob bar */}
        <ProbBar probA={match.probA} probD={match.probD} probB={match.probB} />

        {/* Prob labels */}
        <div className="flex justify-between mt-1 text-[8px] font-mono text-[#9B9B9B]">
          <span>{Math.round(match.probA ?? 0)}%</span>
          <span>{Math.round(match.probD ?? 0)}%</span>
          <span>{Math.round(match.probB ?? 0)}%</span>
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 pb-3">
        <div className="flex items-center justify-between text-[9px] font-mono text-[#8B8B8B] mb-2.5">
          <span className="flex items-center gap-1">
            <Clock className="w-2.5 h-2.5" />
            {isLive && match.minute != null ? `${match.minute}'` : kickoff}
          </span>
          <span className="text-[#3a5c2d] font-semibold">{maxProb.toFixed(0)}%</span>
        </div>

        {/* Prediction */}
        {predLabel && (
          <div className="text-[9px] font-mono text-[#4A4A4A] mb-2.5 truncate">
            Model: <span className="text-[#1C1B17] font-semibold">{predLabel}</span>
          </div>
        )}

        <button
          onClick={() => onViewAnalysis(match)}
          className="w-full px-3 py-1.5 text-[8.5px] font-mono uppercase tracking-[0.18em] border border-[#D4D4D4] text-[#1C1B17] rounded hover:bg-[#F7F4EE] hover:border-[#B8B4AC] transition-all duration-150"
        >
          Analysis →
        </button>
      </div>
    </div>
  );
};

// ─── Left sidebar ─────────────────────────────────────────────────────────────
const LeftSidebar = ({
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
  // Build per-competition live counts
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

  // Only show competitions that have at least 1 match in the feed
  const activeCompetitions = SUPPORTED_COMPETITIONS.filter(
    c => competitionCounts[c.id]?.total > 0
  );

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

      {/* Competitions with matches */}
      {activeCompetitions.length > 0 && (
        <div>
          <h3 className="text-[8.5px] font-mono uppercase tracking-[0.28em] text-[#9B9B9B] mb-3">Competitions</h3>
          <div className="space-y-0.5">
            {activeCompetitions.map(comp => {
              const cnt = competitionCounts[comp.id];
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
                  <span className="truncate">{comp.shortName}</span>
                  <span className={`text-[8px] tabular-nums ml-1 shrink-0 ${activeFilter === comp.id ? 'text-[#F7F4EE]/60' : 'text-[#9B9B9B]'}`}>
                    {cnt.live > 0 ? (
                      <span className="text-red-400 font-bold">{cnt.live} live</span>
                    ) : cnt.total}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="pt-4 border-t border-[#EFEFEF]">
        <div className="space-y-1.5">
          {[
            { color: 'bg-[#3a5c2d]', label: 'Home win %' },
            { color: 'bg-[#8B7355]', label: 'Draw %' },
            { color: 'bg-[#B44C2A]', label: 'Away win %' },
          ].map(item => (
            <div key={item.label} className="flex items-center gap-2">
              <span className={`w-2 h-1.5 rounded-sm ${item.color}`} />
              <span className="text-[8.5px] font-mono text-[#9B9B9B]">{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
};

// ─── Right info panel ─────────────────────────────────────────────────────────
const RightPanel = ({
  matches,
  isLoading,
}: {
  matches: MatchPrediction[];
  isLoading: boolean;
}) => {
  const stats = useMemo(() => {
    const live = matches.filter(m => m.status === 'LIVE').length;
    const today = matches.filter(m => isKickoffToday(m.kickoffTime)).length;
    const upcoming = matches.filter(m => m.status === 'UPCOMING').length;
    const completed = matches.filter(m => m.status === 'COMPLETED').length;
    const confidences = matches.map(m => Math.max(m.probA ?? 0, m.probD ?? 0, m.probB ?? 0)).filter(v => v > 0);
    const highest = confidences.length ? Math.max(...confidences) : 0;
    const avg = confidences.length ? confidences.reduce((a, b) => a + b, 0) / confidences.length : 0;
    return { live, today, upcoming, completed, highest, avg };
  }, [matches]);

  const row = (label: string, value: string | number) => (
    <div className="flex justify-between items-center py-2 border-b border-[#EFEFEF]">
      <span className="text-[8.5px] font-mono uppercase tracking-[0.18em] text-[#9B9B9B]">{label}</span>
      <span className="text-sm font-serif text-[#1C1B17]">{value}</span>
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
        <h3 className="text-[8.5px] font-mono uppercase tracking-[0.28em] text-[#9B9B9B] mb-3">Competitions</h3>
        <div className="space-y-1">
          {SUPPORTED_COMPETITIONS.slice(0, 8).map(c => (
            <div key={c.id} className="text-[8.5px] font-mono text-[#4A4A4A] flex items-center gap-1.5">
              <span className="text-[9px]">{c.country === 'England' ? '🏴󠁧󠁢󠁥󠁮󠁧󠁿' : c.country === 'Spain' ? '🇪🇸' : c.country === 'Germany' ? '🇩🇪' : c.country === 'Italy' ? '🇮🇹' : c.country === 'France' ? '🇫🇷' : c.country === 'Europe' ? '⭐' : '🌍'}</span>
              {c.shortName}
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
  // Build counts per competition
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

  // Build chip list: core filters + only competitions that have matches
  const chips = [
    { id: 'all',       label: 'All',           count: matches.length },
    { id: 'live',      label: '🔴 Live',        count: liveCount },
    { id: 'today',     label: 'Today',          count: todayCount },
    { id: 'tomorrow',  label: 'Tomorrow',       count: tomorrowCount },
    { id: 'favorites', label: '♥ Bookmarks',    count: undefined },
    ...COMPETITION_FILTERS
      .filter(f => !['all','live','today','tomorrow'].includes(f.id))
      .filter(f => compCounts[(f.id ?? '').toUpperCase()] > 0)
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
}: PredictionFeedProps) => {
  const [activeFilter, setActiveFilter] = useState('all');

  // Filter matches by active filter
  const displayMatches = useMemo(() => {
    let list = [...matches].filter(m => {
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
      list = list.filter(m => (m.competitionId ?? '').toUpperCase() === activeFilter.toUpperCase());
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
  }, [matches, activeFilter, favoriteMatchIds]);

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

  // Active filter label for empty state
  const filterLabel = (() => {
    const chip = COMPETITION_FILTERS.find(f => f.id === activeFilter);
    return chip?.label ?? activeFilter;
  })();

  return (
    <div className="min-h-screen bg-[#F7F4EE] flex flex-col">
      {/* Top bar */}
      <div className="border-b border-[#D4D4D4] bg-[#F7F4EE] px-6 py-5">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-baseline gap-3 mb-4">
            <h1 className="text-3xl font-serif text-[#1C1B17] tracking-tight">Prediction Feed</h1>
            {!isLoading && (
              <span className="text-xs font-mono text-[#9B9B9B]">
                {displayMatches.length} match{displayMatches.length !== 1 ? 'es' : ''}
              </span>
            )}
          </div>
          <FilterBar
            matches={matches}
            activeFilter={activeFilter}
            onFilterChange={setActiveFilter}
          />
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 max-w-7xl mx-auto w-full">
        {/* Left sidebar */}
        <LeftSidebar
          matches={matches}
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
          favoriteCount={favoriteMatchIds.length}
          isLoading={isLoading}
        />

        {/* Main content */}
        <main className="flex-1 px-6 py-6 min-w-0">
          {isLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {[...Array(9)].map((_, i) => (
                <div key={i} className="border border-[#D4D4D4] rounded bg-white p-4 space-y-3">
                  <div className="flex justify-between">
                    <Skeleton className="h-2.5 w-24" />
                    <Skeleton className="h-2.5 w-12" />
                  </div>
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-8" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-1.5 w-full rounded-full" />
                  <Skeleton className="h-6 w-full" />
                </div>
              ))}
            </div>
          ) : displayMatches.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <div className="text-4xl mb-4">🔍</div>
              <h3 className="text-lg font-serif text-[#1C1B17] mb-2">No matches found</h3>
              <p className="text-sm text-[#6B6B6B] font-mono max-w-sm">
                No predictions available for <strong>{filterLabel}</strong>.<br />
                Try "All" or a different competition filter.
              </p>
              <button
                onClick={() => setActiveFilter('all')}
                className="mt-6 px-5 py-2.5 text-[9px] font-mono uppercase tracking-[0.2em] bg-[#1C1B17] text-[#F7F4EE] rounded hover:bg-[#3a3a3a] transition-colors"
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
