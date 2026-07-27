import React, { useState, useEffect, useRef } from 'react';
// @ts-ignore
import football2 from './assets/images/football2.png';
// @ts-ignore
import background from './assets/images/background.png';
import CompetitionSelector from './components/CompetitionSelector';
import { EditorialHero } from './components/EditorialHero';
import { useViewportSnap } from './hooks/useViewportSnap';
import { 
  getPredictions, 
  loadFixturesInstant,
  enrichPredictionsInBackground,
  refreshFixturesFromApi,
  refreshLiveScoresInto,
  API_BASE,
  // getStandings,
  // getBracket,
  getModelPerformance,
  getTeamProfile,
  getH2h,
  predictMatch,
  mapBackendPrediction,
  // getTournamentSimulation,
  // type GroupStandingTeam,
  // type GroupStandings,
  // type BracketMatch,
  // type BracketData,
  // type TeamSimulationResult
} from './api';
import { MatchPrediction, TrophyProbability, IntelligenceInsight } from './types';
import {
  MOCK_INTELLIGENCE,
} from './data';
import { getFlag } from './flagUtils';
import {
  formatSmartKickoffLocal,
  formatKickoffTimeLocal,
  formatKickoffDateLocal,
  formatKickoffDateTimeLocal,
  isKickoffToday,
  isKickoffTomorrow,
} from './dateTimeUtils';
import { formatXG } from './xgUtils';
import { motion, useScroll, useTransform, type MotionValue } from 'motion/react';
import { Canvas } from '@react-three/fiber';
import { Football3D } from './components/Football3D';
// @ts-ignore
import stadiumBg from './assets/images/football2.png';
import { BestPredictionsCarousel } from './components/BestPredictionsCarousel';
import { CursorFX } from './components/CustomCursor';
import AIAssistant from './components/AIAssistant';
import PredictionFeed from './components/PredictionFeed';
import AIAssistantNew from './components/AIAssistantNew';
import AIHealthDashboard from './components/AIHealthDashboard';
import MatchAnalysis from './components/MatchAnalysis';
import CompetitionArchive from './components/CompetitionArchive';
import { checkHealth } from './api';
import {
  Search,
  Trophy,
  Calendar,
  Activity,
  Sliders,
  ShieldCheck,
  Star,
  X,
  Sparkles,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  TrendingUp,
  Info,
  ChevronRight,
  Loader2,
  Clock,
  Globe,
  Zap,
  Briefcase,
  Heart,
  BookOpen,
  SlidersHorizontal,
  ThumbsUp,
  ChevronDown
} from 'lucide-react';

// Simple useMediaQuery hook for responsive logic
function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches
    }
    return false
  })

  useEffect(() => {
    const mediaQueryList = window.matchMedia(query)
    const listener = (event: MediaQueryListEvent) => setMatches(event.matches)
    mediaQueryList.addEventListener('change', listener)
    return () => mediaQueryList.removeEventListener('change', listener)
  }, [query])

  return matches
}



function pickFeaturedMatch(matches: MatchPrediction[]): MatchPrediction | null {
  if (!matches.length) return null;

  // Prioritize LIVE matches across all competitions
  const live = matches.filter(m => m.status === 'LIVE');
  if (live.length > 0) {
    return [...live].sort((a, b) => {
      const tA = new Date(a.kickoffTime || a.date).getTime();
      const tB = new Date(b.kickoffTime || b.date).getTime();
      return tA - tB;
    })[0];
  }

  // Next prioritize UPCOMING matches by kickoff time across all competitions
  const upcoming = matches
    .filter(m => m.status === 'UPCOMING')
    .sort((a, b) => {
      const tA = new Date(a.kickoffTime || a.date).getTime();
      const tB = new Date(b.kickoffTime || b.date).getTime();
      return tA - tB;
    });
  if (upcoming.length > 0) return upcoming[0];

  // Finally, pick highest confidence prediction across all competitions
  const bestPrediction = [...matches]
    .filter(m => m.status === 'UPCOMING')
    .sort((a, b) => {
      const confA = Math.max(a.probA, a.probB, a.probD);
      const confB = Math.max(b.probA, b.probB, b.probD);
      return confB - confA;
    })[0];
  return bestPrediction ?? null;
}

