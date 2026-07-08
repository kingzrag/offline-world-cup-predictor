import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Star, TrendingUp, Shield, Target, Zap, Award, Trophy, Goal, ChartColumn, Clock3, Users, History, Scale, BarChart3, ChevronDown, ChevronUp, AlertCircle, Ban } from 'lucide-react';
import { MatchPrediction } from '../types';

interface MatchAnalysisProps {
  match: MatchPrediction;
  onClose: () => void;
  onBack?: () => void;
  drawerTeamLoading?: boolean;
}

// ── Helper: confidence badge ─────────────────────────────────────────────────
function ConfidenceBadge({ probability }: { probability: number | null }) {
  if (probability === null) return <span className="text-xs font-semibold px-2 py-0.5 rounded bg-[#232B36] text-[#98A2B3]">N/A</span>;
  if (probability >= 75) return <span className="text-xs font-semibold px-2 py-0.5 rounded bg-[#34D399]/10 text-[#34D399]">Strong</span>;
  if (probability >= 60) return <span className="text-xs font-semibold px-2 py-0.5 rounded bg-[#34D399]/5 text-[#34D399]/80">Good</span>;
  if (probability >= 45) return <span className="text-xs font-semibold px-2 py-0.5 rounded bg-[#F5B301]/10 text-[#F5B301]">Lean</span>;
  return <span className="text-xs font-semibold px-2 py-0.5 rounded bg-[#232B36] text-[#98A2B3]">Avoid</span>;
}

// ── Helper: progress bar ─────────────────────────────────────────────────────
function ProgressBar({ value, color = '#34D399' }: { value: number; color?: string }) {
  return (
    <div className="w-full h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        whileInView={{ width: `${Math.min(value, 100)}%` }}
        viewport={{ once: true }}
        transition={{ duration: 0.7, ease: 'easeOut' }}
        className="h-full rounded-full"
        style={{ backgroundColor: color }}
      />
    </div>
  );
}

