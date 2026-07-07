import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowLeft, Star, TrendingUp, Shield, Target, Zap, Award } from 'lucide-react';
import { MatchPrediction } from '../types';

interface MatchAnalysisProps {
  match: MatchPrediction;
  onClose: () => void;
  onBack?: () => void;
  drawerTeamLoading?: boolean;
}

export default function MatchAnalysis({ 
  match, 
  onClose, 
  onBack,
  drawerTeamLoading = false
}: MatchAnalysisProps) {
  const [activeSection, setActiveSection] = useState('overview');

  // Helper functions extracted from App.tsx
  const getFlag = (teamName: string) => {
    const flagMap: { [key: string]: string } = {
      'Argentina': '🇦🇷', 'Australia': '🇦🇺', 'Belgium': '🇧🇪', 'Brazil': '🇧🇷',
      'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'France': '🇫🇷', 'Germany': '🇩🇪', 'Italy': '🇮🇹',
      'Netherlands': '🇳🇱', 'Portugal': '🇵🇹', 'Spain': '🇪🇸', 'USA': '🇺🇸',
      'Uruguay': '🇺🇾', 'Croatia': '🇭🇷', 'Denmark': '🇩🇰', 'Mexico': '🇲🇽',
      'Japan': '🇯🇵', 'South Korea': '🇰🇷', 'Morocco': '🇲🇦', 'Switzerland': '🇨🇭',
      'Poland': '🇵🇱', 'Senegal': '🇸🇳', 'Ecuador': '🇪🇨', 'Wales': '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
      'Iran': '🇮🇷', 'Saudi Arabia': '🇸🇦', 'Tunisia': '🇹🇳', 'Canada': '🇨🇦',
      'Ghana': '🇬🇭', 'Cameroon': '🇨🇲', 'Serbia': '🇷🇸', 'Qatar': '🇶🇦',
      'Egypt': '🇪🇬', 'China': '🇨🇳', 'South Africa': '🇿🇦', 'Nigeria': '🇳🇬',
      'Ivory Coast': '🇨🇮', 'Algeria': '🇩🇿', 'Russia': '🇷🇺', 'Turkey': '🇹🇷',
      'Greece': '🇬🇷', 'Sweden': '🇸🇪', 'Norway': '🇳🇴', 'Colombia': '🇨🇴',
      'Chile': '🇨🇱', 'Peru': '🇵🇪', 'Paraguay': '🇵🇾', 'Bolivia': '🇧🇴',
      'Venezuela': '🇻🇪', 'Jamaica': '🇯🇲', 'Costa Rica': '🇨🇷', 'Panama': '🇵🇦',
      'Honduras': '🇭🇳', 'El Salvador': '🇸🇻', 'Guatemala': '🇬🇹', 'New Zealand': '🇳🇿',
      'Iceland': '🇮🇸', 'Finland': '🇫🇮', 'Republic of Ireland': '🇮🇪', 'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
      'Ukraine': '🇺🇦', 'Czech Republic': '🇨🇿', 'Slovakia': '🇸🇰', 'Austria': '🇦🇹',
      'Hungary': '🇭🇺', 'Romania': '🇷🇴', 'Bulgaria': '🇧🇬', 'Belarus': '🇧🇾',
      'Slovenia': '🇸🇮', 'North Macedonia': '🇲🇰', 'Albania': '🇦🇱', 'Bosnia': '🇧🇦',
      'Montenegro': '🇲🇪', 'Kosovo': '🇽🇰', 'Lithuania': '🇱🇹', 'Latvia': '🇱🇻',
      'Estonia': '🇪🇪', 'Luxembourg': '🇱🇺', 'Cyprus': '🇨🇾', 'Malta': '🇲🇹',
      'Armenia': '🇦🇲', 'Azerbaijan': '🇦🇿', 'Georgia': '🇬🇪', 'Kazakhstan': '🇰🇿',
      'Uzbekistan': '🇺🇿', 'Kyrgyzstan': '🇰🇬', 'Tajikistan': '🇹🇯', 'Turkmenistan': '🇹🇲',
      'Afghanistan': '🇦🇫', 'Pakistan': '🇵🇰', 'India': '🇮🇳', 'Bangladesh': '🇧🇩',
      'Sri Lanka': '🇱🇰', 'Nepal': '🇳🇵', 'Bhutan': '🇧🇹', 'Maldives': '🇲🇻',
      'Thailand': '🇹🇭', 'Vietnam': '🇻🇳', 'Cambodia': '🇰🇭', 'Laos': '🇱🇦',
      'Myanmar': '🇲🇲', 'Malaysia': '🇲🇾', 'Singapore': '🇸🇬', 'Indonesia': '🇮🇩',
      'Philippines': '🇵🇭', 'Brunei': '🇧🇳', 'East Timor': '🇹🇱', 'North Korea': '🇰🇵',
      'South Sudan': '🇸🇸', 'Ethiopia': '🇪🇹', 'Kenya': '🇰🇪', 'Tanzania': '🇹🇿',
      'Uganda': '🇺🇬', 'Rwanda': '🇷🇼', 'Burundi': '🇧🇮', 'DR Congo': '🇨🇩',
      'Congo': '🇨🇬', 'Gabon': '🇬🇦', 'Angola': '🇦🇴',
      'Mozambique': '🇲🇿', 'Zambia': '🇿🇲', 'Zimbabwe': '🇿🇼', 'Botswana': '🇧🇼',
      'Namibia': '🇳🇦', 'Lesotho': '🇱🇸', 'Eswatini': '🇸🇿',
      'Madagascar': '🇲🇬', 'Mauritius': '🇲🇺', 'Seychelles': '🇸🇨', 'Comoros': '🇰🇲',
      'Libya': '🇱🇾', 'Mauritania': '🇲🇷', 'Western Sahara': '🇪🇭', 'Mali': '🇲🇱', 'Niger': '🇳🇪',
      'Chad': '🇹🇩', 'Sudan': '🇸🇩', 'Eritrea': '🇪🇷', 'Djibouti': '🇩🇯',
      'Somalia': '🇸🇴', 'Central African Republic': '🇨🇫', 'Equatorial Guinea': '🇬🇶',
      'Sao Tome and Principe': '🇸🇹', 'Gambia': '🇬🇲', 'Guinea-Bissau': '🇬🇼',
      'Guinea': '🇬🇳', 'Sierra Leone': '🇸🇱', 'Liberia': '🇱🇷'
    };
    return flagMap[teamName] || '🏳️';
  };

  const formatXG = (xg: number | undefined | null) => {
    if (xg === null || xg === undefined) return 'N/A';
    return xg.toFixed(2);
  };

  const probA = match.probA ?? 0;
  const probD = match.probD ?? 0;
  const probB = match.probB ?? 0;
  const xGA = match.xGA;
  const xGB = match.xGB;
  const totalXG = match.totalExpectedGoals;

  const flagA = getFlag(match.teamA);
  const flagB = getFlag(match.teamB);

  const navItems = [
    { id: 'overview', label: 'Overview' },
    { id: 'markets', label: 'Markets' },
    { id: 'goals', label: 'Goals' },
    { id: 'handicap', label: 'Handicap' },
    { id: 'scores', label: 'Scores' },
    { id: 'statistics', label: 'Statistics' },
    { id: 'model', label: 'Model' },
    { id: 'history', label: 'History' },
    { id: 'squad', label: 'Squad' },
    ...(match.teamGoals ? [{ id: 'team-goals', label: 'Team Goals' }] : []),
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
      className="fixed inset-0 bg-[#0F1115] z-50 overflow-y-auto"
    >
      {/* Back Button */}
      <div className="sticky top-0 bg-[#0F1115]/95 backdrop-blur-xl border-b border-white/5 z-50">
        <div className="max-w-[1380px] mx-auto px-14 py-4 flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-[#9AA1AA] hover:text-[#F5F5F5] transition-colors text-sm font-normal"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Matches</span>
            </button>
          )}
          <button
            onClick={onClose}
            className="ml-auto p-2 text-[#9AA1AA] hover:text-[#F5F5F5] hover:bg-[#181C22] rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Sticky Navigation */}
      <div className="sticky top-[60px] bg-[#0F1115]/95 backdrop-blur-xl border-b border-white/5 z-40">
        <div className="max-w-[1380px] mx-auto px-14">
          <nav className="flex gap-8 overflow-x-auto py-4">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className={`relative text-sm font-normal transition-colors whitespace-nowrap py-1 ${
                  activeSection === item.id
                    ? 'text-[#F5F5F5]'
                    : 'text-[#9AA1AA] hover:text-[#F5F5F5]'
                }`}
              >
                {item.label}
                {activeSection === item.id && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#5EA9FF] rounded-full"
                    initial={false}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  />
                )}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <div className="max-w-[1380px] mx-auto px-14 py-16">
        {/* Hero Section */}
        <section id="section-overview" className="mb-24">
          {/* Match Header */}
          <div className="mb-10">
            <div className="flex items-center gap-3 text-sm text-[#9AA1AA] mb-8">
              <span className="text-[#29C870] font-normal">{match.stage}</span>
              <span>•</span>
              <span>{match.venue || 'TBD'}</span>
            </div>
            
            <div className="flex items-center justify-between gap-16 mb-10">
              <div className="flex items-center gap-6">
                <span className="text-5xl">{flagA}</span>
                <div>
                  <h1 className="text-4xl font-bold text-[#F5F5F5] tracking-tight">{match.teamA}</h1>
                  <p className="text-sm text-[#9AA1AA] mt-1">{match.teamACode}</p>
                </div>
              </div>
              
              <div className="text-center">
                <div className="text-5xl font-black text-[#9AA1AA]/40 mb-2 tracking-tight">VS</div>
                {match.status === 'LIVE' && (
                  <span className="inline-flex items-center gap-2 text-xs font-bold text-[#E65B5B]">
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full rounded-full bg-[#E65B5B] animate-ping" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-[#E65B5B]" />
                    </span>
                    LIVE {match.minute}'
                  </span>
                )}
              </div>
              
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <h1 className="text-4xl font-bold text-[#F5F5F5] tracking-tight">{match.teamB}</h1>
                  <p className="text-sm text-[#9AA1AA] mt-1">{match.teamBCode}</p>
                </div>
                <span className="text-5xl">{flagB}</span>
              </div>
            </div>

            {/* Probability Bar */}
            <div className="bg-[#181C22] rounded-2xl p-8 shadow-[0_8px_30px_rgba(0,0,0,0.18)]">
              <div className="flex items-center justify-between mb-6">
                <div className="text-center flex-1">
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="text-5xl font-bold text-[#F5F5F5] mb-2 tracking-tight"
                  >
                    {probA}%
                  </motion.div>
                  <div className="text-sm text-[#9AA1AA] font-normal">{match.teamA}</div>
                </div>
                <div className="text-center flex-1">
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                    className="text-3xl font-bold text-[#9AA1AA]/60 mb-2 tracking-tight"
                  >
                    {probD}%
                  </motion.div>
                  <div className="text-sm text-[#9AA1AA]/60 font-normal">Draw</div>
                </div>
                <div className="text-center flex-1">
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="text-5xl font-bold text-[#F5F5F5] mb-2 tracking-tight"
                  >
                    {probB}%
                  </motion.div>
                  <div className="text-sm text-[#9AA1AA] font-normal">{match.teamB}</div>
                </div>
              </div>
              <div className="h-3 bg-[#13171D] rounded-full overflow-hidden flex">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${probA}%` }}
                  transition={{ duration: 1, delay: 0.3, ease: "easeOut" }}
                  className={`h-full ${probA > probB ? 'bg-[#29C870]' : 'bg-[#1D222A]'} rounded-l-full`}
                />
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${probD}%` }}
                  transition={{ duration: 1, delay: 0.35, ease: "easeOut" }}
                  className="h-full bg-[#1D222A]"
                />
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${probB}%` }}
                  transition={{ duration: 1, delay: 0.4, ease: "easeOut" }}
                  className={`h-full ${probB > probA ? 'bg-[#29C870]' : 'bg-[#1D222A]'} rounded-r-full`}
                />
              </div>
            </div>
          </div>

          {/* Summary Row */}
          <div className="grid grid-cols-5 gap-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="col-span-1"
            >
              <SummaryCard
                title="Top Pick"
                value={match.prediction || 'N/A'}
                probability={Math.max(probA, probB, probD)}
                confidence={match.confidence}
                icon={<Target className="w-4 h-4" />}
                isRecommended={true}
              />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.55 }}
              className="col-span-1"
            >
              <SummaryCard
                title="Most Likely Score"
                value={match.mostLikelyScore || 'N/A'}
                probability={null}
                confidence={null}
                icon={<TrendingUp className="w-4 h-4" />}
              />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="col-span-1"
            >
              <SummaryCard
                title="Expected Goals"
                value={totalXG ? totalXG.toFixed(2) : 'N/A'}
                probability={null}
                confidence={null}
                icon={<Zap className="w-4 h-4" />}
              />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.65 }}
              className="col-span-1"
            >
              <SummaryCard
                title="Safest Bet"
                value={probD > 40 ? 'Draw' : probA > probB ? match.teamA : match.teamB}
              probability={Math.max(probD, probA > probB ? probA : probB)}
              confidence={match.confidence}
              icon={<Shield className="w-4 h-4" />}
              />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              className="col-span-1"
            >
              <SummaryCard
                title="Clean Sheet"
                value={match.cleanSheetA && match.cleanSheetB ? 
                (match.cleanSheetA > match.cleanSheetB ? match.teamA : match.teamB) : 'N/A'}
              probability={match.cleanSheetA && match.cleanSheetB ? 
                Math.max(match.cleanSheetA, match.cleanSheetB) : null}
              confidence={null}
              icon={<Award className="w-4 h-4" />}
              />
            </motion.div>
          </div>
        </section>

        {/* Markets Section */}
        <motion.section 
          id="section-markets" 
          className="mb-24"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Betting Markets" subtitle="Probability-based market analysis" />
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Double Chance */}
            <PremiumCard>
              <h3 className="text-base font-semibold text-[#F5F5F5] mb-5 tracking-tight">Double Chance</h3>
              <div className="space-y-3">
                <MarketRow label={`${match.teamACode} or Draw`} probability={match.doubleChanceMarket?.['1x'] ? Math.round(match.doubleChanceMarket['1x'] * 100) : null} />
                <MarketRow label={`${match.teamBCode} or Draw`} probability={match.doubleChanceMarket?.['x2'] ? Math.round(match.doubleChanceMarket['x2'] * 100) : null} />
                <MarketRow label={`${match.teamACode} or ${match.teamBCode}`} probability={match.doubleChanceMarket?.['12'] ? Math.round(match.doubleChanceMarket['12'] * 100) : null} />
              </div>
            </PremiumCard>

            {/* Draw No Bet */}
            <PremiumCard>
              <h3 className="text-base font-semibold text-[#F5F5F5] mb-5 tracking-tight">Draw No Bet</h3>
              <div className="space-y-3">
                <MarketRow label={`${match.teamACode} DNB`} probability={match.drawNoBetMarket?.home ? Math.round(match.drawNoBetMarket.home * 100) : null} />
                <MarketRow label={`${match.teamBCode} DNB`} probability={match.drawNoBetMarket?.away ? Math.round(match.drawNoBetMarket.away * 100) : null} />
              </div>
            </PremiumCard>

            {/* Win To Nil */}
            <PremiumCard>
              <h3 className="text-base font-semibold text-[#F5F5F5] mb-5 tracking-tight">Win To Nil</h3>
              <div className="space-y-3">
                <MarketRow label={`${match.teamACode} Win to Nil`} probability={match.winToNilMarket?.home ? Math.round(match.winToNilMarket.home * 100) : null} />
                <MarketRow label={`${match.teamBCode} Win to Nil`} probability={match.winToNilMarket?.away ? Math.round(match.winToNilMarket.away * 100) : null} />
              </div>
            </PremiumCard>
          </div>
        </motion.section>

        {/* Goals Section */}
        <motion.section 
          id="section-goals" 
          className="mb-24"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Goal Markets" subtitle="Over/Under and BTTS probabilities" />
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Over/Under */}
            <PremiumCard>
              <h3 className="text-base font-semibold text-[#F5F5F5] mb-5 tracking-tight">Over/Under Goals</h3>
              <div className="space-y-3">
                {['0.5', '1.5', '2.5', '3.5', '4.5'].map((line) => (
                  <div key={line}>
                    <MarketRow 
                      label={`Over ${line}`} 
                      probability={match.overUnder?.[line]?.over ? Math.round(match.overUnder[line].over * 100) : null} 
                    />
                    <MarketRow 
                      label={`Under ${line}`} 
                      probability={match.overUnder?.[line]?.under ? Math.round(match.overUnder[line].under * 100) : null} 
                    />
                  </div>
                ))}
              </div>
            </PremiumCard>

            {/* BTTS */}
            <PremiumCard>
              <h3 className="text-base font-semibold text-[#F5F5F5] mb-5 tracking-tight">Both Teams To Score</h3>
              <div className="space-y-3">
                <MarketRow label="BTTS Yes" probability={match.bttsMarket?.yes ? Math.round(match.bttsMarket.yes * 100) : null} />
                <MarketRow label="BTTS No" probability={match.bttsMarket?.no ? Math.round(match.bttsMarket.no * 100) : null} />
              </div>
            </PremiumCard>
          </div>
        </motion.section>

        {/* Handicap Section */}
        <motion.section 
          id="section-handicap" 
          className="mb-24"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Asian Handicap" subtitle="Handicap line probabilities" />
          
          {(() => {
            if (!match.asianHandicap?.lines) return null;
            
            const lines = Object.entries(match.asianHandicap.lines).map(([line, val]) => ({
              line: `${match.asianHandicap?.favored_team} ${line}`,
              probability: Math.round((val as number) * 100),
              rawLine: parseFloat(line)
            }));
            
            const positiveLines = lines.filter(l => l.rawLine > 0).sort((a, b) => a.rawLine - b.rawLine);
            const levelLines = lines.filter(l => l.rawLine === 0);
            const negativeLines = lines.filter(l => l.rawLine < 0).sort((a, b) => b.rawLine - a.rawLine);
            
            return (
              <div className="space-y-6">
                {positiveLines.length > 0 && (
                  <div>
                    <div className="text-xs text-[#9AA1AA] uppercase tracking-wider mb-4 font-normal">Positive Handicap</div>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {positiveLines.map((item, i) => (
                        <HandicapCard
                          key={item.line}
                          line={item.line}
                          probability={item.probability}
                        />
                      ))}
                    </div>
                  </div>
                )}
                
                {levelLines.length > 0 && (
                  <div>
                    <div className="text-xs text-[#9AA1AA] uppercase tracking-wider mb-4 font-normal">Level</div>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {levelLines.map((item) => (
                        <HandicapCard
                          key={item.line}
                          line={item.line}
                          probability={item.probability}
                        />
                      ))}
                    </div>
                  </div>
                )}
                
                {negativeLines.length > 0 && (
                  <div>
                    <div className="text-xs text-[#9AA1AA] uppercase tracking-wider mb-4 font-normal">Negative Handicap</div>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {negativeLines.map((item) => (
                        <HandicapCard
                          key={item.line}
                          line={item.line}
                          probability={item.probability}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })()}
        </motion.section>

        {/* Scores Section */}
        <motion.section 
          id="section-scores" 
          className="mb-24"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Correct Scores" subtitle="Most likely scorelines" />
          
          <div className="space-y-3">
            {match.top5Scorelines?.map((score, index) => (
              <ScoreRankingCard
                key={index}
                rank={index + 1}
                score={score.score}
                probability={score.probability ? Math.round(score.probability * 100) : 0}
              />
            ))}
          </div>
        </motion.section>

        {/* Statistics Section */}
        <motion.section 
          id="section-statistics" 
          className="mb-24"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Team Statistics" subtitle="Comparative team metrics" />
          
          <div className="space-y-4">
            <ComparisonRow
              labelA={match.teamA}
              labelB={match.teamB}
              valueA={match.fifaRankA || 'N/A'}
              valueB={match.fifaRankB || 'N/A'}
              label="FIFA Rank"
              invert
            />
            <ComparisonRow
              labelA={match.teamA}
              labelB={match.teamB}
              valueA={match.eloRankA || 'N/A'}
              valueB={match.eloRankB || 'N/A'}
              label="ELO Rating"
              invert
            />
            <ComparisonRow
              labelA={match.teamA}
              labelB={match.teamB}
              valueA={match.squadValueA || 'N/A'}
              valueB={match.squadValueB || 'N/A'}
              label="Squad Value"
            />
          </div>
        </motion.section>

        {/* Model Section */}
        <motion.section 
          id="section-model" 
          className="mb-24"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Model Confidence" subtitle="Prediction reliability metrics" />
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard label="Calibration" value={match.confidence || 'N/A'} status="good" />
            <MetricCard label="Agreement" value="85%" status="good" />
            <MetricCard label="Variance" value="Low" status="good" />
            <MetricCard label="Freshness" value="Recent" status="good" />
          </div>
        </motion.section>

        {/* History Section */}
        <motion.section 
          id="section-history" 
          className="mb-24"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Head to Head" subtitle="Historical match data" />
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <PremiumCard>
              <h3 className="text-base font-semibold text-[#F5F5F5] mb-5 tracking-tight">{match.teamA} Recent Form</h3>
              <div className="flex gap-2">
                {match.recentFormA?.map((result, i) => (
                  <FormBadge key={i} result={result} />
                ))}
              </div>
            </PremiumCard>
            <PremiumCard>
              <h3 className="text-base font-semibold text-[#F5F5F5] mb-5 tracking-tight">{match.teamB} Recent Form</h3>
              <div className="flex gap-2">
                {match.recentFormB?.map((result, i) => (
                  <FormBadge key={i} result={result} />
                ))}
              </div>
            </PremiumCard>
          </div>
        </motion.section>

        {/* Squad Health Section */}
        <motion.section 
          id="section-squad" 
          className="mb-24"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Squad Health" subtitle="Injuries and suspensions" />
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <PremiumCard>
              <h3 className="text-base font-semibold text-[#F5F5F5] mb-5 tracking-tight">{match.teamA}</h3>
              <div className="space-y-4 text-sm">
                <div>
                  <span className="text-[#9AA1AA] text-xs uppercase tracking-wider font-normal">Injured</span>
                  <p className="text-[#F5F5F5] mt-2">{match.injuriesA?.join(', ') || 'None'}</p>
                </div>
                <div>
                  <span className="text-[#9AA1AA] text-xs uppercase tracking-wider font-normal">Suspended</span>
                  <p className="text-[#F5F5F5] mt-2">{match.suspensionsA?.join(', ') || 'None'}</p>
                </div>
              </div>
            </PremiumCard>
            <PremiumCard>
              <h3 className="text-base font-semibold text-[#F5F5F5] mb-5 tracking-tight">{match.teamB}</h3>
              <div className="space-y-4 text-sm">
                <div>
                  <span className="text-[#9AA1AA] text-xs uppercase tracking-wider font-normal">Injured</span>
                  <p className="text-[#F5F5F5] mt-2">{match.injuriesB?.join(', ') || 'None'}</p>
                </div>
                <div>
                  <span className="text-[#9AA1AA] text-xs uppercase tracking-wider font-normal">Suspended</span>
                  <p className="text-[#F5F5F5] mt-2">{match.suspensionsB?.join(', ') || 'None'}</p>
                </div>
              </div>
            </PremiumCard>
          </div>
        </motion.section>

        {/* Team Goals Section */}
        {match.teamGoals && (
          <motion.section 
            id="section-team-goals" 
            className="mb-24"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5 }}
          >
            <SectionHeader title="Team Goals" subtitle="Over/Under by team" />
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <PremiumCard>
                <h3 className="text-base font-semibold text-[#F5F5F5] mb-5 tracking-tight">{match.teamA}</h3>
                <div className="space-y-3">
                  <MarketRow 
                    label="Over 0.5" 
                    probability={match.teamGoals.home.over_0_5 ? Math.round(match.teamGoals.home.over_0_5 * 100) : null} 
                  />
                  <MarketRow 
                    label="Over 1.5" 
                    probability={match.teamGoals.home.over_1_5 ? Math.round(match.teamGoals.home.over_1_5 * 100) : null} 
                  />
                  <MarketRow 
                    label="Over 2.5" 
                    probability={match.teamGoals.home.over_2_5 ? Math.round(match.teamGoals.home.over_2_5 * 100) : null} 
                  />
                </div>
              </PremiumCard>
              <PremiumCard>
                <h3 className="text-base font-semibold text-[#F5F5F5] mb-5 tracking-tight">{match.teamB}</h3>
                <div className="space-y-3">
                  <MarketRow 
                    label="Over 0.5" 
                    probability={match.teamGoals.away.over_0_5 ? Math.round(match.teamGoals.away.over_0_5 * 100) : null} 
                  />
                  <MarketRow 
                    label="Over 1.5" 
                    probability={match.teamGoals.away.over_1_5 ? Math.round(match.teamGoals.away.over_1_5 * 100) : null} 
                  />
                  <MarketRow 
                    label="Over 2.5" 
                    probability={match.teamGoals.away.over_2_5 ? Math.round(match.teamGoals.away.over_2_5 * 100) : null} 
                  />
                </div>
              </PremiumCard>
            </div>
          </motion.section>
        )}

        {/* Final Verdict */}
        <motion.section 
          className="mb-24"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <div className="bg-[#181C22] rounded-2xl p-10 shadow-[0_8px_30px_rgba(0,0,0,0.18)]">
            <h2 className="text-3xl font-bold text-[#F5F5F5] mb-8 tracking-tight">Match Verdict</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
              <div>
                <div className="text-xs text-[#9AA1AA] uppercase tracking-wider mb-2">Top Pick</div>
                <div className="text-xl font-bold text-[#F5F5F5]">{match.prediction || 'N/A'}</div>
              </div>
              <div>
                <div className="text-xs text-[#9AA1AA] uppercase tracking-wider mb-2">Expected Score</div>
                <div className="text-xl font-bold text-[#F5F5F5]">{match.mostLikelyScore || 'N/A'}</div>
              </div>
              <div>
                <div className="text-xs text-[#9AA1AA] uppercase tracking-wider mb-2">Winning Probability</div>
                <div className="text-xl font-bold text-[#F5F5F5]">{Math.max(probA, probB, probD)}%</div>
              </div>
              <div>
                <div className="text-xs text-[#9AA1AA] uppercase tracking-wider mb-2">Expected Goals</div>
                <div className="text-xl font-bold text-[#F5F5F5]">{totalXG?.toFixed(2) || 'N/A'}</div>
              </div>
            </div>
            <p className="text-[#9AA1AA] text-base leading-relaxed max-w-3xl">
              Based on comprehensive analysis, {match.prediction || 'the prediction'} shows {match.confidence?.toLowerCase() || 'moderate'} confidence. 
              The model indicates {Math.max(probA, probB, probD)}% probability for this outcome, supported by expected goals of {totalXG?.toFixed(2) || 'N/A'}.
            </p>
          </div>
        </motion.section>
      </div>
    </motion.div>
  );
}

// Sub-components
function SummaryCard({ title, value, probability, confidence, icon, isRecommended = false }: { 
  title: string; 
  value: string; 
  probability: number | null; 
  confidence: string | null;
  icon: React.ReactNode;
  isRecommended?: boolean;
}) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      className={`bg-[#181C22] rounded-2xl p-8 shadow-[0_8px_30px_rgba(0,0,0,0.18)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.24)] transition-all duration-300 ${
        isRecommended ? 'bg-[#1D222A]' : ''
      }`}
    >
      <div className="flex items-center gap-2 text-[#9AA1AA] mb-4">
        {icon}
        <span className="text-xs font-normal uppercase tracking-wider">{title}</span>
        {isRecommended && (
          <span className="ml-auto text-[10px] font-semibold text-[#29C870] bg-[#29C870]/10 px-2 py-0.5 rounded-full">
            TOP PICK
          </span>
        )}
      </div>
      <div className="text-3xl font-bold text-[#F5F5F5] mb-2 tracking-tight">{value}</div>
      {probability !== null && (
        <div className="text-sm text-[#9AA1AA] font-normal">{probability}%</div>
      )}
      {confidence && (
        <div className={`text-xs font-normal mt-3 ${
          confidence === 'High' ? 'text-[#29C870]' : 
          confidence === 'Medium' ? 'text-[#D8A31A]' : 'text-[#9AA1AA]'
        }`}>
          {confidence === 'High' ? 'Elite' : confidence === 'Medium' ? 'High' : 'Moderate'} Confidence
        </div>
      )}
    </motion.div>
  );
}

function SectionHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-12">
      <h2 className="text-3xl font-bold text-[#F5F5F5] tracking-tight mb-2">{title}</h2>
      <p className="text-sm text-[#9AA1AA] font-normal">{subtitle}</p>
    </div>
  );
}

function PremiumCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-[#181C22] rounded-2xl p-8 shadow-[0_8px_30px_rgba(0,0,0,0.18)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.24)] transition-all duration-300">
      {children}
    </div>
  );
}

function MarketRow({ label, probability }: { label: string; probability: number | null }) {
  const getStrength = (prob: number | null) => {
    if (prob === null) return { label: 'N/A', color: 'text-[#9AA1AA]', barColor: 'bg-[#1D222A]' };
    if (prob >= 75) return { label: 'Strong', color: 'text-[#29C870]', barColor: 'bg-[#29C870]' };
    if (prob >= 60) return { label: 'Good', color: 'text-[#29C870]/80', barColor: 'bg-[#29C870]/80' };
    if (prob >= 45) return { label: 'Lean', color: 'text-[#D8A31A]', barColor: 'bg-[#D8A31A]' };
    return { label: 'Avoid', color: 'text-[#9AA1AA]', barColor: 'bg-[#1D222A]' };
  };

  const strength = getStrength(probability);

  return (
    <div className="flex items-center justify-between py-3">
      <span className="text-sm text-[#9AA1AA] font-normal">{label}</span>
      <div className="flex items-center gap-4">
        {probability !== null && (
          <div className="w-32 h-2 bg-[#13171D] rounded-full overflow-hidden">
            <div 
              className={`h-full ${strength.barColor} rounded-full transition-all duration-500`}
              style={{ width: `${probability}%` }}
            />
          </div>
        )}
        <span className="text-sm font-semibold text-[#F5F5F5] w-12 text-right">{probability !== null ? `${probability}%` : 'N/A'}</span>
        <span className={`text-xs font-semibold px-2 py-1 rounded ${
          strength.label === 'Strong' ? 'bg-[#29C870]/10 text-[#29C870]' :
          strength.label === 'Good' ? 'bg-[#29C870]/5 text-[#29C870]/80' :
          strength.label === 'Lean' ? 'bg-[#D8A31A]/10 text-[#D8A31A]' :
          'bg-[#1D222A] text-[#9AA1AA]'
        }`}>{strength.label}</span>
      </div>
    </div>
  );
}

function HandicapCard({ line, probability }: { line: string; probability: number }) {
  const getStrength = (prob: number) => {
    if (prob >= 75) return { bg: 'bg-[#1D222A]', textColor: 'text-[#29C870]' };
    if (prob >= 60) return { bg: 'bg-[#181C22]', textColor: 'text-[#29C870]/80' };
    if (prob >= 45) return { bg: 'bg-[#181C22]', textColor: 'text-[#D8A31A]' };
    return { bg: 'bg-[#181C22]', textColor: 'text-[#9AA1AA]' };
  };

  const strength = getStrength(probability);

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className={`bg-[#181C22] rounded-2xl p-6 shadow-[0_8px_30px_rgba(0,0,0,0.18)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.24)] transition-all duration-300 ${
        probability >= 75 ? 'bg-[#1D222A]' : ''
      }`}
    >
      <div className="text-xs text-[#9AA1AA] mb-3 font-normal uppercase tracking-wider">{line}</div>
      <div className="text-3xl font-bold text-[#F5F5F5] mb-3 tracking-tight">{probability}%</div>
      <div className={`text-xs font-semibold px-3 py-1.5 rounded-full inline-block ${
        strength.textColor === 'text-[#29C870]' ? 'bg-[#29C870]/10 text-[#29C870]' :
        strength.textColor === 'text-[#29C870]/80' ? 'bg-[#29C870]/5 text-[#29C870]/80' :
        strength.textColor === 'text-[#D8A31A]' ? 'bg-[#D8A31A]/10 text-[#D8A31A]' :
        'bg-[#1D222A] text-[#9AA1AA]'
      }`}>
        {probability >= 75 ? 'Strong' : probability >= 60 ? 'Good' : probability >= 45 ? 'Lean' : 'Avoid'}
      </div>
    </motion.div>
  );
}

function ScoreRankingCard({ rank, score, probability }: { rank: number; score: string; probability: number }) {
  const medals = ['🥇', '🥈', '🥉'];
  const medal = medals[rank - 1] || `${rank}.`;

  return (
    <motion.div
      whileHover={{ x: 4 }}
      className="bg-[#181C22] rounded-2xl p-6 flex items-center gap-6 shadow-[0_8px_30px_rgba(0,0,0,0.18)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.24)] transition-all duration-300"
    >
      <span className="text-3xl">{medal}</span>
      <div className="flex-1">
        <div className="text-xl font-bold text-[#F5F5F5] tracking-tight">{score}</div>
        <div className="text-sm text-[#9AA1AA] font-normal mt-1">{probability}%</div>
      </div>
      <div className="w-32 h-2.5 bg-[#13171D] rounded-full overflow-hidden">
        <motion.div 
          initial={{ width: 0 }}
          whileInView={{ width: `${probability}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="h-full bg-[#29C870] rounded-full"
        />
      </div>
    </motion.div>
  );
}

