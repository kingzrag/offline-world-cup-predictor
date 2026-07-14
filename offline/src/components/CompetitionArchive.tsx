import { useRef, useState } from 'react';
import { motion, useScroll, useTransform } from 'motion/react';

// ─── Competition data (matches CompetitionSelector exactly) ──────────────────
const SHELF_ONE = [
  { name: 'FIFA World Cup',  abbr: 'WC 2026',   logo: '/leagues/world-cup.svg',         alt: 'FIFA World Cup'    },
  { name: 'Premier League',  abbr: 'EPL',        logo: '/leagues/premier-league.svg',    alt: 'Premier League'    },
  { name: 'La Liga',         abbr: 'LIGA',       logo: '/leagues/la-liga-seeklogo.png',  alt: 'La Liga'           },
  { name: 'Bundesliga',      abbr: 'BL 1',       logo: '/leagues/bundesliga.png',        alt: 'Bundesliga'        },
];

const SHELF_TWO = [
  { name: 'Champions League', abbr: 'UCL',       logo: '/leagues/champions-league.svg',  alt: 'Champions League'  },
  { name: 'Europa League',    abbr: 'UEL',       logo: '/leagues/europa-league.svg',     alt: 'Europa League'     },
  { name: 'Serie A',          abbr: 'SA',        logo: '/leagues/serie-a.png',            alt: 'Serie A'           },
];

// ─── Variants ─────────────────────────────────────────────────────────────────
const headingVariants = {
  hidden: { opacity: 0, y: 28 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.9, ease: [0.16, 1, 0.3, 1] as const } },
};

const dividerVariants = {
  hidden: { scaleX: 0 },
  show:   { scaleX: 1, transition: { duration: 1.0, ease: [0.16, 1, 0.3, 1] as const, delay: 0.2 } },
};

const shelfOneVariants = {
  hidden: { opacity: 0, x: -60 },
  show:   { opacity: 1, x: 0, transition: { duration: 1.0, ease: [0.16, 1, 0.3, 1] as const, delay: 0.35 } },
};

const shelfTwoVariants = {
  hidden: { opacity: 0, x: 60 },
  show:   { opacity: 1, x: 0, transition: { duration: 1.0, ease: [0.16, 1, 0.3, 1] as const, delay: 0.45 } },
};

// ─── Single editorial cover ───────────────────────────────────────────────────
interface CoverProps {
  name:  string;
  abbr:  string;
  logo:  string;
  alt:   string;
  index: number;
  onNavigate: () => void;
}

