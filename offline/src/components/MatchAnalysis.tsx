import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Star, TrendingUp, Shield, Target, Zap, Award, Trophy, Goal, ChartColumn, Clock3, Users, Scale, BarChart3, ChevronDown, ChevronUp, AlertCircle, Ban, HelpCircle } from 'lucide-react';
import { MatchPrediction } from '../types';

interface MatchAnalysisProps {
  match: MatchPrediction;
  onClose: () => void;
  onBack?: () => void;
  drawerTeamLoading?: boolean;
}

// ── Helper: Team Colors (Solid edge for structural identity) ────────────────
const getTeamColor = (teamName: string): string => {
  const colorMap: { [key: string]: string } = {
    'Argentina': '#3071a9', 'Australia': '#dca11d', 'Belgium': '#e30613', 'Brazil': '#f8ec11',
    'England': '#1b2c56', 'France': '#3b4d8c', 'Germany': '#1c1c1c', 'Italy': '#1d4f91',
    'Netherlands': '#f36c21', 'Portugal': '#e41c36', 'Spain': '#c60b1e', 'USA': '#002868',
    'Uruguay': '#5bc2e7', 'Croatia': '#ff0000', 'Denmark': '#c60c30', 'Mexico': '#006341',
    'Japan': '#000080', 'South Korea': '#c60c30', 'Morocco': '#a5322c', 'Switzerland': '#d52b1e',
    'Poland': '#dc143c', 'Senegal': '#00853f', 'Ecuador': '#ffcc00', 'Wales': '#d40000',
    'Iran': '#da291c', 'Saudi Arabia': '#006c35', 'Tunisia': '#e70013', 'Canada': '#c8102e',
    'Ghana': '#da291c', 'Cameroon': '#007a5e', 'Serbia': '#c60c30', 'Qatar': '#8a1538',
  };
  return colorMap[teamName] || '#6b6656';
};

// ── Helper: Confidence Ratings ──────────────────────────────────────────────
type ConfidenceRating = 'STRONG' | 'GOOD' | 'LEAN' | 'AVOID';

function getConfidenceRating(probability: number | null): ConfidenceRating {
  if (probability === null) return 'AVOID';
  if (probability >= 75) return 'STRONG';
  if (probability >= 60) return 'GOOD';
  if (probability >= 45) return 'LEAN';
  return 'AVOID';
}

function getConfidenceColors(rating: ConfidenceRating) {
  switch (rating) {
    case 'STRONG':
      return { text: '#5c8a4a', bg: '#1e2519', borderLeft: '#5c8a4a' };
    case 'GOOD':
      return { text: '#4c8a83', bg: '#1c2621', borderLeft: '#4c8a83' };
    case 'LEAN':
      return { text: '#c9902f', bg: '#2a2317', borderLeft: '#c9902f' };
    case 'AVOID':
    default:
      return { text: '#6b675c', bg: '#232219', borderLeft: '#6b675c' };
  }
}

// ── Editorial Confidence Badge ───────────────────────────────────────────────
function ConfidenceBadge({ rating }: { rating: ConfidenceRating }) {
  const colors = getConfidenceColors(rating);
  return (
    <span
      className="inline-block px-1.5 py-0.5 text-[9px] font-mono font-bold uppercase tracking-wider rounded-[3px]"
      style={{
        color: colors.text,
        backgroundColor: colors.bg,
        borderLeft: `3px solid ${colors.borderLeft}`,
      }}
    >
      {rating}
    </span>
  );
}

// ── Editorial Progress Bar ──────────────────────────────────────────────────
function ProgressBar({ probability, rating }: { probability: number | null; rating: ConfidenceRating }) {
  const pct = probability ?? 0;
  const colors = getConfidenceColors(rating);
  return (
    <div className="w-full h-1.5 bg-[#232219]">
      <motion.div
        initial={{ width: 0 }}
        whileInView={{ width: `${Math.min(pct, 100)}%` }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="h-full"
        style={{ backgroundColor: colors.text }}
      />
    </div>
  );
}

// ── Editorial Section Header ─────────────────────────────────────────────────
function SectionHeader({ title, subtitle, icon }: { title: string; subtitle?: string; icon?: React.ReactNode }) {
  return (
    <div className="mb-4 flex items-center justify-between border-b border-[rgba(237,232,222,0.10)] pb-2.5">
      <div className="flex items-center gap-2">
        {icon && <div className="text-[#ece7da]">{icon}</div>}
        <h2 className="text-base font-sans font-bold uppercase tracking-wider text-[#a39c8a]">{title}</h2>
      </div>
      {subtitle && <span className="text-[10px] font-mono text-[#6b6656] uppercase tracking-wider">{subtitle}</span>}
    </div>
  );
}

// ── Editorial Block ──────────────────────────────────────────────────────────
function EditorialBlock({ id, children }: { id?: string; children: React.ReactNode }) {
  return (
    <motion.div
      id={id}
      className="bg-[#1b1a14] border border-[rgba(237,232,222,0.10)] rounded-[4px] p-5 shadow-none"
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.4 }}
    >
      {children}
    </motion.div>
  );
}