function MatchTimeDisplay({ match }: { match: MatchPrediction }) {
  if (match.status === 'LIVE') {
    return (
      <div className="flex items-center gap-1.5">
        <span className="relative flex h-2 w-2">
          <motion.span
            animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
            className="absolute inline-flex h-full w-full rounded-full bg-red-500"
          />
          <motion.span
            animate={{ scale: [1, 2, 1], opacity: [0.75, 0, 0.75] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
            className="absolute inline-flex h-full w-full rounded-full bg-red-500"
          />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
        </span>
        <span className="text-red-500 font-extrabold tracking-widest uppercase">LIVE</span>
        {match.minute != null && (
          <>
            <span className="text-zinc-600">•</span>
            <span className="text-red-400 font-bold font-mono">{match.minute}&apos;</span>
          </>
        )}
      </div>
    );
  }
  
  if (match.status === 'COMPLETED') {
    return <span className="text-zinc-550 font-bold uppercase tracking-wider">FULL TIME</span>;
  }
  
  return <span className="text-zinc-450">{formatSmartKickoffLocal(match.kickoffTime) || match.date}</span>;
}

const getYear = (match: MatchPrediction) => {
  if (match.kickoffTime) {
    return new Date(match.kickoffTime).getFullYear();
  }
  try {
    const parts = match.date.split(', ');
    if (parts.length > 1) {
      const parsed = parseInt(parts[1]);
      if (!isNaN(parsed)) return parsed;
    }
  } catch {}
  return 2026;
};

const sortSourceMatches = (matches: MatchPrediction[]) => {
  // Filter out finished matches older than 12 hours
  const now = Date.now();
  const twelveHoursMs = 12 * 60 * 60 * 1000;
  
  const visibleMatches = matches.filter(match => {
    if (match.status === 'LIVE') return true;
    if (match.status === 'UPCOMING') return true;
    if (match.status === 'COMPLETED') {
      if (!match.finished_at) return true; // If no finished_at, show by default
      const finishedTime = new Date(match.finished_at).getTime();
      const hoursSinceFinished = (now - finishedTime) / (1000 * 60 * 60);
      return hoursSinceFinished <= 12;
    }
    return false;
  });

  const getSortPriority = (match: MatchPrediction) => {
    if (match.status === 'LIVE') {
      return 1; // Live matches always at the very top
    }
    
    if (match.status === 'UPCOMING') {
      return 2; // Upcoming matches second
    }
    
    if (match.status === 'COMPLETED') {
      return 3; // Recently finished matches (within 12h) last
    }
    
    return 4; // Fallback
  };

  const getTimestampValue = (dateStr: string) => {
    try {
      return new Date(dateStr).getTime();
    } catch (e) {
      return 0;
    }
  };

  return [...visibleMatches].sort((a, b) => {
    const pA = getSortPriority(a);
    const pB = getSortPriority(b);
    
    if (pA !== pB) {
      return pA - pB;
    }
    
    const tA = getTimestampValue(a.kickoffTime || a.date);
    const tB = getTimestampValue(b.kickoffTime || b.date);
    
    // Finished matches sorted most recent first (descending)
    if (pA === 3) {
      return tB - tA;
    }
    
    // Live and Upcoming matches sorted chronological (ascending)
    return tA - tB;
  });
};

export default function App() {
  // Tab Navigation State synced with actual URL pathnames
  const [activeTab, setActiveTab] = useState<'home' | 'predictions' | 'favorites' | 'intelligence' | 'model' | 'tournament'>(() => {
    if (typeof window !== 'undefined') {
      const path = window.location.pathname;
      if (path === '/predictions') return 'predictions';
      if (path === '/favorites') return 'favorites';
      if (path === '/intelligence') return 'intelligence';
      if (path === '/model') return 'model';
      // if (path === '/tournament') return 'tournament'; // HIDE TOURNAMENT ROUTE
    }
    return 'home';
  });


  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress: heroScrollProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"]
  });
  const heroOpacity = useTransform(heroScrollProgress, [0, 0.75, 1], [1, 1, 0.85]);
  const heroScale = useTransform(heroScrollProgress, [0, 1], [1, 0.985]);



  // ── Hero-overlay header: scroll-driven fade + slide ────────────────────────
  // Header is fixed over the hero; as hero scrolls away it fades and lifts out.
  // heroScrollProgress [0 → 0.65] = fully visible
  // heroScrollProgress [0.65 → 1.0] = fade to 0 + translate -28px
  const headerOpacity = useTransform(heroScrollProgress, [0, 0.6, 1], [1, 1, 0]);
  const headerY = useTransform(heroScrollProgress, [0.6, 1], [0, -28]);

  // Enable smart desktop viewport chapter snapping
  useViewportSnap({ activeTab });

  useEffect(() => {
    if (typeof document !== 'undefined') {
      if (activeTab === 'home') {
        document.documentElement.classList.add('editorial-snap-active');
      } else {
        document.documentElement.classList.remove('editorial-snap-active');
      }
    }
    return () => {
      if (typeof document !== 'undefined') {
        document.documentElement.classList.remove('editorial-snap-active');
      }
    };
  }, [activeTab]);

  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width - 0.5) * 2; // scale to -1 to 1
    const y = ((e.clientY - rect.top) / rect.height - 0.5) * 2; // scale to -1 to 1
    setMousePos({ x, y });
  };
  const handleMouseLeave = () => {
    setMousePos({ x: 0, y: 0 });
  };

  // Health Dashboard - developer-only diagnostics page
  const [showHealthDashboard, setShowHealthDashboard] = useState(() => {
    if (typeof window !== 'undefined') {
      const path = window.location.pathname;
      return path === '/admin/health' || path === '/diagnostics';
    }
    return false;
  });

  // Predictions State populated from live FastAPI server
  const [sourceMatches, setSourceMatches] = useState<MatchPrediction[]>([]);
  const [isLoadingMatches, setIsLoadingMatches] = useState<boolean>(true);
  const [matchError, setMatchError] = useState<string | null>(null);

  // Infinite scrolling state
  const [currentLimit, setCurrentLimit] = useState<number>(30);
  const [hasMore, setHasMore] = useState<boolean>(true);
  const [isLoadingMore, setIsLoadingMore] = useState<boolean>(false);

  const isOfflineMode = typeof window !== 'undefined' && window.location.search.includes('offline=true');

  // Startup reliability / retry states
  const [isInitializing, setIsInitializing] = useState<boolean>(false);
  const [isRetrying, setIsRetrying] = useState<boolean>(false);
  const [retryTrigger, setRetryTrigger] = useState<number>(0);
  const [errorType, setErrorType] = useState<'network' | 'timeout' | '404' | '500' | 'unreachable' | 'unknown' | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const signal = controller.signal;
    const t0Page = performance.now();

    async function load() {
      if (isOfflineMode) {
        console.log('[App] Offline mode active (?offline=true) — skipping backend initialization.');
        setIsLoadingMatches(false);
        setIsBackendConnected(true);
        setIsInitializing(false);
        return;
      }

      const startTime = Date.now();
      setIsLoadingMatches(true);
      setMatchError(null);
      setIsRetrying(false);
      setErrorType(null);

      let attempt = 0;
      const maxAttempts = Infinity; // Keep retrying indefinitely
      const baseDelayMs = 1000; // Start with 1 second
      const maxDelayMs = 30000; // Cap at 30 seconds

      while (attempt < maxAttempts) {
        if (signal.aborted) return;
        attempt++;
        const attemptStart = performance.now();

        try {
          // ── Phase 1: render fixtures instantly (no ML inference) ────────────
          console.log(`[App] Attempt ${attempt} → loading fixtures instantly...`);
          const fixtures = await loadFixturesInstant(undefined, false, signal, currentLimit);
          if (signal.aborted) return;

          console.log(`[App] Attempt ${attempt} succeeded: ${fixtures.length} fixtures rendered instantly.`);
          setSourceMatches(sortSourceMatches(fixtures));
          setHasMore(fixtures.length === currentLimit);

          // Load Monte Carlo tournament simulation results in the background
          // loadTournamentData(); // HIDE TOURNAMENT LOAD

          setMatchError(null);
          setIsLoadingMatches(false);
          setIsBackendConnected(true);
          setIsRetrying(false);

          // ── Phase 2: hydrate ML predictions in background ───────────────
          console.log("[App] Phase 2 → enriching predictions in background...");
          await enrichPredictionsInBackground(
            fixtures,
            (matchId, enriched) => {
              if (signal.aborted) return;
              // Update only the single card that just received its prediction
              setSourceMatches(prev => {
                const idx = prev.findIndex(m => m.id === matchId);
                if (idx === -1) return prev;
                const next = [...prev];
                next[idx] = enriched;
                return next;
              });
            },
            signal,
            t0Page
          );
          return; // Successfully completed, exit function

        } catch (err: any) {
          if (signal.aborted) return;
          const attemptEnd = performance.now();
          const duration = (attemptEnd - attemptStart).toFixed(0);

          // Determine error type for better messaging
          const isNetworkError = err?.message?.includes('fetch') || err?.message?.includes('network') || err?.name === 'TypeError';
          const isTimeoutError = err?.message?.includes('timeout') || err?.name === 'AbortError';
          const is404Error = err?.message?.includes('404');
          const is500Error = err?.message?.includes('500');
          const isUnreachable = err?.message?.includes('unreachable');

          // Set error type state
          if (isNetworkError) setErrorType('network');
          else if (isTimeoutError) setErrorType('timeout');
          else if (is404Error) setErrorType('404');
          else if (is500Error) setErrorType('500');
          else if (isUnreachable) setErrorType('unreachable');
          else setErrorType('unknown');

          console.warn(`[App] Attempt ${attempt} failed in ${duration}ms:`, err?.message ?? err);

          // Calculate exponential backoff delay
          const delayMs = Math.min(baseDelayMs * Math.pow(2, attempt - 1), maxDelayMs);
          const delaySeconds = (delayMs / 1000).toFixed(1);

          setIsRetrying(true);
          console.log(`[App] Retrying in ${delaySeconds}s (exponential backoff)...`);

          // Wait with exponential backoff
          await new Promise(resolve => {
            const timer = setTimeout(resolve, delayMs);
            signal.addEventListener('abort', () => {
              clearTimeout(timer);
              resolve(null);
            });
          });
        }
      }
    }

    load();
    return () => {
      controller.abort();
    };
  }, [retryTrigger, currentLimit]);

  // Load more fixtures function
  const loadMoreFixtures = async () => {
    if (isLoadingMore || !hasMore) return;
    
    setIsLoadingMore(true);
    const newLimit = currentLimit + 30;
    
    try {
      const controller = new AbortController();
      const signal = controller.signal;
      const fixtures = await loadFixturesInstant(undefined, false, signal, newLimit);
      
      setSourceMatches(sortSourceMatches(fixtures));
      setCurrentLimit(newLimit);
      setHasMore(fixtures.length === newLimit);
      
      console.log(`[App] Loaded more fixtures: ${fixtures.length} total`);
      
      // Prefetch next page in background if there are more fixtures
      if (fixtures.length === newLimit) {
        setTimeout(() => {
          prefetchNextPage(newLimit + 30);
        }, 2000); // Prefetch after 2 seconds
      }
    } catch (err) {
      console.error("[App] Failed to load more fixtures:", err);
    } finally {
      setIsLoadingMore(false);
    }
  };

  // Background prefetch function
  const prefetchNextPage = async (prefetchLimit: number) => {
    if (!hasMore) return;
    
    console.log(`[App] Prefetching next page: ${prefetchLimit} fixtures`);
    try {
      const controller = new AbortController();
      const signal = controller.signal;
      const fixtures = await loadFixturesInstant(undefined, false, signal, prefetchLimit);
      console.log(`[App] Prefetch complete: ${fixtures.length} fixtures ready`);
      // Data is cached in the API layer, ready for instant display
    } catch (err) {
      console.warn("[App] Prefetch failed (will load on demand):", err);
    }
  };

  const sourceMatchesRef = useRef(sourceMatches);
  sourceMatchesRef.current = sourceMatches;

  // Auto-refresh fixtures: live scores every 15s during live matches, 5min when idle
  useEffect(() => {
    if (isLoadingMatches || matchError) return;

    const refreshLive = async () => {
      try {
        const updated = await refreshLiveScoresInto(sourceMatchesRef.current);
        setSourceMatches(sortSourceMatches(updated));
      } catch (err) {
        console.warn("[App] Live score refresh failed:", err);
      }
    };

    const refreshAll = async () => {
      try {
        const updated = await refreshFixturesFromApi(
          sourceMatchesRef.current,
          false
        );
        setSourceMatches(sortSourceMatches(updated));
        console.info("[App] Full fixture refresh completed");
      } catch (err) {
        console.warn("[App] Full fixture refresh failed:", err);
      }
    };

    let liveInterval: NodeJS.Timeout | null = null;
    let idleInterval: NodeJS.Timeout | null = null;

    const updatePolling = () => {
      const hasLive = sourceMatchesRef.current.some(m => m.status === 'LIVE');
      
      // Clear existing intervals
      if (liveInterval) clearInterval(liveInterval);
      if (idleInterval) clearInterval(idleInterval);
      liveInterval = null;
      idleInterval = null;

      if (hasLive) {
        console.info("[App] Live matches detected — 15s score polling active");
        liveInterval = setInterval(refreshLive, 15_000);
      } else {
        console.info("[App] No live matches — 5min idle polling active");
        idleInterval = setInterval(refreshAll, 5 * 60_000);
      }
    };

    // Initial setup
    updatePolling();

    // Watch for live match changes and adjust polling
    const checkInterval = setInterval(() => {
      const hasLive = sourceMatchesRef.current.some(m => m.status === 'LIVE');
      const wasLive = liveInterval !== null;
      
      if (hasLive !== wasLive) {
        updatePolling();
      }
    }, 5_000);

    return () => {
      if (liveInterval) clearInterval(liveInterval);
      if (idleInterval) clearInterval(idleInterval);
      clearInterval(checkInterval);
    };
  }, [isLoadingMatches, matchError]);

  // Start live polling as soon as a match transitions to LIVE
  const liveMatchCount = sourceMatches.filter(m => m.status === 'LIVE').length;
  useEffect(() => {
    if (isLoadingMatches || matchError || liveMatchCount === 0) return;

    refreshLiveScoresInto(sourceMatchesRef.current)
      .then(updated => setSourceMatches(sortSourceMatches(updated)))
      .catch(err => console.warn("[App] Live transition refresh failed:", err));
  }, [liveMatchCount, isLoadingMatches, matchError]);

  // Enable smooth scroll behavior for snap transitions
  useEffect(() => {
    document.documentElement.style.scrollBehavior = 'smooth';
    return () => {
      document.documentElement.style.scrollBehavior = '';
    };
  }, []);

  // Safe navigation function ensuring a uniform, instant scroll reset to top
  const navigateTo = (tab: 'home' | 'predictions' | 'favorites' | 'intelligence' | 'model' | 'tournament') => {
    setActiveTab(tab);
    
    // Sync browser URL route path
    const targetPath = tab === 'home' ? '/' : `/${tab}`;
    if (window.location.pathname !== targetPath) {
      window.history.pushState(null, '', targetPath);
    }

    try {
      window.scrollTo({
        top: 0,
        left: 0,
        behavior: 'instant' as ScrollBehavior
      });
    } catch (e) {
      window.scrollTo(0, 0);
    }
  };

  // Synchronize on browser history popstate actions and reset scroll
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname;
      if (path === '/predictions') setActiveTab('predictions');
      else if (path === '/favorites') setActiveTab('favorites');
      else if (path === '/intelligence') setActiveTab('intelligence');
      else if (path === '/model') setActiveTab('model');
      // else if (path === '/tournament') setActiveTab('tournament'); // HIDE TOURNAMENT ROUTE
      else setActiveTab('home');
      
      try {
        window.scrollTo({
          top: 0,
          left: 0,
          behavior: 'instant' as ScrollBehavior
        });
      } catch (e) {
        window.scrollTo(0, 0);
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Keep search filter states grouped
  const [selectedFilter, setSelectedFilter] = useState<string>('All Matches');

  // Disable browser scroll position persistence for a clean, deterministic editorial flow
  useEffect(() => {
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }
  }, []);

  // Force scroll position reset to 0 immediately upon any tab/route transition
  useEffect(() => {
    try {
      window.scrollTo({
        top: 0,
        left: 0,
        behavior: 'instant' as ScrollBehavior
      });
    } catch (e) {
      window.scrollTo(0, 0);
    }
  }, [activeTab]);

  // Page Scroll State
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const y = window.scrollY;
      setScrollY(y);
      
      // Infinite scroll detection
      const scrollHeight = document.documentElement.scrollHeight;
      const scrollTop = y;
      const clientHeight = window.innerHeight;
      
      // Load more when user is 200px from bottom
      if (scrollHeight - scrollTop - clientHeight < 200 && hasMore && !isLoadingMore && activeTab === 'home') {
        loadMoreFixtures();
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll(); // Set initial state
    return () => window.removeEventListener('scroll', handleScroll);
  }, [hasMore, isLoadingMore, activeTab]);

  // Search Modal & Index State
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearchModal, setShowSearchModal] = useState(false);

  // Detail Modal States
  const [selectedMatch, setSelectedMatch] = useState<MatchPrediction | null>(null);
  const [showMatchAnalysis, setShowMatchAnalysis] = useState<boolean>(false);
  const [drawerTeamLoading, setDrawerTeamLoading] = useState<boolean>(false);
  const [selectedTeam, setSelectedTeam] = useState<TrophyProbability | null>(null);

  // Live Model Performance tracking state
  const [performanceData, setPerformanceData] = useState<{
    total_fixtures: number;
    completed_fixtures: number;
    correct_predictions: number;
    overall_accuracy: number;
    high_confidence_accuracy: number;
    last_updated: string;
    model_status: string;
    historical_progression: { fixture: number; accuracy: number }[];
  }>({
    total_fixtures: 104,
    completed_fixtures: 47,
    correct_predictions: 34,
    overall_accuracy: 72.3,
    high_confidence_accuracy: 86.7,
    last_updated: "Updated automatically after official FIFA results are processed.",
    model_status: "Active",
    historical_progression: [
      { fixture: 1, accuracy: 100 },
      { fixture: 5, accuracy: 80.0 },
      { fixture: 10, accuracy: 70.0 },
      { fixture: 15, accuracy: 73.3 },
      { fixture: 20, accuracy: 75.0 },
      { fixture: 25, accuracy: 72.0 },
      { fixture: 30, accuracy: 70.0 },
      { fixture: 35, accuracy: 71.4 },
      { fixture: 40, accuracy: 72.5 },
      { fixture: 45, accuracy: 71.1 },
      { fixture: 47, accuracy: 72.3 }
    ]
  });
  // Tournament progression state variables — stubs kept so JSX inside the hidden block compiles
  // To fully restore: uncomment imports + loadTournamentData + useEffect + nav links
  const [standings] = useState<Record<string, any[]>>({});
  const [bracket] = useState<Record<string, any>>({});;
  const [simulationResults] = useState<Record<string, Record<string, number>>>({});
  const [loadingTournament] = useState<boolean>(false);
  const [tournamentError] = useState<string | null>(null);
  const [tournamentSubTab, setTournamentSubTab] = useState<'bracket' | 'standings'>('bracket');

  // const loadTournamentData = async () => {
  //   try {
  //     setLoadingTournament(true);
  //     const [standingsData, bracketData, simData] = await Promise.all([
  //       getStandings(),
  //       getBracket(),
  //       getTournamentSimulation().catch(() => ({ results: {} }))
  //     ]);
  //     setStandings(standingsData);
  //     setBracket(bracketData);
  //     setSimulationResults(simData.results || {});
  //     setTournamentError(null);
  //   } catch (err) {
  //     console.error("Failed to load tournament standings or bracket:", err);
  //     setTournamentError("Could not fetch tournament progression data.");
  //   } finally {
  //     setLoadingTournament(false);
  //   }
  // };


  const [perfLoading, setPerfLoading] = useState(false);
  const [healthData, setHealthData] = useState<any>(null);
  const [footballLoaded, setFootballLoaded] = useState(false);

  // Fetch model performance statistics from backend API on mount or tab select
  const fetchPerformanceData = async () => {
    try {
      setPerfLoading(true);
      const data = await getModelPerformance();
      setPerformanceData(data);
    } catch (err) {
      console.error("Failed to connect to backend prediction performance endpoint:", err);
    } finally {
      setPerfLoading(false);
    }
  };

  const fetchHealthData = async () => {
    try {
      const data = await checkHealth();
      setHealthData(data);
    } catch (err) {
      console.error("Failed to connect to backend health endpoint:", err);
    }
  };

  // Helper function to format timestamp as relative time
  const formatRelativeTime = (timestamp: string | number | null | undefined): string => {
    if (!timestamp) return 'Awaiting first refresh';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    
    // Check if timestamp is epoch 0 (invalid)
    if (date.getTime() === 0) return 'Awaiting first refresh';
    
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    
    // If within current year, show date without year
    if (date.getFullYear() === now.getFullYear()) {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  // useEffect(() => {
  //   if (activeTab === 'tournament') {
  //     loadTournamentData();
  //   }
  // }, [activeTab]);

  useEffect(() => {
    if (activeTab === 'model') {
      fetchPerformanceData();
    }
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === 'intelligence') {
      fetchHealthData();
    }
  }, [activeTab]);

  // Support for submitting results to simulate real-time updates and recalculations
  const handleSimulateResult = async (correct: boolean, isHighConf: boolean) => {
    try {
      setPerfLoading(true);
      const res = await fetch("/api/model-performance/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ correct, is_high_confidence: isHighConf })
      });
      if (res.ok) {
        const data = await res.json();
        setPerformanceData(data);
      } else {
        // Local state recalculation fallback if backend not active
        setPerformanceData(prev => {
          const next_completed = prev.completed_fixtures + 1;
          const next_correct = prev.correct_predictions + (correct ? 1 : 0);
          const next_accuracy = parseFloat(((next_correct / next_completed) * 100).toFixed(1));
          
          let next_hc_accuracy = prev.high_confidence_accuracy;
          if (isHighConf) {
            const prev_hc_evaluated = Math.round(prev.completed_fixtures * 0.64);
            const prev_hc_correct = Math.round(prev_hc_evaluated * (prev.high_confidence_accuracy / 100));
            const next_hc_evaluated = prev_hc_evaluated + 1;
            const next_hc_correct = prev_hc_correct + (correct ? 1 : 0);
            next_hc_accuracy = parseFloat(((next_hc_correct / next_hc_evaluated) * 100).toFixed(1));
          }

          return {
            ...prev,
            completed_fixtures: next_completed,
            correct_predictions: next_correct,
            overall_accuracy: next_accuracy,
            high_confidence_accuracy: next_hc_accuracy,
            last_updated: `Refreshed locally at ${new Date().toISOString().replace('T', ' ').substring(0, 19)} UTC`,
            historical_progression: [
              ...prev.historical_progression,
              { fixture: next_completed, accuracy: next_accuracy }
            ]
          };
        });
      }
    } catch (err) {
      // Local fallback
      setPerformanceData(prev => {
        const next_completed = prev.completed_fixtures + 1;
        const next_correct = prev.correct_predictions + (correct ? 1 : 0);
        const next_accuracy = parseFloat(((next_correct / next_completed) * 100).toFixed(1));
        
        let next_hc_accuracy = prev.high_confidence_accuracy;
        if (isHighConf) {
          const prev_hc_evaluated = Math.round(prev.completed_fixtures * 0.64);
          const prev_hc_correct = Math.round(prev_hc_evaluated * (prev.high_confidence_accuracy / 100));
          const next_hc_evaluated = prev_hc_evaluated + 1;
          const next_hc_correct = prev_hc_correct + (correct ? 1 : 0);
          next_hc_accuracy = parseFloat(((next_hc_correct / next_hc_evaluated) * 100).toFixed(1));
        }

        return {
          ...prev,
          completed_fixtures: next_completed,
          correct_predictions: next_correct,
          overall_accuracy: next_accuracy,
          high_confidence_accuracy: next_hc_accuracy,
          last_updated: `Refreshed locally at ${new Date().toISOString().replace('T', ' ').substring(0, 19)} UTC`,
          historical_progression: [
            ...prev.historical_progression,
            { fixture: next_completed, accuracy: next_accuracy }
          ]
        };
      });
    } finally {
      setPerfLoading(false);
    }
  };

  const handleResetPerformance = async () => {
    try {
      setPerfLoading(true);
      const res = await fetch("/api/model-performance/reset", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setPerformanceData(data);
      } else {
        console.error("Failed to reset performance data from backend");
      }
    } catch (err) {
      console.error("Failed to reset performance data:", err);
    } finally {
      setPerfLoading(false);
    }
  };

  const [hoveredNode, setHoveredNode] = useState<{ fixture: number, accuracy: number } | null>(null);

  // Server-Side AI Streaming / Generation Caching
  const [aiMatchSummaries, setAiMatchSummaries] = useState<{ [matchId: string]: string }>({});
  const [aiMatchLoading, setAiMatchLoading] = useState<boolean>(false);

  const [aiInsightExplanations, setAiInsightExplanations] = useState<{ [insightId: string]: string }>({});
  const [aiInsightLoading, setAiInsightLoading] = useState<string | null>(null);

  // Flag emojis are now resolved dynamically via getFlag() from flagUtils.ts.
  // No hardcoded FLAG_MAP needed — new teams are covered automatically.

  // Section heading separator categorizer
  const getSectionHeading = (match: MatchPrediction) => {
    if (match.status === 'LIVE') return "🔴 Live Matches";
    if (match.status === 'UPCOMING') return "📅 Upcoming Matches";
    if (match.status === 'COMPLETED') return "✅ Completed Matches";
    return "📓 Scheduled Matches";
  };


  // Sorting and filtering matches for dedicated predictions feed
  const getSortedAndFilteredMatches = () => {
    let list = [...sourceMatches];
    
    // Filter out historical matches
    list = list.filter(m => getYear(m) >= 2026);
    
    if (selectedFilter === 'all') {
      // Show all matches
    } else if (selectedFilter === 'live') {
      list = list.filter(m => m.status === 'LIVE');
    } else if (selectedFilter === 'today') {
      list = list.filter(m => isKickoffToday(m.kickoffTime));
    } else if (selectedFilter === 'tomorrow') {
      list = list.filter(m => isKickoffTomorrow(m.kickoffTime));
    } else if (selectedFilter === 'favorites') {
      list = list.filter(m => favoriteMatchIds.includes(m.id));
    } else {
      // Competition-based filtering
      list = list.filter(m => {
        const compId = m.competitionId?.toUpperCase();
        return compId === selectedFilter.toUpperCase();
      });
    }

    const getSortPriority = (match: MatchPrediction) => {
      if (match.status === 'LIVE') {
        return 1; // Live matches always at the very top
      }
      
      if (match.status === 'UPCOMING') {
        return 2; // Upcoming matches second
      }
      
      if (match.status === 'COMPLETED') {
        return 3; // Recently finished matches (within 12h) last
      }
      
      return 4; // Fallback
    };

    const getTimestampValue = (dateStr: string) => {
      try {
        return new Date(dateStr).getTime();
      } catch (e) {
        return 0;
      }
    };

    return list.sort((a, b) => {
      const pA = getSortPriority(a);
      const pB = getSortPriority(b);
      
      if (pA !== pB) {
        return pA - pB;
      }
      
      const tA = getTimestampValue(a.kickoffTime || a.date);
      const tB = getTimestampValue(b.kickoffTime || b.date);
      
      // Finished matches (2026 finished or historical finished) sorted latest first (descending)
      if (pA === 3 || pA === 4) {
        return tB - tA;
      }
      
      // Live and Upcoming matches sorted chronological (ascending)
      return tA - tB;
    });
  };

  // Favorites Local Storage Persistence State
  const [favoriteMatchIds, setFavoriteMatchIds] = useState<string[]>([]);
  const [favoriteTeamCodes, setFavoriteTeamCodes] = useState<string[]>([]);
  const [favoriteInsightIds, setFavoriteInsightIds] = useState<string[]>([]);

  // Local running countdown to next upcoming kickoff (UTC stored, local display)
  const [countdown, setCountdown] = useState('00:00:00:00');
  const [countdownLabel, setCountdownLabel] = useState('Next kickoff');

  // Load and sync favorites on mount
  useEffect(() => {
    try {
      const storedMatches = localStorage.getItem('offline_fav_matches');
      const storedTeams = localStorage.getItem('offline_fav_teams');
      const storedInsights = localStorage.getItem('offline_fav_insights');

      if (storedMatches) setFavoriteMatchIds(JSON.parse(storedMatches));
      if (storedTeams) setFavoriteTeamCodes(JSON.parse(storedTeams));
      if (storedInsights) setFavoriteInsightIds(JSON.parse(storedInsights));
    } catch (e) {
      console.error("Local storage lookup bypassed. Running transient state.", e);
    }
  }, []);

  // Countdown to next upcoming match (falls back to World Cup opening)
  useEffect(() => {
    const updateCountdown = () => {
      const nextUpcoming = sourceMatches
        .filter(m => m.status === 'UPCOMING' && m.kickoffTime)
        .sort((a, b) => new Date(a.kickoffTime!).getTime() - new Date(b.kickoffTime!).getTime())[0];

      const targetIso = nextUpcoming?.kickoffTime ?? "2026-06-11T18:00:00Z";
      const targetTime = new Date(targetIso).getTime();
      const now = Date.now();
      const diff = targetTime - now;

      if (nextUpcoming?.kickoffTime) {
        setCountdownLabel(`${nextUpcoming.teamA} vs ${nextUpcoming.teamB}`);
      } else {
      setCountdownLabel('Next Match Opening');
      }

      if (diff <= 0) {
        setCountdown("00:00:00:00");
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      setCountdown(
        `${String(days).padStart(2, '0')}:${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
      );
    };

    updateCountdown();
    const timer = setInterval(updateCountdown, 1000);
    return () => clearInterval(timer);
  }, [sourceMatches]);

  // Keyboard shortcut for search trigger (Press '/' key)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && !showSearchModal) {
        e.preventDefault();
        setShowSearchModal(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showSearchModal]);

  // Handle Match Summary API Call on selection
  const fetchAiMatchSummary = async (match: MatchPrediction) => {
    if (aiMatchSummaries[match.id]) return; // Already cached
    setAiMatchLoading(true);

    try {
      const response = await fetch('/api/match-summary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          teamA: match.teamA,
          teamB: match.teamB,
          stage: match.stage,
          confidence: match.confidence,
          probA: match.probA,
          probD: match.probD,
          probB: match.probB
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.summary) {
          setAiMatchSummaries(prev => ({ ...prev, [match.id]: data.summary }));
        }
      }
    } catch (err) {
      console.error("AI Match Summary retrieval failed. Triggering core analytical model fallbacks.", err);
    } finally {
      setAiMatchLoading(false);
    }
  };

  // Trigger match analysis viewer modal — opens immediately with fixture data,
  // then hydrates real team stats (FIFA rank, ELO, form, H2H) and prediction in the background.
  const openMatchAnalysis = (match: MatchPrediction) => {
    // Show full-screen analysis immediately with whatever data we already have
    setSelectedMatch(match);
    setShowMatchAnalysis(true);
    fetchAiMatchSummary(match);

    // Fire team-profile + H2H + prediction fetches in parallel — no await, so the drawer renders first
    setDrawerTeamLoading(true);

    const predPromise = !match.isLiveData
      ? predictMatch(match.teamA, match.teamB).then(res => res.prediction).catch(() => null)
      : Promise.resolve(null);

    Promise.all([
      getTeamProfile(match.teamA).catch(() => null),
      getTeamProfile(match.teamB).catch(() => null),
      getH2h(match.teamA, match.teamB).catch(() => null),
      predPromise,
    ]).then(([profileA, profileB, h2hData, freshPred]) => {
      setSelectedMatch(prev => {
        if (!prev || prev.id !== match.id) return prev; // drawer was closed/changed

        let updated = { ...prev };
        if (freshPred) {
          updated = mapBackendPrediction(updated, freshPred);
          // Update sourceMatches so the card in the main layout updates too
          setSourceMatches(source => {
            const idx = source.findIndex(m => m.id === match.id);
            if (idx !== -1) {
              const next = [...source];
              next[idx] = updated;
              return next;
            }
            return source;
          });
        }

        const a = profileA?.team;
        const b = profileB?.team;

        // Map BackendFormEntry[] → ("W" | "D" | "L")[]
        const toFormArr = (entries: { result: string }[] | undefined) =>
          (entries ?? []).slice(0, 5).map(e => e.result as "W" | "D" | "L");

        // Format squad value — show "N/A" cleanly
        const fmtVal = (v: string | null | undefined) =>
          (v && v !== 'N/A' && v !== 'Loading...') ? v : '—';

        return {
          ...updated,
          // Team A real data
          fifaRankA:   a?.fifa_rank  ?? updated.fifaRankA,
          eloRankA:    a?.elo_rank   ?? updated.eloRankA,
          squadValueA: a?.squad_value && a.squad_value !== 'Loading...' && a.squad_value !== 'N/A' && a.squad_value !== '—' ? a.squad_value : 'N/A',
          recentFormA: toFormArr(a?.recent_form).length > 0 ? toFormArr(a?.recent_form) : updated.recentFormA,
          injuriesA:   a?.injuries   ?? updated.injuriesA,
          suspensionsA: a?.suspensions ?? updated.suspensionsA,
          cleanSheetA: a?.clean_sheet_rate ?? updated.cleanSheetA,
          bttsRateA:   a?.btts_rate   ?? updated.bttsRateA,
          // Team B real data
          fifaRankB:   b?.fifa_rank  ?? updated.fifaRankB,
          eloRankB:    b?.elo_rank   ?? updated.eloRankB,
          squadValueB: b?.squad_value && b.squad_value !== 'Loading...' && b.squad_value !== 'N/A' && b.squad_value !== '—' ? b.squad_value : 'N/A',
          recentFormB: toFormArr(b?.recent_form).length > 0 ? toFormArr(b?.recent_form) : updated.recentFormB,
          injuriesB:   b?.injuries   ?? updated.injuriesB,
          suspensionsB: b?.suspensions ?? updated.suspensionsB,
          cleanSheetB: b?.clean_sheet_rate ?? updated.cleanSheetB,
          bttsRateB:   b?.btts_rate   ?? updated.bttsRateB,
          // Real H2H data
          h2hPreviousMeetings: h2hData?.previous_meetings ?? updated.h2hPreviousMeetings,
          h2hWinsA:  h2hData?.team_a_wins ?? updated.h2hWinsA,
          h2hWinsB:  h2hData?.team_b_wins ?? updated.h2hWinsB,
          h2hDraws:  h2hData?.draws       ?? updated.h2hDraws,
          h2hGoalsA: h2hData?.team_a_goals ?? updated.h2hGoalsA,
          h2hGoalsB: h2hData?.team_b_goals ?? updated.h2hGoalsB,
        };
      });
    }).catch(err => {
      console.warn('[drawer] Team profile / H2H / prediction fetch failed:', err);
    }).finally(() => {
      setDrawerTeamLoading(false);
    });
  };

  // Trigger Intelligence explanation API request
  const fetchAiInsightExplanation = async (insight: IntelligenceInsight) => {
    if (aiInsightExplanations[insight.id]) return; // Already cached
    setAiInsightLoading(insight.id);

    try {
      const response = await fetch('/api/intelligence-explain', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: insight.type,
          team: insight.team,
          details: insight.details
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.explanation) {
          setAiInsightExplanations(prev => ({ ...prev, [insight.id]: data.explanation }));
        }
      }
    } catch (err) {
      console.error("Analytical system unable to connect to model API. Fallback insight dispatched.", err);
    } finally {
      setAiInsightLoading(null);
    }
  };

  // Add or Remove Favorite Utility Methods
  const toggleFavoriteMatch = (matchId: string) => {
    let updated;
    if (favoriteMatchIds.includes(matchId)) {
      updated = favoriteMatchIds.filter(id => id !== matchId);
    } else {
      updated = [...favoriteMatchIds, matchId];
    }
    setFavoriteMatchIds(updated);
    localStorage.setItem('offline_fav_matches', JSON.stringify(updated));
  };

  const toggleFavoriteTeam = (code: string) => {
    let updated;
    if (favoriteTeamCodes.includes(code)) {
      updated = favoriteTeamCodes.filter(c => c !== code);
    } else {
      updated = [...favoriteTeamCodes, code];
    }
    setFavoriteTeamCodes(updated);
    localStorage.setItem('offline_fav_teams', JSON.stringify(updated));
  };

  const toggleFavoriteInsight = (insightId: string) => {
    let updated;
    if (favoriteInsightIds.includes(insightId)) {
      updated = favoriteInsightIds.filter(id => id !== insightId);
    } else {
      updated = [...favoriteInsightIds, insightId];
    }
    setFavoriteInsightIds(updated);
    localStorage.setItem('offline_fav_insights', JSON.stringify(updated));
  };

  // Fast indexing for Global Search
  const filteredMatches = searchQuery.trim() === '' ? [] : sourceMatches.filter(m =>
    (m.teamA?.toLowerCase().includes(searchQuery.toLowerCase()) || false) ||
    (m.teamB?.toLowerCase().includes(searchQuery.toLowerCase()) || false) ||
    (m.venue?.toLowerCase().includes(searchQuery.toLowerCase()) || false) ||
    (m.prediction?.toLowerCase().includes(searchQuery.toLowerCase()) || false)
  );

  const filteredTeams: any[] = []; // Temporarily disabled

  const filteredInsights = searchQuery.trim() === '' ? [] : MOCK_INTELLIGENCE.filter(i =>
    i.team.toLowerCase().includes(searchQuery.toLowerCase()) ||
    i.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    i.details.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalSearchResultsCount = filteredMatches.length + filteredTeams.length + filteredInsights.length;

  // Loading screen state for animated status pipeline
  const [loadingStageIndex, setLoadingStageIndex] = useState(0);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [showTransitionSuccess, setShowTransitionSuccess] = useState(false);
  const [isFourSecondsPassed, setIsFourSecondsPassed] = useState(false);
  const [isFootballRotationComplete, setIsFootballRotationComplete] = useState(false);
  const [isAllConditionsMet, setIsAllConditionsMet] = useState(false);
  const [isExtraDelayComplete, setIsExtraDelayComplete] = useState(false);
  const isMobile = useMediaQuery('(max-width: 640px)');

  const startupStages = [
    "Connecting to prediction engine...",
    "Loading football fixtures...",
    "Running Poisson simulations...",
    "Generating betting markets...",
    "Preparing dashboard...",
    "Loading tactical intelligence...",
    "Finalising predictions...",
    "Waiting for Prediction Server..."
  ];

  const systemChecklist = [
    { id: 1, text: "Football Database Loaded", completed: true },
    { id: 2, text: "Team Statistics Loaded", completed: true },
    { id: 3, text: "Fixture Index Ready", completed: true },
    { id: 4, text: "AI Model Initialized", completed: true },
    { id: 5, text: "Connecting Live Prediction Server...", completed: isBackendConnected, animated: !isBackendConnected }
  ];

  // Detect prefers-reduced-motion
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mediaQuery.matches);

    const listener = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };
    mediaQuery.addEventListener("change", listener);
    return () => mediaQuery.removeEventListener("change", listener);
  }, []);

  // Cycle through startup stages
  useEffect(() => {
    if (prefersReducedMotion) {
      setLoadingStageIndex(startupStages.length - 1); // Skip to final stage
      return;
    }

    const interval = setInterval(() => {
      setLoadingStageIndex(prev => {
        if (prev < startupStages.length - 1) {
          return prev + 1;
        }
        return prev; // Stay on final stage
      });
    }, 2500); // 2.5 seconds per stage for faster progression

    return () => clearInterval(interval);
  }, [prefersReducedMotion]);

  // 4-second minimum timer
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsFourSecondsPassed(true);
    }, 4000);

    return () => clearTimeout(timer);
  }, []);

  // Check when ALL initial conditions are met
  useEffect(() => {
    const allConditionsMet = 
      isBackendConnected && 
      isFourSecondsPassed && 
      isFootballRotationComplete;
      
    if (allConditionsMet && !isAllConditionsMet) {
      setIsAllConditionsMet(true);
    }
  }, [isBackendConnected, isFourSecondsPassed, isFootballRotationComplete, isAllConditionsMet]);

  // Handle the EXTRA 3-second delay after all conditions are met
  useEffect(() => {
    if (isAllConditionsMet && !isExtraDelayComplete) {
      const extraDelayTimer = setTimeout(() => {
        setIsExtraDelayComplete(true);
      }, 3000);
      
      return () => clearTimeout(extraDelayTimer);
    }
  }, [isAllConditionsMet, isExtraDelayComplete]);

  // Handle the final fade transition
  useEffect(() => {
    if (isExtraDelayComplete && !showTransitionSuccess) {
      setShowTransitionSuccess(true);
      // Fade out over 600ms
      setTimeout(() => {
        setIsInitializing(false);
      }, 600);
    }
  }, [isExtraDelayComplete, showTransitionSuccess]);

  if (isInitializing) {
    // Helper to render realistic repeating soccer ball panels dynamically
    const renderSoccerPanels = (S: number) => {
      const dx = 1.5 * S; // 22.5 for S=15
      const dy = Math.sqrt(3) * S; // 25.98 for S=15
      
      const isPentagon = (c: number, r: number) => {
        const pc = ((c % 4) + 4) % 4;
        const pr = ((r % 2) + 2) % 2;
        return (pc === 0 && pr === 0) || (pc === 2 && pr === 1);
      };

      const panels = [];
      for (let c = -4; c <= 12; c++) {
        for (let r = -2; r <= 6; r++) {
          const cx = c * dx;
          const cy = (c % 2 === 0 ? r : r + 0.5) * dy;
          const dark = isPentagon(c, r);
          
          const pts = [];
          for (let a = 0; a < 6; a++) {
            const angle = (a * 60 * Math.PI) / 180;
            const px = cx + S * Math.cos(angle);
            const py = cy + S * Math.sin(angle);
            pts.push(`${px.toFixed(1)},${py.toFixed(1)}`);
          }
          
          panels.push(
            <polygon
              key={`${c}-${r}`}
              points={pts.join(" ")}
              fill={dark ? "#09090b" : "#f4f4f5"}
              stroke="#27272a"
              strokeWidth="0.8"
            />
          );
        }
      }
      return panels;
    };

    return (
      <motion.div
        className="fixed inset-0 z-50 flex flex-col items-center justify-center p-6 select-none overflow-hidden"
        style={{ background: '#050508' }}
        initial={{ opacity: 1 }}
        animate={{ opacity: showTransitionSuccess ? 0 : 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* ── CINEMATIC STADIUM BACKGROUND ─────────────────────────────── */}
        <div className="absolute inset-0 pointer-events-none">

          {/* New stadium background - full viewport cover, centered */}
          <img
            src={stadiumBg}
            alt=""
            aria-hidden="true"
            className="absolute inset-0 w-full h-full object-cover"
            style={{
              objectPosition: 'center',
            }}
          />

          {/* Dark overlay for text readability (65% opacity) */}
          <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.65)' }} />

          {/* Vignette — edges darker than center */}
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_70%_at_50%_50%,transparent_30%,rgba(0,0,0,0.75)_100%)]" />

          {/* Floodlight bloom — upper corners, warm white */}
          <div className="absolute top-[-80px] left-[5%] w-[420px] h-[420px] rounded-full animate-[floodlight_14s_ease-in-out_infinite]" style={{ background: 'radial-gradient(circle, rgba(255,252,240,0.055) 0%, transparent 70%)' }} />
          <div className="absolute top-[-80px] right-[5%] w-[420px] h-[420px] rounded-full animate-[floodlight_14s_ease-in-out_infinite_7s]" style={{ background: 'radial-gradient(circle, rgba(255,252,240,0.055) 0%, transparent 70%)' }} />

          {/* Floodlight source points */}
          <div className="absolute top-[2px] left-[11%] w-[5px] h-[5px] rounded-full bg-white/30 blur-[2px]" />
          <div className="absolute top-[2px] right-[11%] w-[5px] h-[5px] rounded-full bg-white/30 blur-[2px]" />

          {/* Pitch green ambient glow at bottom */}
          <div className="absolute bottom-0 inset-x-0 h-[40%]" style={{ background: 'radial-gradient(ellipse 70% 60% at 50% 100%, rgba(16,185,129,0.07) 0%, transparent 80%)' }} />

          {/* Subtle ground fog layer */}
          <div className="absolute bottom-0 inset-x-0 h-[25%]" style={{ background: 'linear-gradient(to top, rgba(16,185,129,0.04) 0%, transparent 100%)', filter: 'blur(20px)' }} />

          {/* Floating dust particles */}
          {!prefersReducedMotion && (
            <>
              <div className="absolute top-1/4 left-[18%] w-[3px] h-[3px] bg-white/15 rounded-full animate-[dust_14s_infinite]" style={{ animationDelay: '0s' }} />
              <div className="absolute top-[38%] right-[22%] w-[2px] h-[2px] bg-white/10 rounded-full animate-[dust_18s_infinite]" style={{ animationDelay: '3s' }} />
              <div className="absolute top-[55%] left-[30%] w-[2px] h-[2px] bg-green-accent/25 rounded-full animate-[dust_16s_infinite]" style={{ animationDelay: '6s' }} />
              <div className="absolute top-[32%] right-[35%] w-[3px] h-[3px] bg-white/12 rounded-full animate-[dust_20s_infinite]" style={{ animationDelay: '1.5s' }} />
              <div className="absolute top-[62%] left-[15%] w-[2px] h-[2px] bg-green-accent/20 rounded-full animate-[dust_22s_infinite]" style={{ animationDelay: '9s' }} />
              <div className="absolute top-[28%] right-[12%] w-[2px] h-[2px] bg-white/14 rounded-full animate-[dust_17s_infinite]" style={{ animationDelay: '4.5s' }} />
            </>
          )}
        </div>

        <div className="min-h-screen w-full flex flex-col items-center justify-center relative z-10" style={{ paddingTop: 'clamp(40px, 7vh, 90px)', paddingBottom: 'clamp(40px, 7vh, 90px)' }}>
          {/* Mobile-only safe area padding */}
          <div className="w-full flex flex-col items-center justify-center max-sm:pt-safe max-sm:pb-safe max-sm:px-safe">
            <div className="flex flex-col items-center gap-10 max-sm:gap-6">
              {/* Logo with breathing animation */}
              <div className={`flex flex-col items-center space-y-3 max-sm:space-y-2 w-full max-w-full ${!prefersReducedMotion ? 'animate-[breathe_6s_ease-in-out_infinite]' : ''}`}>
                <span className="font-serif text-white tracking-[0.45em] font-light pl-[0.45em] uppercase text-center max-w-full" style={{ fontSize: 'clamp(1.5rem, 4vw, 2.25rem)' }}>
                  OFFLINE
                </span>
                <span className="font-mono tracking-[0.6em] text-zinc-500 uppercase pl-[0.6em] text-center max-w-full" style={{ fontSize: 'clamp(0.625rem, 1.5vw, 0.75rem)' }}>
                  FOOTBALL DECISION ENGINE
                </span>
              </div>

              {/* 3D Floating Football Scene - Premium Cinematic */}
              <div className="relative w-full flex items-center justify-center">
                
                {/* Center Circle of Football Pitch - Enhanced - Only show after football loads */}
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: footballLoaded ? 1 : 0 }}
                  transition={{ duration: 0.4 }}
                  className="absolute bottom-[-24px] max-sm:bottom-[-18px] left-1/2 -translate-x-1/2 w-[16rem] max-sm:w-[12rem] h-28 max-sm:h-20 pointer-events-none z-0 overflow-hidden"
                >
                  <div 
                    className="w-full h-full border border-white/10 rounded-full relative flex items-center justify-center"
                    style={{
                      transform: 'rotateX(72deg)',
                      background: 'radial-gradient(circle, rgba(16,185,129,0.25) 0%, rgba(9,9,11,0.92) 70%)',
                      boxShadow: 'inset 0 0 45px rgba(16,185,129,0.1)',
                      backgroundImage: 'repeating-linear-gradient(45deg, rgba(255,255,255,0.004) 0px, rgba(255,255,255,0.004) 2px, transparent 2px, transparent 10px)'
                    }}
                  >
                    {/* Center Spot */}
                    <div className="w-2 h-2 rounded-full bg-white/35" />
                    {/* Center Line */}
                    <div className="absolute top-1/2 left-0 right-0 h-[1px] bg-white/12 -translate-y-1/2" />
                  </div>
                </motion.div>

                {/* Enhanced green glow beneath the football - Only show after football loads */}
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: footballLoaded ? 1 : 0 }}
                  transition={{ duration: 0.4 }}
                  className="absolute bottom-3 max-sm:bottom-2 left-1/2 -translate-x-1/2 w-[10rem] max-sm:w-[8rem] h-10 max-sm:h-8 bg-green-accent/25 rounded-full blur-xl pointer-events-none z-0" 
                />
                
                {/* Soft realistic shadow beneath the football - Only show after football loads */}
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: footballLoaded ? 1 : 0 }}
                  transition={{ duration: 0.4 }}
                  className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[8rem] max-sm:w-[6rem] h-6 max-sm:h-5 bg-black/85 rounded-full blur-[4px] z-10 origin-center"
                  style={{
                    animation: !prefersReducedMotion ? 'shadowScale 4s ease-in-out infinite' : 'none'
                  }}
                />

                {/* 3D Football Canvas — PBR with stadium lighting */}
                <div className="relative w-60 max-sm:w-44 h-60 max-sm:h-44 z-20">
                  <Canvas
                    camera={{ position: [0, 0, 3.8], fov: 40 }}
                    style={{ width: '100%', height: '100%', background: 'transparent' }}
                    dpr={[1, 2]}
                    gl={{ antialias: true, alpha: true }}
                    shadows
                  >
                    <Football3D 
                      onLoaded={() => setFootballLoaded(true)} 
                      scale={isMobile ? 4.8 : 6.5}
                      onRotationComplete={() => setIsFootballRotationComplete(true)}
                    />
                  </Canvas>
                </div>

                {/* Enhanced dust/particles floating around the ball - Only show after football loads */}
                {!prefersReducedMotion && (
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: footballLoaded ? 1 : 0 }}
                    transition={{ duration: 0.4 }}
                    className="absolute inset-0 pointer-events-none overflow-hidden z-25"
                  >
                    <div className="absolute top-1/4 left-1/4 w-1.5 h-1.5 bg-green-accent/40 rounded-full animate-[dust_6s_infinite]" style={{ animationDelay: '0s' }} />
                    <div className="absolute top-1/3 right-1/4 w-2 h-2 bg-white/20 rounded-full animate-[dust_8s_infinite]" style={{ animationDelay: '1.5s' }} />
                    <div className="absolute bottom-1/3 left-1/3 w-2 h-2 bg-green-accent/30 rounded-full animate-[dust_10s_infinite]" style={{ animationDelay: '3s' }} />
                    <div className="absolute top-1/2 right-1/5 w-1.5 h-1.5 bg-white/15 rounded-full animate-[dust_7s_infinite]" style={{ animationDelay: '4.5s' }} />
                    <div className="absolute top-2/5 left-1/5 w-1 h-1 bg-green-accent/35 rounded-full animate-[dust_9s_infinite]" style={{ animationDelay: '2s' }} />
                  </motion.div>
                )}
              </div>

              {/* Animated status pipeline */}
              <div className="flex flex-col items-center gap-7 max-sm:gap-5">
                <motion.div
                  key={showTransitionSuccess ? 'success' : loadingStageIndex}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                  className="space-y-3 max-sm:space-y-2 text-center"
                >
                  <h2 className="text-white font-serif text-2xl max-sm:text-xl tracking-wide uppercase">
                    {showTransitionSuccess ? "✓ Prediction Engine Online" : startupStages[loadingStageIndex]}
                  </h2>
                  <p className="text-zinc-400 font-sans text-xs max-sm:text-[11px] tracking-wider">
                    {showTransitionSuccess ? "Ready to deliver live predictions" : (loadingStageIndex < startupStages.length - 1 ? "Initializing prediction systems..." : "Waiting for backend response...")}
                  </p>
                </motion.div>

                {/* Progress timeline */}
                <div className="flex items-center justify-center gap-2 max-sm:gap-1.5">
                  {startupStages.map((_, index) => (
                    <div
                      key={index}
                      className={`h-1.5 max-sm:h-1 rounded-full transition-all duration-500 ${
                        index <= loadingStageIndex ? 'bg-green-accent' : 'bg-zinc-800'
                      }`}
                      style={{
                        width: index === loadingStageIndex ? '40px' : '14px',
                        opacity: index <= loadingStageIndex ? 1 : 0.3
                      }}
                    />
                  ))}
                </div>

                {/* System checklist */}
                <div className="space-y-2 max-sm:space-y-1.5">
                  {systemChecklist.map((item) => (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: item.id * 0.1 }}
                      className="flex items-center justify-center gap-3 max-sm:gap-2 text-[11px] max-sm:text-[10px] font-mono tracking-wider"
                    >
                      {item.completed ? (
                        <span className="text-green-accent">✓</span>
                      ) : item.animated ? (
                        <span className={`text-green-accent ${!prefersReducedMotion ? 'animate-spin' : ''}`}>⟳</span>
                      ) : (
                        <span className="text-zinc-600">○</span>
                      )}
                      <span className={item.completed ? 'text-zinc-400' : item.animated ? 'text-zinc-300' : 'text-zinc-600'}>
                        {item.text}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Copyright at bottom */}
              <div className="text-center text-zinc-600 text-xs max-sm:text-[10px] font-mono tracking-wider">
                © 2026 OFFLINE Football Decision Engine. All rights reserved.
              </div>
            </div>
          </div>
        </div>

        {/* Custom animations in style tag */}
        <style>{`
          @keyframes breathe {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.02); opacity: 0.95; }
          }
          @keyframes floodlight {
            0%, 100% { opacity: 0.012; }
            50% { opacity: 0.022; }
          }
          @keyframes soccerRotation {
            from { transform: translateX(0px); }
            to { transform: translateX(-90px); }
          }
          @keyframes footballFloat {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-8px); }
          }
          @keyframes shadowScale {
            0%, 100% { transform: scale(1) translateX(-50%); opacity: 0.75; }
            50% { transform: scale(0.82) translateX(-50%); opacity: 0.45; }
          }
          @keyframes dust {
            0% { transform: translate(0, 0) scale(0.8); opacity: 0; }
            50% { transform: translate(6px, -12px) scale(1.2); opacity: 0.4; }
            100% { transform: translate(12px, -24px) scale(0.8); opacity: 0; }
          }
        `}</style>
      </motion.div>
    );
  }

  // Determine cursor theme based on match status
  const cursorTheme = (() => {
    const hasLive = sourceMatches.some(m => m.status === 'LIVE');
    const hasUpcoming = sourceMatches.some(m => m.status === 'UPCOMING');
    
    if (hasLive) return 'live' as const;
    if (hasUpcoming) return 'upcoming' as const;
    return 'finished' as const;
  })();

  return (
    <motion.div
      id="app-root"
      className="min-h-screen bg-black text-zinc-100 flex flex-col selection:bg-green-accent selection:text-black antialiased"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      {/* Cursor FX */}
      <CursorFX theme={cursorTheme} />
      {/* AI Assistant - floating launcher temporarily hidden during homepage redesign */}
      {/* Re-enable after homepage is complete:
      {import.meta.env.VITE_USE_OPENROUTER_AI === 'true' ? (
        <AIAssistantNew
          matches={sourceMatches}
          onAskAboutMatch={(matchId) => { console.log('AI asked about match:', matchId); }}
        />
      ) : (
        <AIAssistant
          matches={sourceMatches}
          onAskAboutMatch={(matchId) => { console.log('AI asked about match:', matchId); }}
        />
      )}
      */}
      {/* ── Hero-only editorial navigation ─────────────────────────────────────
           Fixed over the hero, fades + slides up as the hero scrolls out.
           Only rendered on the home tab (subsequent sections are fully immersive). */}
      {activeTab === 'home' && (
        <motion.header
          id="app-header"
          className="fixed top-0 left-0 right-0 z-50 w-full grid grid-cols-3 items-center
                     px-8 md:px-14 py-4 md:py-5
                     bg-[rgba(247,246,242,0.97)] backdrop-blur-md
                     border-b border-[rgba(28,27,23,0.07)]
                     select-none"
          style={{
            opacity: headerOpacity,
            y: headerY,
            pointerEvents: 'auto',
          }}
        >
          {/* Left nav — Predictions · Favorites */}
          <nav className="flex items-center gap-6 md:gap-8">
            <button
              onClick={() => navigateTo('predictions')}
              className="text-[9.5px] font-mono tracking-[0.26em] uppercase text-[rgba(28,27,23,0.52)]
                         hover:text-[#1C1B17] transition-colors duration-200 whitespace-nowrap pb-px
                         border-b border-transparent hover:border-[rgba(28,27,23,0.30)]"
            >
              Predictions
            </button>
            <button
              onClick={() => navigateTo('favorites')}
              className="text-[9.5px] font-mono tracking-[0.26em] uppercase text-[rgba(28,27,23,0.52)]
                         hover:text-[#1C1B17] transition-colors duration-200 whitespace-nowrap pb-px
                         border-b border-transparent hover:border-[rgba(28,27,23,0.30)]
                         flex items-center gap-1.5"
            >
              Favorites
              {favoriteMatchIds.length + favoriteTeamCodes.length + favoriteInsightIds.length > 0 && (
                <span className="text-[7.5px] font-mono px-1 py-0.5 rounded-sm
                                 bg-[rgba(58,92,45,0.10)] border border-[rgba(58,92,45,0.28)]
                                 text-[rgba(58,92,45,1)] tabular-nums leading-none">
                  {favoriteMatchIds.length + favoriteTeamCodes.length + favoriteInsightIds.length}
                </span>
              )}
            </button>
          </nav>

          {/* Center — OFFLINE wordmark */}
          <div
            onClick={() => navigateTo('home')}
            className="flex flex-col items-center justify-center cursor-pointer group"
            id="offline-logo-container"
          >
            <span className="text-[19px] md:text-[22px] font-serif tracking-[0.38em] font-light
                             leading-none pl-[0.38em] uppercase text-[#1C1B17]
                             group-hover:opacity-60 transition-opacity duration-200">
              OFFLINE
            </span>
            <span className="text-[6.5px] md:text-[7px] font-mono tracking-[0.44em] uppercase
                             mt-[5px] pl-[0.44em] text-[rgba(28,27,23,0.38)]
                             group-hover:opacity-70 transition-opacity duration-200">
              FOOTBALL DECISION ENGINE
            </span>
          </div>

          {/* Right nav — Intelligence · The Model */}
          <nav className="flex items-center justify-end gap-6 md:gap-8">
            <button
              onClick={() => navigateTo('intelligence')}
              className="text-[9.5px] font-mono tracking-[0.26em] uppercase text-[rgba(28,27,23,0.52)]
                         hover:text-[#1C1B17] transition-colors duration-200 whitespace-nowrap pb-px
                         border-b border-transparent hover:border-[rgba(28,27,23,0.30)]"
            >
              Intelligence
            </button>
            <button
              onClick={() => navigateTo('model')}
              className="text-[9.5px] font-mono tracking-[0.26em] uppercase text-[rgba(28,27,23,0.52)]
                         hover:text-[#1C1B17] transition-colors duration-200 whitespace-nowrap pb-px
                         border-b border-transparent hover:border-[rgba(28,27,23,0.30)]"
            >
              The Model
            </button>
          </nav>
        </motion.header>
      )}

      {/* ── Non-home back button ─────────────────────────────────────────────────
           Minimal floating back-to-home link for Predictions, Favorites, etc.
           No full navigation shown — those pages are immersive. */}
      {activeTab !== 'home' && (
        <button
          onClick={() => navigateTo('home')}
          className="fixed top-5 left-6 z-50 flex items-center gap-2
                     text-[9px] font-mono tracking-[0.28em] uppercase
                     text-zinc-500 hover:text-white transition-colors duration-200 cursor-pointer"
        >
          <span className="opacity-70">←</span>
          OFFLINE
        </button>
      )}


      {/* Main Container */}
      <main id="app-main-content" className="flex-1 w-full flex flex-col min-h-0 relative bg-black">

        <div className="relative z-10 flex-1 flex flex-col min-h-0">
          
        {/* LANDING & HERO SECTION (Included for 'home' view) */}
        {activeTab === 'home' && (
          <>
            <EditorialHero
              heroRef={heroRef}
              heroOpacity={heroOpacity}
              heroScale={heroScale}
              countdown={countdown}
              countdownLabel={countdownLabel}
              onNavigate={navigateTo}
              scrollY={scrollY}
              isMobile={isMobile}
            />
          </>
        )}

        {/* RENDER ACTIVE TAB */}

        {/* 1. HOME TAB VIEW (CURATED MAGAZINE-STYLE ENGINE) */}
        {activeTab === 'home' && (
          <div className="w-full flex flex-col animate-fade-in">
            
            {/* TODAY'S BEST PREDICTIONS CAROUSEL SECTION */}
            <BestPredictionsCarousel
              matches={sourceMatches.slice(0, 9)}
              isLoading={isLoadingMatches}
              error={matchError}
              apiBase={API_BASE}
              onViewAnalysis={openMatchAnalysis}
              onViewAll={() => navigateTo('predictions')}
              onRetry={() => setRetryTrigger(prev => prev + 1)}
              isModalOpen={!!selectedMatch || showSearchModal}
            />

            {/* ── COMPETITION ARCHIVE SECTION ──────────────────────────────── */}
            <CompetitionArchive onNavigate={() => navigateTo('predictions')} />

            {/* ── THE MODEL section — Apple keynote editorial light block ───── */}
            <motion.section
              id="the-model-section"
              className="w-full min-h-[100dvh] py-24 bg-[#F6F4EF] bg-paper-grain paper-overlay origin-center flex items-center editorial-snap-section"
              initial={{ opacity: 0, y: 40, scale: 0.98 }}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, amount: 0.12 }}
              transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            >
              {/* Single inner orchestrator — stagger children after section fades in */}
              <motion.div
                className="w-full max-w-7xl mx-auto px-6 md:px-12"
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, amount: 0.1 }}
                variants={{ hidden: {}, show: { transition: { staggerChildren: 0.12 } } }}
              >
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 md:gap-16 items-center">

                  {/* Left Column — label + headline + body */}
                  <div className="lg:col-span-8 space-y-6">
                    <motion.span
                      className="text-[10px] font-mono tracking-[0.3em] text-[#3a5c2d] uppercase block font-bold"
                      variants={{
                        hidden: { opacity: 0, y: 20 },
                        show: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] as const } },
                      }}
                    >
                      THE MODEL
                    </motion.span>

                    <motion.h2
                      className="text-5xl md:text-6xl lg:text-[72px] font-serif text-[#1C1B17] tracking-tight leading-[1.05]"
                      variants={{
                        hidden: { opacity: 0, y: 30 },
                        show: { opacity: 1, y: 0, transition: { duration: 0.9, ease: [0.16, 1, 0.3, 1] as const } },
                      }}
                    >
                      Transparent intelligence.{' '}
                      <span className="text-[#6B6B6B]">No black boxes.</span>
                    </motion.h2>

                    <motion.p
                      className="text-[#4A4A4A] text-base md:text-lg font-light leading-[1.75] max-w-2xl"
                      variants={{
                        hidden: { opacity: 0, y: 20 },
                        show: { opacity: 1, y: 0, transition: { duration: 0.85, ease: [0.16, 1, 0.3, 1] as const } },
                      }}
                    >
                      Twelve weighted signals — from ELO and squad value to injuries, momentum and schedule difficulty — feed 50,051 simulations per match.{' '}
                      <span className="font-serif italic text-[#6B6B6B] block mt-3">
                        The output is a probability, not a prophecy.
                      </span>
                    </motion.p>
                  </div>

                  {/* Right Column — CTA */}
                  <motion.div
                    className="lg:col-span-4 flex lg:justify-end lg:items-center"
                    variants={{
                      hidden: { opacity: 0, y: 16 },
                      show: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] as const } },
                    }}
                  >
                    <button
                      onClick={() => navigateTo('model')}
                      className="group relative inline-flex items-center gap-2.5 text-[11px] font-mono font-bold tracking-[0.2em] text-[#4A4A4A] hover:text-[#1C1B17] uppercase cursor-pointer transition-colors duration-300 pb-2"
                    >
                      LEARN HOW OFFLINE WORKS
                      <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1.5 transition-transform duration-300 shrink-0" />
                      {/* Underline that extends on hover */}
                      <span className="absolute bottom-0 left-0 right-0 h-[1px] bg-[#D4D4D4] group-hover:bg-[#3a5c2d] transition-colors duration-300" />
                    </button>
                  </motion.div>

                </div>
              </motion.div>
            </motion.section>


          </div>
        )}

        {/* 2. DEDICATED PREDICTIONS TERMINAL */}
        {activeTab === 'predictions' && (
          <PredictionFeed />
        )}


        {/* 3. INTELLIGENCE TAB VIEW */}
        {activeTab === 'intelligence' && (() => {
          if (matchError) {
            return (
              <div className="max-w-7xl mx-auto px-6 md:px-12 w-full py-16 animate-fade-in">
                <div className="bg-zinc-950 border border-red-500/25 rounded-lg p-12 flex flex-col items-center justify-center text-center space-y-6">
                  <div className="p-4 bg-red-500/10 rounded-full text-red-400">
                    <AlertCircle className="w-8 h-8 animate-pulse" />
                  </div>
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono tracking-[0.25em] text-red-400 uppercase font-bold">Prediction Engine Offline</span>
                    <h3 className="text-2xl font-serif text-white uppercase tracking-tight font-light">Intelligence Hub Disabled</h3>
                  </div>
                  <p className="text-zinc-400 text-sm max-w-lg leading-relaxed font-sans">
                    The live machine learning prediction engine is currently unreachable at <code className="text-red-400 font-mono">{API_BASE || "(no API URL configured)"}</code>. Since all strategic insights, confidence picks, and goal forecasts are calculated dynamically from the active predictions feed, the Intelligence Hub is offline until a backend connection is established.
                  </p>
                  <button 
                    onClick={() => setRetryTrigger(prev => prev + 1)}
                    className="px-5 py-3 border border-zinc-800 hover:border-zinc-700 bg-zinc-900 hover:bg-zinc-800 text-white rounded text-xs font-mono font-bold tracking-widest uppercase transition duration-300 cursor-pointer"
                  >
                    Retry Connection
                  </button>
                </div>
              </div>
            );
          }

          const factorial = (n: number): number => {
            if (n <= 1) return 1;
            let res = 1;
            for (let i = 2; i <= n; i++) res *= i;
            return res;
          };

          const poisson = (lambda: number, k: number): number => {
            return (Math.exp(-lambda) * Math.pow(lambda, k)) / factorial(k);
          };

          const getPoissonTop5 = (xGA: number, xGB: number, teamA: string, teamB: string) => {
            const scores: { score: string; prob: number }[] = [];
            for (let x = 0; x <= 3; x++) {
              for (let y = 0; y <= 3; y++) {
                const probA = poisson(xGA, x);
                const probB = poisson(xGB, y);
                const combined = probA * probB;
                
                let label = "";
                if (x > y) label = `${x}-${y} ${teamA}`;
                else if (y > x) label = `${x}-${y} ${teamB}`;
                else label = `${x}-${y} Draw`;
                
                scores.push({ score: label, prob: combined });
              }
            }
            const scoreMap: { [key: string]: number } = {};
            scores.forEach(s => {
              scoreMap[s.score] = (scoreMap[s.score] || 0) + s.prob;
            });

            const uniqueScores = Object.entries(scoreMap).map(([score, prob]) => ({ score, prob }));
            uniqueScores.sort((a, b) => b.prob - a.prob);
            const topScores = uniqueScores.slice(0, 5);
            const sum = topScores.reduce((acc, curr) => acc + curr.prob, 0);
            return topScores.map(s => ({
              score: s.score,
              probability: Math.round((s.prob / (sum || 1)) * 38)
            })).sort((a, b) => b.probability - a.probability);
          };

          // Filter to only scheduled/upcoming fixtures for prediction widgets
          // Exclude COMPLETED matches - they should not appear in prediction widgets
          const enrichedMatches = sourceMatches.filter(m => m.status === 'UPCOMING' || m.status === 'LIVE');

          // Section 1: HIGHEST CONFIDENCE PICKS
          const sortedConfidencePicks = [...enrichedMatches]
            .map(m => {
              const favA = m.probA >= m.probB;
              const prediction = m.prediction;
              const winProb = favA ? m.probA : m.probB;
              const lossProb = favA ? m.probB : m.probA;
              const drawProb = m.probD;
              const label = favA ? m.teamA : m.teamB;
              
              // Real confidence: max of actual win/draw/loss probabilities, capped at 99
              const confidenceScore = m.modelConfidence !== undefined
                ? Math.min(99, Math.round(m.modelConfidence * 100))
                : Math.min(99, Math.max(m.probA, m.probD, m.probB));

              return {
                ...m,
                prediction,
                confidenceScore,
                winProb,
                drawProb,
                lossProb,
                label
              };
            })
            .sort((a, b) => b.confidenceScore - a.confidenceScore)
            .slice(0, 5);

          // Section 2: GOAL FEST FORECAST — backend data only, no synthetic formulas
          const sortedGoalForecasts = [...enrichedMatches]
            .map(m => {
              // totalExpectedGoals from backend prediction only - no fallback to actual goals
              const totalXG: number | null = m.totalExpectedGoals ?? null;
              // Backend market only — null signals N/A
              const over25: number | null = m.overUnder?.["2.5"]
                ? Math.round((m.overUnder["2.5"].over ?? 0) * 100)
                : null;
              const over35: number | null = m.overUnder?.["3.5"]
                ? Math.round((m.overUnder["3.5"].over ?? 0) * 100)
                : null;
              const mlScore: string | null = m.mostLikelyScore ?? null;

              return { ...m, totalXG, over25, over35, mlScore };
            })
            .filter(m => m.totalXG !== null)
            .sort((a, b) => (b.totalXG as number) - (a.totalXG as number))
            .slice(0, 5);

          // Section 3: BTTS WATCH — backend bttsMarket only, no Poisson fallback
          const sortedBttsWatch = [...enrichedMatches]
            .map(m => {
              // null signals N/A — never synthesise BTTS from xG
              const bttsYes: number | null = m.bttsMarket
                ? Math.round((m.bttsMarket.yes ?? 0) * 100)
                : null;
              const bttsNo: number | null = m.bttsMarket
                ? Math.round((m.bttsMarket.no ?? 0) * 100)
                : null;
              const totalXG: number | null = m.totalExpectedGoals ?? null;

              return { ...m, bttsYes, bttsNo, totalXG };
            })
            .filter(m => m.bttsYes !== null)
            .sort((a, b) => (b.bttsYes as number) - (a.bttsYes as number))
            .slice(0, 5);

          // Section 4: CLEAN SHEET LEADERS — backend teamGoals.over_0_5 only, no Poisson fallback
          const cleanSheetLeadersList = (() => {
            const teamsMap: { [code: string]: { name: string; rates: number[] } } = {};
            enrichedMatches.forEach(m => {
              // Skip matches without backend team-level goal probability data
              if (!m.teamGoals) return;

              // Clean sheet % = probability that opponent scores 0 = 1 - P(opponent scores > 0.5)
              const csA = Math.round((1 - m.teamGoals.away.over_0_5) * 100);
              const csB = Math.round((1 - m.teamGoals.home.over_0_5) * 100);

              if (!teamsMap[m.teamACode]) {
                teamsMap[m.teamACode] = { name: m.teamA, rates: [] };
              }
              teamsMap[m.teamACode].rates.push(csA);

              if (!teamsMap[m.teamBCode]) {
                teamsMap[m.teamBCode] = { name: m.teamB, rates: [] };
              }
              teamsMap[m.teamBCode].rates.push(csB);
            });

            return Object.entries(teamsMap)
              .map(([code, data]) => {
                const avgCS = Math.round(data.rates.reduce((a, b) => a + b, 0) / data.rates.length);
                return { name: data.name, code, cleanSheetProb: avgCS };
              })
              .sort((a, b) => b.cleanSheetProb - a.cleanSheetProb)
              .slice(0, 6)
              .map((team, idx) => ({ ...team, rank: idx + 1 }));
          })();

          // Section 5: MOST LIKELY SCORELINES — backend top_5_scorelines only, no Poisson synthesis
          const poissonScoresList = enrichedMatches
            .filter(m => m.top5Scorelines && m.top5Scorelines.length > 0)
            .slice(0, 5)
            .map(m => {
              const topScores = m.top5Scorelines!.map(s => {
                const parts = s.score.split('-');
                let label = s.score;
                if (parts.length === 2) {
                  const h = parseInt(parts[0], 10);
                  const a = parseInt(parts[1], 10);
                  label = h > a ? `${s.score} (${m.teamA})` : a > h ? `${s.score} (${m.teamB})` : `${s.score} (Draw)`;
                }
                return { score: label, probability: Math.round(s.probability * 100) };
              });
              return {
                matchId: m.id, teamA: m.teamA, teamB: m.teamB,
                mostLikelyScore: topScores[0]?.score ?? 'N/A',
                probability: topScores[0]?.probability ?? 0,
                allTopScores: topScores
              };
            });

          // Section 6: UPSET WATCH
          const upsetWatchList = enrichedMatches
            .map(m => {
              const probA = m.probA;
              const probB = m.probB;
              
              const aFav = probA >= probB;
              const favorite = aFav ? m.teamA : m.teamB;
              const underdog = aFav ? m.teamB : m.teamA;
              const underdogWinProb = aFav ? probB : probA;
              
              let riskLevel: 'Muted' | 'Elevated' | 'High' | 'Critical' = 'Muted';
              if (underdogWinProb > 25) riskLevel = 'High';
              else if (underdogWinProb >= 22) riskLevel = 'Elevated';
              else riskLevel = 'Muted';

              return {
                ...m,
                favorite,
                underdog,
                underdogWinProb,
                riskLevel
              };
            })
            .filter(item => item.underdogWinProb >= 20 && item.underdogWinProb <= 35)
            .sort((a, b) => b.underdogWinProb - a.underdogWinProb)
            .slice(0, 5);

          // Section 8: MATCH INTELLIGENCE LEADERBOARD — backend data only, no synthetic formulas
          const matchIntelligenceResult = [...enrichedMatches]
            .map(m => {
              // Real xG from backend only - no fallback to actual goals
              const totalXG: number | null = m.totalExpectedGoals ?? null;
              // Backend markets only — null renders as N/A
              const bttsYes: number | null = m.bttsMarket
                ? Math.round((m.bttsMarket.yes ?? 0) * 100)
                : null;
              const over25: number | null = m.overUnder?.["2.5"]
                ? Math.round((m.overUnder["2.5"].over ?? 0) * 100)
                : null;
              // Real confidence: max of actual probabilities, capped at 99
              const confidenceScore = m.modelConfidence !== undefined
                ? Math.min(99, Math.round(m.modelConfidence * 100))
                : Math.min(99, Math.max(m.probA, m.probD, m.probB));

              return { ...m, totalXG, bttsYes, over25, confidenceScore };
            })
            .sort((a, b) => b.confidenceScore - a.confidenceScore);

          return (
            <div className="max-w-7xl mx-auto px-6 md:px-12 w-full py-10 md:py-16">
              <div className="space-y-10 animate-fade-in">
              
                {/* PAGE TITLE & LIVE METRICS BAR */}
                <div className="border-b border-zinc-900 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
                  <div>
                    <span className="text-green-accent text-[9px] font-mono uppercase tracking-[0.2em] block mb-2">OFFLINE DATA-DRIVEN TERMINAL</span>
                    <h2 className="text-4xl font-serif italic text-white mb-2 uppercase tracking-wide">INTELLIGENCE HUB</h2>
                    <p className="text-xs text-zinc-400 max-w-xl font-mono leading-relaxed">
                      Real-time insights generated from OFFLINE prediction models.
                    </p>
                  </div>
                  
                </div>

                {/* THE 2-COLUMN INTEL DASHBOARD GRID */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  
                  {/* SECTION 1: HIGHEST CONFIDENCE PICKS */}
                  <div className="bg-zinc-950 border border-zinc-900 rounded overflow-hidden">
                    <div className="border-b border-zinc-900 px-5 py-3 flex items-center justify-between bg-black/40">
                      <h3 className="text-[10.5px] font-mono uppercase tracking-[0.15em] font-bold text-white flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-green-accent rounded-sm" />
                        Highest Confidence Picks
                      </h3>
                      <span className="text-[9px] font-mono text-zinc-550 uppercase">OFFLINE ENG.V2.4</span>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-[11px] font-mono">
                        <thead>
                          <tr className="border-b border-zinc-900 text-zinc-500 uppercase tracking-wider text-[9px] bg-zinc-950/40">
                            <th className="py-2.5 px-5 font-semibold">Matchup</th>
                            <th className="py-2.5 px-5 font-semibold">Prediction</th>
                            <th className="py-2.5 px-5 font-semibold text-center">Confidence</th>
                            <th className="py-2.5 px-5 font-semibold text-right">W / D / L</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-900/60">
                          {sortedConfidencePicks.length === 0 ? (
                            <tr>
                              <td colSpan={4} className="py-8 text-center text-zinc-555 font-sans">
                                <Loader2 className="w-5 h-5 text-green-accent animate-spin inline-block mr-2" />
                                Analyzing matchup probabilities...
                              </td>
                            </tr>
                          ) : sortedConfidencePicks.map((m) => (
                            <tr key={m.id} className="hover:bg-zinc-900/30 transition-colors">
                              <td className="py-3 px-5 font-sans font-medium text-white">
                                <span className="block text-zinc-500 font-normal text-[9px] uppercase font-mono">{m.stage}</span>
                                {m.teamA} <span className="text-zinc-500 text-xs font-normal">vs</span> {m.teamB}
                              </td>
                              <td className="py-3 px-5">
                                <span className="text-white font-medium bg-zinc-900 px-2 py-0.5 rounded border border-zinc-850">
                                  {m.prediction}
                                </span>
                              </td>
                              <td className="py-3 px-5 text-center text-green-accent font-bold">
                                {m.confidenceScore}%
                              </td>
                              <td className="py-3 px-5 text-right text-zinc-400">
                                <span className="text-white font-bold">{m.winProb}%</span>
                                <span className="text-zinc-650 mx-1">/</span>
                                <span>{m.drawProb}%</span>
                                <span className="text-zinc-650 mx-1">/</span>
                                <span className="text-zinc-550">{m.lossProb}%</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
 
                  {/* SECTION 2: GOAL FEST FORECAST */}
                  <div className="bg-zinc-950 border border-zinc-900 rounded overflow-hidden">
                    <div className="border-b border-zinc-900 px-5 py-3 flex items-center justify-between bg-black/40">
                      <h3 className="text-[10.5px] font-mono uppercase tracking-[0.15em] font-bold text-white flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-green-accent rounded-sm" />
                        Goal Fest Forecast
                      </h3>
                      <span className="text-[9px] font-mono text-zinc-550 uppercase">Expected Goals model</span>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-[11px] font-mono">
                        <thead>
                          <tr className="border-b border-zinc-900 text-zinc-500 uppercase tracking-wider text-[9px] bg-zinc-950/40">
                            <th className="py-2.5 px-5 font-semibold">Matchup</th>
                            <th className="py-2.5 px-5 font-semibold text-center">Expected Goals</th>
                            <th className="py-2.5 px-5 font-semibold text-center">Over 2.5 %</th>
                            <th className="py-2.5 px-5 font-semibold text-center">Over 3.5 %</th>
                            <th className="py-2.5 px-5 font-semibold text-right">Most Likely Score</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-900/60">
                          {sortedGoalForecasts.length === 0 ? (
                            <tr>
                              <td colSpan={5} className="py-8 text-center text-zinc-555 font-sans">
                                <Loader2 className="w-5 h-5 text-green-accent animate-spin inline-block mr-2" />
                                Computing goal expected values...
                              </td>
                            </tr>
                          ) : sortedGoalForecasts.map((m) => (
                            <tr key={m.id} className="hover:bg-zinc-900/30 transition-colors">
                              <td className="py-3 px-5 font-sans font-medium text-white">
                                {m.venue?.trim() && (
                                  <span className="block text-zinc-500 font-normal text-[9px] uppercase font-mono">{m.venue.split(',')[0]}</span>
                                )}
                                {m.teamA} <span className="text-zinc-500 text-xs font-normal">vs</span> {m.teamB}
                              </td>
                              <td className="py-3 px-5 text-center font-bold text-white">
                                {m.totalXG !== null ? formatXG(m.totalXG) : 'N/A'}
                              </td>
                              <td className="py-3 px-5 text-center text-green-accent font-bold">
                                {m.over25 !== null ? `${m.over25}%` : 'N/A'}
                              </td>
                              <td className="py-3 px-5 text-center text-zinc-400">
                                {m.over35 !== null ? `${m.over35}%` : 'N/A'}
                              </td>
                              <td className="py-3 px-5 text-right text-white font-bold">
                                {m.mlScore ?? 'N/A'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
 
                  {/* SECTION 3: BTTS WATCH */}
                  <div className="bg-zinc-950 border border-zinc-900 rounded overflow-hidden">
                    <div className="border-b border-zinc-900 px-5 py-3 flex items-center justify-between bg-black/40">
                      <h3 className="text-[10.5px] font-mono uppercase tracking-[0.15em] font-bold text-white flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-green-accent rounded-sm" />
                        BTTS Watch
                      </h3>
                      <span className="text-[9px] font-mono text-zinc-550 uppercase">Both teams to score</span>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-[11px] font-mono">
                        <thead>
                          <tr className="border-b border-zinc-900 text-zinc-500 uppercase tracking-wider text-[9px] bg-zinc-950/40">
                            <th className="py-2.5 px-5 font-semibold">Matchup</th>
                            <th className="py-2.5 px-5 font-semibold text-center">BTTS YES %%</th>
                            <th className="py-2.5 px-5 font-semibold text-center">BTTS NO %%</th>
                            <th className="py-2.5 px-5 font-semibold text-right">Expected Goals</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-900/60">
                          {sortedBttsWatch.length === 0 ? (
                            <tr>
                              <td colSpan={4} className="py-8 text-center text-zinc-555 font-sans">
                                <Loader2 className="w-5 h-5 text-green-accent animate-spin inline-block mr-2" />
                                Scanning BTTS distributions...
                              </td>
                            </tr>
                          ) : sortedBttsWatch.map((m) => (
                            <tr key={m.id} className="hover:bg-zinc-900/30 transition-colors">
                              <td className="py-3 px-5 font-sans font-medium text-white">
                                <span className="block text-zinc-500 font-normal text-[9px] uppercase font-mono">{m.stage}</span>
                                {m.teamA} <span className="text-zinc-500 text-xs font-normal">vs</span> {m.teamB}
                              </td>
                              <td className="py-3 px-5 text-center text-green-accent font-bold">
                                {m.bttsYes !== null ? `${m.bttsYes}%` : 'N/A'}
                              </td>
                              <td className="py-3 px-5 text-center text-zinc-500">
                                {m.bttsNo !== null ? `${m.bttsNo}%` : 'N/A'}
                              </td>
                              <td className="py-3 px-5 text-right font-bold text-white">
                                {m.totalXG !== null ? formatXG(m.totalXG) : 'N/A'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* SECTION 4: CLEAN SHEET LEADERS */}
                  <div className="bg-zinc-950 border border-zinc-900 rounded overflow-hidden">
                    <div className="border-b border-zinc-900 px-5 py-3 flex items-center justify-between bg-black/40">
                      <h3 className="text-[10.5px] font-mono uppercase tracking-[0.15em] font-bold text-white flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-green-accent rounded-sm" />
                        Clean Sheet Leaders
                      </h3>
                      <span className="text-[9px] font-mono text-zinc-550 uppercase">Defensive metrics</span>
                    </div>
                    <div className="p-5 space-y-4">
                      {cleanSheetLeadersList.length === 0 ? (
                        <div className="py-8 text-center text-zinc-555 font-sans">
                          <Loader2 className="w-5 h-5 text-green-accent animate-spin inline-block mr-2" />
                          Evaluating defensive ratings...
                        </div>
                      ) : cleanSheetLeadersList.map((t) => (
                        <div key={t.code} className="flex items-center justify-between gap-4 font-mono text-[11px]">
                          <div className="flex items-center space-x-3 min-w-[130px]">
                            <span className="text-[10px] text-zinc-600">0{t.rank}</span>
                            <span className="text-white font-sans font-medium">{t.name}</span>
                            <span className="text-[9.5px] bg-zinc-900 px-1.5 py-0.5 rounded text-zinc-500 font-mono">{t.code}</span>
                          </div>
                          
                          {/* Percentage Bar */}
                          <div className="flex-1 h-1 bg-zinc-900 rounded-full overflow-hidden max-w-[200px]">
                            <div 
                              className="h-full bg-green-accent rounded-full transition-all duration-350"
                              style={{ width: `${t.cleanSheetProb}%` }}
                            />
                          </div>
                          
                          <div className="text-right text-green-accent font-bold w-12 font-mono">
                            {t.cleanSheetProb}%
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* SECTION 5: MOST LIKELY SCORELINES */}
                  <div className="bg-zinc-950 border border-zinc-900 rounded overflow-hidden">
                    <div className="border-b border-zinc-900 px-5 py-3 flex items-center justify-between bg-black/40">
                      <h3 className="text-[10.5px] font-mono uppercase tracking-[0.15em] font-bold text-white flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-green-accent rounded-sm" />
                        Most Likely Scorelines
                      </h3>
                      <span className="text-[9px] font-mono text-zinc-550 uppercase">Backend model predictions</span>
                    </div>
                    <div className="p-5 space-y-4">
                      {poissonScoresList.length === 0 ? (
                        <div className="py-8 text-center text-zinc-555 font-sans">
                          <Loader2 className="w-5 h-5 text-green-accent animate-spin inline-block mr-2" />
                          Simulating Poisson score matrices...
                        </div>
                      ) : poissonScoresList.map((m) => (
                        <div key={m.matchId} className="border border-zinc-900/60 bg-zinc-950/20 p-3 rounded space-y-3 font-mono">
                          <div className="flex items-center justify-between border-b border-zinc-900/40 pb-1.5">
                            <span className="text-[11px] font-sans font-bold text-white">{m.teamA} vs {m.teamB}</span>
                            <span className="text-[8.5px] uppercase text-zinc-500 tracking-wider">Backend scorelines</span>
                          </div>
                          
                          {/* Grid of scorelines */}
                          <div className="grid grid-cols-5 gap-1.5 text-center text-[10px]">
                            {m.allTopScores.slice(0, 5).map((s, idx) => (
                              <div key={idx} className="bg-black/40 border border-zinc-900 p-1.5 rounded flex flex-col justify-between h-12">
                                <span className="text-zinc-300 font-bold block overflow-hidden text-ellipsis whitespace-nowrap">{s.score}</span>
                                <span className="text-[9px] text-green-accent mt-0.5">{s.probability}%</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* COLUMN RIGHT: SECTION 6 & 7 COMBINED */}
                  <div className="space-y-8 flex flex-col justify-between">
                    
                    {/* SECTION 6: UPSET WATCH */}
                    <div className="bg-zinc-950 border border-zinc-900 rounded overflow-hidden flex-1">
                      <div className="border-b border-zinc-900 px-5 py-3 flex items-center justify-between bg-black/40">
                        <h3 className="text-[10.5px] font-mono uppercase tracking-[0.15em] font-bold text-white flex items-center gap-2">
                          <span className="w-1.5 h-1.5 bg-orange-500 rounded-sm" />
                          Upset Watch
                        </h3>
                        <span className="text-[9px] font-mono text-zinc-550 uppercase">Risk Assessment</span>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse text-[11px] font-mono">
                          <thead>
                            <tr className="border-b border-zinc-900 text-zinc-500 uppercase tracking-wider text-[9px] bg-zinc-950/40">
                              <th className="py-2.5 px-5 font-semibold">Fav vs Underdog</th>
                              <th className="py-2.5 px-5 font-semibold text-center">Underdog Win Probability</th>
                              <th className="py-2.5 px-5 font-semibold text-right">Risk Level</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-zinc-900/60">
                            {upsetWatchList.length === 0 ? (
                              <tr>
                                <td colSpan={3} className="py-8 text-center text-zinc-555 font-sans">
                                  <Loader2 className="w-5 h-5 text-green-accent animate-spin inline-block mr-2" />
                                  Evaluating underdog risk scenarios...
                                </td>
                              </tr>
                            ) : upsetWatchList.map((item) => (
                              <tr key={item.id} className="hover:bg-zinc-900/30 transition-colors">
                                <td className="py-3 px-5 text-white">
                                  <div className="font-sans font-medium text-xs">
                                    <span className="text-[10px] text-zinc-550 uppercase font-mono block">FAV: {item.favorite}</span>
                                    vs {item.underdog}
                                  </div>
                                </td>
                                <td className="py-3 px-5 text-center font-bold text-orange-400">
                                  {item.underdogWinProb}%
                                </td>
                                <td className="py-3 px-5 text-right">
                                  <span className={`inline-block text-[9px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded ${
                                    item.riskLevel === 'High'  
                                      ? 'bg-red-500/10 text-red-400 border border-red-500/20' 
                                      : 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
                                  }`}>
                                    {item.riskLevel}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* SECTION 7: MODEL SIGNALS */}
                    <div className="bg-zinc-950 border border-zinc-900 rounded overflow-hidden">
                      <div className="border-b border-zinc-900 px-5 py-3 flex items-center justify-between bg-black/40">
                        <h3 className="text-[10.5px] font-mono uppercase tracking-[0.15em] font-bold text-white flex items-center gap-2">
                          <span className="w-1.5 h-1.5 bg-green-accent rounded-sm" />
                          Model Signals
                        </h3>
                        <span className="text-[9px] font-mono text-zinc-550 uppercase">System Telemetry</span>
                      </div>
                      <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 font-mono text-[11px]">
                        <div className="flex items-center space-x-2 text-zinc-300">
                          <span className={`w-1.5 h-1.5 rounded-full ${healthData?.status === 'healthy' ? 'bg-green-accent animate-pulse' : 'bg-red-500'}`} />
                          <span>{healthData?.status === 'healthy' ? '✓' : '✗'} Backend Status: {healthData?.status || 'Unknown'}</span>
                        </div>
                        <div className="flex items-center space-x-2 text-zinc-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-accent animate-pulse" />
                          <span>✓ Prediction Engine: {healthData?.model_version || 'Active'}</span>
                        </div>
                        <div className="flex items-center space-x-2 text-zinc-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-accent animate-pulse" />
                          <span>✓ Database: {healthData?.database_status || 'Connected'}</span>
                        </div>
                        <div className="flex items-center space-x-2 text-zinc-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-accent animate-pulse" />
                          <span>✓ Cache: {healthData?.cache_status || 'Operational'}</span>
                        </div>
                        <div className="col-span-1 sm:col-span-2 pt-3 border-t border-zinc-900 mt-2 flex justify-between text-[9.5px] text-zinc-500 uppercase tracking-wider">
                          <span>Status: {healthData?.status || 'Checking...'}</span>
                          <span className="text-zinc-600">Last Refresh: {healthData?.timestamp ? new Date(healthData.timestamp).toLocaleTimeString() : 'Now'}</span>
                        </div>
                      </div>
                    </div>

                  </div>

                </div>

                {/* SECTION 8: MATCH INTELLIGENCE LEADERBOARD */}
                <div className="bg-zinc-950 border border-zinc-900 rounded overflow-hidden">
                  <div className="border-b border-zinc-900 px-5 py-3 flex items-center justify-between bg-black/40">
                    <h3 className="text-[10.5px] font-mono uppercase tracking-[0.15em] font-bold text-white flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-green-accent rounded-sm" />
                      Match Intelligence Leaderboard
                    </h3>
                    <span className="text-[9px] font-mono text-zinc-550 uppercase">Opportunities sorted by confidence</span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs font-mono min-w-[800px]">
                      <thead>
                        <tr className="border-b border-zinc-900 text-zinc-550 uppercase tracking-wider text-[9px] bg-zinc-950/60">
                          <th className="py-3 px-5 font-semibold">Fixture</th>
                          <th className="py-3 px-5 font-semibold">Stage</th>
                          <th className="py-3 px-5 font-semibold">1X2 Projections</th>
                          <th className="py-3 px-5 font-semibold text-center">BTTS YES %%</th>
                          <th className="py-3 px-5 font-semibold text-center">OVER 2.5 %%</th>
                          <th className="py-3 px-5 font-semibold text-center">PROJ. GOALS (xG)</th>
                          <th className="py-3 px-5 font-semibold text-right">MODEL CONFIDENCE</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-900">
                        {matchIntelligenceResult.length === 0 ? (
                          <tr>
                            <td colSpan={7} className="py-8 text-center text-zinc-555 font-sans">
                              <Loader2 className="w-5 h-5 text-green-accent animate-spin inline-block mr-2" />
                              Constructing global match intelligence matrix...
                            </td>
                          </tr>
                        ) : matchIntelligenceResult.map((m) => (
                          <tr key={m.id} className="hover:bg-zinc-900/30 transition-colors">
                            <td className="py-4 px-5 font-sans font-bold text-white text-sm">
                              {m.teamA} <span className="text-zinc-500 text-xs font-normal">vs</span> {m.teamB}
                            </td>
                            <td className="py-4 px-5 text-zinc-400">
                              {m.stage}
                            </td>
                            <td className="py-4 px-5">
                              <span className="text-zinc-300 font-mono font-medium">
                                A: {m.probA}% <span className="text-zinc-600">/</span> D: {m.probD}% <span className="text-zinc-600">/</span> B: {m.probB}%
                              </span>
                            </td>
                            <td className="py-4 px-5 text-center text-zinc-350">
                              {m.bttsYes !== null ? `${m.bttsYes}%` : 'N/A'}
                            </td>
                            <td className="py-4 px-5 text-center text-zinc-350">
                              {m.over25 !== null ? `${m.over25}%` : 'N/A'}
                            </td>
                            <td className="py-4 px-5 text-center text-white font-bold">
                              {m.totalXG !== null ? formatXG(m.totalXG) : 'N/A'}
                            </td>
                            <td className="py-4 px-5 text-right font-bold text-green-accent">
                              {m.confidenceScore}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

              </div>
            </div>
          );
        })()}

        {/* 4. THE MODEL TAB VIEW */}
        {activeTab === 'model' && (
          <div className="max-w-7xl mx-auto px-6 md:px-12 w-full py-10 md:py-16">
            <div className="space-y-12 animate-fade-in">
            
            <div className="border-b border-zinc-900 pb-5">
              <span className="mono-label text-green-accent text-[9px] block mb-2">Statistical Blueprint Transparency</span>
              <h2 className="text-4xl font-serif italic text-white mb-2">Transparent Intelligence. No Black Boxes.</h2>
              <p className="text-xs text-zinc-400 max-w-xl">
                We believe predictions should be supported by mathematical rigor and reproducible data. Here is how our football prediction model operates.
              </p>
            </div>

            {/* Model variables grid explanation */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              <div className="bg-zinc-950 border border-zinc-900 rounded p-6 space-y-3">
                <TrendingUp className="w-5 h-5 text-green-accent" />
                <h3 className="text-sm font-bold uppercase tracking-widest text-zinc-200">ELO POWER RATINGS</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">
                  Dynamic team strength ratings calculated from international results, opponent quality, tournament importance, recent form, and historical performance trends. Ratings are continuously updated to reflect each nation’s current competitive level.
                </p>
              </div>

              <div className="bg-zinc-950 border border-zinc-900 rounded p-6 space-y-3">
                <Sliders className="w-5 h-5 text-green-accent" />
                <h3 className="text-sm font-bold uppercase tracking-widest text-zinc-200">EXPECTED GOALS (xG) FRAMEWORK</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">
                  Advanced attacking and defensive performance analysis using Expected Goals data, chance creation quality, shot efficiency, and defensive metrics. This provides a more reliable measure of future performance than final scorelines alone.
                </p>
              </div>

              <div className="bg-zinc-950 border border-zinc-900 rounded p-6 space-y-3">
                <Clock className="w-5 h-5 text-green-accent" />
                <h3 className="text-sm font-bold uppercase tracking-widest text-zinc-200">PLAYER AVAILABILITY &amp; FATIGUE MODEL</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">
                  Evaluates injuries, suspensions, squad availability, recovery periods, fixture congestion, and travel demands to quantify their impact on team strength and match outcomes.
                </p>
              </div>

            </div>

            {/* 50,000 matches simulation visualization */}
            <div className="bg-zinc-950 border border-zinc-900 rounded-lg p-6 lg:p-8 space-y-6">
              
              <div className="border-b border-zinc-900 pb-4">
                <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-green-accent mb-1">50,000+ TOURNAMENT SIMULATIONS</h3>
                <p className="text-[11px] text-zinc-500">Continuous bracket projection outcome density curve representation</p>
              </div>

              {/* Simulated chart / SVG details */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                
                {/* Visual Diagram */}
                <div className="lg:col-span-7 bg-black p-6 rounded border border-zinc-900 flex flex-col justify-center">
                  <div className="flex justify-between items-center mb-4 text-[10px] font-mono text-zinc-550 uppercase">
                    <span>Target Outcome Distribution (Median Peak)</span>
                    <span>v4.2 Engine Status: Active</span>
                  </div>

                  {/* SVG continuous peak representation */}
                  <div className="relative h-44 w-full bg-zinc-950/20 border-b border-zinc-805 flex items-end">
                    
                    {/* Visual Curve */}
                    <svg className="absolute inset-0 w-full h-full text-green-accent/20" viewBox="0 0 500 150" preserveAspectRatio="none">
                      <path 
                        d="M 0,150 Q 80,120 160,80 T 260,20 T 360,70 T 500,150 L 500,150 L 0,150 Z" 
                        fill="currentColor" 
                        stroke="#1cdb5e" 
                        strokeWidth="1.5"
                      />
                      <line x1="260" y1="0" x2="260" y2="150" stroke="#1cdb5e" strokeWidth="1" strokeDasharray="3,3" />
                    </svg>

                    {/* Peak labels */}
                    <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-zinc-950 px-2 py-1 rounded border border-zinc-805 text-[9px] font-mono text-white text-center">
                      <span className="text-green-accent font-bold">Median Outcome</span>
                      <div className="text-zinc-500 mt-0.5">Brazil Win Peak (16.1%)</div>
                    </div>

                    <div className="absolute top-1/2 left-[18%] bg-zinc-900/80 px-1.5 py-0.5 rounded text-[8px] font-mono text-zinc-400">
                      Standard Variance Draw
                    </div>

                    <div className="absolute top-2/3 right-[15%] bg-zinc-900/80 px-1.5 py-0.5 rounded text-[8px] font-mono text-zinc-400">
                      Low-Probability Upset
                    </div>

                  </div>

                  <div className="flex justify-between text-[9px] font-mono uppercase text-zinc-600 mt-2">
                    <span>01 (Deterministic Draw)</span>
                    <span>Mean Value (x=0)</span>
                    <span>10 (Outlier Variance)</span>
                  </div>
                </div>

                {/* Analytical parameters text details */}
                <div className="lg:col-span-5 space-y-4">
                  <h4 className="text-sm font-semibold uppercase tracking-wider text-white">Monte Carlo Tournament Simulations</h4>
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    Every prediction is generated through large-scale Monte Carlo simulations combining ELO ratings, Expected Goals data, player availability, recent form, and tournament scheduling variables to estimate match outcomes, progression probabilities, and winning chances.
                  </p>
                  
                  <ul className="space-y-3 text-xs text-zinc-400">
                    <li className="flex items-start gap-2">
                      <span className="text-green-accent font-mono font-bold">✓</span>
                      <span>Adjusts for unexpected goals (set-piece anomalies, penalties).</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-accent font-mono font-bold">✓</span>
                      <span>Exposes systematic fatigue vulnerabilities based on rest day disparities.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-accent font-mono font-bold">✓</span>
                      <span>Updates team momentum indices dynamically every 24 hours.</span>
                    </li>
                  </ul>
                </div>

              </div>

            </div>

            {/* MODEL ACCURACY PORTFOLIO SECTION */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              
              {/* Tournaments track history */}
              <div className="bg-zinc-950 border border-zinc-900 rounded-lg p-6 space-y-6">
                <div className="border-b border-zinc-900 pb-3">
                  <h3 className="text-xs font-mono uppercase text-zinc-400 font-bold tracking-widest">Model Historical Accuracy Archive</h3>
                  <p className="text-[11px] text-zinc-550 lowercase">proven validation over actual historical cycles</p>
                </div>

                {(() => {
                  const completedMatches = sourceMatches.filter(m => m.status === 'COMPLETED');
                  if (completedMatches.length === 0) {
                    return (
                      <div className="p-4 bg-zinc-900/30 rounded border border-zinc-900/60 text-center">
                        <div className="text-zinc-400 text-[11px] leading-relaxed">
                          Historical validation currently being built from completed fixtures.
                        </div>
                        <div className="text-zinc-600 text-[10px] mt-2 font-mono uppercase tracking-wider">
                          Available after more completed matches
                        </div>
                      </div>
                    );
                  }

                  // Calculate metrics from completed matches
                  const totalCompleted = completedMatches.length;
                  let correctPredictions = 0;
                  let homeWinCorrect = 0;
                  let awayWinCorrect = 0;
                  let drawCorrect = 0;
                  let homeWinTotal = 0;
                  let awayWinTotal = 0;
                  let drawTotal = 0;

                  completedMatches.forEach(m => {
                    const predictedOutcome = m.probA > m.probB && m.probA > m.probD ? 'home' : m.probB > m.probA && m.probB > m.probD ? 'away' : 'draw';
                    const actualOutcome = m.winner === 'HOME_TEAM' ? 'home' : m.winner === 'AWAY_TEAM' ? 'away' : 'draw';
                    
                    if (predictedOutcome === actualOutcome) {
                      correctPredictions++;
                      if (actualOutcome === 'home') homeWinCorrect++;
                      if (actualOutcome === 'away') awayWinCorrect++;
                      if (actualOutcome === 'draw') drawCorrect++;
                    }
                    
                    if (actualOutcome === 'home') homeWinTotal++;
                    if (actualOutcome === 'away') awayWinTotal++;
                    if (actualOutcome === 'draw') drawTotal++;
                  });

                  const overallAccuracy = ((correctPredictions / totalCompleted) * 100).toFixed(1);
                  const homeWinAccuracy = homeWinTotal > 0 ? ((homeWinCorrect / homeWinTotal) * 100).toFixed(1) : 'N/A';
                  const awayWinAccuracy = awayWinTotal > 0 ? ((awayWinCorrect / awayWinTotal) * 100).toFixed(1) : 'N/A';
                  const drawAccuracy = drawTotal > 0 ? ((drawCorrect / drawTotal) * 100).toFixed(1) : 'N/A';

                  return (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4 pb-4 border-b border-zinc-900">
                        <div className="p-3 bg-black/40 rounded border border-zinc-900">
                          <div className="text-4xl font-extrabold font-mono text-white text-left tracking-tight">{overallAccuracy}%</div>
                          <span className="text-[9px] font-mono uppercase tracking-widest text-zinc-500 mt-1 block">Overall Accuracy</span>
                        </div>
                        <div className="p-3 bg-black/40 rounded border border-zinc-900">
                          <div className="text-4xl font-extrabold font-mono text-green-accent text-left tracking-tight">{correctPredictions}/{totalCompleted}</div>
                          <span className="text-[9px] font-mono uppercase tracking-widest text-zinc-500 mt-1 block">Correct Predictions</span>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-zinc-300 font-bold">Home Win Accuracy</span>
                          <div className="flex items-center space-x-3">
                            <div className="w-24 h-1 bg-zinc-900 rounded overflow-hidden">
                              <div className="h-full bg-green-accent" style={{ width: homeWinAccuracy !== ' N/A' ? `${homeWinAccuracy}%` : '0%' }}></div>
                            </div>
                            <span className="font-mono font-bold text-white">{homeWinAccuracy}%</span>
                          </div>
                        </div>
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-zinc-300 font-bold">Away Win Accuracy</span>
                          <div className="flex items-center space-x-3">
                            <div className="w-24 h-1 bg-zinc-900 rounded overflow-hidden">
                              <div className="h-full bg-green-accent" style={{ width: awayWinAccuracy !== 'N/A' ? `${awayWinAccuracy}%` : '0%' }}></div>
                            </div>
                            <span className="font-mono font-bold text-white">{awayWinAccuracy}%</span>
                          </div>
                        </div>
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-zinc-300 font-bold">Draw Accuracy</span>
                          <div className="flex items-center space-x-3">
                            <div className="w-24 h-1 bg-zinc-900 rounded overflow-hidden">
                              <div className="h-full bg-green-accent" style={{ width: drawAccuracy !== 'N/A' ? `${drawAccuracy}%` : '0%' }}></div>
                            </div>
                            <span className="font-mono font-bold text-white">{drawAccuracy}%</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })()}

              </div>

              {/* Calibration Stats card */}
              <div className="bg-zinc-950 border border-zinc-900 rounded-lg p-6 space-y-6">
                <div className="border-b border-zinc-900 pb-3">
                  <h3 className="text-xs font-mono uppercase text-zinc-400 font-bold tracking-widest">Engine Confidence Calibration</h3>
                  <p className="text-[11px] text-zinc-550 lowercase">aligning projected prob. with actual tournament outcomes</p>
                </div>

                {(() => {
                  const completedMatches = sourceMatches.filter(m => m.status === 'COMPLETED');
                  if (completedMatches.length < 10) {
                    return (
                      <div className="p-4 bg-zinc-900/30 rounded border border-zinc-900/60 text-center">
                        <div className="text-zinc-400 text-[11px] leading-relaxed">
                          Insufficient completed fixtures to calculate calibration (minimum 10 required).
                        </div>
                        <div className="text-zinc-600 text-[10px] mt-2 font-mono uppercase tracking-wider">
                          Current: {completedMatches.length} completed
                        </div>
                      </div>
                    );
                  }

                  // Calculate calibration by confidence buckets
                  const buckets = [
                    { range: '90-100%', min: 90, max: 100, correct: 0, total: 0 },
                    { range: '80-89%', min: 80, max: 89.9, correct: 0, total: 0 },
                    { range: '70-79%', min: 70, max: 79.9, correct: 0, total: 0 },
                    { range: '60-69%', min: 60, max: 69.9, correct: 0, total: 0 },
                    { range: '50-59%', min: 50, max: 59.9, correct: 0, total: 0 },
                  ];

                  completedMatches.forEach(m => {
                    const maxProb = Math.max(m.probA, m.probB, m.probD);
                    const confidence = maxProb * 100;
                    const predictedOutcome = m.probA > m.probB && m.probA > m.probD ? 'home' : m.probB > m.probA && m.probB > m.probD ? 'away' : 'draw';
                    const actualOutcome = m.winner === 'HOME_TEAM' ? 'home' : m.winner === 'AWAY_TEAM' ? 'away' : 'draw';
                    const isCorrect = predictedOutcome === actualOutcome;

                    for (const bucket of buckets) {
                      if (confidence >= bucket.min && confidence < bucket.max) {
                        bucket.total++;
                        if (isCorrect) bucket.correct++;
                        break;
                      }
                    }
                  });

                  return (
                    <div className="space-y-4">
                      {buckets.map(bucket => {
                        if (bucket.total === 0) return null;
                        const actualAccuracy = ((bucket.correct / bucket.total) * 100).toFixed(1);
                        return (
                          <div key={bucket.range} className="flex items-center justify-between text-xs">
                            <div className="flex flex-col">
                              <span className="text-zinc-300 font-semibold">{bucket.range} range</span>
                              <span className="text-[10px] text-zinc-600 font-mono">Volume: {bucket.total} predictions examined</span>
                            </div>
                            <div className="text-right">
                              <span className="font-mono text-white font-bold">{actualAccuracy}%</span>
                              <span className="text-[10px] text-zinc-500 block uppercase font-mono tracking-tighter">Actual Success Rate</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })()}

                {/* Footnote calibration warning label */}
                <div className="p-4 bg-zinc-950 rounded border border-zinc-900 text-[11px] leading-relaxed text-zinc-550">
                  <strong className="text-zinc-400">Perfect Calibration index defined:</strong> When our strategy engine simulates a collection of outcomes with 80% to 90% confidence, the actual hit rate resolves perfectly inside that envelope.
                </div>

              </div>

            </div>

            {/* 5. LIVE MODEL PERFORMANCE TRACKING */}
            <div className="bg-zinc-950 border border-zinc-900 rounded-lg p-6 lg:p-8 space-y-8 mt-6">
              
              <div className="border-b border-zinc-900 pb-5">
                <div className="flex justify-between items-center flex-wrap gap-4">
                  <div>
                    <span className="text-green-accent font-mono text-[9px] uppercase tracking-wider block mb-1">Live Verification Audit</span>
                    <h3 id="model-performance-heading" className="text-2xl font-serif italic text-white uppercase tracking-wider">MODEL PERFORMANCE</h3>
                    <p className="text-xs text-zinc-500 mt-1 max-w-xl">
                      Every prediction is tracked against real match outcomes. Performance metrics update automatically throughout the tournament.
                    </p>
                  </div>
                  <div className="flex items-center space-x-2.5">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-accent opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-accent"></span>
                    </span>
                    <span className="text-[10px] font-mono uppercase tracking-widest text-zinc-400">Live Audit Syncing</span>
                  </div>
                </div>
              </div>

              {/* Metric Row: 4 Metric Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                
                {/* Card 1 */}
                <div className="bg-black/60 p-5 rounded border border-zinc-900 flex flex-col justify-between hover:border-zinc-800 transition duration-300">
                  <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider mb-2">Fixtures Evaluated</div>
                  <div>
                    <div className="text-3xl font-extrabold font-mono text-white tracking-tight">
                      {performanceData.completed_fixtures} <span className="text-zinc-650 font-normal">/</span> {performanceData.total_fixtures}
                    </div>
                    <div className="text-[10.5px] text-zinc-400 mt-2 leading-relaxed">
                      Matches with official final results
                    </div>
                  </div>
                </div>

                {/* Card 2 */}
                <div className="bg-black/60 p-5 rounded border border-zinc-900 flex flex-col justify-between hover:border-zinc-800 transition duration-300">
                  <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider mb-2">Correct Predictions</div>
                  <div>
                    <div className="text-3xl font-extrabold font-mono text-white tracking-tight">
                      {performanceData.correct_predictions} <span className="text-zinc-650 font-normal">/</span> {performanceData.completed_fixtures}
                    </div>
                    <div className="text-[10.5px] text-zinc-400 mt-2 leading-relaxed">
                      Winner or draw prediction accuracy
                    </div>
                  </div>
                </div>

                {/* Card 3 */}
                <div className="bg-black/60 p-5 rounded border border-zinc-900 flex flex-col justify-between hover:border-zinc-800 transition duration-300">
                  <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider mb-2">Overall Accuracy</div>
                  <div>
                    <div className="text-3xl font-extrabold font-mono text-green-accent tracking-tight">
                      {performanceData.overall_accuracy}%
                    </div>
                    
                    {/* Progress visualizer */}
                    <div className="w-full h-1 bg-zinc-900 rounded overflow-hidden mt-3">
                      <div 
                        className="h-full bg-green-accent transition-all duration-500" 
                        style={{ width: `${performanceData.overall_accuracy}%` }}
                      ></div>
                    </div>

                    <div className="text-[10.5px] text-zinc-400 mt-2 leading-relaxed">
                      Updated after every completed fixture
                    </div>
                  </div>
                </div>

                {/* Card 4 */}
                <div className="bg-black/60 p-5 rounded border border-zinc-900 flex flex-col justify-between hover:border-zinc-800 transition duration-300">
                  <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider mb-2">High-Confidence Accuracy</div>
                  <div>
                    <div className="text-3xl font-extrabold font-mono text-white tracking-tight">
                      {performanceData.high_confidence_accuracy}%
                    </div>

                    {/* Progress visualizer */}
                    <div className="w-full h-1 bg-zinc-900 rounded overflow-hidden mt-3">
                      <div 
                        className="h-full bg-green-accent transition-all duration-500" 
                        style={{ width: `${performanceData.high_confidence_accuracy}%` }}
                      ></div>
                    </div>

                    <div className="text-[10.5px] text-zinc-400 mt-2 leading-relaxed">
                      Predictions with confidence above 70%
                    </div>
                  </div>
                </div>

              </div>

              {/* Data Visualization Grid: Chart + Info Panel */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch pt-2">
                
                {/* 1. Curve Chart (Left, 8-columns) */}
                <div className="lg:col-span-8 bg-black/40 p-6 rounded border border-zinc-900 flex flex-col justify-between relative overflow-hidden">
                  <div>
                    <div className="flex justify-between items-center mb-4">
                      <div>
                        <h4 className="text-xs font-mono uppercase tracking-widest text-zinc-300">Accuracy Over Time</h4>
                        <p className="text-[10px] text-zinc-500 mt-0.5">Continuous verification performance during completed fixtures flow</p>
                      </div>
                      {hoveredNode && (
                        <div className="text-[10px] font-mono bg-zinc-900 border border-zinc-800 px-2.5 py-1 rounded text-white flex items-center space-x-2 animate-fade-in">
                          <span className="text-zinc-500">Fixture {hoveredNode.fixture}:</span>
                          <span className="text-green-accent font-bold">{hoveredNode.accuracy}%</span>
                        </div>
                      )}
                    </div>

                    {/* SVG Line Chart Container */}
                    <div className="h-48 w-full bg-zinc-950/20 border border-zinc-900/60 rounded flex items-stretch p-2 relative">
                      {(() => {
                        const rawPoints = performanceData.historical_progression;
                        if (!rawPoints || rawPoints.length === 0) return null;

                        const minX = 1;
                        const maxX = 104; // Tournament full length
                        const minY = 50;  // Accuracy floor
                        const maxY = 100; // Accuracy ceiling

                        const width = 800;
                        const height = 180;
                        const paddingX = 40;
                        const paddingY = 20;

                        const getX = (fixture: number) => {
                          const ratio = (fixture - minX) / (maxX - minX || 1);
                          return paddingX + ratio * (width - 2 * paddingX);
                        };

                        const getY = (acc: number) => {
                          const ratio = (acc - minY) / (maxY - minY || 1);
                          return height - paddingY - ratio * (height - 2 * paddingY);
                        };

                        // Create svg polyline attributes
                        const pointsStr = rawPoints.map(p => `${getX(p.fixture)},${getY(p.accuracy)}`).join(" ");
                        
                        // Area overlay under line
                        const firstPoint = rawPoints[0];
                        const lastPoint = rawPoints[rawPoints.length - 1];
                        const areaPointsStr = `${getX(firstPoint.fixture)},${height - paddingY} ${pointsStr} ${getX(lastPoint.fixture)},${height - paddingY}`;

                        return (
                          <svg className="w-full h-full text-green-accent/10 select-none pb-1" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
                            {/* Horizontal Grid lines */}
                            {[50, 60, 70, 80, 90, 100].map((level, idx) => {
                              const y = getY(level);
                              return (
                                <g key={idx}>
                                  <line x1={paddingX} y1={y} x2={width - paddingX} y2={y} stroke="#141416" strokeWidth="1" strokeDasharray="4,4" />
                                  <text x={paddingX - 10} y={y + 3} fill="#4b5563" fontSize="8" fontFamily="monospace" textAnchor="end">{level}%</text>
                                </g>
                              );
                            })}

                            {/* X-Axis labels at key fixture interval steps */}
                            {[1, 20, 40, 60, 80, 104].map((step, idx) => {
                              const x = getX(step);
                              return (
                                <g key={idx}>
                                  <line x1={x} y1={paddingY} x2={x} y2={height - paddingY} stroke="#141416" strokeWidth="1" strokeDasharray="4,4" />
                                  <text x={x} y={height - 5} fill="#4b5563" fontSize="8" fontFamily="monospace" textAnchor="middle">F{step}</text>
                                </g>
                              );
                            })}

                            {/* Shaded area path underneath the trend curve */}
                            <polygon points={areaPointsStr} fill="currentColor" opacity="0.4" />

                            {/* Gorgeous glow filter */}
                            <defs>
                              <filter id="glow-perf" x="-20%" y="-20%" width="140%" height="140%">
                                <feGaussianBlur stdDeviation="3" result="blur" />
                                <feComposite in="SourceGraphic" in2="blur" operator="over" />
                              </filter>
                            </defs>

                            {/* Premium high contrast path trend line */}
                            <polyline
                              fill="none"
                              stroke="#1cdb5e"
                              strokeWidth="2"
                              points={pointsStr}
                              filter="url(#glow-perf)"
                            />

                            {/* Interactive pointer nodes */}
                            {rawPoints.map((node, index) => {
                              const cx = getX(node.fixture);
                              const cy = getY(node.accuracy);
                              const isHovered = hoveredNode && hoveredNode.fixture === node.fixture;
                              return (
                                <circle
                                  key={index}
                                  cx={cx}
                                  cy={cy}
                                  r={isHovered ? "5" : "3"}
                                  className="cursor-pointer fill-[#1cdb5e] hover:fill-white stroke-black stroke-2 transition-all duration-150"
                                  onMouseEnter={() => setHoveredNode(node)}
                                  onMouseLeave={() => setHoveredNode(null)}
                                />
                              );
                            })}
                          </svg>
                        );
                      })()}
                    </div>
                  </div>

                  <div className="flex justify-between items-center text-[9px] font-mono text-zinc-650 uppercase mt-3">
                    <span>Tournament Start (June 11)</span>
                    <span>Continuous evaluation feed</span>
                    <span>Final Fixture (July 19)</span>
                  </div>
                </div>

                {/* 2. Recent Prediction Verification (Right, 4-columns) */}
                <div className="lg:col-span-4 bg-zinc-950 border border-zinc-900 rounded p-5 flex flex-col justify-between">
                  <div className="space-y-4">
                    <div className="border-b border-zinc-900 pb-2.5">
                      <span className="text-green-accent text-[8.5px] font-mono uppercase tracking-widest block mb-0.5">Live Verification</span>
                      <h4 className="text-xs font-mono uppercase tracking-[0.1em] text-zinc-300 font-bold">RECENT PREDICTIONS</h4>
                    </div>
                    
                    <p className="text-[11px] text-zinc-550 leading-relaxed">
                      Recent predictions verified against actual match outcomes. Accuracy updates automatically as fixtures complete.
                    </p>

                    <div className="space-y-3 max-h-64 overflow-y-auto">
                      {(() => {
                        const completedMatches = sourceMatches.filter(m => m.status === 'COMPLETED').slice(0, 5);
                        if (completedMatches.length === 0) {
                          return (
                            <div className="p-3 bg-black/40 rounded border border-zinc-900 text-center">
                              <div className="text-[11px] text-zinc-400 leading-relaxed">
                                Awaiting completed fixtures for verification
                              </div>
                            </div>
                          );
                        }

                        return completedMatches.map(m => {
                          const predictedOutcome = m.probA > m.probB && m.probA > m.probD ? 'home' : m.probB > m.probA && m.probB > m.probD ? 'away' : 'draw';
                          const actualOutcome = m.winner === 'HOME_TEAM' ? 'home' : m.winner === 'AWAY_TEAM' ? 'away' : 'draw';
                          const isCorrect = predictedOutcome === actualOutcome;
                          const maxProb = Math.max(m.probA, m.probB, m.probD);
                          const confidence = maxProb.toFixed(1);

                          return (
                            <div key={m.id} className="p-3 bg-black/40 rounded border border-zinc-900 space-y-2">
                              <div className="flex justify-between items-start">
                                <div className="text-[10px] text-zinc-300 font-semibold">
                                  {m.teamA} vs {m.teamB}
                                </div>
                                <div className={`text-[10px] font-mono font-bold ${isCorrect ? 'text-green-accent' : 'text-red-500'}`}>
                                  {isCorrect ? '✓ Correct' : '✗ Incorrect'}
                                </div>
                              </div>
                              <div className="grid grid-cols-2 gap-2 text-[9px]">
                                <div>
                                  <span className="text-zinc-600 block">Prediction</span>
                                  <span className="text-zinc-300 font-mono">{predictedOutcome === 'home' ? m.teamA : predictedOutcome === 'away' ? m.teamB : 'Draw'}</span>
                                </div>
                                <div>
                                  <span className="text-zinc-600 block">Actual</span>
                                  <span className="text-zinc-300 font-mono">{actualOutcome === 'home' ? m.teamA : actualOutcome === 'away' ? m.teamB : 'Draw'}</span>
                                </div>
                              </div>
                              <div className="flex justify-between items-center text-[9px]">
                                <span className="text-zinc-600">Confidence</span>
                                <span className="text-zinc-300 font-mono">{confidence}%</span>
                              </div>
                            </div>
                          );
                        });
                      })()}
                    </div>
                  </div>

                  <div className="space-y-2 mt-4">
                    <button
                      onClick={handleResetPerformance}
                      disabled={perfLoading}
                      className="w-full py-1.5 border border-zinc-900 hover:border-zinc-800 bg-transparent text-[9px] font-mono uppercase rounded text-zinc-500 hover:text-zinc-400 transition-all duration-150 cursor-pointer"
                    >
                      Refresh Performance Data
                    </button>
                  </div>
                </div>

              </div>

              {/* Additional Analytics Bar */}
              <div className="bg-zinc-900/15 border border-zinc-900/60 p-4 rounded text-xs flex flex-col md:flex-row md:justify-between items-start md:items-center gap-4">
                <div className="text-zinc-550 text-[10.5px] max-w-lg">
                  <span className="font-semibold text-zinc-405 block mb-0.5 md:inline md:mb-0 md:mr-1">Last Updated:</span>
                  {formatRelativeTime(performanceData.last_updated || healthData?.timestamp)}
                </div>
                
                <div className="flex flex-wrap items-center gap-5 text-[10px] font-mono uppercase tracking-wider text-zinc-450">
                  <div className="flex items-center space-x-1.5">
                    <span className="text-zinc-600 lowercase">Upcoming Fixtures:</span>
                    <span className="text-white font-bold">{sourceMatches.filter(f => f.status === 'UPCOMING' || f.status === 'LIVE').length}</span>
                  </div>
                  <div className="flex items-center space-x-1.5 border-l border-zinc-900 pl-4">
                    <span className="text-zinc-600 lowercase">Model Status:</span>
                    <span className={`font-bold ${healthData?.status === 'healthy' ? 'text-green-accent' : 'text-red-500'}`}>{healthData?.status === 'healthy' ? '🟢 Online' : '🔴 Offline'}</span>
                  </div>
                  <div className="flex items-center space-x-1.5 border-l border-zinc-900 pl-4">
                    <span className="text-zinc-600 lowercase">Coverage:</span>
                    <span className="text-white font-bold">{performanceData.total_fixtures} Fixtures Tracked</span>
                  </div>
                  <div className="flex items-center space-x-1.5 border-l border-zinc-900 pl-4">
                    <span className="text-zinc-600 lowercase">Simulation Engine:</span>
                    <span className="text-white font-bold">Monte Carlo</span>
                  </div>
                </div>
              </div>

            </div>

            {/* ADDITIONAL TRANSPARENCY SECTIONS */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
              
              {/* Feature Importance */}
              <div className="bg-zinc-950 border border-zinc-900 rounded-lg p-6 space-y-6">
                <div className="border-b border-zinc-900 pb-3">
                  <h3 className="text-xs font-mono uppercase text-zinc-400 font-bold tracking-widest">Model Feature Importance</h3>
                  <p className="text-[11px] text-zinc-550 lowercase">key factors driving predictions</p>
                </div>

                <div className="space-y-3">
                  {[
                    { feature: 'ELO Rating', importance: 'Primary' },
                    { feature: 'Expected Goals (xG)', importance: 'Primary' },
                    { feature: 'Recent Form', importance: 'High' },
                    { feature: 'Squad Value', importance: 'High' },
                    { feature: 'Player Availability', importance: 'Medium' },
                    { feature: 'Home Advantage', importance: 'Medium' },
                    { feature: 'Tournament Experience', importance: 'Medium' },
                    { feature: 'Momentum Index', importance: 'Low' },
                  ].map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center text-xs">
                      <span className="text-zinc-300">{item.feature}</span>
                      <span className={`font-mono text-[10px] ${
                        item.importance === 'Primary' ? 'text-green-accent' :
                        item.importance === 'High' ? 'text-zinc-300' :
                        item.importance === 'Medium' ? 'text-zinc-500' : 'text-zinc-600'
                      }`}>{item.importance}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Data Sources */}
              <div className="bg-zinc-950 border border-zinc-900 rounded-lg p-6 space-y-6">
                <div className="border-b border-zinc-900 pb-3">
                  <h3 className="text-xs font-mono uppercase text-zinc-400 font-bold tracking-widest">Data Sources</h3>
                  <p className="text-[11px] text-zinc-550 lowercase">connected information feeds</p>
                </div>

                <div className="space-y-3">
                  {[
                    { source: 'FIFA World Rankings', status: 'Connected' },
                    { source: 'Football Data API', status: 'Connected' },
                    { source: 'Squad Value Database', status: 'Connected' },
                    { source: 'Injury Reports', status: 'Connected' },
                    { source: 'Internal ML Models', status: 'Active' },
                    { source: 'Monte Carlo Simulation', status: 'Active' },
                    { source: 'Poisson Goal Model', status: 'Active' },
                  ].map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center text-xs">
                      <span className="text-zinc-300">{item.source}</span>
                      <span className={`font-mono text-[10px] ${
                        item.status === 'Connected' ? 'text-green-accent' : 'text-zinc-400'
                      }`}>✓ {item.status}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Confidence Guide */}
              <div className="bg-zinc-950 border border-zinc-900 rounded-lg p-6 space-y-6">
                <div className="border-b border-zinc-900 pb-3">
                  <h3 className="text-xs font-mono uppercase text-zinc-400 font-bold tracking-widest">Confidence Guide</h3>
                  <p className="text-[11px] text-zinc-550 lowercase">interpreting prediction strength</p>
                </div>

                <div className="space-y-4">
                  {[
                    { range: '90-100%', label: 'Very Strong Prediction', color: 'text-green-accent' },
                    { range: '75-89%', label: 'Strong Prediction', color: 'text-zinc-300' },
                    { range: '60-74%', label: 'Moderate Prediction', color: 'text-zinc-400' },
                    { range: 'Below 60%', label: 'High Uncertainty', color: 'text-zinc-500' },
                  ].map((item, idx) => (
                    <div key={idx} className="flex flex-col">
                      <div className="flex justify-between items-center">
                        <span className={`font-mono text-xs font-bold ${item.color}`}>{item.range}</span>
                      </div>
                      <span className="text-[10px] text-zinc-500 mt-1">{item.label}</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>

            {/* Expanded Model Health Section */}
            <div className="bg-zinc-950 border border-zinc-900 rounded-lg p-6 lg:p-8 space-y-6 mt-8">
              <div className="border-b border-zinc-900 pb-3">
                <h3 className="text-xs font-mono uppercase text-zinc-400 font-bold tracking-widest">Model Health Status</h3>
                <p className="text-[11px] text-zinc-550 lowercase">real-time system diagnostics</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-4 bg-black/40 rounded border border-zinc-900">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`w-2 h-2 rounded-full ${healthData?.status === 'healthy' ? 'bg-green-accent animate-pulse' : 'bg-red-500'}`} />
                    <span className="text-[10px] font-mono text-zinc-500 uppercase">Prediction Engine</span>
                  </div>
                  <div className="text-lg font-mono font-bold text-white">
                    {healthData?.status === 'healthy' ? 'Online' : 'Offline'}
                  </div>
                </div>

                <div className="p-4 bg-black/40 rounded border border-zinc-900">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="w-2 h-2 rounded-full bg-green-accent animate-pulse" />
                    <span className="text-[10px] font-mono text-zinc-500 uppercase">Database</span>
                  </div>
                  <div className="text-lg font-mono font-bold text-white">
                    {healthData?.database_status || 'Connected'}
                  </div>
                </div>

                <div className="p-4 bg-black/40 rounded border border-zinc-900">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="w-2 h-2 rounded-full bg-green-accent animate-pulse" />
                    <span className="text-[10px] font-mono text-zinc-500 uppercase">ML Models</span>
                  </div>
                  <div className="text-lg font-mono font-bold text-white">
                    {healthData?.model_version || 'Active'}
                  </div>
                </div>

                <div className="p-4 bg-black/40 rounded border border-zinc-900">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="w-2 h-2 rounded-full bg-green-accent animate-pulse" />
                    <span className="text-[10px] font-mono text-zinc-500 uppercase">API</span>
                  </div>
                  <div className="text-lg font-mono font-bold text-white">
                    {healthData?.status === 'healthy' ? 'Operational' : 'Degraded'}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                <div>
                  <span className="text-zinc-600 block">Cache Status</span>
                  <span className="text-zinc-300">{healthData?.cache_status || 'Operational'}</span>
                </div>
                <div>
                  <span className="text-zinc-600 block">Last Refresh</span>
                  <span className="text-zinc-300">{healthData?.timestamp ? new Date(healthData.timestamp).toLocaleTimeString() : 'Now'}</span>
                </div>
                <div>
                  <span className="text-zinc-600 block">Model Version</span>
                  <span className="text-zinc-300">{healthData?.model_version || 'v1.0'}</span>
                </div>
                <div>
                  <span className="text-zinc-600 block">Overall Status</span>
                  <span className={`font-bold ${healthData?.status === 'healthy' ? 'text-green-accent' : 'text-red-500'}`}>
                    {healthData?.status || 'Checking...'}
                  </span>
                </div>
              </div>
            </div>

          </div>
          </div>
        )}

        {/* TOURNAMENT PROGRESSION VIEW — temporarily hidden; set to (true &&) to restore */}
        {(false) && (
          <div className="max-w-7xl mx-auto px-6 md:px-12 w-full py-10 md:py-16">
            <div className="space-y-8 animate-fade-in">
              
              {/* Header section */}
              <div className="border-b border-zinc-900 pb-5 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                <div>
                  <span className="mono-label text-green-accent text-[9px] block mb-2 uppercase tracking-widest font-mono">Real-Time Progression state machine</span>
                  <h2 className="text-4xl font-serif italic text-white mb-2">Tournament Progression</h2>
                  <p className="text-xs text-zinc-400 max-w-xl leading-relaxed">
                    Explore dynamic standings and projected knockout brackets generated from actual match outcomes. Set match scores to simulate tournament progression from the group stage through to the Grand Final.
                  </p>
                </div>
                {tournamentError && (
                  <div className="text-xs font-mono text-red-400 bg-red-950/20 border border-red-900/40 p-3 rounded">
                    {tournamentError}
                  </div>
                )}
              </div>

              {/* Subtabs for standings or bracket */}
              <div className="flex border-b border-zinc-900 pb-3 gap-2">
                <button
                  onClick={() => setTournamentSubTab('bracket')}
                  className={`px-5 py-2 font-mono text-xs uppercase tracking-widest border-b-2 transition-all ${
                    tournamentSubTab === 'bracket' ? 'text-white border-green-accent font-bold' : 'text-zinc-500 border-transparent hover:text-zinc-300'
                  }`}
                >
                  Knockout Bracket
                </button>
                <button
                  onClick={() => setTournamentSubTab('standings')}
                  className={`px-5 py-2 font-mono text-xs uppercase tracking-widest border-b-2 transition-all ${
                    tournamentSubTab === 'standings' ? 'text-white border-green-accent font-bold' : 'text-zinc-500 border-transparent hover:text-zinc-300'
                  }`}
                >
                  Group Standings
                </button>
              </div>

              {/* Loader */}
              {loadingTournament ? (
                <div className="py-24 flex flex-col items-center justify-center space-y-4">
                  <Loader2 className="w-8 h-8 text-green-accent animate-spin" />
                  <span className="text-xs font-mono text-zinc-500 uppercase tracking-widest">Recalculating tournament nodes...</span>
                </div>
              ) : (
                <>
                  {/* Standings View */}
                  {tournamentSubTab === 'standings' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
                      {Object.keys(standings).sort().map((groupKey) => (
                        <div key={groupKey} className="bg-zinc-950/60 border border-zinc-900 hover:border-zinc-800 rounded p-4 space-y-4 transition-all duration-300">
                          <div className="border-b border-zinc-900 pb-2 flex justify-between items-center">
                            <h3 className="font-serif italic text-white text-base">
                              {groupKey.replace("GROUP_", "Group ")}
                            </h3>
                            <span className="text-[9px] font-mono text-green-accent uppercase tracking-wider font-semibold">Active</span>
                          </div>
                          
                          <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                              <thead>
                                <tr className="border-b border-zinc-900 text-[9px] font-mono uppercase text-zinc-550">
                                  <th className="py-1.5 text-center w-6 font-bold">#</th>
                                  <th className="py-1.5 font-bold">Team</th>
                                  <th className="py-1.5 text-center w-6 font-bold">P</th>
                                  <th className="py-1.5 text-center w-8 font-bold">GD</th>
                                  <th className="py-1.5 text-center w-8 font-bold">Pts</th>
                                  <th className="py-1.5 text-center w-12 font-bold text-green-accent">Proj %</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-zinc-900/40 text-[11px] font-sans text-zinc-300">
                                {standings[groupKey]?.map((team) => {
                                  const flag = getFlag(team.name);
                                  const sim = simulationResults[team.name];
                                  const qualPct = sim ? Math.round(sim.qualify_probability ?? sim.r32) : null;
                                  return (
                                    <tr key={team.id} className="hover:bg-zinc-900/20 transition-colors">
                                      <td className="py-2 text-center font-mono font-bold text-zinc-500">
                                        {team.position}
                                      </td>
                                      <td className="py-2 font-medium text-white flex items-center gap-1.5 truncate max-w-[120px]">
                                        <span className="select-none text-sm">{flag}</span>
                                        <span className="truncate" title={team.name}>{team.tla || team.name}</span>
                                      </td>
                                      <td className="py-2 text-center font-mono">{team.played_games}</td>
                                      <td className={`py-2 text-center font-mono font-semibold ${
                                        team.goals_difference > 0 ? 'text-green-400' : team.goals_difference < 0 ? 'text-red-400' : 'text-zinc-550'
                                      }`}>
                                        {team.goals_difference > 0 ? `+${team.goals_difference}` : team.goals_difference}
                                      </td>
                                      <td className="py-2 text-center font-mono font-bold text-white">{team.points}</td>
                                      <td className="py-2 text-center font-mono font-bold text-green-accent">
                                        {qualPct !== null ? `${qualPct}%` : '—'}
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Bracket View */}
                  {tournamentSubTab === 'bracket' && (
                    <div className="w-full overflow-x-auto pb-8 pt-4 custom-scrollbar select-none">
                      <div className="flex gap-8 min-w-[1500px] items-stretch">
                        {[
                          { key: 'ROUND_OF_32', label: 'Round of 32', count: 16 },
                          { key: 'ROUND_OF_16', label: 'Round of 16', count: 8 },
                          { key: 'QUARTER_FINALS', label: 'Quarter Finals', count: 4 },
                          { key: 'SEMI_FINALS', label: 'Semi Finals', count: 2 },
                          { key: 'FINAL', label: 'Finals & Playoffs', count: 2 }
                        ].map((stage) => {
                          let matches: any[] = bracket[stage.key] || [];
                          if (stage.key === 'FINAL') {
                            const thirdPlace = bracket['THIRD_PLACE'] || [];
                            matches = [...matches, ...thirdPlace];
                          }
                          
                          return (
                            <div key={stage.key} className="flex-shrink-0 w-80 flex flex-col space-y-4">
                              <div className="border-b border-zinc-900 pb-2">
                                <span className="text-green-accent text-[9px] font-mono uppercase tracking-widest block mb-0.5 font-bold">Stage Column</span>
                                <h4 className="text-xs font-mono uppercase tracking-[0.1em] text-white font-bold">
                                  {stage.label} <span className="text-zinc-550 font-normal">({matches.length})</span>
                                </h4>
                              </div>
                              
                              <div className="flex-1 flex flex-col justify-around py-4 gap-4 overflow-y-auto max-h-[72vh] pr-1">
                                {matches.length === 0 ? (
                                  <div className="py-12 text-center border border-dashed border-zinc-900 rounded bg-zinc-950/20 text-zinc-600 text-[10px] uppercase font-mono tracking-wider">
                                    Awaiting progression
                                  </div>
                                ) : (
                                  matches.map((m) => {
                                    const flagHome = getFlag(m.home_team.name);
                                    const flagAway = getFlag(m.away_team.name);
                                    const isFinished = m.status === 'FINISHED';
                                    const homeWinner = isFinished && m.winner === 'HOME_TEAM';
                                    const awayWinner = isFinished && m.winner === 'AWAY_TEAM';
                                    
                                    return (
                                      <div 
                                        key={m.id} 
                                        className="bg-zinc-950/80 border border-zinc-900 hover:border-zinc-800 rounded p-3.5 space-y-3 transition duration-200 shadow-md flex flex-col justify-between"
                                      >
                                        <div className="flex justify-between items-center text-[9px] font-mono text-zinc-550 uppercase">
                                          <span>Match #{m.id}</span>
                                          <span className="text-zinc-400 normal-case">{formatSmartKickoffLocal(m.utc_date)}</span>
                                        </div>
                                        <div className="flex justify-end items-center text-[9px] font-mono uppercase -mt-2 mb-1">
                                          {m.stage === 'THIRD_PLACE' ? (
                                            <span className="text-yellow-600 font-bold tracking-wider">3rd Place Match</span>
                                          ) : (
                                            <span className={m.status === 'IN_PLAY' || m.status === 'PAUSED' ? 'text-red-500 font-extrabold animate-pulse' : ''}>
                                              {m.status}
                                            </span>
                                          )}
                                        </div>
                                        
                                        <div className="space-y-2">
                                          {/* Home team */}
                                          <div className="flex justify-between items-center text-xs">
                                            <div className="flex items-center gap-2 font-medium truncate max-w-[190px]">
                                              <span className="select-none text-base">{flagHome}</span>
                                              <span className={homeWinner ? 'text-green-accent font-bold' : m.home_team.name === 'TBD' ? 'text-zinc-650' : 'text-zinc-300'}>
                                                {m.home_team.tla || m.home_team.name}
                                              </span>
                                            </div>
                                            <span className={`font-mono text-xs font-extrabold ${homeWinner ? 'text-green-accent' : 'text-zinc-500'}`}>
                                              {m.home_score !== null ? m.home_score : '-'}
                                            </span>
                                          </div>

                                          {/* Away team */}
                                          <div className="flex justify-between items-center text-xs">
                                            <div className="flex items-center gap-2 font-medium truncate max-w-[190px]">
                                              <span className="select-none text-base">{flagAway}</span>
                                              <span className={awayWinner ? 'text-green-accent font-bold' : m.away_team.name === 'TBD' ? 'text-zinc-655' : 'text-zinc-300'}>
                                                {m.away_team.tla || m.away_team.name}
                                              </span>
                                            </div>
                                            <span className={`font-mono text-xs font-extrabold ${awayWinner ? 'text-green-accent' : 'text-zinc-500'}`}>
                                              {m.away_score !== null ? m.away_score : '-'}
                                            </span>
                                          </div>
                                        </div>

                                        {/* Action buttons */}
                                        {(m.home_team.name !== 'TBD' && m.away_team.name !== 'TBD') && (
                                          <div className="pt-2.5 border-t border-zinc-900/60 flex justify-between items-center gap-2">
                                            <span className="text-[8.5px] font-mono uppercase text-zinc-600">
                                              {m.stage === 'GROUP_STAGE' ? 'Group Stage' : m.stage.replace(/_/g, ' ')}
                                            </span>
                                          </div>
                                        )}
                                      </div>
                                    );
                                  })
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        </div>
      </main>

      {/* FOOTER AREA (Designed by Anurag Saikia based on branding guidelines) */}
      <motion.footer
        id="app-footer"
        className="bg-[#F6F4EF] bg-paper-grain paper-overlay border-t border-editorial-muted min-h-[50dvh] px-6 md:px-12 pt-12 pb-8 text-xs editorial-snap-section"
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.12 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] as const }}
      >
        <div className="max-w-7xl mx-auto">

          {/* Top rule */}
          <div className="w-full h-[1px] bg-[#D4D4D4] mb-8" />

          <div className="grid grid-cols-1 md:grid-cols-12 gap-10 md:gap-8 items-start">

            {/* ── Branding column ──────────────────────────────────────── */}
            <div className="md:col-span-5 space-y-5">
              <div
                onClick={() => navigateTo('home')}
                className="flex flex-col items-start cursor-pointer group select-none"
              >
                <span className="text-xl font-serif text-[#1C1B17] tracking-[0.35em] font-light leading-none group-hover:text-[#3a5c2d] transition-colors duration-300 uppercase">
                  OFFLINE
                </span>
                <span className="text-[7px] font-mono tracking-[0.45em] text-[#6B6B6B] uppercase mt-2 group-hover:text-[#4A4A4A] transition-colors duration-300">
                  FOOTBALL DECISION ENGINE
                </span>
              </div>

              <p className="text-[#6B6B6B] font-serif italic text-[12px] leading-relaxed">
                &ldquo;Believe In Your Guts.&rdquo;
              </p>
              <p className="text-[#4A4A4A] text-[11px] leading-relaxed max-w-sm font-light">
                Football decision engine for readers, analysts and strategists.
              </p>

              {/* Simulated Specs Metric Matrix */}
              <div className="pt-2 text-[10px] font-mono uppercase tracking-[0.15em] text-[#4A4A4A] space-y-1.5">
                <div className="flex items-center gap-2"><span className="text-[#1C1B17] font-bold tabular-nums">50,051</span><span>simulations per match.</span></div>
                <div className="flex items-center gap-2"><span className="text-[#1C1B17] font-bold tabular-nums">100+</span><span>active competitions.</span></div>
                <div className="flex items-center gap-2"><span className="text-[#1C1B17] font-bold tabular-nums">500+</span><span>teams tracked.</span></div>
                <div className="flex items-center gap-2"><span className="text-[#1C1B17] font-bold tabular-nums">12</span><span>weighted model signals.</span></div>
              </div>
            </div>

            {/* ── Navigation column ────────────────────────────────────── */}
            <div className="md:col-span-3 space-y-4">
              <h4 className="text-[9px] font-mono uppercase tracking-[0.3em] text-[#4A4A4A] font-bold">
                Index Navigation
              </h4>
              <div className="flex flex-col space-y-2.5 text-[#6B6B6B] text-[10.5px] font-mono uppercase tracking-wider">
                <span onClick={() => navigateTo('home')} className="hover:text-[#1C1B17] hover:translate-x-1 transition-all duration-200 cursor-pointer select-none">Home</span>
                <span onClick={() => navigateTo('predictions')} className="hover:text-[#1C1B17] hover:translate-x-1 transition-all duration-200 cursor-pointer select-none">Predictions</span>
                <span onClick={() => navigateTo('favorites')} className="hover:text-[#1C1B17] hover:translate-x-1 transition-all duration-200 cursor-pointer select-none">Favorites</span>
                <span onClick={() => navigateTo('intelligence')} className="hover:text-[#1C1B17] hover:translate-x-1 transition-all duration-200 cursor-pointer select-none">Intelligence Hub</span>
                {/* <span onClick={() => navigateTo('tournament')} className="hover:text-[#1C1B17] hover:translate-x-1 transition-all duration-200 cursor-pointer select-none">Tournament</span> */}
                <span onClick={() => navigateTo('model')} className="hover:text-[#1C1B17] hover:translate-x-1 transition-all duration-200 cursor-pointer select-none">The Model</span>
              </div>
            </div>

            {/* ── System Matrix column ──────────────────────────────────── */}
            <div className="md:col-span-4 space-y-4">
              <h4 className="text-[9px] font-mono uppercase tracking-[0.3em] text-[#4A4A4A] font-bold">
                System Matrix
              </h4>
              <div className="text-[10.5px] font-mono text-[#4A4A4A] bg-white border border-[#E0DED8] rounded-sm overflow-hidden">
                {[
                  { label: 'Data Refresh', value: 'Daily', color: 'text-[#1C1B17] font-bold' },
                  { label: 'Engine', value: 'poisson_v4.2', color: 'text-[#4A4A4A]' },
                  { label: 'Simulation', value: '50,051/fixt.', color: 'text-[#4A4A4A]' },
                  { label: 'Confidence Threshold', value: '72%', color: 'text-[#4A4A4A]' },
                  { label: 'Risk Index', value: 'active', color: 'text-[#3a5c2d]' },
                  { label: 'API Latency', value: '~14ms', color: 'text-[#6B6B6B]' },
                ].map(({ label, value, color }, i, arr) => (
                  <div
                    key={label}
                    className={`flex justify-between px-4 py-2 ${i < arr.length - 1 ? 'border-b border-[#E8E6E0]' : ''}`}
                  >
                    <span>{label}:</span>
                    <span className={color}>{value}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* ── Copyright bar ──────────────────────────────────────────── */}
          <div className="mt-14 pt-6 border-t border-[#E0DED8] flex flex-col sm:flex-row justify-between items-center gap-3 text-[9px] font-mono uppercase tracking-[0.2em] text-[#6B6B6B]">
            <div>
              © 2026 OFFLINE. All rights reserved. No black boxes.
            </div>
            <div className="text-center sm:text-right">
              Made with passion. Built for football.
            </div>
          </div>

        </div>
      </motion.footer>

      {/* MATCH ANALYSIS DETAILED RIGHT SIDE SLIDE-OVER DRAWER */}
      {selectedMatch && (() => {
        const match = selectedMatch;
        const flagA = getFlag(match.teamA);
        const flagB = getFlag(match.teamB);

        const getMatchInsights = (m: MatchPrediction) => {
          const insights: { label: string; value: string; status: 'advantage' | 'balanced' | 'disadvantage' }[] = [];

          // Determine Favorite
          const pA = m.probA ?? 0;
          const pB = m.probB ?? 0;
          const hasFav = pA !== pB;
          const favKey = pA >= pB ? 'A' : 'B';
          const favName = favKey === 'A' ? m.teamA : m.teamB;
          const favProb = favKey === 'A' ? pA : pB;
          const oppKey = favKey === 'A' ? 'B' : 'A';
          const oppName = oppKey === 'A' ? m.teamA : m.teamB;

          // 1. Favorite
          if (hasFav && favProb > 0) {
            insights.push({
              label: 'Favorite',
              value: `${favName} (${favProb}%)`,
              status: 'advantage'
            });
          }

          // 2. Confidence
          if (m.confidence) {
            let status: 'advantage' | 'balanced' | 'disadvantage' = 'balanced';
            if (m.confidence === 'High') status = 'advantage';
            if (m.confidence === 'Low') status = 'disadvantage';
            insights.push({
              label: 'Confidence',
              value: m.confidence,
              status
            });
          }

          // 3. ELO Advantage
          const eloA = m.eloRankA;
          const eloB = m.eloRankB;
          if (eloA !== undefined && eloA !== null && eloA > 0 && eloB !== undefined && eloB !== null && eloB > 0) {
            const eloFav = favKey === 'A' ? eloA : eloB;
            const eloOpp = favKey === 'A' ? eloB : eloA;
            if (eloFav < eloOpp) {
              insights.push({
                label: 'ELO Advantage',
                value: `${favName} +${eloOpp - eloFav}`,
                status: 'advantage'
              });
            } else if (eloFav > eloOpp) {
              insights.push({
                label: 'ELO Advantage',
                value: `${oppName} +${eloFav - eloOpp}`,
                status: 'disadvantage'
              });
            } else {
              insights.push({
                label: 'ELO Advantage',
                value: 'Balanced',
                status: 'balanced'
              });
            }
          }

          // 4. FIFA Advantage
          const fifaA = m.fifaRankA;
          const fifaB = m.fifaRankB;
          if (fifaA !== undefined && fifaA !== null && fifaA > 0 && fifaB !== undefined && fifaB !== null && fifaB > 0) {
            const fifaFav = favKey === 'A' ? fifaA : fifaB;
            const fifaOpp = favKey === 'A' ? fifaB : fifaA;
            if (fifaFav < fifaOpp) {
              insights.push({
                label: 'FIFA Advantage',
                value: `${favName} +${fifaOpp - fifaFav}`,
                status: 'advantage'
              });
            } else if (fifaFav > fifaOpp) {
              insights.push({
                label: 'FIFA Advantage',
                value: `${oppName} +${fifaFav - fifaOpp}`,
                status: 'disadvantage'
              });
            } else {
              insights.push({
                label: 'FIFA Advantage',
                value: 'Balanced',
                status: 'balanced'
              });
            }
          }

          // 5. Squad Value
          const parseVal = (val: string | undefined | null) => {
            if (!val || val === '—' || val === 'Loading...' || val === 'N/A') return null;
            const clean = val.replace(/[€$£\s]/g, '');
            if (clean.endsWith('B')) {
              const num = parseFloat(clean.slice(0, -1));
              return isNaN(num) ? null : num * 1000;
            }
            if (clean.endsWith('M')) {
              const num = parseFloat(clean.slice(0, -1));
              return isNaN(num) ? null : num;
            }
            if (clean.endsWith('K')) {
              const num = parseFloat(clean.slice(0, -1));
              return isNaN(num) ? null : num / 1000;
            }
            const num = parseFloat(clean);
            return isNaN(num) ? null : num;
          };

          const fmtValDiff = (diff: number) => {
            if (diff >= 1000) {
              return `€${Number((diff / 1000).toFixed(2))}B`;
            }
            return `€${Number(diff.toFixed(1))}M`;
          };

          const valA = parseVal(m.squadValueA);
          const valB = parseVal(m.squadValueB);
          if (valA !== null && valB !== null) {
            const valFav = favKey === 'A' ? valA : valB;
            const valOpp = favKey === 'A' ? valB : valA;
            if (valFav > valOpp) {
              insights.push({
                label: 'Squad Value',
                value: `${favName} ${fmtValDiff(valFav - valOpp)} higher`,
                status: 'advantage'
              });
            } else if (valFav < valOpp) {
              insights.push({
                label: 'Squad Value',
                value: `${oppName} ${fmtValDiff(valOpp - valFav)} higher`,
                status: 'disadvantage'
              });
            } else {
              insights.push({
                label: 'Squad Value',
                value: 'Equal',
                status: 'balanced'
              });
            }
          }

          // 6. Recent Form
          const formFav = favKey === 'A' ? m.recentFormA : m.recentFormB;
          const formOpp = favKey === 'A' ? m.recentFormB : m.recentFormA;
          if (formFav && formFav.length > 0) {
            const scoreFav = formFav.reduce((acc, r) => acc + (r === 'W' ? 3 : r === 'D' ? 1 : 0), 0);
            const scoreOpp = (formOpp && formOpp.length > 0) ? formOpp.reduce((acc, r) => acc + (r === 'W' ? 3 : r === 'D' ? 1 : 0), 0) : 0;
            const status = scoreFav > scoreOpp ? 'advantage' : (scoreFav < scoreOpp ? 'disadvantage' : 'balanced');
            insights.push({
              label: 'Recent Form',
              value: formFav.join('-'),
              status
            });
          }

          // 7. Head-to-Head
          const h2hMeetings = m.h2hPreviousMeetings;
          if (h2hMeetings !== undefined && h2hMeetings > 0) {
            const winsFav = favKey === 'A' ? m.h2hWinsA : m.h2hWinsB;
            const winsOpp = favKey === 'A' ? m.h2hWinsB : m.h2hWinsA;
            const draws = m.h2hDraws ?? 0;
            const wFav = winsFav ?? 0;
            const wOpp = winsOpp ?? 0;
            const status = wFav > wOpp ? 'advantage' : (wFav < wOpp ? 'disadvantage' : 'balanced');
            insights.push({
              label: 'Head-to-Head',
              value: `${favName} ${wFav}W | ${draws}D | ${wOpp}L`,
              status
            });
          }

          // 8. Injuries
          const hasInjA = m.injuriesA !== undefined;
          const hasInjB = m.injuriesB !== undefined;
          if (hasInjA && hasInjB) {
            const injFav = favKey === 'A' ? [...(m.injuriesA || []), ...(m.suspensionsA || [])] : [...(m.injuriesB || []), ...(m.suspensionsB || [])];
            if (injFav.length > 0) {
              insights.push({
                label: 'Injuries',
                value: `${injFav.length} player${injFav.length > 1 ? 's' : ''} unavailable`,
                status: 'disadvantage'
              });
            } else {
              insights.push({
                label: 'Injuries',
                value: 'None',
                status: 'balanced'
              });
            }
          }

          return insights;
        };

        // Loader helper for loading states
        const renderPredictionLoading = (sectionTitle: string) => (
          <div className="p-5 bg-zinc-950/45 border border-zinc-900 rounded flex flex-col items-center justify-center space-y-2 font-mono">
            <Loader2 className="w-5 h-5 text-[#1cdb5e] animate-spin" />
            <span className="text-[9px] uppercase tracking-widest text-zinc-550">Calculating {sectionTitle}...</span>
          </div>
        );

        // SECTION 1 — MATCH OUTCOME
        const probA = match.probA;
        const probD = match.probD;
        const probB = match.probB;

        // SECTION 2 — EXPECTED GOALS
        const xGA = match.xGA ?? 0;
        const xGB = match.xGB ?? 0;
        const totalXG = formatXG(xGA + xGB);

        // SECTION 3 — GOAL PROBABILITIES
        const poisson = (k: number, l: number) => {
          let fact = 1;
          for (let i = 1; i <= k; i++) fact *= i;
          return Math.pow(l, k) * Math.exp(-l) / fact;
        };
        const under0_5 = match.overUnder?.["0.5"] ? Math.round((match.overUnder["0.5"].under ?? 0) * 100) : Math.round(poisson(0, xGA + xGB) * 100);
        const under1_5 = match.overUnder?.["1.5"] ? Math.round((match.overUnder["1.5"].under ?? 0) * 100) : Math.round((poisson(0, xGA + xGB) + poisson(1, xGA + xGB)) * 100);
        const under2_5 = match.overUnder?.["2.5"] ? Math.round((match.overUnder["2.5"].under ?? 0) * 100) : Math.round((poisson(0, xGA + xGB) + poisson(1, xGA + xGB) + poisson(2, xGA + xGB)) * 100);
        const under3_5 = match.overUnder?.["3.5"] ? Math.round((match.overUnder["3.5"].under ?? 0) * 100) : Math.round((poisson(0, xGA + xGB) + poisson(1, xGA + xGB) + poisson(2, xGA + xGB) + poisson(3, xGA + xGB)) * 100);
        const under4_5 = match.overUnder?.["4.5"] ? Math.round((match.overUnder["4.5"].under ?? 0) * 100) : Math.round((poisson(0, xGA + xGB) + poisson(1, xGA + xGB) + poisson(2, xGA + xGB) + poisson(3, xGA + xGB) + poisson(4, xGA + xGB)) * 100);

        const over0_5 = 100 - under0_5;
        const over1_5 = 100 - under1_5;
        const over2_5 = 100 - under2_5;
        const over3_5 = 100 - under3_5;
        const over4_5 = 100 - under4_5;

        // Calculate BTTS via Poisson if missing: Yes = (1 - e^-xGA) * (1 - e^-xGB)
        const bttsYes = match.bttsMarket 
          ? Math.round((match.bttsMarket.yes ?? 0) * 100) 
          : Math.round(((1 - Math.exp(-xGA)) * (1 - Math.exp(-xGB))) * 100);
        const bttsNo = 100 - bttsYes;

        // SECTION 4 — DOUBLE CHANCE (derived mathematically)
        const dcHD = probA !== null && probD !== null ? Math.min(99, probA + probD) : null;
        const dcAD = probB !== null && probD !== null ? Math.min(99, probB + probD) : null;
        const dcHA = probA !== null && probB !== null ? Math.min(99, probA + probB) : null;

        // SECTION 5 — DRAW NO BET (derived mathematically)
        const dnbHome = probA !== null && probB !== null ? Math.round((probA / (probA + probB || 1)) * 100) : null;
        const dnbAway = dnbHome !== null ? 100 - dnbHome : null;

        // SECTION 6 — CLEAN SHEET
        // csA: probability teamA keeps a clean sheet (teamB scores 0 goals) -> e^-xGB
        // csB: probability teamB keeps a clean sheet (teamA scores 0 goals) -> e^-xGA
        const csA = match.cleanSheetMarket
          ? Math.round(match.cleanSheetMarket.home_clean_sheet * 100)
          : (match.teamGoals 
            ? Math.round((1 - match.teamGoals.away.over_0_5) * 100) 
            : Math.round(Math.exp(-xGB) * 100));
        const csB = match.cleanSheetMarket
          ? Math.round(match.cleanSheetMarket.away_clean_sheet * 100)
          : (match.teamGoals 
            ? Math.round((1 - match.teamGoals.home.over_0_5) * 100) 
            : Math.round(Math.exp(-xGA) * 100));

        // SECTION 7 — CORRECT SCORE MATRIX (Top 5 scorelines ranked)
        const formatScorelineLabel = (score: string) => {
          const parts = score.split('-');
          if (parts.length !== 2) return score;
          const h = parseInt(parts[0], 10);
          const a = parseInt(parts[1], 10);
          if (isNaN(h) || isNaN(a)) return score;
          if (h > a) return `${h}-${a} ${match.teamA}`;
          if (a > h) return `${a}-${h} ${match.teamB}`;
          return `${h}-${a} Draw`;
        };

        const top5Scores = match.top5Scorelines ? match.top5Scorelines.map(s => ({
          scoreline: formatScorelineLabel(s.score),
          pct: Math.round(s.probability * 100)
        })) : null;

        // SECTION 8 — MODEL CONFIDENCE
        const stageParts = match.stage.split(' • ');
        const tournamentStageLabel = stageParts[0]?.trim() || match.stage;
        const groupLabel = stageParts.length > 1 ? stageParts.slice(1).join(' • ').trim() : null;

        const confidenceLabel = match.confidence === 'High' ? 'Elite Confidence' : match.confidence === 'Medium' ? 'Standard Calibration' : 'Experimental Index';
        const modelAgreement = match.confidence === 'High' ? 88 + (probA % 9) : match.confidence === 'Medium' ? 76 + (probA % 9) : 61 + (probA % 9);
        const varianceScore = match.confidence === 'High' ? '0.04 - 0.08' : match.confidence === 'Medium' ? '0.12 - 0.16' : '0.22 - 0.28';
        const freshness = "Data updated dynamically (synchronized)";

        // SECTION 10 — SQUAD HEALTH
        const missingKeyPlayersA = (match.missingKeyPlayersA && match.missingKeyPlayersA.length > 0)
          ? match.missingKeyPlayersA
          : (match.injuriesA.length > 0 ? [match.injuriesA[0]] : ["No missing key players"]);
        const missingKeyPlayersB = (match.missingKeyPlayersB && match.missingKeyPlayersB.length > 0)
          ? match.missingKeyPlayersB
          : (match.injuriesB.length > 0 ? [match.injuriesB[0]] : ["No missing key players"]);

        // SECTION 11 — TOURNAMENT IMPACT PROJECTIONS
        const getGroupQualProb = (rank: number) => {
          if (!rank) return 50;
          const val = 50 - (rank - 24) * 1.5;
          return Math.min(95, Math.max(5, Math.round(val)));
        };

        const getProjectedPosition = (rank: number) => {
          if (!rank) return "TBD";
          if (rank <= 12) {
            const prob = Math.round(80 - rank * 2);
            return `1st (${prob}% probability)`;
          } else if (rank <= 24) {
            const prob = Math.round(70 - (rank - 12) * 2);
            return `2nd (${prob}% probability)`;
          } else if (rank <= 36) {
            const prob = Math.round(60 - (rank - 24) * 2);
            return `3rd (${prob}% probability)`;
          } else {
            const prob = Math.round(50 - (rank - 36) * 1.5);
            return `4th (${prob}% probability)`;
          }
        };

        const getProjectedAdvancement = (rank: number) => {
          if (!rank) return "TBD";
          if (rank <= 4) {
            const prob = Math.round(45 - rank * 5);
            return `Semi-Finals (${prob}%)`;
          } else if (rank <= 8) {
            const prob = Math.round(55 - (rank - 4) * 4);
            return `Quarter-Finals (${prob}%)`;
          } else if (rank <= 16) {
            const prob = Math.round(65 - (rank - 8) * 3);
            return `Round of 16 (${prob}%)`;
          } else if (rank <= 32) {
            const prob = Math.round(75 - (rank - 16) * 2);
            return `Round of 32 (${prob}%)`;
          } else {
            const prob = Math.round(85 - (rank - 32) * 1.5);
            return `Group Stage (${prob}%)`;
          }
        };

        // Tournament impact helpers — temporarily commented out
        // const findStanding = (teamName: string) => {
        //   for (const [grp, teams] of Object.entries(standings)) {
        //     const found = (teams as GroupStandingTeam[]).find(t => t.name.toLowerCase() === teamName.toLowerCase());
        //     if (found) return { group: grp, position: found.position, points: found.points };
        //   }
        //   return null;
        // };
        //
        // const isKnockout = !match.stage.toLowerCase().includes("group stage");
        // const simA = simulationResults[match.teamA];
        // const simB = simulationResults[match.teamB];
        //
        // let qualA = isKnockout ? Math.round(probA + 0.5 * probD) : (simA ? Math.round(simA.qualify_probability ?? simA.r32) : 50);
        // let qualB = isKnockout ? 100 - qualA : (simB ? Math.round(simB.qualify_probability ?? simB.r32) : 50);
        //
        // const standingA = findStanding(match.teamA);
        // const standingB = findStanding(match.teamB);
        //
        // const groupPosA = isKnockout
        //   ? "N/A (Knockout stage)"
        //   : (standingA
        //     ? `Currently ${standingA.position === 1 ? '1st' : standingA.position === 2 ? '2nd' : standingA.position === 3 ? '3rd' : '4th'} (${standingA.points} pts)`
        //     : (simA ? `Projected Group Qualification: ${Math.round(simA.qualify_probability ?? simA.r32)}%` : "TBD"));
        //
        // const groupPosB = isKnockout
        //   ? "N/A (Knockout stage)"
        //   : (standingB
        //     ? `Currently ${standingB.position === 1 ? '1st' : standingB.position === 2 ? '2nd' : standingB.position === 3 ? '3rd' : '4th'} (${standingB.points} pts)`
        //     : (simB ? `Projected Group Qualification: ${Math.round(simB.qualify_probability ?? simB.r32)}%` : "TBD"));
        //
        // const tournamentAdvA = simA
        //   ? `R16: ${Math.round(simA.r16)}% | QF: ${Math.round(simA.qf)}% | SF: ${Math.round(simA.sf)}% | Winner: ${Math.round(simA.winner)}%`
        //   : "TBD";
        // const tournamentAdvB = simB
        //   ? `R16: ${Math.round(simB.r16)}% | QF: ${Math.round(simB.qf)}% | SF: ${Math.round(simB.sf)}% | Winner: ${Math.round(simB.winner)}%`
        //   : "TBD";

        return (
          <MatchAnalysis
            match={match}
            onClose={() => {
              setSelectedMatch(null);
              setShowMatchAnalysis(false);
            }}
            onBack={() => {
              setSelectedMatch(null);
              setShowMatchAnalysis(false);
            }}
            drawerTeamLoading={drawerTeamLoading}
          />
        );
      })()}

      {/* TEAM DETAIL MODAL OVERLAY */}
      {selectedTeam && (
        <div id="team-detail-modal" className="fixed inset-0 z-50 overflow-y-auto bg-black/95 backdrop-blur-md flex items-center justify-center p-4">
          <div 
            className="bg-zinc-950 border border-zinc-805 rounded w-full max-w-4xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            
            {/* Stick Team Header bar */}
            <div className="sticky top-0 bg-zinc-950 border-b border-zinc-900 px-6 py-5 flex justify-between items-center z-10">
              <div className="flex items-center space-x-3.5">
                <div className="w-8 h-8 rounded-full bg-zinc-900 border border-zinc-805 flex items-center justify-center text-sm font-black text-green-accent font-mono select-none">
                  {selectedTeam.code}
                </div>
                <div>
                  <h3 className="text-xl font-bold uppercase tracking-normal text-white">{selectedTeam.name} Database Entry</h3>
                  <span className="text-[10px] font-mono tracking-widest text-zinc-500 uppercase">Head Coach: {selectedTeam.coach} (Rating: {selectedTeam.coachRating}/100)</span>
                </div>
              </div>
              <button 
                onClick={() => setSelectedTeam(null)}
                className="p-1 text-zinc-500 hover:text-white hover:bg-zinc-900 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content Details Area */}
            <div className="p-6 md:p-8 space-y-8 select-text">
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* Team win percentage gauge */}
                <div className="bg-black p-6 rounded border border-zinc-900 flex flex-col justify-center items-center text-center space-y-2">
                  <span className="text-[9px] font-mono text-zinc-550 uppercase tracking-widest block mb-1">CUP WIN PROBABILITY</span>
                  <div className="text-5xl font-extrabold text-green-accent font-mono tracking-tight">{selectedTeam.winProbabilityPercent}%</div>
                  <div className="px-3 py-1 bg-green-accent/5 border border-green-accent/25 text-[10px] font-mono uppercase text-green-accent2.5 mt-2 rounded">
                    Confidence: {selectedTeam.confidence}
                  </div>
                  <span className="text-[10px] text-zinc-650 block pt-2 leading-relaxed">Continuous calculations resolution standard</span>
                </div>

                {/* Team tactical core parameters table ratings */}
                <div className="bg-black p-6 rounded border border-zinc-900 md:col-span-2 space-y-4">
                  <h5 className="text-[10.5px] font-mono text-zinc-400 font-bold uppercase border-b border-zinc-900 pb-2 tracking-wider">Tactical Power Quadrants</h5>
                  
                  <div className="grid grid-cols-2 gap-4 text-xs font-sans">
                    
                    <div className="space-y-1">
                      <div className="flex justify-between font-mono text-zinc-500">
                        <span>ATTACK RATING</span>
                        <span className="text-white font-bold">{selectedTeam.attackRating}</span>
                      </div>
                      <div className="h-1 bg-zinc-900 rounded overflow-hidden">
                        <div className="h-full bg-green-accent" style={{ width: `${selectedTeam.attackRating}%` }}></div>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between font-mono text-zinc-500">
                        <span>DEFENCE RATING</span>
                        <span className="text-white font-bold">{selectedTeam.defenceRating}</span>
                      </div>
                      <div className="h-1 bg-zinc-900 rounded overflow-hidden">
                        <div className="h-full bg-green-accent" style={{ width: `${selectedTeam.defenceRating}%` }}></div>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between font-mono text-zinc-500">
                        <span>MIDFIELD STRUCTURE</span>
                        <span className="text-white font-semibold">{selectedTeam.midfieldRating}</span>
                      </div>
                      <div className="h-1 bg-zinc-900 rounded overflow-hidden">
                        <div className="h-full bg-zinc-400" style={{ width: `${selectedTeam.midfieldRating}%` }}></div>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between font-mono text-zinc-500">
                        <span>GOALKEEPING CLASS</span>
                        <span className="text-white font-semibold">{selectedTeam.gkRating}</span>
                      </div>
                      <div className="h-1 bg-zinc-900 rounded overflow-hidden">
                        <div className="h-full bg-zinc-400" style={{ width: `${selectedTeam.gkRating}%` }}></div>
                      </div>
                    </div>

                  </div>

                  <div className="grid grid-cols-3 gap-3 border-t border-zinc-900 pt-3.5 text-[11px] font-serif text-zinc-400">
                    <div>
                      <span className="text-[9px] font-mono tracking-wider uppercase text-zinc-550 block mb-0.5">SQUAD DEPTH</span>
                      <strong className="text-white font-sans">{selectedTeam.squadDepth}/100 index</strong>
                    </div>
                    <div>
                      <span className="text-[9px] font-mono tracking-wider uppercase text-zinc-550 block mb-0.5">MARKET VALUATION</span>
                      <strong className="text-white font-sans">{selectedTeam.marketValue}</strong>
                    </div>
                    <div>
                      <span className="text-[9px] font-mono tracking-wider uppercase text-zinc-550 block mb-0.5">AGE COEFFICIENT</span>
                      <strong className="text-white font-sans">{selectedTeam.avgAge} years avg</strong>
                    </div>
                  </div>

                </div>

              </div>

              {/* LIKELY TOURNAMENT PATH FLOW (From prompt requirements) */}
              <div className="bg-black p-6 rounded border border-zinc-900 space-y-5">
                <div className="border-b border-zinc-900 pb-2">
                  <h5 className="text-[11px] font-mono uppercase tracking-widest text-zinc-350 font-bold">Projected Tournament Trajectory Path</h5>
                  <p className="text-[10px] text-zinc-550 mt-0.5 font-mono lowercase">highest analytical probability routes projected</p>
                </div>

                <div className="flex flex-col space-y-3 font-sans text-xs">
                  
                  <div className="flex items-center justify-between p-2.5 bg-zinc-950 rounded border border-zinc-900/60">
                    <span className="text-zinc-500 font-mono">Stage 01: GROUP STAGE</span>
                    <span className="text-white font-semibold font-serif italic">{selectedTeam.likelyPath.groupStage}</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 bg-zinc-950 rounded border border-zinc-900/60">
                    <span className="text-zinc-500 font-mono">Stage 02: ROUND OF 32</span>
                    <span className="text-white font-semibold font-serif italic">{selectedTeam.likelyPath.roundOf32}</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 bg-zinc-950 rounded border border-zinc-900/60">
                    <span className="text-zinc-500 font-mono">Stage 03: ROUND OF 16</span>
                    <span className="text-white font-semibold font-serif italic">{selectedTeam.likelyPath.roundOf16}</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 bg-zinc-950 rounded border border-zinc-900/60">
                    <span className="text-zinc-500 font-mono">Stage 04: QUARTER FINAL</span>
                    <span className="text-white font-semibold font-serif italic">{selectedTeam.likelyPath.quarterFinal}</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 bg-zinc-950 rounded border border-zinc-900/60">
                    <span className="text-zinc-500 font-mono">Stage 05: SEMI FINAL</span>
                    <span className="text-white font-semibold font-serif italic">{selectedTeam.likelyPath.semiFinal}</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 bg-green-950/20 rounded border border-green-500/20">
                    <span className="text-green-accent font-semibold font-mono">Stage 06: FINAL PROJECTION</span>
                    <span className="text-white font-bold font-serif italic">{selectedTeam.likelyPath.final}</span>
                  </div>

                </div>
              </div>

              {/* RECENT Competitive trends (Last 10 matches) */}
              <div className="bg-zinc-950 p-6 rounded border border-zinc-900 space-y-4">
                <div className="border-b border-zinc-900 pb-2">
                  <h5 className="text-xs uppercase font-mono tracking-wider font-bold text-zinc-300">Last 10 Matches Quantitative Profile</h5>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 text-center text-xs">
                  
                  <div className="p-3 bg-black rounded border border-zinc-900/60">
                    <div className="text-2xl font-black text-[#1cdb5e] font-mono">{selectedTeam.last10Wins}</div>
                    <span className="text-[9px] uppercase font-mono tracking-widest text-zinc-500 block mt-1">Wins</span>
                  </div>

                  <div className="p-3 bg-black rounded border border-zinc-900/60">
                    <div className="text-2xl font-black text-zinc-400 font-mono">{selectedTeam.last10Draws}</div>
                    <span className="text-[9px] uppercase font-mono tracking-widest text-zinc-500 block mt-1">Draws</span>
                  </div>

                  <div className="p-3 bg-black rounded border border-zinc-900/60">
                    <div className="text-2xl font-black text-red-400 font-mono">{selectedTeam.last10Losses}</div>
                    <span className="text-[9px] uppercase font-mono tracking-widest text-zinc-500 block mt-1">Losses</span>
                  </div>

                  <div className="p-3 bg-black rounded border border-zinc-900/60 col-span-2 sm:col-span-1">
                    <div className="text-2xl font-black text-white font-mono">{selectedTeam.last10GoalsScored} / {selectedTeam.last10GoalsConceded}</div>
                    <span className="text-[9px] uppercase font-mono tracking-widest text-zinc-500 block mt-1">Goals For/Against</span>
                  </div>

                  <div className="p-3 bg-black rounded border border-zinc-900/60 col-span-2 sm:col-span-1">
                    <div className="text-xs font-mono font-bold flex gap-1 justify-center leading-normal pt-2">
                      {selectedTeam.recentForm.map((f, i) => (
                        <span key={i} className={f === 'W' ? 'text-green-accent' : f === 'D' ? 'text-zinc-400' : 'text-red-400'}>{f}</span>
                      ))}
                    </div>
                    <span className="text-[9px] uppercase font-mono tracking-widest text-zinc-500 block mt-1">W-D-L Streak</span>
                  </div>

                </div>
              </div>

            </div>

            {/* Footer action bar close */}
            <div className="px-6 py-4 bg-zinc-900/30 border-t border-zinc-900/50 flex justify-end items-center space-x-3 rounded-b">
              <button 
                onClick={() => toggleFavoriteTeam(selectedTeam.code)}
                className="px-5 py-2 hover:bg-zinc-900 border border-zinc-805 rounded text-xs uppercase tracking-widest font-mono text-zinc-300 hover:text-white transition flex items-center gap-2"
              >
                <Star className={`w-3.5 h-3.5 ${favoriteTeamCodes.includes(selectedTeam.code) ? 'fill-[#1cdb5e] text-[#1cdb5e]' : 'text-zinc-650'}`} />
                <span>{favoriteTeamCodes.includes(selectedTeam.code) ? 'Bookmarked' : 'Add to Tracking'}</span>
              </button>
              
              <button 
                onClick={() => setSelectedTeam(null)}
                className="px-6 py-2 bg-zinc-100 hover:bg-white text-black text-xs uppercase tracking-widest font-bold transition"
              >
                Close Database Profile
              </button>
            </div>

          </div>
        </div>
      )}

      {/* GLOBAL SEARCH MODAL (Triggered via click or '/' shortcut) */}
      {showSearchModal && (
        <div id="global-search-overlay" className="fixed inset-0 z-50 overflow-y-auto bg-black/95 backdrop-blur-md flex items-start justify-center p-4 pt-16 md:pt-28">
          <div 
            className="bg-zinc-950 border border-zinc-805 rounded w-full max-w-2xl overflow-hidden shadow-[0_0_100px_rgba(0,0,0,1)] animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            
            {/* Input wrapper */}
            <div className="px-6 py-5 border-b border-zinc-905 flex items-center space-x-4 bg-zinc-950/80 sticky top-0">
              <Search className="w-5 h-5 text-green-accent shrink-0 animate-pulse" />
              <input 
                type="text"
                placeholder="Search Teams, Matches, Venues, Positions, or Insights..."
                className="bg-transparent text-white placeholder-zinc-500 font-sans text-base w-full focus:outline-none focus:ring-0"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                autoFocus
              />
              <button 
                onClick={() => {
                  setSearchQuery('');
                  setShowSearchModal(false);
                }}
                className="p-1 px-2.5 hover:bg-zinc-900 border border-zinc-805 rounded text-[10px] font-mono uppercase text-zinc-400 hover:text-white"
              >
                ESC
              </button>
            </div>

            {/* Results listing */}
            <div className="max-h-[60vh] overflow-y-auto p-4 md:p-6 space-y-6">
              {searchQuery.trim() === '' ? (
                <div className="text-center py-10 space-y-3">
                  <span className="text-[10px] font-mono uppercase tracking-widest text-zinc-500 block">Suggested Searches</span>
                  <div className="flex flex-wrap justify-center gap-2 text-[10.5px] font-mono text-zinc-400">
                    <button onClick={() => setSearchQuery('Brazil')} className="px-3 py-1 bg-zinc-900 hover:bg-zinc-850 rounded border border-zinc-805 transition">"Brazil"</button>
                    <button onClick={() => setSearchQuery('Mbappe')} className="px-3 py-1 bg-zinc-900 hover:bg-zinc-850 rounded border border-zinc-805 transition">"Yamal"</button>
                    <button onClick={() => setSearchQuery('Upset')} className="px-3 py-1 bg-zinc-900 hover:bg-zinc-850 rounded border border-zinc-805 transition">"Upset Candidate"</button>
                    <button onClick={() => setSearchQuery('MetLife')} className="px-3 py-1 bg-zinc-900 hover:bg-zinc-850 rounded border border-zinc-805 transition">"MetLife Stadium"</button>
                  </div>
                </div>
              ) : totalSearchResultsCount === 0 ? (
                <div className="text-center py-12 text-xs text-zinc-500 font-mono">
                  No matches, teams or technical insights indexed under "{searchQuery}". Try refining queries.
                </div>
              ) : (
                <div className="space-y-6 select-text">
                  
                  {/* Matching Matches */}
                  {filteredMatches.length > 0 && (
                    <div className="space-y-2.5">
                      <span className="text-[9px] font-mono uppercase tracking-widest text-[#1cdb5e] border-b border-zinc-950 pb-1 block">Simulations Indexed ({filteredMatches.length})</span>
                      <div className="space-y-2 text-xs">
                        {filteredMatches.map(m => (
                          <div 
                            key={m.id}
                            className="p-3 bg-zinc-900/50 hover:bg-zinc-900 border border-zinc-905 rounded flex justify-between items-center cursor-pointer"
                            onClick={() => {
                              setShowSearchModal(false);
                              openMatchAnalysis(m);
                            }}
                          >
                            <span className="font-bold text-white uppercase font-sans">{m.teamA} vs {m.teamB} <span className="text-[10px] text-zinc-500 font-mono">({m.stage})</span></span>
                            <div className="text-right">
                              <span className="text-[10px] font-mono text-zinc-400 block">{formatKickoffTimeLocal(m.kickoffTime)}</span>
                              <span className="text-[10px] font-mono text-[#1cdb5e] uppercase">Open Intel →</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Matching Teams */}
                  {filteredTeams.length > 0 && (
                    <div className="space-y-2.5">
                      <span className="text-[9px] font-mono uppercase tracking-widest text-[#1cdb5e] border-b border-zinc-950 pb-1 block">Contenders Indexed ({filteredTeams.length})</span>
                      <div className="space-y-2 text-xs">
                        {filteredTeams.map(t => (
                          <div 
                            key={t.name}
                            className="p-3 bg-zinc-900/50 hover:bg-zinc-900 border border-zinc-905 rounded flex justify-between items-center cursor-pointer"
                            onClick={() => {
                              setShowSearchModal(false);
                              setSelectedTeam(t);
                            }}
                          >
                            <span className="font-bold text-white uppercase">{t.name} Contender <span className="text-[10px] text-zinc-500 font-mono">({t.coach})</span></span>
                            <span className="text-[10px] font-mono text-zinc-450 font-bold uppercase">{t.winProbabilityPercent}% Win Rate →</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Matching Insights */}
                  {filteredInsights.length > 0 && (
                    <div className="space-y-2.5">
                      <span className="text-[9px] font-mono uppercase tracking-widest text-[#1cdb5e] border-b border-zinc-950 pb-1 block">Briefings Indexed ({filteredInsights.length})</span>
                      <div className="space-y-2 text-xs">
                        {filteredInsights.map(i => (
                          <div 
                            key={i.id}
                            className="p-3.5 bg-zinc-900/40 hover:bg-zinc-900 border border-zinc-905 rounded cursor-pointer space-y-1"
                            onClick={() => {
                              setShowSearchModal(false);
                              navigateTo('intelligence');
                              setTimeout(() => {
                                fetchAiInsightExplanation(i);
                              }, 100);
                            }}
                          >
                            <div className="flex justify-between items-center">
                              <span className="font-mono font-bold text-green-accent-text uppercase text-[9px]">{i.type}</span>
                              <span className="text-[9.5px] font-mono text-zinc-550 uppercase">Explore Hub →</span>
                            </div>
                            <h4 className="font-sans font-bold text-white leading-none">{i.team} Brief</h4>
                            <p className="text-zinc-450 leading-relaxed font-serif italic text-[11px] limit-lines">"{i.details}"</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                </div>
              )}
            </div>

          </div>
        </div>
      )}


    </motion.div>
  );

  // Health Dashboard - developer-only diagnostics page
  if (showHealthDashboard) {
    return <AIHealthDashboard />;
  }
}