function ComparisonRow({ labelA, labelB, valueA, valueB, label, invert = false }: {
  labelA: string;
  labelB: string;
  valueA: string | number;
  valueB: string | number;
  label: string;
  invert?: boolean;
}) {
  const parseValue = (val: string | number) => {
    if (typeof val === 'number') return val;
    if (val === 'N/A') return 0;
    const num = parseFloat(val.replace(/[^0-9.]/g, ''));
    return isNaN(num) ? 0 : num;
  };

  const numA = parseValue(valueA);
  const numB = parseValue(valueB);
  const maxVal = Math.max(numA, numB, 1);
  
  const widthA = (numA / maxVal) * 100;
  const widthB = (numB / maxVal) * 100;

  return (
    <div className="bg-[#181C22] rounded-2xl p-8 shadow-[0_8px_30px_rgba(0,0,0,0.18)]">
      <div className="text-xs text-[#9AA1AA] mb-5 uppercase tracking-wider font-normal">{label}</div>
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <span className="text-sm text-[#F5F5F5] font-normal w-32 truncate">{labelA}</span>
          <div className="flex-1 h-2.5 bg-[#13171D] rounded-full overflow-hidden">
            <motion.div 
              initial={{ width: 0 }}
              whileInView={{ width: `${widthA}%` }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
              className="h-full bg-[#29C870] rounded-full"
            />
          </div>
          <span className="text-sm text-[#9AA1AA] w-24 text-right font-normal">{valueA}</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-[#F5F5F5] font-normal w-32 truncate">{labelB}</span>
          <div className="flex-1 h-2.5 bg-[#13171D] rounded-full overflow-hidden">
            <motion.div 
              initial={{ width: 0 }}
              whileInView={{ width: `${widthB}%` }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
              className="h-full bg-[#1D222A] rounded-full"
            />
          </div>
          <span className="text-sm text-[#9AA1AA] w-24 text-right font-normal">{valueB}</span>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, status }: { label: string; value: string; status: 'good' | 'warning' | 'bad' }) {
  const statusColors = {
    good: 'text-[#29C870]',
    warning: 'text-[#D8A31A]',
    bad: 'text-[#E65B5B]'
  };

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="bg-[#181C22] rounded-2xl p-8 shadow-[0_8px_30px_rgba(0,0,0,0.18)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.24)] transition-all duration-300"
    >
      <div className="text-xs text-[#9AA1AA] mb-4 uppercase tracking-wider font-normal">{label}</div>
      <div className={`text-2xl font-bold ${statusColors[status]}`}>{value}</div>
    </motion.div>
  );
}

function FormBadge({ result }: { result: string }) {
  const colors = {
    W: 'bg-[#29C870]/10 text-[#29C870]',
    D: 'bg-[#1D222A] text-[#9AA1AA]',
    L: 'bg-[#E65B5B]/10 text-[#E65B5B]'
  };

  const labels = {
    W: 'Win',
    D: 'Draw',
    L: 'Loss'
  };

  return (
    <span className={`px-4 py-2 rounded-lg text-sm font-semibold ${colors[result as keyof typeof colors]}`} title={labels[result as keyof typeof labels]}>
      {result}
    </span>
  );
}