// ── Outcome Option Card (within a structured block) ─────────────────────────
function OutcomeCard({
  label,
  probability,
  isTopPick = false,
}: {
  label: string;
  probability: number | null;
  isTopPick?: boolean;
}) {
  const rating = getConfidenceRating(probability);
  return (
    <div
      className={`flex-1 p-3.5 bg-[#232219] border rounded-[4px] text-center transition-all ${
        isTopPick
          ? 'border-[#c1703b]'
          : 'border-[rgba(237,232,222,0.06)]'
      }`}
    >
      <div className="text-[10px] font-mono text-[#a39c8a] uppercase tracking-wider mb-1.5">{label}</div>
      <div
        className="text-2xl font-mono font-bold tracking-tight mb-2"
        style={{ color: isTopPick ? '#c1703b' : '#ece7da' }}
      >
        {probability !== null ? `${probability}%` : 'N/A'}
      </div>
      <div className="flex items-center justify-center gap-1">
        {isTopPick && (
          <span className="text-[8px] font-mono font-bold uppercase px-1.5 py-0.5 bg-[#c1703b]/10 text-[#c1703b] border-l-2 border-[#c1703b] rounded-[3px] mr-1">
            TOP PICK
          </span>
        )}
        <ConfidenceBadge rating={rating} />
      </div>
    </div>
  );
}

// ── Editorial Table Row (Total Goals, Handicap, etc.) ───────────────────────
function EditorialRow({
  label,
  probability,
  borderBottom = true,
}: {
  label: string;
  probability: number | null;
  borderBottom?: boolean;
}) {
  const rating = getConfidenceRating(probability);
  return (
    <div
      className={`flex items-center gap-4 py-2.5 px-3 transition-colors hover:bg-[rgba(237,232,222,0.02)] ${
        borderBottom ? 'border-b border-[rgba(237,232,222,0.06)]' : ''
      }`}
    >
      <span className="text-xs font-mono text-[#ece7da] w-36 shrink-0">{label}</span>
      <div className="flex-1">
        <ProgressBar probability={probability} rating={rating} />
      </div>
      <span className="text-xs font-mono font-semibold text-[#ece7da] w-12 text-right">
        {probability !== null ? `${probability}%` : 'N/A'}
      </span>
      <div className="w-20 flex justify-end shrink-0">
        <ConfidenceBadge rating={rating} />
      </div>
    </div>
  );
}

