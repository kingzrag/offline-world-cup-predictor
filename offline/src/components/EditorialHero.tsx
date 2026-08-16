import React, { useState, useEffect } from 'react';
import { motion, MotionValue } from 'motion/react';
import { ChevronDown } from 'lucide-react';

interface EditorialHeroSet {
  id: string;
  title: string;
  left: string;
  center: string;
  right: string;
}

// Built-in list of all 15 editorial hero photo sets deployed under /editorial/hero-01 .. /hero-15
const BUILTIN_EDITORIAL_SETS: EditorialHeroSet[] = [
  { id: 'hero-01', title: 'The Final',               left: '/editorial/hero-01/left.jpg', center: '/editorial/hero-01/cover.jpg', right: '/editorial/hero-01/right.jpg' },
  { id: 'hero-02', title: 'Champions League Night', left: '/editorial/hero-02/left.jpg', center: '/editorial/hero-02/cover.jpg', right: '/editorial/hero-02/right.jpg' },
  { id: 'hero-03', title: 'Derby Day',              left: '/editorial/hero-03/left.jpg', center: '/editorial/hero-03/cover.jpg', right: '/editorial/hero-03/right.jpg' },
  { id: 'hero-04', title: 'Tactical Masterclass',   left: '/editorial/hero-04/left.jpg', center: '/editorial/hero-04/cover.jpg', right: '/editorial/hero-04/right.jpg' },
  { id: 'hero-05', title: 'Wonderkid',              left: '/editorial/hero-05/left.jpg', center: '/editorial/hero-05/cover.jpg', right: '/editorial/hero-05/right.jpg' },
  { id: 'hero-06', title: 'Goalkeeper',             left: '/editorial/hero-06/left.jpg', center: '/editorial/hero-06/cover.jpg', right: '/editorial/hero-06/right.jpg' },
  { id: 'hero-07', title: 'Premier League',         left: '/editorial/hero-07/left.jpg', center: '/editorial/hero-07/cover.jpg', right: '/editorial/hero-07/right.jpg' },
  { id: 'hero-08', title: 'La Liga',                left: '/editorial/hero-08/left.jpg', center: '/editorial/hero-08/cover.jpg', right: '/editorial/hero-08/right.jpg' },
  { id: 'hero-09', title: 'Serie A',                left: '/editorial/hero-09/left.jpg', center: '/editorial/hero-09/cover.jpg', right: '/editorial/hero-09/right.jpg' },
  { id: 'hero-10', title: 'Bundesliga',             left: '/editorial/hero-10/left.jpg', center: '/editorial/hero-10/cover.jpg', right: '/editorial/hero-10/right.jpg' },
  { id: 'hero-11', title: 'Ligue 1',                 left: '/editorial/hero-11/left.jpg', center: '/editorial/hero-11/cover.jpg', right: '/editorial/hero-11/right.jpg' },
  { id: 'hero-12', title: 'Champions League',       left: '/editorial/hero-12/left.jpg', center: '/editorial/hero-12/cover.jpg', right: '/editorial/hero-12/right.jpg' },
  { id: 'hero-13', title: 'World Cup History',      left: '/editorial/hero-13/left.jpg', center: '/editorial/hero-13/cover.jpg', right: '/editorial/hero-13/right.jpg' },
  { id: 'hero-14', title: 'Golden Boot',            left: '/editorial/hero-14/left.jpg', center: '/editorial/hero-14/cover.jpg', right: '/editorial/hero-14/right.jpg' },
  { id: 'hero-15', title: 'Football Culture',       left: '/editorial/hero-15/left.jpg', center: '/editorial/hero-15/cover.jpg', right: '/editorial/hero-15/right.jpg' },
];

interface EditorialHeroProps {
  heroRef: React.RefObject<HTMLDivElement | null>;
  heroOpacity: MotionValue<number>;
  heroScale: MotionValue<number>;
  countdown: string;
  countdownLabel: string;
  onNavigate: (tab: 'predictions' | 'favorites' | 'intelligence' | 'model') => void;
  scrollY: number;
  isMobile: boolean;
}

