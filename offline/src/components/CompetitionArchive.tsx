import { useRef, useState } from 'react';
import { motion, useScroll, useTransform } from 'motion/react';

// ─── Competition data (matches CompetitionSelector exactly) ──────────────────
const SHELF_ONE = [
  { name: 'FIFA World Cup',   abbr: 'WC 2026',   logo: '/leagues/world-cup.svg',         alt: 'FIFA World Cup'    },
  { name: 'Premier League',   abbr: 'EPL',        logo: '/leagues/premier-league.svg',    alt: 'Premier League'    },
  { name: 'La Liga',          abbr: 'LIGA',       logo: '/leagues/la-liga-seeklogo.png',  alt: 'La Liga'           },
  { name: 'Bundesliga',       abbr: 'BL 1',       logo: '/leagues/bundesliga.png',        alt: 'Bundesliga'        },
];

const SHELF_TWO = [
  { name: 'Champions League',  abbr: 'UCL',       logo: '/leagues/champions-league.svg',  alt: 'Champions League'  },
  { name: 'Europa League',     abbr: 'UEL',       logo: '/leagues/europa-league.svg',     alt: 'Europa League'     },
  { name: 'Serie A',           abbr: 'SA',        logo: '/leagues/serie-a.png',            alt: 'Serie A'           },
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

const fadeVariants = {
  hidden: { opacity: 0 },
  show:   { opacity: 1, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] as const, delay: 0.3 } },
};

