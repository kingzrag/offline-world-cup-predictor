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
        gradient: 'bg-gradient-to-br from-[#1A1A1A] via-[#0A0A0A] to-[#0D0D0D]',
        overlay: (
          <>
            {/* Trophy silhouette - subtle gold glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-56 h-56 opacity-15">
              <div className="absolute inset-0 bg-gradient-to-br from-[#D4AF37] via-[#FFD700] to-[#B8860B] blur-3xl rounded-full" />
            </div>
            {/* Subtle trophy shape silhouette */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-40 opacity-8">
              <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-24 h-24 bg-[#D4AF37] rounded-full blur-sm" />
              <div className="absolute bottom-20 left-1/2 -translate-x-1/2 w-8 h-16 bg-[#D4AF37] rounded-t-lg blur-sm" />
            </div>
            {/* Paper texture */}
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGZpbHRlciBpZD0ibm9pc2UiPjxmZVR1cmJ1bGVuY2UgdHlwZT0iZnJhY3RhbE5vaXNlIiBiYXNlRnJlcXVlbmN5PSIwLjUiIHN0aXRjaFRpbGVzPSJzdGl0Y2giLz48L2ZpbHRlcj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWx0ZXI9InVybCgjbm9pc2UpIiBvcGFjaXR5PSIwLjAyIi8+PC9zdmc+')] opacity-30" />
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
            {/* Soft spotlight from top */}
            <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-[#6366F1]/15 to-transparent" />
            {/* Lion watermark - subtle geometric lion silhouette */}
            <div className="absolute bottom-8 right-8 w-40 h-40 opacity-8">
              <div className="absolute inset-0 border-2 border-[#6366F1]/20 rounded-t-full" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-24 bg-[#6366F1]/10 rounded-t-full" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 w-16 h-4 bg-[#6366F1]/10 rounded-full" />
            </div>
            {/* Subtle crown element */}
            <div className="absolute top-12 left-12 w-16 h-8 opacity-6">
              <div className="absolute bottom-0 left-0 right-0 h-2 bg-[#FFD700]/30 rounded" />
              <div className="absolute bottom-2 left-2 w-3 h-4 bg-[#FFD700]/20 rounded-t" />
              <div className="absolute bottom-2 right-2 w-3 h-4 bg-[#FFD700]/20 rounded-t" />
              <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-[#FFD700]/20 rounded-t" />
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
            {/* Stadium lighting effect - warm orange glow from top */}
            <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-[#FF6B35]/12 to-transparent" />
            {/* Stadium silhouette - subtle arches */}
            <div className="absolute bottom-0 left-0 right-0 h-32 opacity-6">
              <div className="absolute bottom-0 left-4 w-20 h-24 bg-[#FF6B35]/10 rounded-t-full" />
              <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-32 h-28 bg-[#FF6B35]/10 rounded-t-full" />
              <div className="absolute bottom-0 right-4 w-20 h-24 bg-[#FF6B35]/10 rounded-t-full" />
            </div>
            {/* Soft orange gradient accent */}
            <div className="absolute bottom-0 left-0 right-0 h-1/3 bg-gradient-to-t from-[#FF6B35]/8 to-transparent" />
          </>
        ),
        textColor: 'text-[#1C1B17]',
        accentColor: '#FF6B35'
      };
    case 'Bundesliga':
      return {
        background: 'bg-[#FFFFFF]',
        gradient: 'bg-gradient-to-br from-[#FAFAFA] via-[#FFFFFF] to-[#F5F5F5]',
        overlay: (
          <>
            {/* Modern geometric pattern - clean lines */}
            <div className="absolute inset-0 opacity-4">
              <div className="absolute top-8 left-8 w-24 h-24 border border-[#1C1B17]/10 rotate-45" />
              <div className="absolute bottom-8 right-8 w-32 h-32 border border-[#1C1B17]/8" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-40 border border-[#1C1B17]/6 rounded-full" />
            </div>
            {/* Red accent line */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#DC2626]/20 to-transparent" />
            {/* Subtle red dot accent */}
            <div className="absolute top-6 right-6 w-1.5 h-1.5 bg-[#DC2626] rounded-full" />
            {/* Charcoal geometric elements */}
            <div className="absolute bottom-12 left-12 w-12 h-12 border-l-2 border-b-2 border-[#1C1B17]/10" />
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
            {/* Constellation pattern - elegant stars */}
            <div className="absolute inset-0 opacity-25">
              <div className="absolute top-12 left-16 w-1.5 h-1.5 bg-white rounded-full" />
              <div className="absolute top-20 left-24 w-1 h-1 bg-white rounded-full" />
              <div className="absolute top-8 left-32 w-1 h-1 bg-white rounded-full" />
              <div className="absolute top-16 right-20 w-1.5 h-1.5 bg-white rounded-full" />
              <div className="absolute bottom-24 right-16 w-1 h-1 bg-white rounded-full" />
              <div className="absolute bottom-16 left-20 w-1 h-1 bg-white rounded-full" />
              <div className="absolute top-1/3 right-1/3 w-1 h-1 bg-white rounded-full" />
              <div className="absolute bottom-1/3 left-1/3 w-1 h-1 bg-white rounded-full" />
              {/* Constellation lines */}
              <svg className="absolute inset-0 w-full h-full" style={{ opacity: 0.15 }}>
                <line x1="64" y1="48" x2="96" y2="80" stroke="white" strokeWidth="0.5" />
                <line x1="96" y1="80" x2="128" y2="32" stroke="white" strokeWidth="0.5" />
                <line x1="128" y1="32" x2="192" y2="64" stroke="white" strokeWidth="0.5" />
              </svg>
            </div>
            {/* Elegant blue glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-[#0066CC]/15 rounded-full blur-3xl" />
            {/* Star burst accent */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 opacity-10">
              <div className="absolute inset-0 bg-gradient-to-br from-[#0066CC] to-transparent" style={{ clipPath: 'polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)' }} />
            </div>
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
            {/* Orange lighting from top-right */}
            <div className="absolute top-0 right-0 w-40 h-40 bg-[#F97316]/12 rounded-full blur-3xl" />
            <div className="absolute top-8 right-8 w-24 h-24 bg-[#F97316]/8 rounded-full blur-2xl" />
            {/* Subtle orange accent lines */}
            <div className="absolute top-0 right-0 w-full h-full opacity-6">
              <div className="absolute top-12 right-12 w-20 h-0.5 bg-[#F97316]/30" />
              <div className="absolute top-16 right-8 w-16 h-0.5 bg-[#F97316]/20" />
              <div className="absolute top-20 right-4 w-12 h-0.5 bg-[#F97316]/15" />
            </div>
            {/* Bottom orange glow */}
            <div className="absolute bottom-0 left-0 w-32 h-32 bg-[#F97316]/6 rounded-full blur-2xl" />
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
            {/* Italian marble texture - subtle veining */}
            <div className="absolute inset-0 opacity-6">
              <div className="absolute top-8 left-8 w-32 h-48 bg-[#1E40AF]/5 rounded-full blur-2xl" />
              <div className="absolute bottom-12 right-12 w-24 h-32 bg-[#1E40AF]/4 rounded-full blur-xl" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-40 bg-[#1E40AF]/3 rounded-full blur-3xl" />
            </div>
            {/* Elegant blue architectural lines */}
            <div className="absolute inset-0 opacity-8">
              <div className="absolute top-12 left-12 w-20 h-20 border-l-2 border-t-2 border-[#1E40AF]/20" />
              <div className="absolute top-12 right-12 w-20 h-20 border-r-2 border-t-2 border-[#1E40AF]/20" />
              <div className="absolute bottom-12 left-12 w-20 h-20 border-l-2 border-b-2 border-[#1E40AF]/20" />
              <div className="absolute bottom-12 right-12 w-20 h-20 border-r-2 border-b-2 border-[#1E40AF]/20" />
              {/* Central architectural element */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-16 h-24 border border-[#1E40AF]/15 rounded-t-full" />
            </div>
            {/* Subtle column silhouette */}
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-12 h-16 bg-[#1E40AF]/4 rounded-t-lg" />
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
        y: -8,
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
          relative w-[320px] h-[320px]
          ${design.background} ${design.gradient}
          rounded-sm overflow-hidden
          shadow-[0_12px_32px_rgba(0,0,0,0.06)]
          group-hover:shadow-[0_20px_48px_rgba(0,0,0,0.12)]
          group-hover:scale-[1.03]
          transition-all duration-350
          transition-timing-function cubic-bezier(0.215, 0.61, 0.355, 1)
        `}
      >
        {/* Premium depth layers */}
        {/* Soft vignette */}
        <div className="absolute inset-0 bg-gradient-to-b from-black/0 via-transparent to-black/20 pointer-events-none z-10" />
        {/* Gentle top highlight */}
        <div className="absolute top-0 left-0 right-0 h-1/3 bg-gradient-to-b from-white/10 to-transparent pointer-events-none z-10" />
        {/* Paper grain overlay */}
        <div className="absolute inset-0 bg-paper-grain opacity-15 pointer-events-none z-10" />

        {/* Competition-specific overlay */}
        {design.overlay}

        {/* Top metadata strip - unified template */}
        <div className="absolute top-0 left-0 right-0 px-5 pt-4 pb-2 flex items-center justify-between z-20">
          <span className="text-[6.5px] font-mono tracking-[0.3em] text-white/50 uppercase font-medium">OFFLINE</span>
          <span className="text-[6.5px] font-mono tracking-[0.25em] text-white/40 uppercase">{abbr}</span>
        </div>

        {/* Logo centered with generous whitespace */}
        <div className="absolute inset-0 flex items-center justify-center z-20 px-10">
          <img
            src={logo}
            alt={alt}
            loading="lazy"
            className="w-28 h-28 object-contain drop-shadow-[0_6px_16px_rgba(0,0,0,0.3)] transition-transform duration-500 group-hover:scale-105"
          />
        </div>

        {/* Thin editorial divider */}
        <div className="absolute bottom-12 left-8 right-8 h-[0.5px] bg-white/15 z-20" />

        {/* Competition name at bottom with premium typography */}
        <div className="absolute bottom-0 left-0 right-0 px-5 pb-5 pt-2 bg-gradient-to-t from-black/50 via-black/30 to-transparent z-20">
          <p className={`text-[10px] font-serif tracking-[0.12em] leading-tight text-center ${design.textColor} uppercase`}>
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
      
      {/* Subtle plaster texture for museum wall */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZmlsdGVyIGlkPSJwbGFzdGVyIj48ZmVUdXJidWxlbmNlIHR5cGU9ImZyYWN0YWxOb2lzZSIgYmFzZUZyZXF1ZW5jeT0iMC44IiBudW1PY3RhdmVzPSIzIiBzdGl0Y2hUaWxlcz0ic3RpdGNoIi8+PC9maWx0ZXI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsdGVyPSJ1cmwoI3BsYXN0ZXIpIiBvcGFjaXR5PSIwLjAyIi8+PC9zdmc+')] opacity-30 pointer-events-none" />
      
      {/* Very subtle grain layer */}
      <div className="absolute inset-0 bg-paper-grain opacity-10 pointer-events-none" />

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
        <motion.div variants={shelfVariants} className="relative mt-6 space-y-28">
          
          {/* ── Shelf One ── */}
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 1.0, ease: [0.16, 1, 0.3, 1] as const, delay: 0.4 }}
            className="relative"
          >
            {/* Realistic floating shelf - mounted to wall */}
            <div className="relative w-[85%] mx-auto">
              {/* Tight contact shadow directly under shelf */}
              <div className="absolute bottom-0 left-4 right-4 h-1 bg-[#1C1B17]/12 blur-sm" />
              
              {/* Larger soft ambient shadow fading onto wall */}
              <div className="absolute -bottom-4 left-8 right-8 h-8 bg-[#1C1B17]/6 blur-2xl rounded-full" />
              <div className="absolute -bottom-2 left-12 right-12 h-4 bg-[#1C1B17]/3 blur-xl rounded-full" />
              
              {/* Realistic shelf - 10px thick with bevel */}
              <div className="relative h-[10px] bg-gradient-to-b from-[#D4D0C4] via-[#C9C3B7] to-[#BEB8AC] rounded-b-sm shadow-[0_2px_8px_rgba(28,27,23,0.12)]">
                {/* Front bevel highlight */}
                <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-b from-[#E8E4DB] to-[#D4D0C4]" />
                {/* Rounded front edge highlight */}
                <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-t from-[#A9A398] to-[#BEB8AC] rounded-b-sm" />
                
                {/* Cards resting on shelf - bottom edge touching */}
                <div className="absolute -top-[320px] left-0 right-0 flex items-end justify-center gap-12 sm:gap-16 px-12">
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
            {/* Realistic floating shelf - mounted to wall */}
            <div className="relative w-[85%] mx-auto">
              {/* Tight contact shadow directly under shelf */}
              <div className="absolute bottom-0 left-4 right-4 h-1 bg-[#1C1B17]/12 blur-sm" />
              
              {/* Larger soft ambient shadow fading onto wall */}
              <div className="absolute -bottom-4 left-8 right-8 h-8 bg-[#1C1B17]/6 blur-2xl rounded-full" />
              <div className="absolute -bottom-2 left-12 right-12 h-4 bg-[#1C1B17]/3 blur-xl rounded-full" />
              
              {/* Realistic shelf - 10px thick with bevel */}
              <div className="relative h-[10px] bg-gradient-to-b from-[#D4D0C4] via-[#C9C3B7] to-[#BEB8AC] rounded-b-sm shadow-[0_2px_8px_rgba(28,27,23,0.12)]">
                {/* Front bevel highlight */}
                <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-b from-[#E8E4DB] to-[#D4D0C4]" />
                {/* Rounded front edge highlight */}
                <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-t from-[#A9A398] to-[#BEB8AC] rounded-b-sm" />
                
                {/* Cards resting on shelf - bottom edge touching */}
                <div className="absolute -top-[320px] left-0 right-0 flex items-end justify-center gap-12 sm:gap-16 px-12">
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