// ── Section Header ────────────────────────────────────────────────────────────
function SectionHeader({ title, subtitle, icon }: { title: string; subtitle?: string; icon?: React.ReactNode }) {
  return (
    <div className="mb-5 flex items-center gap-3">
      {icon && <div className="text-[#4F8CFF]">{icon}</div>}
      <div>
        <h2 className="text-base font-semibold text-[#F5F5F5] tracking-tight">{title}</h2>
        {subtitle && <p className="text-[10px] text-[#98A2B3] font-normal mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

// ── Outcome Card (for 1X2, Double Chance, DNB, BTTS, To Qualify) ──────────────
function OutcomeCard({
  label,
  probability,
  highlighted = false,
  sub,
}: {
  label: string;
  probability: number | null;
  highlighted?: boolean;
  sub?: string;
}) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      className={`flex-1 rounded-xl p-4 text-center transition-all duration-200 ${
        highlighted
          ? 'bg-[#1E2A1E] border border-[#34D399]/30 shadow-[0_0_16px_rgba(52,211,153,0.08)]'
          : 'bg-[#1C222C] border border-transparent hover:bg-[#232B36]'
      }`}
    >
      <div className="text-xs text-[#98A2B3] mb-2 font-normal">{label}</div>
      <div className={`text-2xl font-bold mb-1 tracking-tight ${highlighted ? 'text-[#34D399]' : 'text-[#F5F5F5]'}`}>
        {probability !== null ? `${probability}%` : 'N/A'}
      </div>
      {sub && <div className="text-[10px] text-[#98A2B3] mt-1">{sub}</div>}
      <div className="mt-2">
        <ConfidenceBadge probability={probability} />
      </div>
    </motion.div>
  );
}

// ── Market Row (for Total Goals table-style) ──────────────────────────────────
function MarketRow({
  label,
  probability,
  borderBottom = true,
}: {
  label: string;
  probability: number | null;
  borderBottom?: boolean;
}) {
  const pct = probability ?? null;
  return (
    <div className={`flex items-center gap-4 px-4 py-3 hover:bg-[#1C222C]/60 transition-colors duration-150 ${borderBottom ? 'border-b border-[#1C222C]' : ''}`}>
      <span className="text-sm text-[#F5F5F5] w-28 font-normal shrink-0">{label}</span>
      <div className="flex-1">
        <ProgressBar value={pct ?? 0} color={pct && pct >= 60 ? '#34D399' : pct && pct >= 45 ? '#F5B301' : '#4F8CFF'} />
      </div>
      <span className="text-sm font-semibold text-[#F5F5F5] w-10 text-right">{pct !== null ? `${pct}%` : 'N/A'}</span>
      <div className="w-14 flex justify-end">
        <ConfidenceBadge probability={pct} />
      </div>
    </div>
  );
}

// ── Over/Under Row Pair ───────────────────────────────────────────────────────
function OverUnderRowPair({
  line,
  over,
  under,
  isLast = false,
}: {
  line: string;
  over: number | null;
  under: number | null;
  isLast?: boolean;
}) {
  return (
    <>
      <MarketRow label={`Over ${line}`} probability={over} borderBottom />
      <MarketRow label={`Under ${line}`} probability={under} borderBottom={!isLast} />
      {!isLast && <div className="h-px bg-[#232B36] mx-4" />}
    </>
  );
}

// ── Collapsible Section ───────────────────────────────────────────────────────
function CollapsibleSection({
  title,
  subtitle,
  icon,
  children,
  defaultOpen = false,
}: {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="bg-[#151A22] rounded-xl shadow-[0_4px_18px_rgba(0,0,0,0.16)] overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-[#1C222C]/40 transition-colors duration-150"
      >
        <div className="flex items-center gap-3">
          {icon && <div className="text-[#4F8CFF]">{icon}</div>}
          <div className="text-left">
            <div className="text-sm font-semibold text-[#F5F5F5]">{title}</div>
            {subtitle && <div className="text-[10px] text-[#98A2B3] mt-0.5">{subtitle}</div>}
          </div>
        </div>
        {open ? (
          <ChevronUp className="w-4 h-4 text-[#98A2B3] shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-[#98A2B3] shrink-0" />
        )}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="border-t border-[#1C222C]">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Form Badge ────────────────────────────────────────────────────────────────
function FormBadge({ result }: { result: string }) {
  const colors = {
    W: 'bg-[#34D399]/10 text-[#34D399]',
    D: 'bg-[#1D222A] text-[#98A2B3]',
    L: 'bg-[#EF4444]/10 text-[#EF4444]',
  };
  const labels = { W: 'Win', D: 'Draw', L: 'Loss' };
  return (
    <span
      className={`w-7 h-7 flex items-center justify-center rounded text-xs font-bold ${colors[result as keyof typeof colors]}`}
      title={labels[result as keyof typeof labels]}
    >
      {result}
    </span>
  );
}

// ── section motion wrapper ────────────────────────────────────────────────────
function AnimSection({ id, children, className = '' }: { id?: string; children: React.ReactNode; className?: string }) {
  return (
    <motion.section
      id={id}
      className={className}
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.45 }}
    >
      {children}
    </motion.section>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function MatchAnalysis({
  match,
  onClose,
  onBack,
  drawerTeamLoading = false,
}: MatchAnalysisProps) {
  const [activeSection, setActiveSection] = useState('overview');

  const getFlag = (teamName: string) => {
    const flagMap: { [key: string]: string } = {
      Argentina: '🇦🇷', Australia: '🇦🇺', Belgium: '🇧🇪', Brazil: '🇧🇷',
      England: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', France: '🇫🇷', Germany: '🇩🇪', Italy: '🇮🇹',
      Netherlands: '🇳🇱', Portugal: '🇵🇹', Spain: '🇪🇸', USA: '🇺🇸',
      Uruguay: '🇺🇾', Croatia: '🇭🇷', Denmark: '🇩🇰', Mexico: '🇲🇽',
      Japan: '🇯🇵', 'South Korea': '🇰🇷', Morocco: '🇲🇦', Switzerland: '🇨🇭',
      Poland: '🇵🇱', Senegal: '🇸🇳', Ecuador: '🇪🇨', Wales: '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
      Iran: '🇮🇷', 'Saudi Arabia': '🇸🇦', Tunisia: '🇹🇳', Canada: '🇨🇦',
      Ghana: '🇬🇭', Cameroon: '🇨🇲', Serbia: '🇷🇸', Qatar: '🇶🇦',
      Egypt: '🇪🇬', China: '🇨🇳', 'South Africa': '🇿🇦', Nigeria: '🇳🇬',
      'Ivory Coast': '🇨🇮', Algeria: '🇩🇿', Russia: '🇷🇺', Turkey: '🇹🇷',
      Greece: '🇬🇷', Sweden: '🇸🇪', Norway: '🇳🇴', Colombia: '🇨🇴',
      Chile: '🇨🇱', Peru: '🇵🇪', Paraguay: '🇵🇾', Bolivia: '🇧🇴',
      Venezuela: '🇻🇪', Jamaica: '🇯🇲', 'Costa Rica': '🇨🇷', Panama: '🇵🇦',
      Honduras: '🇭🇳', 'El Salvador': '🇸🇻', Guatemala: '🇬🇹', 'New Zealand': '🇳🇿',
      Iceland: '🇮🇸', Finland: '🇫🇮', 'Republic of Ireland': '🇮🇪', Scotland: '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
      Ukraine: '🇺🇦', 'Czech Republic': '🇨🇿', Slovakia: '🇸🇰', Austria: '🇦🇹',
      Hungary: '🇭🇺', Romania: '🇷🇴', Bulgaria: '🇧🇬', Belarus: '🇧🇾',
      Slovenia: '🇸🇮', 'North Macedonia': '🇲🇰', Albania: '🇦🇱', Bosnia: '🇧🇦',
      Montenegro: '🇲🇪', Kosovo: '🇽🇰', Lithuania: '🇱🇹', Latvia: '🇱🇻',
      Estonia: '🇪🇪', Luxembourg: '🇱🇺', Cyprus: '🇨🇾', Malta: '🇲🇹',
      Armenia: '🇦🇲', Azerbaijan: '🇦🇿', Georgia: '🇬🇪', Kazakhstan: '🇰🇿',
      Uzbekistan: '🇺🇿', Kyrgyzstan: '🇰🇬', Tajikistan: '🇹🇯', Turkmenistan: '🇹🇲',
      Afghanistan: '🇦🇫', Pakistan: '🇵🇰', India: '🇮🇳', Bangladesh: '🇧🇩',
      'Sri Lanka': '🇱🇰', Nepal: '🇳🇵', Bhutan: '🇧🇹', Maldives: '🇲🇻',
      Thailand: '🇹🇭', Vietnam: '🇻🇳', Cambodia: '🇰🇭', Laos: '🇱🇦',
      Myanmar: '🇲🇲', Malaysia: '🇲🇾', Singapore: '🇸🇬', Indonesia: '🇮🇩',
      Philippines: '🇵🇭', Brunei: '🇧🇳', 'East Timor': '🇹🇱', 'North Korea': '🇰🇵',
      'South Sudan': '🇸🇸', Ethiopia: '🇪🇹', Kenya: '🇰🇪', Tanzania: '🇹🇿',
      Uganda: '🇺🇬', Rwanda: '🇷🇼', Burundi: '🇧🇮', 'DR Congo': '🇨🇩',
      Congo: '🇨🇬', Gabon: '🇬🇦', Angola: '🇦🇴',
      Mozambique: '🇲🇿', Zambia: '🇿🇲', Zimbabwe: '🇿🇼', Botswana: '🇧🇼',
      Namibia: '🇳🇦', Lesotho: '🇱🇸', Eswatini: '🇸🇿',
      Madagascar: '🇲🇬', Mauritius: '🇲🇺', Seychelles: '🇸🇨', Comoros: '🇰🇲',
      Libya: '🇱🇾', Mauritania: '🇲🇷', 'Western Sahara': '🇪🇭', Mali: '🇲🇱', Niger: '🇳🇪',
      Chad: '🇹🇩', Sudan: '🇸🇩', Eritrea: '🇪🇷', Djibouti: '🇩🇯',
      Somalia: '🇸🇴', 'Central African Republic': '🇨🇫', 'Equatorial Guinea': '🇬🇶',
      'Sao Tome and Principe': '🇸🇹', Gambia: '🇬🇲', 'Guinea-Bissau': '🇬🇼',
      Guinea: '🇬🇳', 'Sierra Leone': '🇸🇱', Liberia: '🇱🇷',
    };
    return flagMap[teamName] || '🏳️';
  };

  const probA = match.probA ?? 0;
  const probD = match.probD ?? 0;
  const probB = match.probB ?? 0;
  const xGA = match.xGA;
  const xGB = match.xGB;
  const totalXG = match.totalExpectedGoals;

  const flagA = getFlag(match.teamA);
  const flagB = getFlag(match.teamB);

  // Which outcome is the top pick
  const topProbability = Math.max(probA, probB, probD);
  const isKnockout = match.stage?.toLowerCase().includes('knockout') ||
    match.stage?.toLowerCase().includes('round of') ||
    match.stage?.toLowerCase().includes('quarter') ||
    match.stage?.toLowerCase().includes('semi') ||
    match.stage?.toLowerCase().includes('final') ||
    !!match.qualifyProbA;

  // Double Chance computed values (raw probabilities are 0-1 or already 0-100)
  const dc1x = match.doubleChanceMarket?.['1x'] != null ? Math.round((match.doubleChanceMarket['1x'] <= 1 ? match.doubleChanceMarket['1x'] * 100 : match.doubleChanceMarket['1x'])) : null;
  const dc12 = match.doubleChanceMarket?.['12'] != null ? Math.round((match.doubleChanceMarket['12'] <= 1 ? match.doubleChanceMarket['12'] * 100 : match.doubleChanceMarket['12'])) : null;
  const dcX2 = match.doubleChanceMarket?.['x2'] != null ? Math.round((match.doubleChanceMarket['x2'] <= 1 ? match.doubleChanceMarket['x2'] * 100 : match.doubleChanceMarket['x2'])) : null;

  // DNB
  const dnbHome = match.drawNoBetMarket?.home != null ? Math.round((match.drawNoBetMarket.home <= 1 ? match.drawNoBetMarket.home * 100 : match.drawNoBetMarket.home)) : null;
  const dnbAway = match.drawNoBetMarket?.away != null ? Math.round((match.drawNoBetMarket.away <= 1 ? match.drawNoBetMarket.away * 100 : match.drawNoBetMarket.away)) : null;

  // BTTS
  const bttsYes = match.bttsMarket?.yes != null ? Math.round((match.bttsMarket.yes <= 1 ? match.bttsMarket.yes * 100 : match.bttsMarket.yes)) : null;
  const bttsNo = match.bttsMarket?.no != null ? Math.round((match.bttsMarket.no <= 1 ? match.bttsMarket.no * 100 : match.bttsMarket.no)) : null;

  // Over/Under helper
  const ouPct = (line: string, side: 'over' | 'under'): number | null => {
    const val = match.overUnder?.[line as keyof typeof match.overUnder]?.[side];
    if (val == null) return null;
    return Math.round(val <= 1 ? val * 100 : val);
  };

  // Asian Total lines
  const asianTotalLines = ['1.25', '1.5', '1.75', '2', '2.25', '2.5', '2.75', '3'];

  // Qualify probs
  const qualifyA = match.qualifyProbA != null ? Math.round(match.qualifyProbA) : null;
  const qualifyB = match.qualifyProbB != null ? Math.round(match.qualifyProbB) : null;

  const navItems = [
    { id: 'overview', label: 'Overview' },
    { id: 'main-markets', label: 'Main Markets' },
    { id: 'goals', label: 'Goals' },
    { id: 'handicap', label: 'Handicap' },
    { id: 'scores', label: 'Scores' },
    { id: 'statistics', label: 'Statistics' },
    { id: 'team-news', label: 'Team News' },
  ];

  const scrollToSection = (sectionId: string) => {
    setActiveSection(sectionId);
    const element = document.getElementById(`section-${sectionId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-[#0E1117] z-50 overflow-y-auto"
    >
      {/* Top bar — Back button only */}
      <div className="sticky top-0 bg-[#0E1117]/95 backdrop-blur-xl border-b border-white/5 z-50">
        <div className="max-w-[1380px] mx-auto px-6 py-3 flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-[#98A2B3] hover:text-[#F5F5F5] transition-colors text-sm font-normal"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>← Back to Matches</span>
            </button>
          )}
        </div>
      </div>

      {/* Sticky Navigation */}
      <div className="sticky top-[49px] bg-[#0E1117]/95 backdrop-blur-xl border-b border-white/5 z-40">
        <div className="max-w-[1380px] mx-auto px-6">
          <nav className="flex gap-6 overflow-x-auto py-3 scrollbar-hide">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className={`relative text-sm font-normal transition-colors whitespace-nowrap py-1 ${
                  activeSection === item.id
                    ? 'text-[#F5F5F5]'
                    : 'text-[#98A2B3] hover:text-[#F5F5F5]'
                }`}
              >
                {item.label}
                {activeSection === item.id && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#4F8CFF] rounded-full"
                    initial={false}
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                )}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <div className="max-w-[1380px] mx-auto px-6 py-6 space-y-8">

        {/* ── HERO SECTION ─────────────────────────────────────────────────── */}
        <AnimSection id="section-overview">
          <div className="bg-[#151A22] rounded-xl p-5 shadow-[0_4px_20px_rgba(0,0,0,0.2)]">
            {/* Teams header */}
            <div className="flex items-center justify-between mb-4">
              {/* Team A */}
              <div className="flex items-center gap-3">
                <span className="text-3xl">{flagA}</span>
                <div>
                  <h1 className="text-xl font-bold text-[#F5F5F5] tracking-tight">{match.teamA}</h1>
                  <p className="text-[10px] text-[#98A2B3]">{match.teamACode}</p>
                </div>
              </div>

              {/* Center: probabilities */}
              <div className="flex items-center gap-5 text-center">
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                  <div className="text-2xl font-bold text-[#F5F5F5]">{probA}%</div>
                  <div className="text-[10px] text-[#98A2B3] mt-0.5">Home</div>
                </motion.div>
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
                  <div className="text-base font-bold text-[#98A2B3]/60">{probD}%</div>
                  <div className="text-[10px] text-[#98A2B3]/60 mt-0.5">Draw</div>
                </motion.div>
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                  <div className="text-2xl font-bold text-[#F5F5F5]">{probB}%</div>
                  <div className="text-[10px] text-[#98A2B3] mt-0.5">Away</div>
                </motion.div>
              </div>

              {/* Team B */}
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <h1 className="text-xl font-bold text-[#F5F5F5] tracking-tight">{match.teamB}</h1>
                  <p className="text-[10px] text-[#98A2B3]">{match.teamBCode}</p>
                </div>
                <span className="text-3xl">{flagB}</span>
              </div>
            </div>

            {/* Probability bar */}
            <div className="h-1.5 bg-[#0E1117] rounded-full overflow-hidden flex mb-4">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${probA}%` }}
                transition={{ duration: 0.8, delay: 0.3, ease: 'easeOut' }}
                className={`h-full ${probA > probB ? 'bg-[#34D399]' : 'bg-[#4F8CFF]'} rounded-l-full`}
              />
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${probD}%` }}
                transition={{ duration: 0.8, delay: 0.35, ease: 'easeOut' }}
                className="h-full bg-[#232B36]"
              />
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${probB}%` }}
                transition={{ duration: 0.8, delay: 0.4, ease: 'easeOut' }}
                className={`h-full ${probB > probA ? 'bg-[#34D399]' : 'bg-[#4F8CFF]'} rounded-r-full`}
              />
            </div>

            {/* Meta info grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <div className="bg-[#1C222C] rounded-lg px-3 py-2.5">
                <div className="text-[10px] text-[#98A2B3] uppercase tracking-wider mb-1">Predicted Score</div>
                <div className="text-sm font-semibold text-[#F5F5F5]">{match.mostLikelyScore || 'N/A'}</div>
              </div>
              <div className="bg-[#1C222C] rounded-lg px-3 py-2.5">
                <div className="text-[10px] text-[#98A2B3] uppercase tracking-wider mb-1">Expected Goals (xG)</div>
                <div className="text-sm font-semibold text-[#F5F5F5]">
                  {xGA?.toFixed(2) || '—'} – {xGB?.toFixed(2) || '—'}
                </div>
              </div>
              <div className="bg-[#1C222C] rounded-lg px-3 py-2.5">
                <div className="text-[10px] text-[#98A2B3] uppercase tracking-wider mb-1">Confidence</div>
                <div className={`text-sm font-semibold ${
                  match.confidence === 'High' ? 'text-[#34D399]' :
                  match.confidence === 'Medium' ? 'text-[#F5B301]' : 'text-[#98A2B3]'
                }`}>{match.confidence || 'N/A'}</div>
              </div>
              <div className="bg-[#1C222C] rounded-lg px-3 py-2.5">
                <div className="text-[10px] text-[#98A2B3] uppercase tracking-wider mb-1">Top Pick</div>
                <div className="text-sm font-semibold text-[#4F8CFF]">{match.prediction || 'N/A'}</div>
              </div>
            </div>

            {/* Tournament + Venue */}
            <div className="flex items-center justify-between text-[11px] text-[#98A2B3]">
              <div className="flex items-center gap-2">
                {match.status === 'LIVE' && (
                  <span className="flex items-center gap-1 text-[#EF4444] font-semibold">
                    <span className="relative flex h-1.5 w-1.5">
                      <span className="absolute inline-flex h-full w-full rounded-full bg-[#EF4444] animate-ping" />
                      <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#EF4444]" />
                    </span>
                    LIVE {match.minute}'
                  </span>
                )}
                <Trophy className="w-3.5 h-3.5 text-[#F5B301]" />
                <span className="text-[#34D399]">{match.stage}</span>
              </div>
              {match.venue && (
                <div className="flex items-center gap-1">
                  <span>🏟</span>
                  <span>{match.venue}</span>
                </div>
              )}
            </div>
          </div>
        </AnimSection>

        {/* ── MAIN MARKETS ─────────────────────────────────────────────────── */}
        <AnimSection id="section-main-markets" className="space-y-6">

          {/* 1. 1X2 Prediction */}
          <div className="bg-[#151A22] rounded-xl p-5 shadow-[0_4px_18px_rgba(0,0,0,0.16)]">
            <SectionHeader
              title="1X2 Prediction"
              subtitle="Match Result Probability"
              icon={<Trophy className="w-4 h-4" />}
            />
            <div className="flex gap-3">
              <OutcomeCard
                label={match.teamA}
                probability={probA}
                highlighted={probA === topProbability}
              />
              <OutcomeCard
                label="Draw"
                probability={probD}
                highlighted={probD === topProbability}
              />
              <OutcomeCard
                label={match.teamB}
                probability={probB}
                highlighted={probB === topProbability}
              />
            </div>
          </div>

          {/* 2. To Qualify — knockout only */}
          {isKnockout && (qualifyA !== null || qualifyB !== null) && (
            <div className="bg-[#151A22] rounded-xl p-5 shadow-[0_4px_18px_rgba(0,0,0,0.16)]">
              <SectionHeader
                title="To Qualify"
                subtitle="Knockout Advancement Probability"
                icon={<Award className="w-4 h-4" />}
              />
              <div className="flex gap-3">
                <OutcomeCard
                  label={match.teamA}
                  probability={qualifyA}
                  highlighted={(qualifyA ?? 0) >= (qualifyB ?? 0)}
                />
                <OutcomeCard
                  label={match.teamB}
                  probability={qualifyB}
                  highlighted={(qualifyB ?? 0) > (qualifyA ?? 0)}
                />
              </div>
            </div>
          )}

          {/* 3. Double Chance */}
          {(dc1x !== null || dc12 !== null || dcX2 !== null) && (
            <div className="bg-[#151A22] rounded-xl p-5 shadow-[0_4px_18px_rgba(0,0,0,0.16)]">
              <SectionHeader
                title="Double Chance"
                subtitle="Combined Match Result Probability"
                icon={<Shield className="w-4 h-4" />}
              />
              <div className="flex gap-3">
                <OutcomeCard
                  label={`${match.teamA} or Draw`}
                  probability={dc1x}
                  highlighted={dc1x !== null && dc1x === Math.max(dc1x ?? 0, dc12 ?? 0, dcX2 ?? 0)}
                />
                <OutcomeCard
                  label={`${match.teamA} or ${match.teamB}`}
                  probability={dc12}
                  highlighted={dc12 !== null && dc12 === Math.max(dc1x ?? 0, dc12 ?? 0, dcX2 ?? 0)}
                />
                <OutcomeCard
                  label={`Draw or ${match.teamB}`}
                  probability={dcX2}
                  highlighted={dcX2 !== null && dcX2 === Math.max(dc1x ?? 0, dc12 ?? 0, dcX2 ?? 0)}
                />
              </div>
            </div>
          )}

          {/* 4. Draw No Bet */}
          {(dnbHome !== null || dnbAway !== null) && (
            <div className="bg-[#151A22] rounded-xl p-5 shadow-[0_4px_18px_rgba(0,0,0,0.16)]">
              <SectionHeader
                title="Draw No Bet"
                subtitle="Win probability excluding draw scenarios"
                icon={<Scale className="w-4 h-4" />}
              />
              <div className="flex gap-3">
                <OutcomeCard
                  label={match.teamA}
                  probability={dnbHome}
                  highlighted={(dnbHome ?? 0) >= (dnbAway ?? 0)}
                />
                <OutcomeCard
                  label={match.teamB}
                  probability={dnbAway}
                  highlighted={(dnbAway ?? 0) > (dnbHome ?? 0)}
                />
              </div>
            </div>
          )}

          {/* 5. Both Teams To Score */}
          {(bttsYes !== null || bttsNo !== null) && (
            <div className="bg-[#151A22] rounded-xl p-5 shadow-[0_4px_18px_rgba(0,0,0,0.16)]">
              <SectionHeader
                title="Both Teams To Score"
                subtitle="BTTS Market Probability"
                icon={<Target className="w-4 h-4" />}
              />
              <div className="flex gap-3">
                <OutcomeCard
                  label="Yes"
                  probability={bttsYes}
                  highlighted={(bttsYes ?? 0) >= (bttsNo ?? 0)}
                />
                <OutcomeCard
                  label="No"
                  probability={bttsNo}
                  highlighted={(bttsNo ?? 0) > (bttsYes ?? 0)}
                />
              </div>
            </div>
          )}

        </AnimSection>

        {/* ── GOALS ─────────────────────────────────────────────────────────── */}
        <AnimSection id="section-goals" className="space-y-6">

          {/* 6. Total Goals */}
          <div className="bg-[#151A22] rounded-xl shadow-[0_4px_18px_rgba(0,0,0,0.16)] overflow-hidden">
            <div className="px-5 pt-5 pb-4">
              <SectionHeader
                title="Total Goals"
                subtitle="Over / Under Probability"
                icon={<Goal className="w-4 h-4" />}
              />
            </div>
            <div className="border-t border-[#1C222C]">
              {(['0.5', '1.5', '2.5', '3.5', '4.5'] as const).map((line, i, arr) => (
                <React.Fragment key={line}>
                  <OverUnderRowPair
                    line={line}
                    over={ouPct(line, 'over')}
                    under={ouPct(line, 'under')}
                    isLast={i === arr.length - 1}
                  />
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Team Goals */}
          {match.teamGoals && (
            <div className="bg-[#151A22] rounded-xl p-5 shadow-[0_4px_18px_rgba(0,0,0,0.16)]">
              <SectionHeader
                title="Team Goals"
                subtitle="Individual team goal probability"
                icon={<Goal className="w-4 h-4" />}
              />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Home */}
                <div className="bg-[#1C222C] rounded-lg p-4 space-y-3">
                  <div className="text-xs font-semibold text-[#F5F5F5] mb-3">{match.teamA} Goals</div>
                  {[
                    { label: 'Over 0.5', val: match.teamGoals.home.over_0_5 },
                    { label: 'Over 1.5', val: match.teamGoals.home.over_1_5 },
                    { label: 'Over 2.5', val: match.teamGoals.home.over_2_5 },
                  ].map(({ label, val }) => {
                    const pct = val != null ? Math.round(val <= 1 ? val * 100 : val) : null;
                    return (
                      <div key={label} className="flex items-center gap-3">
                        <span className="text-xs text-[#98A2B3] w-16 shrink-0">{label}</span>
                        <div className="flex-1">
                          <ProgressBar value={pct ?? 0} />
                        </div>
                        <span className="text-xs font-semibold text-[#F5F5F5] w-8 text-right">{pct !== null ? `${pct}%` : 'N/A'}</span>
                      </div>
                    );
                  })}
                </div>
                {/* Away */}
                <div className="bg-[#1C222C] rounded-lg p-4 space-y-3">
                  <div className="text-xs font-semibold text-[#F5F5F5] mb-3">{match.teamB} Goals</div>
                  {[
                    { label: 'Over 0.5', val: match.teamGoals.away.over_0_5 },
                    { label: 'Over 1.5', val: match.teamGoals.away.over_1_5 },
                    { label: 'Over 2.5', val: match.teamGoals.away.over_2_5 },
                  ].map(({ label, val }) => {
                    const pct = val != null ? Math.round(val <= 1 ? val * 100 : val) : null;
                    return (
                      <div key={label} className="flex items-center gap-3">
                        <span className="text-xs text-[#98A2B3] w-16 shrink-0">{label}</span>
                        <div className="flex-1">
                          <ProgressBar value={pct ?? 0} />
                        </div>
                        <span className="text-xs font-semibold text-[#F5F5F5] w-8 text-right">{pct !== null ? `${pct}%` : 'N/A'}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* First Team To Score */}
          <div className="bg-[#151A22] rounded-xl p-5 shadow-[0_4px_18px_rgba(0,0,0,0.16)]">
            <SectionHeader
              title="First Team To Score"
              subtitle="Which team scores first"
              icon={<Zap className="w-4 h-4" />}
            />
            {(() => {
              // Derive from xG proportionally
              const totalXg = (match.xGA ?? 0) + (match.xGB ?? 0);
              const noGoalProb = match.overUnder?.['0.5']?.under != null
                ? Math.round((match.overUnder['0.5'].under <= 1 ? match.overUnder['0.5'].under * 100 : match.overUnder['0.5'].under))
                : null;
              const scoringProb = noGoalProb != null ? 100 - noGoalProb : 100;
              const ftsA = totalXg > 0 ? Math.round(((match.xGA ?? 0) / totalXg) * scoringProb) : null;
              const ftsB = totalXg > 0 ? Math.round(((match.xGB ?? 0) / totalXg) * scoringProb) : null;
              return (
                <div className="flex gap-3">
                  <OutcomeCard label={match.teamA} probability={ftsA} highlighted={(ftsA ?? 0) >= (ftsB ?? 0)} />
                  <OutcomeCard label="No Goal" probability={noGoalProb} highlighted={false} />
                  <OutcomeCard label={match.teamB} probability={ftsB} highlighted={(ftsB ?? 0) > (ftsA ?? 0)} />
                </div>
              );
            })()}
          </div>

        </AnimSection>

        {/* ── HANDICAP ──────────────────────────────────────────────────────── */}
        <AnimSection id="section-handicap" className="space-y-6">

          {/* Asian Handicap — collapsible */}
          <CollapsibleSection
            title="Asian Handicap"
            subtitle="Handicap line probabilities — click to expand"
            icon={<BarChart3 className="w-4 h-4" />}
          >
            {match.asianHandicap?.lines ? (
              <div>
                {/* Header row */}
                <div className="flex items-center gap-4 px-4 py-2 bg-[#1C222C]">
                  <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider w-28">Line</span>
                  <span className="flex-1 text-[10px] text-[#98A2B3] uppercase tracking-wider">Probability</span>
                  <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider w-10 text-right">%</span>
                  <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider w-14 text-right">Rating</span>
                </div>
                {Object.entries(match.asianHandicap.lines)
                  .map(([line, val]) => ({
                    label: `${match.asianHandicap!.favored_team} ${line}`,
                    prob: Math.round((val as number) <= 1 ? (val as number) * 100 : (val as number)),
                    rawLine: parseFloat(line),
                  }))
                  .sort((a, b) => b.rawLine - a.rawLine)
                  .map((item, idx, arr) => (
                    <MarketRow
                      key={item.label}
                      label={item.label}
                      probability={item.prob}
                      borderBottom={idx < arr.length - 1}
                    />
                  ))}
              </div>
            ) : (
              <div className="px-5 py-6 text-sm text-[#98A2B3] text-center">No handicap data available</div>
            )}
          </CollapsibleSection>

          {/* Asian Total — collapsible */}
          <CollapsibleSection
            title="Asian Total"
            subtitle="Quarter-ball over/under lines — click to expand"
            icon={<TrendingUp className="w-4 h-4" />}
          >
            <div>
              <div className="flex items-center gap-4 px-4 py-2 bg-[#1C222C]">
                <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider w-28">Line</span>
                <span className="flex-1 text-[10px] text-[#98A2B3] uppercase tracking-wider">Probability</span>
                <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider w-10 text-right">%</span>
                <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider w-14 text-right">Rating</span>
              </div>
              {asianTotalLines.map((line, idx) => {
                // Interpolate from surrounding integer/half lines
                const lineNum = parseFloat(line);
                const lower = Math.floor(lineNum * 2) / 2;
                const upper = Math.ceil(lineNum * 2) / 2;
                const lKey = lower === Math.floor(lower) ? lower.toFixed(1) : lower.toString();
                const uKey = upper === Math.floor(upper) ? upper.toFixed(1) : upper.toString();
                const lOver = match.overUnder?.[lKey as keyof typeof match.overUnder]?.over;
                const uOver = match.overUnder?.[uKey as keyof typeof match.overUnder]?.over;
                let overPct: number | null = null;
                let underPct: number | null = null;
                if (lOver != null && uOver != null && lower !== upper) {
                  const t = (lineNum - lower) / (upper - lower);
                  const raw = lOver + t * (uOver - lOver);
                  overPct = Math.round(raw <= 1 ? raw * 100 : raw);
                  underPct = 100 - overPct;
                } else if (lOver != null) {
                  overPct = Math.round(lOver <= 1 ? lOver * 100 : lOver);
                  underPct = 100 - overPct;
                }
                const isLast = idx === asianTotalLines.length - 1;
                return (
                  <React.Fragment key={line}>
                    <MarketRow label={`Over ${line}`} probability={overPct} borderBottom />
                    <MarketRow label={`Under ${line}`} probability={underPct} borderBottom={!isLast} />
                    {!isLast && <div className="h-px bg-[#232B36] mx-4" />}
                  </React.Fragment>
                );
              })}
            </div>
          </CollapsibleSection>

        </AnimSection>

        {/* ── CORRECT SCORES ────────────────────────────────────────────────── */}
        <AnimSection id="section-scores">
          <div className="bg-[#151A22] rounded-xl p-5 shadow-[0_4px_18px_rgba(0,0,0,0.16)]">
            <SectionHeader
              title="Correct Score"
              subtitle="Top 5 most likely scorelines"
              icon={<ChartColumn className="w-4 h-4" />}
            />
            <div className="space-y-3">
              {match.top5Scorelines?.slice(0, 5).map((score, index) => {
                const pct = score.probability != null ? Math.round(score.probability <= 1 ? score.probability * 100 : score.probability) : 0;
                const medals = ['🥇', '🥈', '🥉'];
                const medal = medals[index] || `${index + 1}.`;
                return (
                  <motion.div
                    key={index}
                    whileHover={{ x: 3 }}
                    className="flex items-center gap-4 bg-[#1C222C] rounded-lg px-4 py-3 hover:bg-[#232B36] transition-colors duration-200"
                  >
                    <span className="text-xl w-8 shrink-0">{medal}</span>
                    <span className="text-base font-bold text-[#F5F5F5] w-16">{score.score}</span>
                    <div className="flex-1">
                      <ProgressBar value={pct} />
                    </div>
                    <span className="text-sm font-semibold text-[#F5F5F5] w-10 text-right">{pct}%</span>
                    <ConfidenceBadge probability={pct} />
                  </motion.div>
                );
              })}
              {(!match.top5Scorelines || match.top5Scorelines.length === 0) && (
                <div className="text-sm text-[#98A2B3] text-center py-6">No scoreline data available</div>
              )}
            </div>
          </div>
        </AnimSection>

        {/* ── STATISTICS / TEAM COMPARISON ──────────────────────────────────── */}
        <AnimSection id="section-statistics">
          <div className="bg-[#151A22] rounded-xl p-5 shadow-[0_4px_18px_rgba(0,0,0,0.16)]">
            <SectionHeader
              title="Team Comparison"
              subtitle="Head-to-head statistical breakdown"
              icon={<BarChart3 className="w-4 h-4" />}
            />

            <div className="space-y-4">
              {/* Comparison rows */}
              {[
                {
                  label: 'FIFA Ranking',
                  valA: match.fifaRankA ? `#${match.fifaRankA}` : 'N/A',
                  valB: match.fifaRankB ? `#${match.fifaRankB}` : 'N/A',
                  numA: match.fifaRankA ? (200 - match.fifaRankA) : 0,
                  numB: match.fifaRankB ? (200 - match.fifaRankB) : 0,
                },
                {
                  label: 'ELO Rating',
                  valA: match.eloRankA ? `${match.eloRankA}` : 'N/A',
                  valB: match.eloRankB ? `${match.eloRankB}` : 'N/A',
                  numA: match.eloRankA ?? 0,
                  numB: match.eloRankB ?? 0,
                },
                {
                  label: 'Squad Value',
                  valA: match.squadValueA || 'N/A',
                  valB: match.squadValueB || 'N/A',
                  numA: parseFloat((match.squadValueA || '0').replace(/[^0-9.]/g, '')),
                  numB: parseFloat((match.squadValueB || '0').replace(/[^0-9.]/g, '')),
                },
                {
                  label: 'Attack Rating',
                  valA: `${match.attackA ?? 'N/A'}`,
                  valB: `${match.attackB ?? 'N/A'}`,
                  numA: match.attackA ?? 0,
                  numB: match.attackB ?? 0,
                },
                {
                  label: 'Defence Rating',
                  valA: `${match.defenceA ?? 'N/A'}`,
                  valB: `${match.defenceB ?? 'N/A'}`,
                  numA: match.defenceA ?? 0,
                  numB: match.defenceB ?? 0,
                },
                {
                  label: 'Expected Goals (xG)',
                  valA: xGA?.toFixed(2) ?? 'N/A',
                  valB: xGB?.toFixed(2) ?? 'N/A',
                  numA: xGA ?? 0,
                  numB: xGB ?? 0,
                },
              ].map(({ label, valA, valB, numA, numB }) => {
                const maxVal = Math.max(numA, numB, 1);
                const wA = (numA / maxVal) * 100;
                const wB = (numB / maxVal) * 100;
                const aWins = numA >= numB;
                return (
                  <div key={label} className="bg-[#1C222C] rounded-lg px-4 py-3">
                    <div className="text-[10px] text-[#98A2B3] uppercase tracking-wider mb-2">{label}</div>
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-semibold w-20 shrink-0 ${aWins ? 'text-[#F5F5F5]' : 'text-[#98A2B3]'}`}>{match.teamACode}</span>
                      <div className="flex-1 flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-[#0E1117] rounded-full overflow-hidden flex justify-end">
                          <motion.div
                            initial={{ width: 0 }}
                            whileInView={{ width: `${wA}%` }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.7 }}
                            className={`h-full rounded-full ${aWins ? 'bg-[#34D399]' : 'bg-[#4F8CFF]'}`}
                            style={{ marginLeft: 'auto' }}
                          />
                        </div>
                        <span className="text-xs text-[#98A2B3] w-16 text-center">{valA} – {valB}</span>
                        <div className="flex-1 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            whileInView={{ width: `${wB}%` }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.7 }}
                            className={`h-full rounded-full ${!aWins ? 'bg-[#34D399]' : 'bg-[#4F8CFF]'}`}
                          />
                        </div>
                      </div>
                      <span className={`text-xs font-semibold w-20 shrink-0 text-right ${!aWins ? 'text-[#F5F5F5]' : 'text-[#98A2B3]'}`}>{match.teamBCode}</span>
                    </div>
                  </div>
                );
              })}

              {/* Recent Form */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-[#1C222C] rounded-lg px-4 py-3">
                  <div className="text-[10px] text-[#98A2B3] uppercase tracking-wider mb-2">Recent Form — {match.teamA}</div>
                  <div className="flex gap-1.5">
                    {match.recentFormA?.map((r, i) => <FormBadge key={i} result={r} />) ?? <span className="text-sm text-[#98A2B3]">N/A</span>}
                  </div>
                </div>
                <div className="bg-[#1C222C] rounded-lg px-4 py-3">
                  <div className="text-[10px] text-[#98A2B3] uppercase tracking-wider mb-2">Recent Form — {match.teamB}</div>
                  <div className="flex gap-1.5">
                    {match.recentFormB?.map((r, i) => <FormBadge key={i} result={r} />) ?? <span className="text-sm text-[#98A2B3]">N/A</span>}
                  </div>
                </div>
              </div>

              {/* H2H */}
              {match.h2hPreviousMeetings > 0 && (
                <div className="bg-[#1C222C] rounded-lg px-4 py-3">
                  <div className="text-[10px] text-[#98A2B3] uppercase tracking-wider mb-3">Head to Head — Last {match.h2hPreviousMeetings} Meetings</div>
                  <div className="flex items-center justify-around text-center">
                    <div>
                      <div className="text-2xl font-bold text-[#F5F5F5]">{match.h2hWinsA}</div>
                      <div className="text-[10px] text-[#98A2B3] mt-1">{match.teamA} Wins</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-[#98A2B3]">{match.h2hDraws}</div>
                      <div className="text-[10px] text-[#98A2B3] mt-1">Draws</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-[#F5F5F5]">{match.h2hWinsB}</div>
                      <div className="text-[10px] text-[#98A2B3] mt-1">{match.teamB} Wins</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </AnimSection>

        {/* ── TEAM NEWS ─────────────────────────────────────────────────────── */}
        <AnimSection id="section-team-news">
          <div className="bg-[#151A22] rounded-xl p-5 shadow-[0_4px_18px_rgba(0,0,0,0.16)]">
            <SectionHeader
              title="Team News"
              subtitle="Injuries and suspensions"
              icon={<Users className="w-4 h-4" />}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Team A */}
              <div className="bg-[#1C222C] rounded-lg p-4">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-xl">{flagA}</span>
                  <span className="text-sm font-semibold text-[#F5F5F5]">{match.teamA}</span>
                  <span className={`ml-auto text-[10px] font-semibold px-2 py-0.5 rounded ${
                    match.impactRatingA === 'Critical' ? 'bg-[#EF4444]/10 text-[#EF4444]' :
                    match.impactRatingA === 'Moderate' ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                    'bg-[#34D399]/10 text-[#34D399]'
                  }`}>{match.impactRatingA}</span>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center gap-1.5 mb-2">
                      <AlertCircle className="w-3.5 h-3.5 text-[#EF4444]" />
                      <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal">Injuries</span>
                    </div>
                    {match.injuriesA?.length ? (
                      <div className="flex flex-wrap gap-1.5">
                        {match.injuriesA.map((p, i) => (
                          <span key={i} className="text-xs bg-[#EF4444]/10 text-[#EF4444] px-2 py-0.5 rounded">{p}</span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-[#98A2B3]">None reported</p>
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5 mb-2">
                      <Ban className="w-3.5 h-3.5 text-[#F5B301]" />
                      <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal">Suspensions</span>
                    </div>
                    {match.suspensionsA?.length ? (
                      <div className="flex flex-wrap gap-1.5">
                        {match.suspensionsA.map((p, i) => (
                          <span key={i} className="text-xs bg-[#F5B301]/10 text-[#F5B301] px-2 py-0.5 rounded">{p}</span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-[#98A2B3]">None reported</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Team B */}
              <div className="bg-[#1C222C] rounded-lg p-4">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-xl">{flagB}</span>
                  <span className="text-sm font-semibold text-[#F5F5F5]">{match.teamB}</span>
                  <span className={`ml-auto text-[10px] font-semibold px-2 py-0.5 rounded ${
                    match.impactRatingB === 'Critical' ? 'bg-[#EF4444]/10 text-[#EF4444]' :
                    match.impactRatingB === 'Moderate' ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                    'bg-[#34D399]/10 text-[#34D399]'
                  }`}>{match.impactRatingB}</span>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center gap-1.5 mb-2">
                      <AlertCircle className="w-3.5 h-3.5 text-[#EF4444]" />
                      <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal">Injuries</span>
                    </div>
                    {match.injuriesB?.length ? (
                      <div className="flex flex-wrap gap-1.5">
                        {match.injuriesB.map((p, i) => (
                          <span key={i} className="text-xs bg-[#EF4444]/10 text-[#EF4444] px-2 py-0.5 rounded">{p}</span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-[#98A2B3]">None reported</p>
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5 mb-2">
                      <Ban className="w-3.5 h-3.5 text-[#F5B301]" />
                      <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal">Suspensions</span>
                    </div>
                    {match.suspensionsB?.length ? (
                      <div className="flex flex-wrap gap-1.5">
                        {match.suspensionsB.map((p, i) => (
                          <span key={i} className="text-xs bg-[#F5B301]/10 text-[#F5B301] px-2 py-0.5 rounded">{p}</span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-[#98A2B3]">None reported</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </AnimSection>

        {/* ── PREDICTION CONFIDENCE ─────────────────────────────────────────── */}
        <AnimSection>
          <div className="bg-[#151A22] rounded-xl p-5 shadow-[0_4px_18px_rgba(0,0,0,0.16)]">
            <SectionHeader
              title="Prediction Confidence"
              subtitle="Model reliability indicators"
              icon={<Zap className="w-4 h-4" />}
            />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                {
                  label: 'Calibration',
                  value: match.confidence || 'N/A',
                  icon: <Scale className="w-4 h-4 text-[#4F8CFF]" />,
                  color: match.confidence === 'High' ? 'text-[#34D399]' : match.confidence === 'Medium' ? 'text-[#F5B301]' : 'text-[#98A2B3]',
                },
                {
                  label: 'Agreement',
                  value: match.modelConfidence ? `${Math.round(match.modelConfidence * 100)}%` : '85%',
                  icon: <BarChart3 className="w-4 h-4 text-[#4F8CFF]" />,
                  color: 'text-[#F5F5F5]',
                },
                {
                  label: 'Variance',
                  value: match.confidence === 'High' ? 'Low' : match.confidence === 'Medium' ? 'Medium' : 'High',
                  icon: <ChartColumn className="w-4 h-4 text-[#4F8CFF]" />,
                  color: match.confidence === 'High' ? 'text-[#34D399]' : match.confidence === 'Medium' ? 'text-[#F5B301]' : 'text-[#EF4444]',
                },
                {
                  label: 'Freshness',
                  value: 'Recent',
                  icon: <Clock3 className="w-4 h-4 text-[#4F8CFF]" />,
                  color: 'text-[#34D399]',
                },
              ].map(({ label, value, icon, color }) => (
                <motion.div
                  key={label}
                  whileHover={{ y: -2 }}
                  className="bg-[#1C222C] rounded-lg p-4 hover:bg-[#232B36] transition-colors duration-200"
                >
                  <div className="flex items-center gap-2 mb-3">
                    {icon}
                    <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider">{label}</span>
                  </div>
                  <div className={`text-xl font-bold ${color}`}>{value}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </AnimSection>

        {/* ── AI MATCH SUMMARY ──────────────────────────────────────────────── */}
        <AnimSection>
          <div className="bg-[#151A22] rounded-xl p-5 shadow-[0_4px_18px_rgba(0,0,0,0.16)] border-t-2 border-[#4F8CFF]">
            <div className="flex items-center gap-2 mb-5">
              <Star className="w-4 h-4 text-[#F5B301]" />
              <h2 className="text-base font-semibold text-[#F5F5F5] tracking-tight">AI Match Summary</h2>
            </div>

            {/* Summary grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-5">
              {[
                { label: 'Top Pick', value: match.prediction || 'N/A', color: 'text-[#4F8CFF]' },
                { label: 'Predicted Score', value: match.mostLikelyScore || 'N/A', color: 'text-[#F5F5F5]' },
                { label: 'Win Probability', value: `${topProbability}%`, color: 'text-[#34D399]' },
                {
                  label: 'Expected Goals',
                  value: totalXG ? `${totalXG.toFixed(2)} xG` : `${((xGA ?? 0) + (xGB ?? 0)).toFixed(2)} xG`,
                  color: 'text-[#F5F5F5]',
                },
                {
                  label: 'Best Goal Market',
                  value: (() => {
                    const ou25 = ouPct('2.5', 'over');
                    const ou15 = ouPct('1.5', 'over');
                    if (ou25 && ou25 >= 60) return `Over 2.5 (${ou25}%)`;
                    if (ou15 && ou15 >= 70) return `Over 1.5 (${ou15}%)`;
                    return 'N/A';
                  })(),
                  color: 'text-[#F5B301]',
                },
                {
                  label: 'Safest Bet',
                  value: (() => {
                    const max1x2 = topProbability;
                    if (dc1x && dc1x > max1x2 + 5) return `DC: ${match.teamACode} or Draw`;
                    if (dcX2 && dcX2 > max1x2 + 5) return `DC: Draw or ${match.teamBCode}`;
                    return match.prediction || 'N/A';
                  })(),
                  color: 'text-[#34D399]',
                },
              ].map(({ label, value, color }) => (
                <div key={label} className="bg-[#1C222C] rounded-lg px-3 py-2.5">
                  <div className="text-[10px] text-[#98A2B3] uppercase tracking-wider mb-1">{label}</div>
                  <div className={`text-sm font-semibold ${color}`}>{value}</div>
                </div>
              ))}
            </div>

            {/* AI text summary */}
            <div className="bg-[#1C222C] rounded-lg p-4">
              <p className="text-sm text-[#98A2B3] leading-relaxed">
                {match.aiSummary ||
                  `Based on comprehensive analysis, ${match.prediction || 'the prediction'} shows ${match.confidence?.toLowerCase() || 'moderate'} confidence. ` +
                  `The model projects ${match.teamA} with ${probA}% probability vs ${match.teamB} at ${probB}% (Draw ${probD}%). ` +
                  `Expected goals: ${xGA?.toFixed(2) || '—'} (${match.teamA}) — ${xGB?.toFixed(2) || '—'} (${match.teamB}), ` +
                  `with a predicted scoreline of ${match.mostLikelyScore || 'TBD'}.`}
              </p>
            </div>
          </div>
        </AnimSection>

        {/* Bottom spacing */}
        <div className="h-8" />
      </div>
    </motion.div>
  );
}
