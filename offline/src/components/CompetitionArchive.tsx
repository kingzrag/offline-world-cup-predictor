import { useRef, useState } from 'react';
import { motion, useScroll, useTransform } from 'motion/react';
import { DOMESTIC_LEAGUES, EUROPEAN_COMPETITIONS, CompetitionConfig } from '../config/competitions';

// ─── Variants ─────────────────────────────────────────────────────────────────
const headingVariants = {
  hidden: { opacity: 0, y: 28 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.9, ease: [0.16, 1, 0.3, 1] as const } },
};

const dividerVariants = {
  hidden: { scaleX: 0 },
  show:   { scaleX: 1, transition: { duration: 1.0, ease: [0.16, 1, 0.3, 1] as const, delay: 0.2 } },
};

// ─── Single editorial cover ───────────────────────────────────────────────────
interface CoverProps {
  comp: CompetitionConfig;
  index: number;
  onNavigate: (compId?: string) => void;
}

function getCoverDesign(name: string) {
  switch (name) {
    case 'Premier League':
      return {
        background: 'bg-[#1E1B4B]',
        gradient: 'bg-gradient-to-br from-[#2D2676] via-[#1E1B4B] to-[#0F0D2A]',
        overlay: (
          <>
            <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-[#6366F1]/15 to-transparent" />
            <div className="absolute bottom-8 right-8 w-40 h-40 opacity-8">
              <div className="absolute inset-0 border-2 border-[#6366F1]/20 rounded-t-full" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-24 bg-[#6366F1]/10 rounded-t-full" />
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
            <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-[#FF6B35]/12 to-transparent" />
            <div className="absolute bottom-0 left-0 right-0 h-1/3 bg-gradient-to-t from-[#FF6B35]/8 to-transparent" />
          </>
        ),
        textColor: 'text-[#1C1B17]',
        accentColor: '#FF6B35'
      };
    case 'Bundesliga':
      return {
        background: 'bg-[#F7F4EE]',
        gradient: 'bg-gradient-to-br from-[#FAF8F5] via-[#F7F4EE] to-[#F0EDE4]',
        overlay: (
          <>
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#DC2626]/20 to-transparent" />
            <div className="absolute top-6 right-6 w-1.5 h-1.5 bg-[#DC2626] rounded-full" />
          </>
        ),
        textColor: 'text-[#1C1B17]',
        accentColor: '#DC2626'
      };
    case 'Serie A':
      return {
        background: 'bg-[#F7F4EE]',
        gradient: 'bg-gradient-to-br from-[#FAF8F5] via-[#F7F4EE] to-[#E8E4DB]',
        overlay: (
          <>
            <div className="absolute inset-0 opacity-8">
              <div className="absolute top-12 left-12 w-20 h-20 border-l-2 border-t-2 border-[#1E40AF]/20" />
              <div className="absolute top-12 right-12 w-20 h-20 border-r-2 border-t-2 border-[#1E40AF]/20" />
            </div>
          </>
        ),
        textColor: 'text-[#1C1B17]',
        accentColor: '#1E40AF'
      };
    case 'Ligue 1':
      return {
        background: 'bg-[#F8F4EE]',
        gradient: 'bg-gradient-to-br from-[#FDF9F4] via-[#F8F4EE] to-[#EDEAE4]',
        overlay: (
          <>
            <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-[#003189]/10 to-transparent" />
            <div className="absolute bottom-0 right-0 w-32 h-32 bg-[#EF0107]/8 rounded-full blur-2xl" />
          </>
        ),
        textColor: 'text-[#1C1B17]',
        accentColor: '#003189'
      };
    case 'Eredivisie':
      return {
        background: 'bg-[#FFF7ED]',
        gradient: 'bg-gradient-to-br from-[#FFEDD5] via-[#FFF7ED] to-[#FED7AA]',
        overlay: (
          <>
            <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-[#EA580C]/10 to-transparent" />
            <div className="absolute top-6 right-6 w-1.5 h-1.5 bg-[#EA580C] rounded-full" />
          </>
        ),
        textColor: 'text-[#1C1B17]',
        accentColor: '#EA580C'
      };
    case 'Brasileirão Série A':
      return {
        background: 'bg-[#F0FDF4]',
        gradient: 'bg-gradient-to-br from-[#DCFCE7] via-[#F0FDF4] to-[#BBF7D0]',
        overlay: (
          <>
            <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-[#16A34A]/10 to-transparent" />
            <div className="absolute top-6 right-6 w-1.5 h-1.5 bg-[#16A34A] rounded-full" />
          </>
        ),
        textColor: 'text-[#1C1B17]',
        accentColor: '#16A34A'
      };
    case 'Major League Soccer':
      return {
        background: 'bg-[#EFF6FF]',
        gradient: 'bg-gradient-to-br from-[#DBEAFE] via-[#EFF6FF] to-[#BFDBFE]',
        overlay: (
          <>
            <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-[#2563EB]/10 to-transparent" />
          </>
        ),
        textColor: 'text-[#1C1B17]',
        accentColor: '#2563EB'
      };
    case 'UEFA Champions League':
      return {
        background: 'bg-[#0A1628]',
        gradient: 'bg-gradient-to-br from-[#2A4A7F] via-[#1A3050] to-[#0A1628]',
        overlay: (
          <>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-40 bg-[#4A7ABF]/20 rounded-full blur-2xl" />
            <div className="absolute inset-0 opacity-20">
              <div className="absolute top-12 left-16 w-1.5 h-1.5 bg-white rounded-full" />
              <div className="absolute top-20 left-24 w-1 h-1 bg-white rounded-full" />
            </div>
          </>
        ),
        textColor: 'text-white',
        accentColor: '#0066CC'
      };
    case 'UEFA Europa League':
      return {
        background: 'bg-[#1F2937]',
        gradient: 'bg-gradient-to-br from-[#4B5563] via-[#2D3748] to-[#1A202C]',
        overlay: (
          <>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-36 h-36 bg-[#F97316]/15 rounded-full blur-2xl" />
          </>
        ),
        textColor: 'text-white',
        accentColor: '#F97316'
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

function CompetitionCover({ comp, index, onNavigate }: CoverProps) {
  const design = getCoverDesign(comp.name);
  const isSupported = comp.status === 'SUPPORTED';

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{
        duration: 0.85,
        ease: [0.16, 1, 0.3, 1] as const,
        delay: 0.1 + index * 0.05,
      }}
      whileHover={{
        y: -6,
        scale: 1.02,
        transition: { duration: 0.35, ease: [0.215, 0.61, 0.355, 1] as const },
      }}
      onClick={() => onNavigate(comp.id)}
      className="relative flex flex-col items-center cursor-pointer group select-none"
      aria-label={`Browse ${comp.name}`}
    >
      {/* Contact shadow */}
      <div className="absolute top-1 left-1 right-1 bottom-0 bg-[#1C1B17]/6 blur-md rounded-sm -z-10" />
      <div className="absolute top-3 left-3 right-3 bottom-[-4px] bg-[#1C1B17]/4 blur-lg rounded-sm -z-10" />

      {/* Cover card */}
      <div
        className={`
          relative w-[165px] h-[175px] sm:w-[180px] sm:h-[180px]
          ${design.background} ${design.gradient}
          rounded-sm overflow-hidden
          shadow-[0_8px_24px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)]
          group-hover:shadow-[0_12px_32px_rgba(0,0,0,0.10),0_0_0_1px_rgba(0,0,0,0.06)]
          transition-all duration-350 ease-out
        `}
      >
        {/* Depth layers */}
        <div className="absolute inset-0 bg-gradient-to-b from-black/0 via-transparent to-black/10 pointer-events-none z-10" />
        <div className="absolute top-0 left-0 right-0 h-1/3 bg-gradient-to-b from-white/10 to-transparent pointer-events-none z-10" />
        <div className="absolute inset-0 bg-paper-grain opacity-15 pointer-events-none z-10" />

        {design.overlay}

        {/* Top metadata strip */}
        <div className="absolute top-0 left-0 right-0 px-3 pt-2.5 pb-1 flex items-center justify-between z-20">
          <span className="text-[5px] font-mono tracking-[0.3em] text-white/50 uppercase font-medium">OFFLINE</span>
          <span className="text-[5.5px] font-mono tracking-[0.2em] text-white/50 uppercase font-bold">{comp.shortName}</span>
        </div>

        {/* Logo centered */}
        <div className="absolute inset-0 flex flex-col items-center justify-center z-20 px-4 -mt-2">
          <img
            src={comp.logo}
            alt={comp.name}
            loading="lazy"
            className="w-12 h-12 sm:w-14 sm:h-14 object-contain drop-shadow-[0_4px_12px_rgba(0,0,0,0.25)] transition-transform duration-500 group-hover:scale-105"
          />
        </div>

        {/* Status Overlay Badge if not fully active */}
        {!isSupported && comp.statusText && (
          <div className="absolute inset-x-2 bottom-8 z-30 flex justify-center">
            <span className="px-2 py-0.5 text-[6.5px] font-mono uppercase tracking-wider rounded bg-black/65 text-amber-200 border border-amber-400/30 backdrop-blur-sm shadow-sm text-center leading-tight">
              {comp.statusText}
            </span>
          </div>
        )}

        {/* Thin divider */}
        <div className="absolute bottom-8 left-4 right-4 h-[0.5px] bg-white/15 z-20" />

        {/* Competition name */}
        <div className="absolute bottom-0 left-0 right-0 px-2 pb-2.5 pt-1.5 bg-gradient-to-t from-black/60 via-black/40 to-transparent z-20">
          <p className={`text-[7.5px] sm:text-[8px] font-serif tracking-[0.12em] leading-tight text-center ${design.textColor} uppercase font-medium line-clamp-1`}>
            {comp.name}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
interface CompetitionArchiveProps {
  onNavigate: (compId?: string) => void;
}

export default function CompetitionArchive({ onNavigate }: CompetitionArchiveProps) {
  const sectionRef = useRef<HTMLElement>(null);
  const [settled, setSettled] = useState(false);

  const { scrollYProgress: exitProgress } = useScroll({
    target: sectionRef,
    offset: ['start start', 'end start'],
  });
  const exitOpacity = useTransform(exitProgress, [0, 0.85, 1], [1, 1, 0.9]);

  return (
    <motion.section
      ref={sectionRef}
      id="competition-archive"
      className="relative w-full py-20 bg-[#F6F4EF] bg-paper-grain paper-overlay flex flex-col justify-center border-t border-[#1C1B17]/8"
      aria-label="Explore Competitions"
      style={{ opacity: exitOpacity }}
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.08 }}
      transition={{ duration: 1.0, ease: [0.16, 1, 0.3, 1] }}
      onAnimationComplete={() => setSettled(true)}
    >
      <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-white/40 to-transparent pointer-events-none" />
      <div className="absolute inset-0 bg-paper-grain opacity-10 pointer-events-none" />

      <motion.div
        className="relative z-10 w-full max-w-7xl mx-auto px-6 md:px-12 flex flex-col"
        initial="hidden"
        animate={settled ? 'show' : 'hidden'}
      >
        {/* Heading */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-3">
          <motion.div variants={headingVariants}>
            <span className="text-[10px] font-mono tracking-[0.3em] text-[#3a5c2d] uppercase block font-bold mb-1">
              SUPPORTED COMPETITIONS
            </span>
            <h2 className="text-3xl sm:text-4xl md:text-[40px] font-serif text-[#1C1B17] tracking-tight leading-tight">
              Explore Active Competitions
            </h2>
            <p className="text-[#1C1B17]/60 text-xs mt-1.5 max-w-2xl font-sans font-light leading-relaxed">
              Explore domestic football leagues and European club competitions supported by our platform. 
              Click any competition to view live predictions, xG analytics, and betting markets.
            </p>
          </motion.div>
        </div>

        <motion.div
          className="w-full h-[1px] bg-[#1C1B17]/12 origin-left mb-12"
          variants={dividerVariants}
        />

        {/* ── Section 1: DOMESTIC LEAGUES ────────────────────────────────────── */}
        <div className="mb-14">
          <div className="flex items-center gap-2 mb-6">
            <span className="text-xs font-mono uppercase tracking-[0.25em] text-[#1C1B17]/50 font-semibold">01 /</span>
            <h3 className="text-sm font-mono uppercase tracking-[0.25em] text-[#1C1B17] font-bold">Domestic Leagues</h3>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-4 gap-6 sm:gap-8 justify-items-center">
            {DOMESTIC_LEAGUES.map((comp, i) => (
              <CompetitionCover
                key={comp.id}
                comp={comp}
                index={i}
                onNavigate={onNavigate}
              />
            ))}
          </div>
        </div>

        {/* ── Section 2: EUROPEAN CLUB COMPETITIONS ──────────────────────────── */}
        <div>
          <div className="flex items-center gap-2 mb-6">
            <span className="text-xs font-mono uppercase tracking-[0.25em] text-[#1C1B17]/50 font-semibold">02 /</span>
            <h3 className="text-sm font-mono uppercase tracking-[0.25em] text-[#1C1B17] font-bold">European Club Competitions</h3>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 sm:gap-8 justify-items-start">
            {EUROPEAN_COMPETITIONS.map((comp, i) => (
              <CompetitionCover
                key={comp.id}
                comp={comp}
                index={i + 8}
                onNavigate={onNavigate}
              />
            ))}
          </div>
        </div>

      </motion.div>
    </motion.section>
  );
}