function CompetitionCover({ name, abbr, logo, alt, index, onNavigate }: CoverProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 32 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{
        duration: 0.85,
        ease: [0.16, 1, 0.3, 1] as const,
        delay: 0.4 + index * 0.08,
      }}
      whileHover={{
        y: -10,
        rotate: index % 2 === 0 ? 1.5 : -1.5,
        scale: 1.03,
        transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] as const },
      }}
      onClick={onNavigate}
      className="relative flex flex-col items-center cursor-pointer group select-none"
      aria-label={`Browse ${name}`}
    >
      {/* Cover card */}
      <div
        className="
          relative w-36 sm:w-40 md:w-44 aspect-[2/3]
          bg-[#F3F0E8] border border-[#1C1B17]/10
          rounded-sm overflow-hidden
          shadow-[0_6px_28px_rgba(28,27,23,0.10),0_2px_6px_rgba(28,27,23,0.06)]
          group-hover:shadow-[0_18px_52px_rgba(28,27,23,0.20),0_4px_12px_rgba(28,27,23,0.10)]
          group-hover:border-[#1C1B17]/20
          transition-shadow transition-border duration-500
        "
      >
        {/* Paper grain overlay */}
        <div className="absolute inset-0 bg-paper-grain opacity-30 pointer-events-none z-10" />

        {/* Top thin rule */}
        <div className="absolute top-0 left-0 right-0 h-[3px] bg-[#1C1B17]/90 z-20" />

        {/* Top metadata strip */}
        <div className="absolute top-[3px] left-0 right-0 px-3 pt-2 pb-1 flex items-center justify-between z-20">
          <span className="text-[6.5px] font-mono tracking-[0.25em] text-[#1C1B17]/50 uppercase">OFFLINE</span>
          <span className="text-[6.5px] font-mono tracking-[0.2em] text-[#1C1B17]/40 uppercase">{abbr}</span>
        </div>

        {/* Logo centred */}
        <div className="absolute inset-0 flex items-center justify-center z-20">
          <img
            src={logo}
            alt={alt}
            loading="lazy"
            className="w-16 h-16 sm:w-20 sm:h-20 object-contain drop-shadow-[0_2px_8px_rgba(28,27,23,0.18)] transition-transform duration-500 group-hover:scale-105"
          />
        </div>

        {/* Bottom title strip */}
        <div className="absolute bottom-0 left-0 right-0 px-3 pt-2 pb-3 bg-gradient-to-t from-[#F3F0E8] via-[#F3F0E8]/90 to-transparent z-20">
          <div className="h-[0.5px] w-full bg-[#1C1B17]/12 mb-2" />
          <p className="text-[8px] font-serif text-[#1C1B17]/80 tracking-[0.08em] leading-tight text-center line-clamp-2 uppercase">
            {name}
          </p>
        </div>

        {/* Hover reveal — green accent edge */}
        <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-[#3a5c2d] opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-30" />
      </div>

      {/* Below-card index number */}
      <span className="mt-3 text-[9px] font-mono tracking-[0.25em] text-[#1C1B17]/30 uppercase">
        {String(index + 1).padStart(2, '0')}
      </span>
    </motion.div>
  );
}

// ─── Main exported section ────────────────────────────────────────────────────
interface CompetitionArchiveProps {
  onNavigate: () => void;   // navigateTo('predictions') — already implemented
}

export default function CompetitionArchive({ onNavigate }: CompetitionArchiveProps) {
  const sectionRef = useRef<HTMLElement>(null);
  const [settled, setSettled] = useState(false);

  // Subtle scroll parallax — shelves drift upward slower than page
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start end', 'end start'],
  });
  const shelvesY = useTransform(scrollYProgress, [0, 1], [0, -40]);

  // Scroll-driven exit — section gently dims and compresses as it scrolls away
  const { scrollYProgress: exitProgress } = useScroll({
    target: sectionRef,
    offset: ['start start', 'end start'],
  });
  const exitOpacity = useTransform(exitProgress, [0, 0.75, 1], [1, 1, 0.85]);
  const exitScale   = useTransform(exitProgress, [0, 1], [1, 0.985]);

  return (
    <motion.section
      ref={sectionRef}
      id="competition-archive"
      className="relative w-full h-[100dvh] bg-editorial-white overflow-hidden snap-start origin-center"
      aria-label="Explore Every Competition"
      style={{ opacity: exitOpacity, scale: exitScale }}
      initial={{ opacity: 0, y: 40, scale: 0.98 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true, amount: 0.12 }}
      transition={{ duration: 0.7, ease: [0.215, 0.61, 0.355, 1] }}
      onAnimationComplete={() => setSettled(true)}
    >
      {/* Very subtle grain layer */}
      <div className="absolute inset-0 bg-paper-grain opacity-20 pointer-events-none" />

      <motion.div
        className="relative z-10 w-full max-w-7xl mx-auto px-6 md:px-12"
        initial="hidden"
        animate={settled ? 'show' : 'hidden'}
      >
        {/* ── Heading block ─────────────────────────────────────────────── */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-7">
          <motion.div variants={headingVariants}>
            <span className="text-[10px] font-mono tracking-[0.3em] text-[#3a5c2d] uppercase block font-bold mb-2">
              COMPETITION ARCHIVE
            </span>
            <h2 className="text-3xl sm:text-4xl md:text-[46px] font-serif text-[#1C1B17] tracking-tight leading-tight">
              Explore Every Competition
            </h2>
            <p className="text-[#1C1B17]/50 text-sm mt-3 max-w-xl font-sans font-light leading-relaxed">
              Browse every football competition through OFFLINE Intelligence.
              Every competition contains predictions, statistics, AI insights and match analysis.
            </p>
          </motion.div>
        </div>

        {/* ── Thin full-width divider (draws left → right) ──────────────── */}
        <motion.div
          className="w-full h-[1px] bg-[#1C1B17]/12 origin-left mb-14"
          variants={dividerVariants}
        />

        {/* ── Shelves with scroll-parallax ──────────────────────────────── */}
        <motion.div style={{ y: shelvesY }} className="flex flex-col gap-14">

          {/* ── Shelf 1 ── slides from left ──────────────────────────────── */}
          <motion.div variants={shelfOneVariants} className="relative">
            {/* Shelf plank */}
            <div className="relative">
              <div className="flex flex-wrap sm:flex-nowrap items-end gap-6 sm:gap-8 pb-5">
                {SHELF_ONE.map((comp, i) => (
                  <CompetitionCover
                    key={comp.name}
                    {...comp}
                    index={i}
                    onNavigate={onNavigate}
                  />
                ))}
              </div>
              {/* Shelf ledge */}
              <div className="w-full h-[1.5px] bg-gradient-to-r from-[#1C1B17]/18 via-[#1C1B17]/10 to-transparent rounded-full" />
              <div className="w-full h-[4px] bg-gradient-to-b from-[#1C1B17]/6 to-transparent rounded-b-sm" />
            </div>
          </motion.div>

          {/* ── Shelf 2 ── slides from right ─────────────────────────────── */}
          <motion.div variants={shelfTwoVariants} className="relative">
            <div className="relative">
              <div className="flex flex-wrap sm:flex-nowrap items-end gap-6 sm:gap-8 pb-5">
                {SHELF_TWO.map((comp, i) => (
                  <CompetitionCover
                    key={comp.name}
                    {...comp}
                    index={i}
                    onNavigate={onNavigate}
                  />
                ))}
              </div>
              {/* Shelf ledge */}
              <div className="w-full h-[1.5px] bg-gradient-to-r from-[#1C1B17]/18 via-[#1C1B17]/10 to-transparent rounded-full" />
              <div className="w-full h-[4px] bg-gradient-to-b from-[#1C1B17]/6 to-transparent rounded-b-sm" />
            </div>
          </motion.div>

        </motion.div>
      </motion.div>
    </motion.section>
  );
}