const shelfVariants = {
  hidden: { opacity: 0, y: 30 },
  show:   { opacity: 1, y: 0, transition: { duration: 1.0, ease: [0.16, 1, 0.3, 1] as const, delay: 0.4 } },
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

// ─── Competition-specific cover designs ─────────────────────────────────────────
function getCoverDesign(name: string) {
  switch (name) {
    case 'FIFA World Cup':
      return {
        background: 'bg-[#0A0A0A]',
        gradient: 'bg-gradient-to-br from-[#1A1A1A] via-[#0A0A0A] to-[#151515]',
        overlay: (
          <>
            <div className="absolute inset-0 opacity-20">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 rounded-full bg-gradient-to-br from-[#D4AF37] to-transparent blur-3xl" />
            </div>
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGZpbHRlciBpZD0ibm9pc2UiPjxmZVR1cmJ1bGVuY2UgdHlwZT0iZnJhY3RhbE5vaXNlIiBiYXNlRnJlcXVlbmN5PSIwLjUiIHN0aXRjaFRpbGVzPSJzdGl0Y2giLz48L2ZpbHRlcj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWx0ZXI9InVybCgjbm9pc2UpIiBvcGFjaXR5PSIwLjAzIi8+PC9zdmc+')] opacity-40" />
          </>
        ),
        textColor: 'text-[#D4AF37]',
        accentColor: '#D4AF37'
      };
    case 'Premier League':
      return {
        background: 'bg-[#1E1B4B]',
        gradient: 'bg-gradient-to-br from-[#2D2676] via-[#1E1B4B] to-[#0F0D2A]',
        overlay: (
          <>
            <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-[#6366F1]/20 to-transparent" />
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-8 right-8 w-32 h-32 border border-[#6366F1]/30 rounded-full" />
              <div className="absolute bottom-12 left-12 w-24 h-24 border border-[#6366F1]/20 rounded-full" />
            </div>
          </>
        ),
        textColor: 'text-white',
        accentColor: '#6366F1'
      };
    case 'La Liga':
      return {
        background: 'bg-[#F5F0E6]',
        gradient: 'bg-gradient-to-br from-[#FFF8F0] via-[#F5F0E6] to-[#FFE8D6]',
        overlay: (
          <>
            <div className="absolute top-0 left-0 right-0 h-1/3 bg-gradient-to-b from-[#FF6B35]/15 to-transparent" />
            <div className="absolute bottom-0 left-0 right-0 h-1/4 bg-gradient-to-t from-[#FF6B35]/10 to-transparent" />
          </>
        ),
        textColor: 'text-[#1C1B17]',
        accentColor: '#FF6B35'
      };
    case 'Bundesliga':
      return {
        background: 'bg-[#FFFFFF]',
        gradient: 'bg-gradient-to-br from-[#FAFAFA] via-[#FFFFFF] to-[#F0F0F0]',
        overlay: (
          <>
            <div className="absolute inset-0 opacity-5">
              <div className="absolute top-0 left-0 w-full h-full" style={{
                backgroundImage: 'linear-gradient(45deg, #DC2626 25%, transparent 25%, transparent 75%, #DC2626 75%, #DC2626), linear-gradient(45deg, #DC2626 25%, transparent 25%, transparent 75%, #DC2626 75%, #DC2626)',
                backgroundSize: '20px 20px',
                backgroundPosition: '0 0, 10px 10px'
              }} />
            </div>
            <div className="absolute top-4 right-4 w-2 h-2 bg-[#DC2626] rounded-full" />
          </>
        ),
        textColor: 'text-[#1C1B17]',
        accentColor: '#DC2626'
      };
    case 'Champions League':
      return {
        background: 'bg-[#0A1628]',
        gradient: 'bg-gradient-to-br from-[#1E3A5F] via-[#0A1628] to-[#050A14]',
        overlay: (
          <>
            <div className="absolute inset-0 opacity-30">
              {Array.from({ length: 20 }).map((_, i) => (
                <div
                  key={i}
                  className="absolute w-1 h-1 bg-white rounded-full"
                  style={{
                    top: `${Math.random() * 100}%`,
                    left: `${Math.random() * 100}%`,
                    opacity: Math.random() * 0.5 + 0.2
                  }}
                />
              ))}
            </div>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-40 bg-[#0066CC]/20 rounded-full blur-2xl" />
          </>
        ),
        textColor: 'text-white',
        accentColor: '#0066CC'
      };
    case 'Europa League':
      return {
        background: 'bg-[#1F2937]',
        gradient: 'bg-gradient-to-br from-[#374151] via-[#1F2937] to-[#111827]',
        overlay: (
          <>
            <div className="absolute top-0 right-0 w-32 h-32 bg-[#F97316]/10 rounded-full blur-2xl" />
            <div className="absolute bottom-0 left-0 w-24 h-24 bg-[#F97316]/5 rounded-full blur-xl" />
          </>
        ),
        textColor: 'text-white',
        accentColor: '#F97316'
      };
    case 'Serie A':
      return {
        background: 'bg-[#F5F0E6]',
        gradient: 'bg-gradient-to-br from-[#FFF8F0] via-[#F5F0E6] to-[#E8E4DB]',
        overlay: (
          <>
            <div className="absolute inset-0 opacity-8">
              <div className="absolute top-0 left-0 w-full h-full" style={{
                backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 20px, #1E40AF 20px, #1E40AF 21px), repeating-linear-gradient(0deg, transparent, transparent 20px, #1E40AF 20px, #1E40AF 21px)',
                opacity: 0.03
              }} />
            </div>
            <div className="absolute top-6 left-6 w-16 h-16 border-l-2 border-t-2 border-[#1E40AF]/30" />
            <div className="absolute bottom-6 right-6 w-16 h-16 border-r-2 border-b-2 border-[#1E40AF]/30" />
          </>
        ),
        textColor: 'text-[#1C1B17]',
        accentColor: '#1E40AF'
      };
    default:
      return {
        background: 'bg-[#F3F0E8]',
        gradient: 'bg-gradient-to-br from-[#F8F5F0] via-[#F3F0E8] to-[#E8E4DB]',
        overlay: null,
        textColor: 'text-[#1C1B17]',
        accentColor: '#1C1B17'
      };
  }
}

function CompetitionCover({ name, abbr, logo, alt, index, onNavigate }: CoverProps) {
  const design = getCoverDesign(name);
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{
        duration: 0.85,
        ease: [0.16, 1, 0.3, 1] as const,
        delay: 0.15 + index * 0.06,
      }}
      whileHover={{
        y: -10,
        rotate: index % 2 === 0 ? 2 : -2,
        scale: 1.03,
        transition: { duration: 0.35, ease: [0.215, 0.61, 0.355, 1] as const },
      }}
      onClick={onNavigate}
      className="relative flex flex-col items-center cursor-pointer group select-none"
      aria-label={`Browse ${name}`}
    >
      {/* Cover card */}
      <div
        className={`
          relative w-[280px] h-[280px]
          ${design.background} ${design.gradient}
          rounded-sm overflow-hidden
          shadow-[0_18px_45px_rgba(0,0,0,0.08)]
          group-hover:shadow-[0_28px_70px_rgba(0,0,0,0.14)]
          group-hover:scale-[1.03]
          group-hover:brightness-110
          transition-all duration-350
          transition-timing-function cubic-bezier(0.215, 0.61, 0.355, 1)
        `}
      >
        {/* Paper grain overlay */}
        <div className="absolute inset-0 bg-paper-grain opacity-20 pointer-events-none z-10" />

        {/* Competition-specific overlay */}
        {design.overlay}

        {/* Top metadata strip */}
        <div className="absolute top-0 left-0 right-0 px-4 pt-3 pb-2 flex items-center justify-between z-20">
          <span className="text-[7px] font-mono tracking-[0.25em] text-white/40 uppercase">OFFLINE</span>
          <span className="text-[7px] font-mono tracking-[0.2em] text-white/30 uppercase">{abbr}</span>
        </div>

        {/* Logo centered with generous whitespace */}
        <div className="absolute inset-0 flex items-center justify-center z-20 px-8">
          <img
            src={logo}
            alt={alt}
            loading="lazy"
            className="w-24 h-24 object-contain drop-shadow-[0_4px_12px_rgba(0,0,0,0.25)] transition-transform duration-500 group-hover:scale-110"
          />
        </div>

        {/* Competition name at bottom with premium typography */}
        <div className="absolute bottom-0 left-0 right-0 px-4 pb-4 pt-8 bg-gradient-to-t from-black/40 via-black/20 to-transparent z-20">
          <div className="h-[0.5px] w-full bg-white/20 mb-3" />
          <p className={`text-[11px] font-serif tracking-[0.08em] leading-tight text-center ${design.textColor} uppercase`}>
            {name}
          </p>
        </div>
      </div>

      {/* Below-card index number */}
      <span className="mt-2 text-[8px] font-mono tracking-[0.25em] text-[#1C1B17]/30 uppercase">
        {String(index + 1).padStart(2, '0')}
      </span>
    </motion.div>
  );
}

// ─── Main exported section ────────────────────────────────────────────────────
interface CompetitionArchiveProps {
  onNavigate: () => void;
}

export default function CompetitionArchive({ onNavigate }: CompetitionArchiveProps) {
  const sectionRef = useRef<HTMLElement>(null);
  const [settled, setSettled] = useState(false);

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
      className="relative w-full h-[100dvh] bg-[#F6F4EF] overflow-hidden snap-start origin-center flex flex-col justify-center"
      aria-label="Explore Every Competition"
      style={{ opacity: exitOpacity, scale: exitScale }}
      initial={{ opacity: 0, y: 40, scale: 0.98 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true, amount: 0.12 }}
      transition={{ duration: 0.7, ease: [0.215, 0.61, 0.355, 1] }}
      onAnimationComplete={() => setSettled(true)}
    >
      {/* Soft ambient light from above */}
      <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-white/40 to-transparent pointer-events-none" />
      
      {/* Very subtle grain layer */}
      <div className="absolute inset-0 bg-paper-grain opacity-15 pointer-events-none" />

      <motion.div
        className="relative z-10 w-full max-w-7xl mx-auto px-6 md:px-12 flex flex-col justify-center"
        initial="hidden"
        animate={settled ? 'show' : 'hidden'}
      >
        {/* ── Heading block ─────────────────────────────────────────────── */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-3">
          <motion.div variants={headingVariants}>
            <span className="text-[10px] font-mono tracking-[0.3em] text-[#3a5c2d] uppercase block font-bold mb-1">
              COMPETITION ARCHIVE
            </span>
            <h2 className="text-3xl sm:text-4xl md:text-[40px] font-serif text-[#1C1B17] tracking-tight leading-tight">
              Explore Every Competition
            </h2>
            <p className="text-[#1C1B17]/50 text-xs mt-1.5 max-w-xl font-sans font-light leading-relaxed">
              Browse every football competition through OFFLINE Intelligence.
              Every competition contains predictions, statistics, AI insights and match analysis.
            </p>
          </motion.div>
        </div>

        {/* ── Thin full-width divider (draws left → right) ──────────────── */}
        <motion.div
          className="w-full h-[1px] bg-[#1C1B17]/12 origin-left mb-6"
          variants={dividerVariants}
        />

        {/* ── Premium floating museum shelves ──────────────────────────────────── */}
        <motion.div variants={shelfVariants} className="relative mt-6 space-y-20">
          
          {/* ── Shelf One ── */}
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 1.0, ease: [0.16, 1, 0.3, 1] as const, delay: 0.4 }}
            className="relative"
          >
            {/* Shelf platform with depth */}
            <div className="relative w-[85%] mx-auto">
              {/* Enhanced floating shadow */}
              <div className="absolute -bottom-8 left-6 right-6 h-12 bg-[#1C1B17]/12 blur-2xl rounded-full" />
              <div className="absolute -bottom-4 left-8 right-8 h-8 bg-[#1C1B17]/6 blur-xl rounded-full" />
              
              {/* Shelf surface */}
              <div className="relative bg-gradient-to-b from-[#E8E4DB] to-[#D9D5CC] rounded-sm shadow-[0_12px_40px_rgba(28,27,23,0.15),0_4px_12px_rgba(28,27,23,0.10)]">
                {/* Shelf top edge highlight */}
                <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-[#1C1B17]/15 via-[#1C1B17]/8 to-[#1C1B17]/15" />
                
                {/* Cards on shelf */}
                <div className="flex items-end justify-center gap-10 sm:gap-14 px-10 py-8">
                  {SHELF_ONE.map((comp, i) => (
                    <CompetitionCover
                      key={comp.name}
                      {...comp}
                      index={i}
                      onNavigate={onNavigate}
                    />
                  ))}
                </div>
              </div>
            </div>
          </motion.div>

          {/* ── Shelf Two ── */}
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 1.0, ease: [0.16, 1, 0.3, 1] as const, delay: 0.5 }}
            className="relative"
          >
            {/* Shelf platform with depth */}
            <div className="relative w-[85%] mx-auto">
              {/* Enhanced floating shadow */}
              <div className="absolute -bottom-8 left-6 right-6 h-12 bg-[#1C1B17]/12 blur-2xl rounded-full" />
              <div className="absolute -bottom-4 left-8 right-8 h-8 bg-[#1C1B17]/6 blur-xl rounded-full" />
              
              {/* Shelf surface */}
              <div className="relative bg-gradient-to-b from-[#E8E4DB] to-[#D9D5CC] rounded-sm shadow-[0_12px_40px_rgba(28,27,23,0.15),0_4px_12px_rgba(28,27,23,0.10)]">
                {/* Shelf top edge highlight */}
                <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-[#1C1B17]/15 via-[#1C1B17]/8 to-[#1C1B17]/15" />
                
                {/* Cards on shelf */}
                <div className="flex items-end justify-center gap-10 sm:gap-14 px-10 py-8">
                  {SHELF_TWO.map((comp, i) => (
                    <CompetitionCover
                      key={comp.name}
                      {...comp}
                      index={i + 4}
                      onNavigate={onNavigate}
                    />
                  ))}
                </div>
              </div>
            </div>
          </motion.div>

        </motion.div>

      </motion.div>
    </motion.section>
  );
}

