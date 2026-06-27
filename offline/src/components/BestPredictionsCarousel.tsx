import { useCallback, useEffect, useRef, useState, type RefObject } from "react";
import { motion, type PanInfo } from "motion/react";
import { AlertCircle, ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import type { MatchPrediction } from "../types";
import { getFlag } from "../flagUtils";
import { formatSmartKickoffLocal } from "../dateTimeUtils";

const TRANSITION = { duration: 0.45, ease: [0.32, 0.72, 0, 1] as const };
const DRAG_THRESHOLD = 48;
const VELOCITY_THRESHOLD = 400;

// Skeleton loader for match cards
function MatchCardSkeleton() {
  return (
    <div className="bg-zinc-950 border border-zinc-900 rounded-lg px-7 py-6 flex flex-col justify-between min-h-[400px] h-full">
      <div className="flex flex-col gap-2.5 sm:flex-row sm:items-start sm:justify-between sm:gap-4 mb-1">
        <div className="flex flex-col items-start gap-1.5 min-w-0 flex-1">
          <div className="h-3 w-20 bg-zinc-900 rounded animate-pulse" />
          <div className="h-4 w-16 bg-zinc-900 rounded animate-pulse" />
        </div>
        <div className="h-4 w-24 bg-zinc-900 rounded animate-pulse shrink-0" />
      </div>

      <div className="flex-1 flex flex-col justify-center my-3 min-h-0 space-y-2.5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-zinc-900 rounded animate-pulse shrink-0" />
          <div className="h-6 w-32 bg-zinc-900 rounded animate-pulse" />
        </div>
        <div className="h-4 w-12 bg-zinc-900 rounded animate-pulse ml-11" />
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-zinc-900 rounded animate-pulse shrink-0" />
          <div className="h-6 w-32 bg-zinc-900 rounded animate-pulse" />
        </div>
      </div>

      <div className="space-y-3">
        <div className="h-2 w-full bg-zinc-900 rounded animate-pulse" />
        <div className="h-2 w-3/4 bg-zinc-900 rounded animate-pulse" />
        <div className="h-8 w-full bg-zinc-900 rounded animate-pulse mt-4" />
      </div>
    </div>
  );
}

function getLoopOffset(index: number, active: number, total: number): number {
  if (total <= 0) return 0;
  let diff = index - active;
  const half = total / 2;
  if (diff > half) diff -= total;
  if (diff < -half) diff += total;
  return diff;
}

function MatchTimeDisplay({ match }: { match: MatchPrediction }) {
  if (match.status === "LIVE") {
    return (
      <div className="flex items-center gap-1.5">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
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

  if (match.status === "COMPLETED") {
    return <span className="text-zinc-550 font-bold uppercase tracking-wider">FULL TIME</span>;
  }

  return (
    <span className="text-zinc-450">
      {formatSmartKickoffLocal(match.kickoffTime) || match.date}
    </span>
  );
}

interface PredictionCardProps {
  match: MatchPrediction;
  isActive: boolean;
  onViewAnalysis: (match: MatchPrediction) => void;
}

function PredictionCard({ match, isActive, onViewAnalysis }: PredictionCardProps) {
  const flagA = getFlag(match.teamA);
  const flagB = getFlag(match.teamB);

  return (
    <div
      className={`bg-zinc-950 border rounded-lg px-7 py-6 flex flex-col justify-between min-h-[400px] h-full transition-colors duration-300 ${
        isActive
          ? "border-zinc-700 shadow-[0_24px_80px_-20px_rgba(0,0,0,0.85)]"
          : "border-zinc-900 hover:border-zinc-800"
      }`}
    >
      {/* Header: stage + badge left, kickoff right — responsive, no overlap */}
      <div className="flex flex-col gap-2.5 sm:flex-row sm:items-start sm:justify-between sm:gap-4 mb-1 min-w-0">
        <div className="flex flex-col items-start gap-1.5 min-w-0 flex-1">
          <span className="text-[10px] font-mono text-zinc-500 tracking-wider uppercase leading-snug break-words">
            {match.stage}
          </span>
          {match.isLiveData ? (
            <span className="inline-flex shrink-0 text-green-accent text-[8px] bg-green-accent/10 border border-green-accent/25 px-2 py-0.5 rounded leading-none select-none tracking-widest uppercase font-bold">
              LIVE MODEL
            </span>
          ) : (
            <span className="inline-flex shrink-0 text-zinc-500 text-[8px] bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded leading-none select-none tracking-widest uppercase">
              LOCAL
            </span>
          )}
        </div>
        <div className="shrink-0 text-left sm:text-right min-w-[7.5rem] sm:min-w-[8.5rem] text-[10px] font-mono self-start sm:self-auto">
          <MatchTimeDisplay match={match} />
        </div>
      </div>

      <div className="flex-1 flex flex-col justify-center my-3 min-h-0">
        <div className="text-xl font-bold text-white uppercase tracking-normal space-y-2.5">
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-2xl leading-none select-none shrink-0">{flagA}</span>
            <span className="truncate leading-tight">{match.teamA}</span>
          </div>
          <div className="text-zinc-500 text-[10px] font-mono uppercase pl-11 font-medium">vs</div>
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-2xl leading-none select-none shrink-0">{flagB}</span>
            <span className="truncate leading-tight">{match.teamB}</span>
          </div>
        </div>

        {match.status === "LIVE" ? (
          <div className="mt-6 flex flex-col justify-center items-start gap-1.5">
            <span className="text-[9px] font-mono uppercase tracking-widest text-red-500 block animate-pulse font-bold">
              Live Score
            </span>
            <div className="flex items-center gap-3 text-3xl font-black text-white tracking-wider">
              <span>{match.liveScore?.home ?? 0}</span>
              <span className="text-zinc-700 font-light">—</span>
              <span>{match.liveScore?.away ?? 0}</span>
            </div>
          </div>
        ) : match.status === "COMPLETED" ? (
          (() => {
            const isCorrect =
              (match.prediction === `${match.teamA} Win` && match.winner === "HOME_TEAM") ||
              (match.prediction === `${match.teamB} Win` && match.winner === "AWAY_TEAM") ||
              (match.prediction === "Draw" && match.winner === "DRAW");
            return (
              <div className="mt-6 flex flex-col justify-center items-start gap-1.5">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[9px] font-mono uppercase tracking-widest text-zinc-500 block font-bold">
                    Final Score
                  </span>
                  <span
                    className={`text-[8.5px] font-mono font-bold px-1.5 py-0.5 rounded leading-none select-none tracking-widest uppercase ${
                      isCorrect
                        ? "text-green-accent bg-green-accent/15 border border-green-accent/25"
                        : "text-red-400 bg-red-950/20 border border-red-900/20"
                    }`}
                  >
                    {isCorrect ? "✓ Correct" : "✕ Miss"}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-3xl font-black text-white tracking-wider">
                  <span>{match.liveScore?.home ?? 0}</span>
                  <span className="text-zinc-700 font-light">—</span>
                  <span>{match.liveScore?.away ?? 0}</span>
                </div>
              </div>
            );
          })()
        ) : (
          <div className="mt-6 space-y-1.5">
            <span className="text-[9px] font-mono uppercase tracking-widest text-zinc-500 block">
              Assessment
            </span>
            <span className="text-white text-base font-medium tracking-normal leading-snug block">
              {match.prediction}
            </span>
          </div>
        )}
      </div>

      <div className="mt-auto pt-1">
        <div className="mb-4">
          <div className="flex justify-between items-center gap-2 text-[11px] font-mono text-zinc-400 mb-2 min-w-0">
            <span className="truncate font-semibold text-zinc-300">
              {match.teamACode} {match.probA}%
            </span>
            <span className="shrink-0 font-semibold text-zinc-400">Draw {match.probD}%</span>
            <span className="truncate font-semibold text-zinc-300 text-right">
              {match.teamBCode} {match.probB}%
            </span>
          </div>
          <div className="h-1.5 w-full bg-zinc-900 flex rounded overflow-hidden">
            <div className="h-full bg-green-accent" style={{ width: `${match.probA}%` }} />
            <div className="h-full bg-zinc-750" style={{ width: `${match.probD}%` }} />
            <div className="h-full bg-zinc-800" style={{ width: `${match.probB}%` }} />
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-zinc-900 gap-3">
          <span
            className={`text-[10px] font-mono uppercase tracking-widest font-bold shrink-0 ${
              match.confidence === "High" ? "text-green-accent" : "text-yellow-500"
            }`}
          >
            {match.confidence} Confidence
          </span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onViewAnalysis(match);
            }}
            onPointerDown={(e) => e.stopPropagation()}
            className="text-xs font-mono font-bold text-white hover:text-green-accent flex items-center gap-1.5 transition-colors cursor-pointer shrink-0"
          >
            View Analysis <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

function useCarouselMetrics(containerRef: RefObject<HTMLDivElement | null>) {
  const [metrics, setMetrics] = useState({ cardWidth: 380, stride: 340 });

  useEffect(() => {
    const update = () => {
      const w = containerRef.current?.offsetWidth ?? 0;
      if (w === 0) return;

      const isLg = window.innerWidth >= 1024;
      const isMd = window.innerWidth >= 768;

      const cardWidth = isLg ? w * 0.36 : isMd ? w * 0.52 : w * 0.78;
      const stride = isLg ? w * 0.34 : isMd ? w * 0.48 : w * 0.72;

      setMetrics({ cardWidth, stride });
    };

    update();
    const ro = new ResizeObserver(update);
    if (containerRef.current) ro.observe(containerRef.current);
    window.addEventListener("resize", update);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", update);
    };
  }, [containerRef]);

  return metrics;
}

export interface BestPredictionsCarouselProps {
  matches: MatchPrediction[];
  isLoading?: boolean;
  error?: string | null;
  apiBase?: string;
  onViewAnalysis: (match: MatchPrediction) => void;
  onViewAll?: () => void;
  onRetry?: () => void;
  isModalOpen?: boolean;
}

export function BestPredictionsCarousel({
  matches,
  isLoading = false,
  error = null,
  apiBase = "",
  onViewAnalysis,
  onViewAll,
  onRetry,
  isModalOpen = false,
}: BestPredictionsCarouselProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const { cardWidth, stride } = useCarouselMetrics(containerRef);

  const total = matches.length;

  // Easing curve duration adjusted to 600ms (within 500-700ms range)
  const premiumTransition = { duration: 0.6, ease: [0.16, 1, 0.3, 1] as const };

  // Detect prefers-reduced-motion setting
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mediaQuery.matches);

    const listener = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };
    mediaQuery.addEventListener("change", listener);
    return () => mediaQuery.removeEventListener("change", listener);
  }, []);

  const goNext = useCallback(() => {
    if (total === 0) return;
    setActiveIndex(i => (i + 1) % total);
  }, [total]);

  const goPrev = useCallback(() => {
    if (total === 0) return;
    setActiveIndex(i => (i - 1 + total) % total);
  }, [total]);

  const handleDragStart = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handleDragEnd = useCallback(
    (_: unknown, info: PanInfo) => {
      setIsDragging(false);
      if (info.offset.x < -DRAG_THRESHOLD || info.velocity.x < -VELOCITY_THRESHOLD) {
        goNext();
      } else if (info.offset.x > DRAG_THRESHOLD || info.velocity.x > VELOCITY_THRESHOLD) {
        goPrev();
      }
    },
    [goNext, goPrev]
  );

  useEffect(() => {
    if (activeIndex >= total && total > 0) {
      setActiveIndex(0);
    }
  }, [activeIndex, total]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") goPrev();
      if (e.key === "ArrowRight") goNext();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [goNext, goPrev]);

  // Auto slide configuration: pause on hover, dragging, modal open, or accessibility preference
  const isSystemPaused = isHovered || isDragging || isModalOpen;
  const shouldAutoSlide = !prefersReducedMotion && !isSystemPaused && total > 0;

  return (
    <div
      id="todays-best-predictions"
      className="max-w-7xl mx-auto px-6 md:px-12 w-full py-16 scroll-mt-24"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex flex-col md:flex-row md:items-end justify-between border-b border-zinc-900 pb-6 mb-10 gap-6">
        <div>
          <span className="text-[10px] font-mono tracking-[0.3em] text-green-accent uppercase block font-bold mb-1.5 animate-pulse">
            CURATED SELECTIONS
          </span>
          <span className="text-3xl font-serif text-white tracking-tight block">
            Today&apos;s Best Predictions
          </span>
          <p className="text-zinc-550 text-xs mt-2 max-w-xl font-sans">
            The highest confidence distributions, prominent fixtures, and decisive matchups simulated
            50,051 times by the OFFLINE quantitative intelligence model.
          </p>
        </div>

        {!isLoading && !error && total > 0 && (
          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={goPrev}
              className="p-3 rounded-full border border-zinc-900 hover:border-zinc-550 bg-zinc-950 text-zinc-455 hover:text-white transition-all cursor-pointer group"
              aria-label="Previous prediction"
            >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
            </button>
            <button
              onClick={goNext}
              className="p-3 rounded-full border border-zinc-900 hover:border-zinc-550 bg-zinc-950 text-zinc-455 hover:text-white transition-all cursor-pointer group"
              aria-label="Next prediction"
            >
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="flex gap-6 justify-center pb-8">
          {Array.from({ length: 3 }).map((_, idx) => (
            <MatchCardSkeleton key={idx} />
          ))}
        </div>
      ) : error ? (
        <div className="w-full bg-zinc-950 border border-red-500/20 rounded p-12 text-center flex flex-col items-center justify-center space-y-4">
          <AlertCircle className="w-10 h-10 text-red-500 animate-pulse" />
          <span className="text-[10px] font-mono tracking-[0.2em] text-red-400 uppercase block font-bold">
            Prediction Engine Offline
          </span>
          <h4 className="text-xl font-serif text-white tracking-tight uppercase">Connection Failed</h4>
          <p className="text-zinc-400 text-xs max-w-lg leading-relaxed font-sans">
            The live machine learning prediction engine is currently unreachable at{" "}
            <code className="text-red-400 font-mono">{apiBase || "(no API URL configured)"}</code>.
            Live predictions have been disabled to prevent displaying fallback/mock data. Please verify
            your backend server is running and reload.
          </p>
          <button
            onClick={onRetry || (() => window.location.reload())}
            className="px-5 py-2.5 bg-zinc-900 hover:bg-zinc-800 text-white rounded text-xs font-mono font-bold tracking-widest uppercase border border-zinc-800 hover:border-zinc-700 cursor-pointer transition duration-300"
          >
            Retry Connection
          </button>
        </div>
      ) : total === 0 ? null : (
        <div className="relative select-none">
          <div
            className="pointer-events-none absolute inset-y-0 left-0 w-16 md:w-24 z-20 bg-gradient-to-r from-black via-black/80 to-transparent"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute inset-y-0 right-0 w-16 md:w-24 z-20 bg-gradient-to-l from-black via-black/80 to-transparent"
            aria-hidden
          />

          <motion.div
            ref={containerRef}
            className="relative h-[420px] overflow-hidden cursor-grab active:cursor-grabbing touch-pan-y"
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            dragElastic={0.12}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
            role="region"
            aria-roledescription="carousel"
            aria-label="Today's best predictions"
          >
            {matches.map((match, index) => {
              const offset = getLoopOffset(index, activeIndex, total);
              if (Math.abs(offset) > 2) return null;

              const isActive = offset === 0;

              return (
                <motion.div
                  key={match.id}
                  className="absolute top-0 left-1/2 will-change-transform"
                  style={{ width: cardWidth }}
                  initial={false}
                  animate={{
                    x: offset * stride - cardWidth / 2,
                    scale: isActive ? 1 : 0.92,
                    opacity: isActive ? 1 : 0.7,
                    zIndex: isActive ? 20 : 10 - Math.abs(offset),
                  }}
                  transition={premiumTransition}
                >
                  <PredictionCard
                    match={match}
                    isActive={isActive}
                    onViewAnalysis={onViewAnalysis}
                  />
                </motion.div>
              );
            })}
          </motion.div>

          <div className="flex justify-center gap-2 mt-6">
            {matches.map((match, i) => {
              const isActive = i === activeIndex;
              return (
                <button
                  key={match.id}
                  type="button"
                  aria-label={`Go to ${match.teamA} vs ${match.teamB}`}
                  aria-current={isActive ? "true" : undefined}
                  onClick={() => setActiveIndex(i)}
                  className={`h-1.5 rounded-full relative overflow-hidden transition-all duration-[450ms] ${
                    isActive
                      ? "w-8 bg-zinc-800"
                      : "w-1.5 bg-zinc-800 hover:bg-zinc-605"
                  }`}
                >
                  {isActive && (
                    shouldAutoSlide ? (
                      <motion.span
                        key={`${i}-${activeIndex}-${shouldAutoSlide}`}
                        initial={{ width: 0 }}
                        animate={{ width: "100%" }}
                        transition={{ duration: 7, ease: "linear" }}
                        className="absolute left-0 top-0 bottom-0 bg-green-accent rounded-full"
                        onAnimationComplete={goNext}
                      />
                    ) : (
                      <span className="absolute inset-0 bg-green-accent rounded-full" />
                    )
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {onViewAll && (
        <div className="flex justify-center mt-10">
          <button
            onClick={onViewAll}
            className="group inline-flex items-center gap-2.5 px-8 py-3.5 bg-zinc-950 border border-zinc-900 hover:border-zinc-700 rounded text-xs font-mono font-bold tracking-widest text-white uppercase cursor-pointer hover:bg-zinc-900 transition-all duration-300"
          >
            VIEW ALL PREDICTIONS{" "}
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      )}
    </div>
  );
}
