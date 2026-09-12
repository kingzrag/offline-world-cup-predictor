import { useCallback, useEffect, useRef, useState, memo, type RefObject } from "react";
import { motion, useScroll, useTransform, type PanInfo } from "motion/react";
import { AlertCircle, ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import type { MatchPrediction } from "../types";
import { formatSmartKickoffLocal } from "../dateTimeUtils";
import { TeamBadge } from "../teamAssetUtils";

const TRANSITION = { duration: 0.45, ease: [0.32, 0.72, 0, 1] as const };
const DRAG_THRESHOLD = 48;
const VELOCITY_THRESHOLD = 400;

// Skeleton loader for match cards
function MatchCardSkeleton() {
  return (
    <div className="bg-zinc-950 border border-zinc-900 rounded-lg px-7 py-6 flex flex-col justify-between min-h-[340px] h-full">
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

const PredictionCard = memo(function PredictionCard({ match, isActive, onViewAnalysis }: PredictionCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, ease: [0.32, 0.72, 0, 1] }}
      className={`bg-zinc-950 border rounded-lg px-5 py-4.5 flex flex-col justify-between min-h-[285px] h-full transition-colors duration-300 ${
        isActive
          ? "border-zinc-700 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.85),0_0_0_1px_rgba(16,185,129,0.15)]"
          : "border-zinc-900 hover:border-zinc-800"
      }`}
    >
      {/* Header: stage + badge left, kickoff right — responsive, no overlap */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between sm:gap-3 mb-0.5 min-w-0">
        <div className="flex flex-col items-start gap-1 min-w-0 flex-1">
          <span className="text-[9.5px] font-mono text-zinc-500 tracking-wider uppercase leading-snug break-words">
            {match.competition || match.stage}
          </span>
          {match.isLiveData ? (
            <span className="inline-flex shrink-0 text-green-accent text-[7.5px] bg-green-accent/10 border border-green-accent/25 px-1.5 py-0.5 rounded leading-none select-none tracking-widest uppercase font-bold">
              LIVE MODEL
            </span>
          ) : (
            <span className="inline-flex shrink-0 text-zinc-500 text-[7.5px] bg-zinc-900 border border-zinc-800 px-1.5 py-0.5 rounded leading-none select-none tracking-widest uppercase">
              LOCAL
            </span>
          )}
        </div>
        <div className="shrink-0 text-left sm:text-right min-w-[7rem] sm:min-w-[8rem] text-[9.5px] font-mono self-start sm:self-auto">
          <MatchTimeDisplay match={match} />
        </div>
      </div>

      <div className="flex-1 flex flex-col justify-center my-2 min-h-0">
        <div className="text-lg font-bold text-white uppercase tracking-normal space-y-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <TeamBadge name={match.teamA} crestUrl={match.teamACrest} size="md" />
            <span className="truncate leading-tight">{match.teamA}</span>
          </div>
          <div className="text-zinc-500 text-[9px] font-mono uppercase pl-8 font-medium">vs</div>
          <div className="flex items-center gap-2.5 min-w-0">
            <TeamBadge name={match.teamB} crestUrl={match.teamBCrest} size="md" />
            <span className="truncate leading-tight">{match.teamB}</span>
          </div>
        </div>

        {match.status === "LIVE" ? (
          <div className="mt-4 flex flex-col justify-center items-start gap-1">
            <span className="text-[8.5px] font-mono uppercase tracking-widest text-red-500 block animate-pulse font-bold">
              Live Score
            </span>
            <div className="flex items-center gap-2.5 text-2xl font-black text-white tracking-wider">
              <motion.span
                key={`home-${match.liveScore?.home ?? 0}`}
                initial={{ scale: 1.2, color: "#22C55E" }}
                animate={{ scale: 1, color: "#ffffff" }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              >
                {match.liveScore?.home ?? 0}
              </motion.span>
              <span className="text-zinc-700 font-light">—</span>
              <motion.span
                key={`away-${match.liveScore?.away ?? 0}`}
                initial={{ scale: 1.2, color: "#22C55E" }}
                animate={{ scale: 1, color: "#ffffff" }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              >
                {match.liveScore?.away ?? 0}
              </motion.span>
            </div>
          </div>
        ) : match.status === "COMPLETED" ? (
          (() => {
            const isCorrect =
              (match.prediction === `${match.teamA} Win` && match.winner === "HOME_TEAM") ||
              (match.prediction === `${match.teamB} Win` && match.winner === "AWAY_TEAM") ||
              (match.prediction === "Draw" && match.winner === "DRAW");
            return (
              <div className="mt-4 flex flex-col justify-center items-start gap-1">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-[8.5px] font-mono uppercase tracking-widest text-zinc-500 block font-bold">
                    Final Score
                  </span>
                  <span
                    className={`text-[8px] font-mono font-bold px-1 py-0.5 rounded leading-none select-none tracking-widest uppercase ${
                      isCorrect
                        ? "text-green-accent bg-green-accent/15 border border-green-accent/25"
                        : "text-red-400 bg-red-950/20 border border-red-900/20"
                    }`}
                  >
                    {isCorrect ? "✓ Correct" : "✕ Miss"}
                  </span>
                </div>
                <div className="flex items-center gap-2.5 text-2xl font-black text-white tracking-wider">
                  <span>{match.liveScore?.home ?? 0}</span>
                  <span className="text-zinc-700 font-light">—</span>
                  <span>{match.liveScore?.away ?? 0}</span>
                </div>
              </div>
            );
          })()
        ) : (
          <div className="mt-4 space-y-1">
            <span className="text-[8.5px] font-mono uppercase tracking-widest text-zinc-500 block">
              Assessment
            </span>
            <span className="text-white text-sm font-medium tracking-normal leading-snug block">
              {match.prediction}
            </span>
          </div>
        )}
      </div>

      <div className="mt-auto pt-1">
        <div className="mb-3">
          <div className="flex justify-between items-center gap-2 text-[10px] font-mono text-zinc-400 mb-1.5 min-w-0">
            <motion.span
              key={`probA-${match.id}-${match.probA}`}
              initial={{ scale: 1.1, color: "#22C55E" }}
              animate={{ scale: 1, color: "#D4D4D8" }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="truncate font-semibold text-zinc-300"
            >
              {match.teamACode} {match.probA}%
            </motion.span>
            <motion.span
              key={`probD-${match.id}-${match.probD}`}
              initial={{ scale: 1.1, color: "#22C55E" }}
              animate={{ scale: 1, color: "#A1A1AA" }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="shrink-0 font-semibold text-zinc-400"
            >
              Draw {match.probD}%
            </motion.span>
            <motion.span
              key={`probB-${match.id}-${match.probB}`}
              initial={{ scale: 1.1, color: "#22C55E" }}
              animate={{ scale: 1, color: "#D4D4D8" }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="truncate font-semibold text-zinc-300 text-right"
            >
              {match.teamBCode} {match.probB}%
            </motion.span>
          </div>
          <div className="h-1.5 w-full bg-zinc-900 flex rounded overflow-hidden">
            <motion.div
              key={`barA-${match.id}-${match.probA}`}
              initial={{ width: 0 }}
              animate={{ width: `${match.probA}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="h-full bg-green-accent"
            />
            <motion.div
              key={`barD-${match.id}-${match.probD}`}
              initial={{ width: 0 }}
              animate={{ width: `${match.probD}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="h-full bg-zinc-750"
            />
            <motion.div
              key={`barB-${match.id}-${match.probB}`}
              initial={{ width: 0 }}
              animate={{ width: `${match.probB}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="h-full bg-zinc-800"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-zinc-900 gap-2">
          <span
            className={`text-[9px] font-mono uppercase tracking-widest font-bold shrink-0 ${
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
            className="text-[11px] font-mono font-bold text-white hover:text-green-accent flex items-center gap-1 transition-colors cursor-pointer shrink-0"
          >
            View Analysis <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      </div>
    </motion.div>
  );
});

function useCarouselMetrics(containerRef: RefObject<HTMLDivElement | null>) {
  const [metrics, setMetrics] = useState({ cardWidth: 380, stride: 340 });

  useEffect(() => {
    const update = () => {
      const w = containerRef.current?.offsetWidth ?? 0;
      if (w === 0) return;

      const isLg = window.innerWidth >= 1024;
      const isMd = window.innerWidth >= 768;

      const cardWidth = isLg ? w * 0.315 : isMd ? w * 0.46 : w * 0.70;
      const stride = isLg ? w * 0.29 : isMd ? w * 0.42 : w * 0.64;

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

const titleVariants = {
  hidden: { opacity: 0, y: 25 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.9, ease: [0.16, 1, 0.3, 1] as const }
  }
};

const dividerVariants = {
  hidden: { scaleX: 0 },
  show: {
    scaleX: 1,
    transition: { duration: 1.0, ease: [0.16, 1, 0.3, 1] as const, delay: 0.25 }
  }
};

const fadeVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] as const, delay: 0.35 }
  }
};

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

  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);
  const [sectionSettled, setSectionSettled] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 640);
      setIsTablet(window.innerWidth >= 640 && window.innerWidth < 1024);
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

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

  // ── Section-level scroll-driven exit transform ────────────────────────────
  // As the section scrolls out of view upward, it subtly dims and compresses.
  // Incoming: opacity 0→1, translateY 40→0, scale 0.98→1 over 700ms power3.out.
  // Outgoing: opacity 1→0.85, scale 1→0.985 (driven by scroll position).
  const sectionRef = useRef<HTMLElement>(null);
  const { scrollYProgress: sectionScrollProgress } = useScroll({
    target: sectionRef,
    offset: ["start start", "end start"],
  });
  const exitOpacity = useTransform(sectionScrollProgress, [0, 0.75, 1], [1, 1, 0.85]);
  const exitScale  = useTransform(sectionScrollProgress, [0, 1], [1, 0.985]);

  return (
    <motion.section
      ref={sectionRef}
      id="todays-best-predictions"
      className="relative w-full h-[100dvh] flex flex-col justify-center pb-4 lg:pb-2 bg-[#070707] text-zinc-150 select-none z-20 origin-center editorial-snap-section"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{ opacity: exitOpacity }}
      initial={{ opacity: 0, y: 80, scale: 0.98 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true, amount: 0.12 }}
      transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
      onAnimationComplete={() => setSectionSettled(true)}
    >
      {/* Subtle vignette and ambient background glow behind featured card */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(0,0,0,0)_20%,rgba(0,0,0,0.95)_100%)]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] rounded-full bg-green-accent/5 filter blur-[120px] opacity-40" />
      </div>

      <div className="relative z-10 w-full max-w-7xl mx-auto px-6 md:px-12 flex flex-col justify-center h-full py-2 lg:py-3.5">
        <div className="flex flex-col md:flex-row md:items-end justify-between pb-1.5 mb-3.5 gap-4 relative">
          <motion.div 
            variants={titleVariants}
            initial="hidden"
            animate={sectionSettled ? "show" : "hidden"}
          >
            <span className="text-[10px] font-mono tracking-[0.3em] text-green-accent uppercase block font-bold mb-2">
              CURATED SELECTIONS
            </span>
            <h2 className="text-3xl sm:text-4xl md:text-[40px] font-serif text-white tracking-tight leading-tight block">
              Today&apos;s Best Predictions
            </h2>
            <p className="text-zinc-400 text-xs mt-1.5 max-w-xl font-sans font-light leading-relaxed">
              The highest confidence distributions, prominent fixtures, and decisive matchups simulated 50,051 times by the OFFLINE quantitative intelligence model.
            </p>
          </motion.div>

          {!isLoading && !error && total > 0 && (
            <motion.div 
              className="flex items-center space-x-3 shrink-0 self-end md:self-auto"
              variants={fadeVariants}
              initial="hidden"
              animate={sectionSettled ? "show" : "hidden"}
            >
              <motion.button
                onClick={goPrev}
                whileHover={{ scale: 1.05, borderColor: "#ffffff" }}
                whileTap={{ scale: 0.95 }}
                className="w-11 h-11 rounded-full border border-zinc-850 flex items-center justify-center text-zinc-400 hover:text-white transition-all duration-300 bg-transparent cursor-pointer group"
                aria-label="Previous prediction"
              >
                <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform duration-300" />
              </motion.button>
              <motion.button
                onClick={goNext}
                whileHover={{ scale: 1.05, borderColor: "#ffffff" }}
                whileTap={{ scale: 0.95 }}
                className="w-11 h-11 rounded-full border border-zinc-855 flex items-center justify-center text-zinc-400 hover:text-white transition-all duration-300 bg-transparent cursor-pointer group"
                aria-label="Next prediction"
              >
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform duration-300" />
              </motion.button>
            </motion.div>
          )}
        </div>

        {/* Thin divider with left-to-right drawing animation */}
        <div className="relative w-full mb-3.5">
          <motion.div 
            className="w-full h-[1px] bg-zinc-800 origin-left"
            variants={dividerVariants}
            initial="hidden"
            animate={sectionSettled ? "show" : "hidden"}
          />
        </div>

        {isLoading ? (
          <div className="flex gap-6 justify-center py-8">
            {Array.from({ length: isMobile ? 1 : isTablet ? 2 : 3 }).map((_, idx) => (
              <div key={idx} style={{ width: cardWidth }} className="h-full">
                <MatchCardSkeleton />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="w-full bg-[#0E0E0E] border border-red-500/10 rounded-lg p-12 text-center flex flex-col items-center justify-center space-y-4">
            <AlertCircle className="w-10 h-10 text-red-500 animate-pulse" />
            <span className="text-[10px] font-mono tracking-[0.2em] text-red-400 uppercase block font-bold">
              Prediction Engine Offline
            </span>
            <h4 className="text-xl font-serif text-white tracking-tight uppercase">Connection Failed</h4>
            <p className="text-zinc-400 text-xs max-w-lg leading-relaxed font-sans font-light">
              The live machine learning prediction engine is currently unreachable at{" "}
              <code className="text-red-400 font-mono">{apiBase || "(no API URL configured)"}</code>.
              Live predictions have been disabled to prevent displaying fallback/mock data. Please verify your backend server is running and reload.
            </p>
            <button
              onClick={onRetry || (() => window.location.reload())}
              className="px-6 py-3 bg-zinc-900 hover:bg-zinc-800 text-white rounded text-xs font-mono font-bold tracking-widest uppercase border border-zinc-800 hover:border-zinc-700 cursor-pointer transition duration-300"
            >
              Retry Connection
            </button>
          </div>
        ) : total === 0 ? null : (
          <div className="relative select-none w-full">
            {/* Cropping gradients for Awwwards / Framer feel */}
            <div
              className="pointer-events-none absolute inset-y-0 left-0 w-8 md:w-20 z-20 bg-gradient-to-r from-[#070707] to-transparent"
              aria-hidden
            />
            <div
              className="pointer-events-none absolute inset-y-0 right-0 w-8 md:w-20 z-20 bg-gradient-to-l from-[#070707] to-transparent"
              aria-hidden
            />

            <motion.div
              ref={containerRef}
              className="relative h-[355px] overflow-hidden cursor-grab active:cursor-grabbing touch-pan-y pt-3"
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
                // On mobile, only render the active card. On tablet/desktop, render surrounding cards.
                if (isMobile && Math.abs(offset) > 0) return null;
                if (Math.abs(offset) > 2) return null;

                const isActive = offset === 0;
                
                // Opacity logic matching: center 100%, left/right 75%, mobile hidden
                const cardOpacity = isActive ? 1 : isMobile ? 0 : 0.75;
                
                // Sequence delay calculations for staggered entrance after section settles
                // Left gets 0, Center gets 0.15s, Right gets 0.3s
                const seqDelay = (offset + 1) * 0.15;

                return (
                  <motion.div
                    key={match.id}
                    className="absolute top-4 left-1/2 will-change-transform"
                    style={{ width: cardWidth }}
                    initial={false}
                    animate={{
                      x: offset * stride - cardWidth / 2,
                      scale: isActive ? 1.02 : 0.92,
                      opacity: cardOpacity,
                      zIndex: isActive ? 20 : 10 - Math.abs(offset),
                    }}
                    transition={premiumTransition}
                  >
                    {/* Inner wrapper for Entrance slide + Hover elevation */}
                    <motion.div
                      initial="hidden"
                      animate={sectionSettled ? "show" : "hidden"}
                      variants={{
                        hidden: { opacity: 0, y: 30 },
                        show: {
                          opacity: 1,
                          y: 0,
                          transition: {
                            duration: 0.85,
                            ease: [0.16, 1, 0.3, 1] as const,
                            delay: seqDelay
                          }
                        }
                      }}
                      whileHover={{
                        y: -6,
                        scale: isActive ? 1.03 : 0.94,
                        transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] }
                      }}
                      className="h-full w-full rounded-lg"
                    >
                      <PredictionCard
                        match={match}
                        isActive={isActive}
                        onViewAnalysis={onViewAnalysis}
                      />
                    </motion.div>
                  </motion.div>
                );
              })}
            </motion.div>

            {/* Premium editorial dots */}
            <div className="flex justify-center gap-3 mt-3.5">
              {matches.map((match, i) => {
                const isActive = i === activeIndex;
                return (
                  <button
                    key={match.id}
                    type="button"
                    aria-label={`Go to ${match.teamA} vs ${match.teamB}`}
                    aria-current={isActive ? "true" : undefined}
                    onClick={() => setActiveIndex(i)}
                    className="relative w-3.5 h-3.5 flex items-center justify-center cursor-pointer group"
                  >
                    {/* Small background dot */}
                    <span className="w-1.5 h-1.5 rounded-full bg-zinc-800 transition-colors duration-300 group-hover:bg-zinc-600" />
                    
                    {/* Active ring layout animation */}
                    {isActive && (
                      <motion.span
                        layoutId="activeDot"
                        className="absolute inset-0 border border-green-accent rounded-full scale-[0.68]"
                        transition={{ type: "spring", stiffness: 320, damping: 28 }}
                      />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {onViewAll && (
          <div className="flex justify-center mt-3.5">
            <motion.button
              onClick={onViewAll}
              whileHover={{ y: -2, borderColor: "#ffffff", backgroundColor: "rgba(255,255,255,0.03)" }}
              whileTap={{ scale: 0.98 }}
              className="group inline-flex items-center gap-3 px-8 py-3 bg-transparent border border-zinc-800 rounded text-[10px] font-mono font-bold tracking-[0.25em] text-white uppercase cursor-pointer transition-all duration-300"
            >
              VIEW ALL PREDICTIONS{" "}
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1.5 transition-transform duration-300" />
            </motion.button>
          </div>
        )}
      </div>
    </motion.section>
  );
}