// ── Collapsible Editorial Block ──────────────────────────────────────────────
function CollapsibleEditorialBlock({
  title,
  subtitle,
  icon,
  children,
}: {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-[#1b1a14] border border-[rgba(237,232,222,0.10)] rounded-[4px] overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between p-4 hover:bg-[rgba(237,232,222,0.02)] transition-colors duration-150 text-left"
      >
        <div className="flex items-center gap-2">
          {icon && <div className="text-[#ece7da]">{icon}</div>}
          <div>
            <h2 className="text-sm font-sans font-bold uppercase tracking-wider text-[#ece7da]">{title}</h2>
            {subtitle && <p className="text-[10px] font-mono text-[#6b6656] uppercase mt-0.5">{subtitle}</p>}
          </div>
        </div>
        {open ? (
          <ChevronUp className="w-4 h-4 text-[#a39c8a]" />
        ) : (
          <ChevronDown className="w-4 h-4 text-[#a39c8a]" />
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
            className="overflow-hidden border-t border-[rgba(237,232,222,0.10)] bg-[#15140f]/20"
          >
            <div>{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

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

  const topProbability = Math.max(probA, probB, probD);
  const isKnockout = match.stage?.toLowerCase().includes('knockout') ||
    match.stage?.toLowerCase().includes('round of') ||
    match.stage?.toLowerCase().includes('quarter') ||
    match.stage?.toLowerCase().includes('semi') ||
    match.stage?.toLowerCase().includes('final') ||
    !!match.qualifyProbA;

  // Double Chance computed values
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

  const asianTotalLines = ['1.25', '1.5', '1.75', '2', '2.25', '2.5', '2.75', '3'];

  // Qualify probs
  const qualifyA = match.qualifyProbA != null ? Math.round(match.qualifyProbA) : null;
  const qualifyB = match.qualifyProbB != null ? Math.round(match.qualifyProbB) : null;

  // Navigation structure based on editorial panels
  const navItems = [
    { id: 'overview', label: 'Overview' },
    { id: 'match-markets', label: 'Match Markets' },
    { id: 'goal-markets', label: 'Goal Markets' },
    { id: 'asian-markets', label: 'Asian Markets' },
    { id: 'correct-score', label: 'Correct Score' },
    { id: 'team-news', label: 'Team News' },
    { id: 'model-insights', label: 'Model Insights' },
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
      className="fixed inset-0 bg-[#15140f] z-50 overflow-y-auto selection:bg-[#c1703b] selection:text-[#15140f]"
    >
      {/* Top bar — Back button only */}
      <div className="sticky top-0 bg-[#15140f]/95 backdrop-none border-b border-[rgba(237,232,222,0.10)] z-50">
        <div className="max-w-[1080px] mx-auto px-6 py-3 flex items-center">
          {onBack && (
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-[#a39c8a] hover:text-[#ece7da] transition-colors text-sm font-sans uppercase font-bold tracking-wider"
            >
              <ArrowLeft className="w-4 h-4 text-[#a39c8a]" />
              <span>Back to Matches</span>
            </button>
          )}
        </div>
      </div>

      {/* Sticky Navigation */}
      <div className="sticky top-[45px] bg-[#15140f]/95 backdrop-none border-b border-[rgba(237,232,222,0.10)] z-40">
        <div className="max-w-[1080px] mx-auto px-6">
          <nav className="flex gap-6 overflow-x-auto py-2.5 scrollbar-none">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className={`relative text-xs font-sans uppercase font-bold tracking-wider transition-colors whitespace-nowrap py-1 ${
                  activeSection === item.id ? 'text-[#c1703b]' : 'text-[#a39c8a] hover:text-[#ece7da]'
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <div className="max-w-[1080px] mx-auto px-6 py-8 space-y-6">

        {/* ── HERO SECTION ─────────────────────────────────────────────────── */}
        <EditorialBlock id="section-overview">
          <div className="flex flex-col gap-6">
            {/* Header info / Meta */}
            <div className="flex items-center justify-between text-[10px] font-mono text-[#6b6656] uppercase tracking-wider border-b border-[rgba(237,232,222,0.10)] pb-2">
              <div className="flex items-center gap-1.5">
                <Trophy className="w-3.5 h-3.5 text-[#6b6656] stroke-[1.75]" />
                <span className="text-[#ece7da]">{match.stage}</span>
              </div>
              {match.venue && (
                <div className="flex items-center gap-1.5">
                  <span>STADIUM:</span>
                  <span className="text-[#ece7da]">{match.venue}</span>
                </div>
              )}
            </div>

            {/* Teams and 1X2 Probabilities Row */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              {/* Home Team */}
              <div
                className="flex items-center gap-4 py-2 px-3 border-l-4 bg-[#232219]/30 rounded-r-[4px]"
                style={{ borderLeftColor: getTeamColor(match.teamA) }}
              >
                <span className="text-3xl">{flagA}</span>
                <div>
                  <h1 className="text-xl font-sans font-bold uppercase tracking-wide text-[#ece7da]">{match.teamA}</h1>
                  <p className="text-[10px] font-mono text-[#6b6656] mt-0.5">HOME TEAM · {match.teamACode}</p>
                </div>
              </div>

              {/* Data overview */}
              <div className="flex items-center justify-center gap-6 py-2 px-4 border border-[rgba(237,232,222,0.08)] bg-[#232219]/20 rounded-[4px]">
                <div className="text-center">
                  <div className="text-xs font-mono text-[#6b6656] uppercase tracking-wider mb-1">HOME</div>
                  <div className="text-xl font-mono font-bold text-[#ece7da]">{probA}%</div>
                </div>
                <div className="text-center border-x border-[rgba(237,232,222,0.08)] px-4">
                  <div className="text-xs font-mono text-[#6b6656] uppercase tracking-wider mb-1">DRAW</div>
                  <div className="text-base font-mono font-bold text-[#a39c8a]">{probD}%</div>
                </div>
                <div className="text-center">
                  <div className="text-xs font-mono text-[#6b6656] uppercase tracking-wider mb-1">AWAY</div>
                  <div className="text-xl font-mono font-bold text-[#ece7da]">{probB}%</div>
                </div>
              </div>

              {/* Away Team */}
              <div
                className="flex items-center justify-end gap-4 py-2 px-3 border-r-4 bg-[#232219]/30 rounded-l-[4px] text-right"
                style={{ borderRightColor: getTeamColor(match.teamB) }}
              >
                <div>
                  <h1 className="text-xl font-sans font-bold uppercase tracking-wide text-[#ece7da]">{match.teamB}</h1>
                  <p className="text-[10px] font-mono text-[#6b6656] mt-0.5">AWAY TEAM · {match.teamBCode}</p>
                </div>
                <span className="text-3xl">{flagB}</span>
              </div>
            </div>

            {/* Probability visual bar */}
            <div className="h-1.5 bg-[#232219] flex">
              <div
                className="h-full transition-all"
                style={{
                  width: `${probA}%`,
                  backgroundColor: getTeamColor(match.teamA),
                }}
              />
              <div
                className="h-full transition-all"
                style={{
                  width: `${probD}%`,
                  backgroundColor: '#403e35',
                }}
              />
              <div
                className="h-full transition-all"
                style={{
                  width: `${probB}%`,
                  backgroundColor: getTeamColor(match.teamB),
                }}
              />
            </div>

            {/* Structured Editorial Metadata Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 border-t border-[rgba(237,232,222,0.10)] pt-4">
              <div>
                <span className="block text-[10px] font-mono text-[#6b6656] uppercase tracking-wider mb-1">Predicted Score</span>
                <span className="text-sm font-mono font-bold text-[#ece7da]">{match.mostLikelyScore || 'N/A'}</span>
              </div>
              <div>
                <span className="block text-[10px] font-mono text-[#6b6656] uppercase tracking-wider mb-1">Expected Goals (xG)</span>
                <span className="text-sm font-mono font-bold text-[#ece7da]">
                  {xGA?.toFixed(2) || '—'} – {xGB?.toFixed(2) || '—'}
                </span>
              </div>
              <div>
                <span className="block text-[10px] font-mono text-[#6b6656] uppercase tracking-wider mb-1">Confidence</span>
                <span className="text-sm font-mono font-bold text-[#ece7da]">{match.confidence || 'N/A'}</span>
              </div>
              <div>
                <span className="block text-[10px] font-mono text-[#c1703b] uppercase tracking-wider mb-1">Top Pick</span>
                <div className="flex items-center gap-1.5 text-sm font-mono font-bold text-[#c1703b]">
                  <Star className="w-3.5 h-3.5 text-[#c1703b] stroke-[1.75]" />
                  <span>{match.prediction || 'N/A'}</span>
                </div>
              </div>
            </div>
          </div>
        </EditorialBlock>

        {/* ── MATCH MARKETS ─────────────────────────────────────────────────── */}
        <EditorialBlock id="section-match-markets">
          <SectionHeader
            title="Match Markets"
            subtitle="1X2, Qualification, Double Chance, DNB, BTTS"
            icon={<Shield className="w-[18px] h-[18px] stroke-[1.75]" />}
          />

          <div className="space-y-6">
            {/* 1. 1X2 Prediction */}
            <div>
              <div className="text-[10px] font-mono text-[#6b6656] uppercase tracking-wider mb-3">1X2 Prediction</div>
              <div className="flex flex-col md:flex-row gap-3">
                <OutcomeCard
                  label={match.teamA}
                  probability={probA}
                  isTopPick={match.prediction === match.teamA}
                />
                <OutcomeCard
                  label="Draw"
                  probability={probD}
                  isTopPick={match.prediction === 'Draw' || match.prediction === 'X'}
                />
                <OutcomeCard
                  label={match.teamB}
                  probability={probB}
                  isTopPick={match.prediction === match.teamB}
                />
              </div>
            </div>

            <div className="h-px bg-[rgba(237,232,222,0.10)]" />

            {/* 2. To Qualify */}
            {isKnockout && (qualifyA !== null || qualifyB !== null) && (
              <>
                <div>
                  <div className="text-[10px] font-mono text-[#6b6656] uppercase tracking-wider mb-3">To Qualify</div>
                  <div className="flex flex-col md:flex-row gap-3">
                    <OutcomeCard
                      label={match.teamA}
                      probability={qualifyA}
                      isTopPick={qualifyA !== null && qualifyA > (qualifyB ?? 0) && match.prediction === match.teamA}
                    />
                    <OutcomeCard
                      label={match.teamB}
                      probability={qualifyB}
                      isTopPick={qualifyB !== null && qualifyB > (qualifyA ?? 0) && match.prediction === match.teamB}
                    />
                  </div>
                </div>
                <div className="h-px bg-[rgba(237,232,222,0.10)]" />
              </>
            )}

            {/* 3. Double Chance */}
            {(dc1x !== null || dc12 !== null || dcX2 !== null) && (
              <>
                <div>
                  <div className="text-[10px] font-mono text-[#6b6656] uppercase tracking-wider mb-3">Double Chance</div>
                  <div className="flex flex-col md:flex-row gap-3">
                    <OutcomeCard
                      label={`${match.teamA} or Draw`}
                      probability={dc1x}
                    />
                    <OutcomeCard
                      label={`${match.teamA} or ${match.teamB}`}
                      probability={dc12}
                    />
                    <OutcomeCard
                      label={`Draw or ${match.teamB}`}
                      probability={dcX2}
                    />
                  </div>
                </div>
                <div className="h-px bg-[rgba(237,232,222,0.10)]" />
              </>
            )}

            {/* 4. Draw No Bet */}
            {(dnbHome !== null || dnbAway !== null) && (
              <>
                <div>
                  <div className="text-[10px] font-mono text-[#6b6656] uppercase tracking-wider mb-3">Draw No Bet</div>
                  <div className="flex flex-col md:flex-row gap-3">
                    <OutcomeCard
                      label={match.teamA}
                      probability={dnbHome}
                    />
                    <OutcomeCard
                      label={match.teamB}
                      probability={dnbAway}
                    />
                  </div>
                </div>
                <div className="h-px bg-[rgba(237,232,222,0.10)]" />
              </>
            )}

            {/* 5. Both Teams To Score */}
            {(bttsYes !== null || bttsNo !== null) && (
              <div>
                <div className="text-[10px] font-mono text-[#6b6656] uppercase tracking-wider mb-3">Both Teams To Score</div>
                <div className="flex flex-col md:flex-row gap-3">
                  <OutcomeCard
                    label="Yes"
                    probability={bttsYes}
                    isTopPick={(bttsYes ?? 0) > (bttsNo ?? 0) && match.prediction?.toLowerCase().includes('btts')}
                  />
                  <OutcomeCard
                    label="No"
                    probability={bttsNo}
                    isTopPick={(bttsNo ?? 0) > (bttsYes ?? 0) && match.prediction?.toLowerCase().includes('clean sheet')}
                  />
                </div>
              </div>
            )}
          </div>
        </EditorialBlock>

        {/* ── GOAL MARKETS ─────────────────────────────────────────────────── */}
        <EditorialBlock id="section-goal-markets">
          <SectionHeader
            title="Goal Markets"
            subtitle="Totals, Team Goals, First Goalscorer"
            icon={<Goal className="w-[18px] h-[18px] stroke-[1.75]" />}
          />

          <div className="space-y-6">
            {/* Total Goals */}
            <div>
              <div className="text-[10px] font-mono text-[#6b6656] uppercase tracking-wider mb-2">Total Goals (Over / Under)</div>
              <div className="bg-[#232219]/20 border border-[rgba(237,232,222,0.06)] rounded-[4px] overflow-hidden">
                {(['0.5', '1.5', '2.5', '3.5', '4.5'] as const).map((line, i, arr) => (
                  <React.Fragment key={line}>
                    <EditorialRow label={`Over ${line}`} probability={ouPct(line, 'over')} borderBottom />
                    <EditorialRow label={`Under ${line}`} probability={ouPct(line, 'under')} borderBottom={i < arr.length - 1} />
                  </React.Fragment>
                ))}
              </div>
            </div>

            <div className="h-px bg-[rgba(237,232,222,0.10)]" />

            {/* Team Goals */}
            {match.teamGoals && (
              <>
                <div>
                  <div className="text-[10px] font-mono text-[#6b6656] uppercase tracking-wider mb-3">Team Goals</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Home Team Goals */}
                    <div
                      className="bg-[#232219]/30 border border-[rgba(237,232,222,0.06)] p-4 rounded-[4px] border-l-4"
                      style={{ borderLeftColor: getTeamColor(match.teamA) }}
                    >
                      <div className="text-xs font-sans font-bold uppercase tracking-wider text-[#ece7da] mb-3">{match.teamA} Goals</div>
                      <div className="space-y-3">
                        {[
                          { label: 'Over 0.5', val: match.teamGoals.home.over_0_5 },
                          { label: 'Over 1.5', val: match.teamGoals.home.over_1_5 },
                          { label: 'Over 2.5', val: match.teamGoals.home.over_2_5 },
                        ].map(({ label, val }) => {
                          const pct = val != null ? Math.round(val <= 1 ? val * 100 : val) : null;
                          const rating = getConfidenceRating(pct);
                          return (
                            <div key={label} className="flex items-center gap-3">
                              <span className="text-xs font-mono text-[#a39c8a] w-16 shrink-0">{label}</span>
                              <div className="flex-1">
                                <ProgressBar probability={pct} rating={rating} />
                              </div>
                              <span className="text-xs font-mono font-semibold text-[#ece7da] w-8 text-right">
                                {pct !== null ? `${pct}%` : 'N/A'}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Away Team Goals */}
                    <div
                      className="bg-[#232219]/30 border border-[rgba(237,232,222,0.06)] p-4 rounded-[4px] border-l-4"
                      style={{ borderLeftColor: getTeamColor(match.teamB) }}
                    >
                      <div className="text-xs font-sans font-bold uppercase tracking-wider text-[#ece7da] mb-3">{match.teamB} Goals</div>
                      <div className="space-y-3">
                        {[
                          { label: 'Over 0.5', val: match.teamGoals.away.over_0_5 },
                          { label: 'Over 1.5', val: match.teamGoals.away.over_1_5 },
                          { label: 'Over 2.5', val: match.teamGoals.away.over_2_5 },
                        ].map(({ label, val }) => {
                          const pct = val != null ? Math.round(val <= 1 ? val * 100 : val) : null;
                          const rating = getConfidenceRating(pct);
                          return (
                            <div key={label} className="flex items-center gap-3">
                              <span className="text-xs font-mono text-[#a39c8a] w-16 shrink-0">{label}</span>
                              <div className="flex-1">
                                <ProgressBar probability={pct} rating={rating} />
                              </div>
                              <span className="text-xs font-mono font-semibold text-[#ece7da] w-8 text-right">
                                {pct !== null ? `${pct}%` : 'N/A'}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="h-px bg-[rgba(237,232,222,0.10)]" />
              </>
            )}

            {/* First Team To Score */}
            <div>
              <div className="text-[10px] font-mono text-[#6b6656] uppercase tracking-wider mb-3">First Team To Score</div>
              {(() => {
                const totalXg = (match.xGA ?? 0) + (match.xGB ?? 0);
                const noGoalProb = match.overUnder?.['0.5']?.under != null
                  ? Math.round((match.overUnder['0.5'].under <= 1 ? match.overUnder['0.5'].under * 100 : match.overUnder['0.5'].under))
                  : null;
                const scoringProb = noGoalProb != null ? 100 - noGoalProb : 100;
                const ftsA = totalXg > 0 ? Math.round(((match.xGA ?? 0) / totalXg) * scoringProb) : null;
                const ftsB = totalXg > 0 ? Math.round(((match.xGB ?? 0) / totalXg) * scoringProb) : null;
                return (
                  <div className="flex flex-col md:flex-row gap-3">
                    <OutcomeCard label={match.teamA} probability={ftsA} />
                    <OutcomeCard label="No Goal" probability={noGoalProb} />
                    <OutcomeCard label={match.teamB} probability={ftsB} />
                  </div>
                );
              })()}
            </div>
          </div>
        </EditorialBlock>

        {/* ── ASIAN MARKETS ────────────────────────────────────────────────── */}
        <div id="section-asian-markets" className="space-y-4">
          {/* Asian Handicap */}
          <CollapsibleEditorialBlock
            title="Asian Handicap"
            subtitle="Handicap line probabilities"
            icon={<BarChart3 className="w-[18px] h-[18px] stroke-[1.75]" />}
          >
            {match.asianHandicap?.lines ? (
              <div className="overflow-hidden">
                {/* Header row */}
                <div className="flex items-center gap-4 px-4 py-2 bg-[#232219] border-b border-[rgba(237,232,222,0.06)] font-mono text-[9px] text-[#a39c8a] uppercase tracking-wider">
                  <span className="w-36 shrink-0">Line</span>
                  <span className="flex-1">Probability</span>
                  <span className="w-12 text-right">Prob</span>
                  <span className="w-20 text-right">Confidence</span>
                </div>
                <div>
                  {Object.entries(match.asianHandicap.lines)
                    .map(([line, val]) => ({
                      label: `${match.asianHandicap!.favored_team} ${line}`,
                      prob: Math.round((val as number) <= 1 ? (val as number) * 100 : (val as number)),
                      rawLine: parseFloat(line),
                    }))
                    .sort((a, b) => b.rawLine - a.rawLine)
                    .map((item, idx, arr) => (
                      <EditorialRow
                        key={item.label}
                        label={item.label}
                        probability={item.prob}
                        borderBottom={idx < arr.length - 1}
                      />
                    ))}
                </div>
              </div>
            ) : (
              <div className="px-5 py-6 text-xs font-mono text-[#6b6656] text-center">No handicap data available</div>
            )}
          </CollapsibleEditorialBlock>

          {/* Asian Total */}
          <CollapsibleEditorialBlock
            title="Asian Total"
            subtitle="Quarter-ball over/under lines"
            icon={<TrendingUp className="w-[18px] h-[18px] stroke-[1.75]" />}
          >
            <div className="overflow-hidden">
              {/* Header row */}
              <div className="flex items-center gap-4 px-4 py-2 bg-[#232219] border-b border-[rgba(237,232,222,0.06)] font-mono text-[9px] text-[#a39c8a] uppercase tracking-wider">
                <span className="w-36 shrink-0">Line</span>
                <span className="flex-1">Probability</span>
                <span className="w-12 text-right">Prob</span>
                <span className="w-20 text-right">Confidence</span>
              </div>
              <div>
                {asianTotalLines.map((line, idx) => {
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
                      <EditorialRow label={`Over ${line}`} probability={overPct} borderBottom />
                      <EditorialRow label={`Under ${line}`} probability={underPct} borderBottom={!isLast} />
                    </React.Fragment>
                  );
                })}
              </div>
            </div>
          </CollapsibleEditorialBlock>
        </div>

        {/* ── CORRECT SCORES ────────────────────────────────────────────────── */}
        <EditorialBlock id="section-correct-score">
          <SectionHeader
            title="Correct Score"
            subtitle="Top 5 most likely scorelines"
            icon={<ChartColumn className="w-[18px] h-[18px] stroke-[1.75]" />}
          />
          <div className="space-y-2">
            {match.top5Scorelines?.slice(0, 5).map((score, index) => {
              const pct = score.probability != null ? Math.round(score.probability <= 1 ? score.probability * 100 : score.probability) : 0;
              const rating = getConfidenceRating(pct);
              const medals = ['🥇', '🥈', '🥉'];
              const medal = medals[index] || `${index + 1}.`;
              return (
                <div
                  key={index}
                  className="flex items-center gap-4 bg-[#232219]/20 border border-[rgba(237,232,222,0.06)] rounded-[4px] px-4 py-2.5"
                >
                  <span className="text-base font-mono w-8 shrink-0">{medal}</span>
                  <span className="text-sm font-mono font-bold text-[#ece7da] w-16">{score.score}</span>
                  <div className="flex-1">
                    <ProgressBar probability={pct} rating={rating} />
                  </div>
                  <span className="text-xs font-mono font-semibold text-[#ece7da] w-10 text-right">{pct}%</span>
                  <div className="w-20 flex justify-end shrink-0">
                    <ConfidenceBadge rating={rating} />
                  </div>
                </div>
              );
            })}
            {(!match.top5Scorelines || match.top5Scorelines.length === 0) && (
              <div className="text-xs font-mono text-[#6b6656] text-center py-6">No scoreline data available</div>
            )}
          </div>
        </EditorialBlock>

        {/* ── TEAM NEWS ─────────────────────────────────────────────────────── */}
        <EditorialBlock id="section-team-news">
          <SectionHeader
            title="Team News"
            subtitle="Injuries and Suspensions report"
            icon={<Users className="w-[18px] h-[18px] stroke-[1.75]" />}
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Team A News */}
            <div
              className="bg-[#232219]/20 border border-[rgba(237,232,222,0.06)] p-4 rounded-[4px] border-l-4"
              style={{ borderLeftColor: getTeamColor(match.teamA) }}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{flagA}</span>
                  <span className="text-sm font-sans font-bold uppercase tracking-wider text-[#ece7da]">{match.teamA}</span>
                </div>
                <span className={`text-[9px] font-mono font-bold uppercase px-1.5 py-0.5 rounded-[3px] ${
                  match.impactRatingA === 'Critical' ? 'bg-[#EF4444]/15 text-[#EF4444] border-l border-[#EF4444]' :
                  match.impactRatingA === 'Moderate' ? 'bg-[#c9902f]/15 text-[#c9902f] border-l border-[#c9902f]' :
                  'bg-[#5c8a4a]/15 text-[#5c8a4a] border-l border-[#5c8a4a]'
                }`}>{match.impactRatingA || 'Minimal'} Impact</span>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center gap-1.5 text-[9px] font-mono text-[#6b6656] uppercase tracking-wider mb-2">
                    <AlertCircle className="w-3.5 h-3.5 text-[#6b6656] stroke-[1.75]" />
                    <span>Injuries</span>
                  </div>
                  {match.injuriesA?.length ? (
                    <div className="flex flex-wrap gap-1.5">
                      {match.injuriesA.map((p, i) => (
                        <span key={i} className="text-[11px] font-mono bg-[#232219] border border-[rgba(237,232,222,0.08)] text-[#a39c8a] px-2 py-0.5 rounded-[3px]">{p}</span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs font-serif italic text-[#6b6656]">No players reported injured</p>
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-1.5 text-[9px] font-mono text-[#6b6656] uppercase tracking-wider mb-2">
                    <Ban className="w-3.5 h-3.5 text-[#6b6656] stroke-[1.75]" />
                    <span>Suspensions</span>
                  </div>
                  {match.suspensionsA?.length ? (
                    <div className="flex flex-wrap gap-1.5">
                      {match.suspensionsA.map((p, i) => (
                        <span key={i} className="text-[11px] font-mono bg-[#232219] border border-[rgba(237,232,222,0.08)] text-[#a39c8a] px-2 py-0.5 rounded-[3px]">{p}</span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs font-serif italic text-[#6b6656]">No players suspended</p>
                  )}
                </div>
              </div>
            </div>

            {/* Team B News */}
            <div
              className="bg-[#232219]/20 border border-[rgba(237,232,222,0.06)] p-4 rounded-[4px] border-l-4"
              style={{ borderLeftColor: getTeamColor(match.teamB) }}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{flagB}</span>
                  <span className="text-sm font-sans font-bold uppercase tracking-wider text-[#ece7da]">{match.teamB}</span>
                </div>
                <span className={`text-[9px] font-mono font-bold uppercase px-1.5 py-0.5 rounded-[3px] ${
                  match.impactRatingB === 'Critical' ? 'bg-[#EF4444]/15 text-[#EF4444] border-l border-[#EF4444]' :
                  match.impactRatingB === 'Moderate' ? 'bg-[#c9902f]/15 text-[#c9902f] border-l border-[#c9902f]' :
                  'bg-[#5c8a4a]/15 text-[#5c8a4a] border-l border-[#5c8a4a]'
                }`}>{match.impactRatingB || 'Minimal'} Impact</span>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center gap-1.5 text-[9px] font-mono text-[#6b6656] uppercase tracking-wider mb-2">
                    <AlertCircle className="w-3.5 h-3.5 text-[#6b6656] stroke-[1.75]" />
                    <span>Injuries</span>
                  </div>
                  {match.injuriesB?.length ? (
                    <div className="flex flex-wrap gap-1.5">
                      {match.injuriesB.map((p, i) => (
                        <span key={i} className="text-[11px] font-mono bg-[#232219] border border-[rgba(237,232,222,0.08)] text-[#a39c8a] px-2 py-0.5 rounded-[3px]">{p}</span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs font-serif italic text-[#6b6656]">No players reported injured</p>
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-1.5 text-[9px] font-mono text-[#6b6656] uppercase tracking-wider mb-2">
                    <Ban className="w-3.5 h-3.5 text-[#6b6656] stroke-[1.75]" />
                    <span>Suspensions</span>
                  </div>
                  {match.suspensionsB?.length ? (
                    <div className="flex flex-wrap gap-1.5">
                      {match.suspensionsB.map((p, i) => (
                        <span key={i} className="text-[11px] font-mono bg-[#232219] border border-[rgba(237,232,222,0.08)] text-[#a39c8a] px-2 py-0.5 rounded-[3px]">{p}</span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs font-serif italic text-[#6b6656]">No players suspended</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </EditorialBlock>

        {/* ── MODEL INSIGHTS & AI SUMMARY ────────────────────────────────────── */}
        <EditorialBlock id="section-model-insights">
          <SectionHeader
            title="Model Insights"
            subtitle="Calibration, variance & AI summary"
            icon={<Zap className="w-[18px] h-[18px] stroke-[1.75]" />}
          />

          <div className="space-y-6">
            {/* Prediction Confidence Cards */}
            <div>
              <div className="text-[10px] font-mono text-[#6b6656] uppercase tracking-wider mb-3">Model Confidence Indicators</div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  {
                    label: 'Calibration',
                    value: match.confidence || 'N/A',
                    color: match.confidence === 'High' ? '#5c8a4a' : match.confidence === 'Medium' ? '#c9902f' : '#6b675c',
                  },
                  {
                    label: 'Agreement',
                    value: match.modelConfidence ? `${Math.round(match.modelConfidence * 100)}%` : '85%',
                    color: '#ece7da',
                  },
                  {
                    label: 'Variance',
                    value: match.confidence === 'High' ? 'Low' : match.confidence === 'Medium' ? 'Medium' : 'High',
                    color: match.confidence === 'High' ? '#5c8a4a' : match.confidence === 'Medium' ? '#c9902f' : '#6b675c',
                  },
                  {
                    label: 'Freshness',
                    value: 'Recent',
                    color: '#4c8a83',
                  },
                ].map(({ label, value, color }) => (
                  <div
                    key={label}
                    className="bg-[#232219]/20 border border-[rgba(237,232,222,0.06)] p-3.5 rounded-[4px]"
                  >
                    <span className="block text-[9px] font-mono text-[#6b6656] uppercase tracking-wider mb-2">{label}</span>
                    <span className="text-base font-mono font-bold" style={{ color }}>{value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="h-px bg-[rgba(237,232,222,0.10)]" />

            {/* AI Match Summary */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Star className="w-[18px] h-[18px] text-[#c1703b] stroke-[1.75]" />
                <h3 className="text-sm font-sans font-bold uppercase tracking-wider text-[#ece7da]">AI Match Summary</h3>
              </div>

              {/* Grid of key recommendations */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                {[
                  { label: 'Top Pick', value: match.prediction || 'N/A', isAccent: true },
                  { label: 'Predicted Score', value: match.mostLikelyScore || 'N/A' },
                  { label: 'Win Probability', value: `${topProbability}%` },
                  {
                    label: 'Expected Goals',
                    value: totalXG ? `${totalXG.toFixed(2)} xG` : `${((xGA ?? 0) + (xGB ?? 0)).toFixed(2)} xG`,
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
                  },
                  {
                    label: 'Safest Bet',
                    value: (() => {
                      if (dc1x && dc1x > topProbability + 5) return `Double Chance: ${match.teamACode} or Draw`;
                      if (dcX2 && dcX2 > topProbability + 5) return `Double Chance: Draw or ${match.teamBCode}`;
                      return match.prediction || 'N/A';
                    })(),
                    isAccent: true,
                  },
                ].map(({ label, value, isAccent }) => (
                  <div
                    key={label}
                    className="bg-[#232219]/25 border border-[rgba(237,232,222,0.06)] px-3 py-2 rounded-[4px]"
                  >
                    <span className="block text-[9px] font-mono text-[#6b6656] uppercase tracking-wider mb-1">{label}</span>
                    <span
                      className="text-xs font-mono font-bold"
                      style={{ color: isAccent ? '#c1703b' : '#ece7da' }}
                    >
                      {value}
                    </span>
                  </div>
                ))}
              </div>

              {/* AI text summary */}
              <div className="bg-[#232219]/15 border border-[rgba(237,232,222,0.06)] p-4 rounded-[4px]">
                <p className="text-sm font-serif leading-relaxed text-[#ece7da]">
                  {match.aiSummary ||
                    `Analysis suggests ${match.prediction || 'the prediction'} holds ${match.confidence?.toLowerCase() || 'moderate'} confidence. ` +
                    `The model rates ${match.teamA} with ${probA}% probability against ${match.teamB} at ${probB}% (Draw ${probD}%). ` +
                    `Expectation is ${xGA?.toFixed(2) || '—'} goals for ${match.teamA} and ${xGB?.toFixed(2) || '—'} goals for ${match.teamB}, ` +
                    `resulting in a projected final scoreline of ${match.mostLikelyScore || 'TBD'}.`}
                </p>
              </div>
            </div>
          </div>
        </EditorialBlock>

        {/* Bottom spacer */}
        <div className="h-6" />
      </div>
    </motion.div>
  );
}