export function EditorialHero({
  heroRef,
  heroOpacity,
  heroScale,
  countdown,
  countdownLabel,
  onNavigate,
  scrollY,
  isMobile,
}: EditorialHeroProps) {
  const [editorialHeroes, setEditorialHeroes] = useState<EditorialHeroSet[]>(BUILTIN_EDITORIAL_SETS);
  const [currentHeroIdx, setCurrentHeroIdx] = useState(0);

  // Fetch manifest.json to sync any server-side metadata updates if available
  useEffect(() => {
    const EDITORIAL_BASE = '/editorial';
    fetch(`${EDITORIAL_BASE}/manifest.json`)
      .then((r) => {
        const contentType = r.headers.get('content-type') || '';
        if (!r.ok || contentType.includes('text/html')) {
          return null;
        }
        return r.json();
      })
      .then((manifest: Array<{ id: string; title: string; cover: string; left: string; right: string }> | null) => {
        if (Array.isArray(manifest) && manifest.length > 0) {
          const available: EditorialHeroSet[] = manifest.map((entry) => ({
            id: entry.id,
            title: entry.title,
            left: `${EDITORIAL_BASE}/${entry.id}/${entry.left}`,
            center: `${EDITORIAL_BASE}/${entry.id}/${entry.cover}`,
            right: `${EDITORIAL_BASE}/${entry.id}/${entry.right}`,
          }));
          setEditorialHeroes(available);
        }
      })
      .catch(() => {
        // Silent fallback to built-in editorial sets
      });
  }, []);

  // Preload the next hero set to prevent layout flashing or blank images during transitions
  useEffect(() => {
    if (editorialHeroes.length <= 1) return;
    const nextIdx = (currentHeroIdx + 1) % editorialHeroes.length;
    const nextHero = editorialHeroes[nextIdx];

    const preloadLeft = new Image();
    preloadLeft.src = nextHero.left;

    const preloadCenter = new Image();
    preloadCenter.src = nextHero.center;

    const preloadRight = new Image();
    preloadRight.src = nextHero.right;
  }, [currentHeroIdx, editorialHeroes]);

  // Rotate through editorial heroes every 8 seconds
  useEffect(() => {
    if (editorialHeroes.length < 2) return;
    const timer = setInterval(() => {
      setCurrentHeroIdx((idx) => (idx + 1) % editorialHeroes.length);
    }, 8000);
    return () => clearInterval(timer);
  }, [editorialHeroes]);

  const currentHero = editorialHeroes[currentHeroIdx] || BUILTIN_EDITORIAL_SETS[0];
  const heroLeft = currentHero.left;
  const heroCenter = currentHero.center;
  const heroRight = currentHero.right;

  // Mouse parallax state
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
    const y = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
    setMousePos({ x, y });
  };
  const handleMouseLeave = () => {
    setMousePos({ x: 0, y: 0 });
  };

  return (
    <motion.div
      ref={heroRef}
      id="editorial-hero"
      className="relative w-full h-[100dvh] flex flex-col justify-between bg-editorial-white bg-paper-grain paper-overlay overflow-hidden select-none text-editorial-dark editorial-snap-section"
      style={{ opacity: heroOpacity, scale: heroScale }}
      initial={{ opacity: 0, y: 80, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Main Content Layout */}
      <div className="relative z-10 w-full max-w-7xl mx-auto px-6 md:px-12 pt-[86px] flex-1 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left Column (Col 2): Editorial metadata */}
        <motion.div
          className="hidden lg:flex flex-col justify-between h-[50vh] text-[9px] tracking-[0.3em] font-mono uppercase text-editorial-dim border-r border-editorial-muted pr-8"
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.0, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
        >
          <div className="space-y-4">
            <div>GLOBAL EDITION</div>
            <div>ISSUE 002</div>
            <div>UPDATED DAILY</div>
          </div>
          {/* Large empty whitespace underneath */}
          <div className="flex-1"></div>
        </motion.div>

        {/* Center Column (Col 6): Overlapping magazine cover football cards */}
        <motion.div
          className="lg:col-span-6 flex items-center justify-center relative w-full"
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
        >
          <div className="relative flex items-center justify-center w-full h-[320px] sm:h-[380px] md:h-[450px]">
            {/* Left Card */}
            <motion.div
              className="absolute rounded border border-[#1C1B17]/10 bg-[#F6F4EF] overflow-hidden"
              style={{
                width: isMobile ? 120 : 200,
                height: isMobile ? 170 : 280,
                y: scrollY * 0.1,
                rotate: -8 + mousePos.x * 2.0,
                x: isMobile ? -40 + mousePos.x * 5 : -80 + mousePos.x * 8,
                zIndex: 10,
                transformOrigin: 'bottom right',
                boxShadow: '0 10px 25px rgba(28, 27, 23, 0.08)',
              }}
              initial={{ x: 0, rotate: 0, opacity: 0 }}
              animate={{
                x: isMobile ? -40 : -80,
                rotate: -8,
                opacity: 1,
              }}
              transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1], delay: 0.3 }}
            >
              <motion.img
                key={currentHeroIdx + '-left'}
                src={heroLeft}
                alt="Cover Left"
                className="w-full h-full object-cover"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.7 }}
              />
            </motion.div>

            {/* Right Card */}
            <motion.div
              className="absolute rounded border border-[#1C1B17]/10 bg-[#F6F4EF] overflow-hidden"
              style={{
                width: isMobile ? 120 : 200,
                height: isMobile ? 170 : 280,
                y: scrollY * 0.1,
                rotate: 8 + mousePos.x * 2.0,
                x: isMobile ? 40 + mousePos.x * 5 : 80 + mousePos.x * 8,
                zIndex: 10,
                transformOrigin: 'bottom left',
                boxShadow: '0 10px 25px rgba(28, 27, 23, 0.08)',
              }}
              initial={{ x: 0, rotate: 0, opacity: 0 }}
              animate={{
                x: isMobile ? 40 : 80,
                rotate: 8,
                opacity: 1,
              }}
              transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1], delay: 0.3 }}
            >
              <motion.img
                key={currentHeroIdx + '-right'}
                src={heroRight}
                alt="Cover Right"
                className="w-full h-full object-cover"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.7 }}
              />
            </motion.div>

            {/* Center Card */}
            <motion.div
              className="absolute rounded border border-[#1C1B17]/15 bg-[#F6F4EF] overflow-hidden"
              style={{
                width: isMobile ? 140 : 230,
                height: isMobile ? 200 : 320,
                y: scrollY * 0.16,
                rotate: mousePos.x * 2.5,
                x: mousePos.x * 12,
                zIndex: 20,
                boxShadow: '0 25px 45px rgba(28, 27, 23, 0.14)',
              }}
              initial={{ scale: 0.92, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
            >
              <motion.img
                key={currentHeroIdx + '-center'}
                src={heroCenter}
                alt="Cover Center"
                className="w-full h-full object-cover"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.7 }}
              />
            </motion.div>
          </div>
        </motion.div>

        {/* Right Column (Col 4): Editorial Content */}
        <motion.div
          className="lg:col-span-4 flex flex-col justify-center text-left py-6 lg:py-0"
          initial="hidden"
          animate="show"
          variants={{
            hidden: {},
            show: {
              transition: {
                staggerChildren: 0.15,
                delayChildren: 0.25,
              },
            },
          }}
        >
          <motion.span
            className="text-[10px] sm:text-[11px] font-mono uppercase tracking-[0.25em] text-editorial-dim mb-3 sm:mb-4 block"
            variants={{
              hidden: { opacity: 0, y: 15 },
              show: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } },
            }}
          >
            SUMMER 2026
          </motion.span>

          <motion.h1
            className="editorial-title text-3xl sm:text-4xl md:text-5xl lg:text-[40px] xl:text-[46px] font-light text-editorial-dark mb-4 sm:mb-5 leading-[1.08] tracking-tight"
            style={{ y: scrollY * 0.06 }}
            variants={{
              hidden: { opacity: 0, y: 20 },
              show: { opacity: 1, y: 0, transition: { duration: 0.9, ease: [0.16, 1, 0.3, 1] } },
            }}
          >
            Football belongs <br />
            to those who <br />
            <span className="italic font-normal">see the game</span> <br />
            differently.
          </motion.h1>

          <motion.p
            className="text-xs sm:text-sm text-editorial-muted font-light leading-relaxed max-w-md mb-6 sm:mb-8"
            variants={{
              hidden: { opacity: 0 },
              show: { opacity: 1, transition: { duration: 1.0, ease: [0.16, 1, 0.3, 1] } },
            }}
          >
            A quantitative expected value simulation index and elite football decision engine publication built for analysts, experts, and readers who demand mathematical clarity over gambling noise.
          </motion.p>

          <motion.div
            variants={{
              hidden: { opacity: 0, y: 10 },
              show: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } },
            }}
          >
            <button
              onClick={() => onNavigate('predictions')}
              className="editorial-underline-hover inline-flex items-center text-xs font-mono uppercase tracking-[0.2em] font-bold text-editorial-dark transition-all duration-300 gap-2 hover:opacity-80 pb-1 cursor-pointer"
            >
              DISCOVER PREDICTIONS <span className="text-sm">→</span>
            </button>
          </motion.div>
        </motion.div>
      </div>

      {/* Bottom Panel: Countdown + Scroll indicator */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1], delay: 0.4 }}
        className="relative z-10 w-full"
      >
        <div className="max-w-7xl mx-auto px-6 md:px-14 pb-7 pt-4">
          <div className="flex items-end justify-center">
            {/* Scroll to Explore indicator */}
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col items-center cursor-pointer group"
              onClick={() => {
                const el = document.getElementById('todays-best-predictions');
                if (el) el.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              <span className="text-[9px] uppercase tracking-[0.3em] text-[#1C1B17]/60 group-hover:text-[#1C1B17]/85 transition-colors duration-300 font-mono">
                Scroll to Explore
              </span>
              <motion.div
                animate={{ y: [0, 6, 0] }}
                transition={{
                  repeat: Infinity,
                  duration: 2.2,
                  ease: 'easeInOut',
                }}
                className="text-[#1C1B17]/60 group-hover:text-[#1C1B17]/85 transition-colors duration-300 mt-1.5"
              >
                <ChevronDown className="w-4 h-4" strokeWidth={1.2} />
              </motion.div>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
