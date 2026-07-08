import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowLeft, Star, TrendingUp, Shield, Target, Zap, Award, Trophy, Goal, ChartColumn, Clock3, Users, History, Scale, BarChart3 } from 'lucide-react';
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
      className="fixed inset-0 bg-[#0E1117] z-50 overflow-y-auto"
    >
      {/* Back Button */}
      <div className="sticky top-0 bg-[#0E1117]/95 backdrop-blur-xl border-b border-white/5 z-50">
        <div className="max-w-[1380px] mx-auto px-10 py-3 flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-[#98A2B3] hover:text-[#F5F5F5] transition-colors text-sm font-normal"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Matches</span>
            </button>
          )}
          <button
            onClick={onClose}
            className="ml-auto p-2 text-[#98A2B3] hover:text-[#F5F5F5] hover:bg-[#181C22] rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Sticky Navigation */}
      <div className="sticky top-[60px] bg-[#0E1117]/95 backdrop-blur-xl border-b border-white/5 z-40">
        <div className="max-w-[1380px] mx-auto px-10">
          <nav className="flex gap-6 overflow-x-auto py-3">
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
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  />
                )}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <div className="max-w-[1380px] mx-auto px-10 py-6">
        {/* Hero Section - Ultra Compact */}
        <section id="section-overview" className="mb-8">
          <div className="bg-[#151A22] rounded-xl p-4 shadow-[0_4px_20px_rgba(0,0,0,0.15)]">
            {/* Match Header Row */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{flagA}</span>
                <div>
                  <h1 className="text-lg font-semibold text-[#F5F5F5] tracking-tight">{match.teamA}</h1>
                  <p className="text-[10px] text-[#98A2B3]">{match.teamACode}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="text-xl font-bold text-[#F5F5F5] tracking-tight"
                  >
                    {probA}%
                  </motion.div>
                </div>
                <div className="text-center">
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                    className="text-sm font-bold text-[#98A2B3]/40 tracking-tight"
                  >
                    {probD}%
                  </motion.div>
                </div>
                <div className="text-center">
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="text-xl font-bold text-[#F5F5F5] tracking-tight"
                  >
                    {probB}%
                  </motion.div>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <h1 className="text-lg font-semibold text-[#F5F5F5] tracking-tight">{match.teamB}</h1>
                  <p className="text-[10px] text-[#98A2B3]">{match.teamBCode}</p>
                </div>
                <span className="text-2xl">{flagB}</span>
              </div>
            </div>

            {/* Probability Bar */}
            <div className="h-1.5 bg-[#0E1117] rounded-full overflow-hidden flex mb-3">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${probA}%` }}
                transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
                className={`h-full ${probA > probB ? 'bg-[#34D399]' : 'bg-[#232B36]'} rounded-l-full`}
              />
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${probD}%` }}
                transition={{ duration: 0.8, delay: 0.35, ease: "easeOut" }}
                className="h-full bg-[#232B36]"
              />
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${probB}%` }}
                transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
                className={`h-full ${probB > probA ? 'bg-[#34D399]' : 'bg-[#232B36]'} rounded-r-full`}
              />
            </div>

            {/* Match Info Row */}
            <div className="flex items-center justify-between text-[10px] text-[#98A2B3]">
              <div className="flex items-center gap-2">
                {match.status === 'LIVE' && (
                  <span className="flex items-center gap-1 text-[#EF4444] font-semibold">
                    <span className="relative flex h-1 w-1">
                      <span className="absolute inline-flex h-full w-full rounded-full bg-[#EF4444] animate-ping" />
                      <span className="relative inline-flex rounded-full h-1 w-1 bg-[#EF4444]" />
                    </span>
                    LIVE {match.minute}'
                  </span>
                )}
                <span className="text-[#34D399]">{match.stage}</span>
                <span>•</span>
                <span>{match.venue || 'TBD'}</span>
              </div>
              <div className="flex items-center gap-1">
                <span>⭐</span>
                <span className="text-[#F5F5F5] font-semibold">Top Pick:</span>
                <span className="text-[#4F8CFF]">{match.prediction || 'N/A'}</span>
              </div>
            </div>
          </div>
        </section>

        {/* Key Insights - Horizontal Pills */}
        <section className="mb-6">
          <div className="flex gap-3 overflow-x-auto pb-2">
            <div className="flex-shrink-0 bg-[#1C222C] rounded-lg px-4 py-2 shadow-[0_4px_18px_rgba(0,0,0,0.16)] flex items-center gap-2 hover:bg-[#232B36] transition-colors duration-250">
              <Goal className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
              <span className="text-[10px] text-[#98A2B3]">xG</span>
              <span className="text-xs font-semibold text-[#F5F5F5]">{totalXG?.toFixed(2) || 'N/A'}</span>
            </div>
            <div className="flex-shrink-0 bg-[#1C222C] rounded-lg px-4 py-2 shadow-[0_4px_18px_rgba(0,0,0,0.16)] flex items-center gap-2 hover:bg-[#232B36] transition-colors duration-250">
              <Target className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
              <span className="text-[10px] text-[#98A2B3]">BTTS</span>
              <span className="text-xs font-semibold text-[#F5F5F5]">{match.bttsMarket?.yes ? Math.round(match.bttsMarket.yes * 100) : 'N/A'}%</span>
            </div>
            <div className="flex-shrink-0 bg-[#1C222C] rounded-lg px-4 py-2 shadow-[0_4px_18px_rgba(0,0,0,0.16)] flex items-center gap-2 hover:bg-[#232B36] transition-colors duration-250">
              <Trophy className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
              <span className="text-[10px] text-[#98A2B3]">{probB > probA ? match.teamB : match.teamA}</span>
              <span className="text-xs font-semibold text-[#34D399]">Favoured</span>
            </div>
            <div className="flex-shrink-0 bg-[#1C222C] rounded-lg px-4 py-2 shadow-[0_4px_18px_rgba(0,0,0,0.16)] flex items-center gap-2 hover:bg-[#232B36] transition-colors duration-250">
              <TrendingUp className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
              <span className="text-[10px] text-[#98A2B3]">Over 2.5</span>
              <span className="text-xs font-semibold text-[#F5F5F5]">{match.overUnder?.['2.5']?.over ? Math.round(match.overUnder['2.5'].over * 100) : 'N/A'}%</span>
            </div>
            <div className="flex-shrink-0 bg-[#1C222C] rounded-lg px-4 py-2 shadow-[0_4px_18px_rgba(0,0,0,0.16)] flex items-center gap-2 hover:bg-[#232B36] transition-colors duration-250">
              <Scale className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
              <span className="text-[10px] text-[#98A2B3]">Value</span>
              <span className="text-xs font-semibold text-[#4F8CFF]">Strong</span>
            </div>
          </div>
        </section>

        {/* Featured Prediction + Summary Cards */}
        <section className="mb-8">
          <div className="grid grid-cols-4 gap-4">
            {/* Large Featured Card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="col-span-2"
              whileHover={{ y: -2 }}
            >
              <div className="bg-[#222933] rounded-xl p-6 shadow-[0_4px_18px_rgba(0,0,0,0.16)] h-full border-t-2 border-[#F5B301] hover:shadow-[0_6px_24px_rgba(0,0,0,0.2)] transition-shadow duration-250">
                <div className="flex items-center gap-2 mb-5">
                  <Trophy className="w-4 h-4 text-[#F5B301]" />
                  <span className="text-xs font-semibold text-[#98A2B3] uppercase tracking-wider">Model Pick</span>
                </div>
                <div className="text-3xl font-bold text-[#F5F5F5] mb-3 tracking-tight">{match.prediction || 'N/A'}</div>
                <div className="text-2xl font-semibold text-[#98A2B3] mb-4 tracking-tight">{Math.max(probA, probB, probD)}%</div>
                <div className="flex items-center gap-2 mb-6">
                  <span className="relative flex h-1.5 w-1.5">
                    <span className="absolute inline-flex h-full w-full rounded-full bg-[#34D399]" />
                  </span>
                  <span className="text-xs text-[#98A2B3] font-normal">
                    {match.confidence === 'High' ? 'Elite Confidence' : match.confidence === 'Medium' ? 'High Confidence' : 'Moderate Confidence'}
                  </span>
                </div>
                <div className="mt-auto pt-4 border-t border-[#2A323E] flex items-center gap-2">
                  <Trophy className="w-3 h-3 text-[#F5B301]" />
                  <span className="text-[10px] text-[#98A2B3] font-normal">Updated just now</span>
                </div>
              </div>
            </motion.div>

            {/* Smaller Cards */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 }}
              className="col-span-1"
            >
              <div className="bg-[#1C222C] rounded-lg p-4 shadow-[0_4px_18px_rgba(0,0,0,0.16)] h-full hover:bg-[#232B36] transition-colors duration-250">
                <div className="flex items-center gap-2 mb-2">
                  <Goal className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
                  <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider">xG</span>
                </div>
                <div className="text-xl font-semibold text-[#F5F5F5]">{totalXG?.toFixed(2) || 'N/A'}</div>
              </div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="col-span-1"
            >
              <div className="bg-[#1C222C] rounded-lg p-4 shadow-[0_4px_18px_rgba(0,0,0,0.16)] h-full hover:bg-[#232B36] transition-colors duration-250">
                <div className="flex items-center gap-2 mb-2">
                  <ChartColumn className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
                  <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider">Prediction</span>
                </div>
                <div className="text-xl font-semibold text-[#F5F5F5]">{match.mostLikelyScore || 'N/A'}</div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Markets Section */}
        <motion.section 
          id="section-markets" 
          className="mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Betting Markets" subtitle="Probability-based market analysis" />
          
          <div className="bg-[#171C24] rounded-xl shadow-[0_4px_18px_rgba(0,0,0,0.16)] overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#1C222C] border-b border-[#232B36]">
                  <th className="text-left text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">Market</th>
                  <th className="text-center text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">Probability</th>
                  <th className="text-center text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">Strength</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-[#1C222C] hover:bg-[#1C222C]/50 transition-colors duration-250">
                  <td className="px-4 py-2.5 text-[#F5F5F5] font-normal">{match.teamACode} or Draw</td>
                  <td className="px-4 py-2.5 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-[#F5F5F5] text-sm">{match.doubleChanceMarket?.['1x'] ? Math.round(match.doubleChanceMarket['1x'] * 100) : 'N/A'}%</span>
                      <div className="w-16 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-[#34D399] rounded-full"
                          style={{ width: `${match.doubleChanceMarket?.['1x'] ? Math.round(match.doubleChanceMarket['1x'] * 100) : 0}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      (match.doubleChanceMarket?.['1x'] || 0) >= 75 ? 'bg-[#34D399]/10 text-[#34D399]' :
                      (match.doubleChanceMarket?.['1x'] || 0) >= 60 ? 'bg-[#34D399]/5 text-[#34D399]/80' :
                      (match.doubleChanceMarket?.['1x'] || 0) >= 45 ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                      'bg-[#232B36] text-[#98A2B3]'
                    }`}>
                      {(match.doubleChanceMarket?.['1x'] || 0) >= 75 ? 'Strong' : (match.doubleChanceMarket?.['1x'] || 0) >= 60 ? 'Good' : (match.doubleChanceMarket?.['1x'] || 0) >= 45 ? 'Lean' : 'Avoid'}
                    </span>
                  </td>
                </tr>
                <tr className="border-b border-[#1C222C] hover:bg-[#1C222C]/50 transition-colors duration-250">
                  <td className="px-4 py-2.5 text-[#F5F5F5] font-normal">{match.teamBCode} or Draw</td>
                  <td className="px-4 py-2.5 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-[#F5F5F5] text-sm">{match.doubleChanceMarket?.['x2'] ? Math.round(match.doubleChanceMarket['x2'] * 100) : 'N/A'}%</span>
                      <div className="w-16 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-[#34D399] rounded-full"
                          style={{ width: `${match.doubleChanceMarket?.['x2'] ? Math.round(match.doubleChanceMarket['x2'] * 100) : 0}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      (match.doubleChanceMarket?.['x2'] || 0) >= 75 ? 'bg-[#34D399]/10 text-[#34D399]' :
                      (match.doubleChanceMarket?.['x2'] || 0) >= 60 ? 'bg-[#34D399]/5 text-[#34D399]/80' :
                      (match.doubleChanceMarket?.['x2'] || 0) >= 45 ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                      'bg-[#232B36] text-[#98A2B3]'
                    }`}>
                      {(match.doubleChanceMarket?.['x2'] || 0) >= 75 ? 'Strong' : (match.doubleChanceMarket?.['x2'] || 0) >= 60 ? 'Good' : (match.doubleChanceMarket?.['x2'] || 0) >= 45 ? 'Lean' : 'Avoid'}
                    </span>
                  </td>
                </tr>
                <tr className="border-b border-[#1C222C] hover:bg-[#1C222C]/50 transition-colors duration-250">
                  <td className="px-4 py-2.5 text-[#F5F5F5] font-normal">{match.teamACode} or {match.teamBCode}</td>
                  <td className="px-4 py-2.5 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-[#F5F5F5] text-sm">{match.doubleChanceMarket?.['12'] ? Math.round(match.doubleChanceMarket['12'] * 100) : 'N/A'}%</span>
                      <div className="w-16 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-[#34D399] rounded-full"
                          style={{ width: `${match.doubleChanceMarket?.['12'] ? Math.round(match.doubleChanceMarket['12'] * 100) : 0}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      (match.doubleChanceMarket?.['12'] || 0) >= 75 ? 'bg-[#34D399]/10 text-[#34D399]' :
                      (match.doubleChanceMarket?.['12'] || 0) >= 60 ? 'bg-[#34D399]/5 text-[#34D399]/80' :
                      (match.doubleChanceMarket?.['12'] || 0) >= 45 ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                      'bg-[#232B36] text-[#98A2B3]'
                    }`}>
                      {(match.doubleChanceMarket?.['12'] || 0) >= 75 ? 'Strong' : (match.doubleChanceMarket?.['12'] || 0) >= 60 ? 'Good' : (match.doubleChanceMarket?.['12'] || 0) >= 45 ? 'Lean' : 'Avoid'}
                    </span>
                  </td>
                </tr>
                <tr className="border-b border-[#1C222C] hover:bg-[#1C222C]/50 transition-colors duration-250">
                  <td className="px-4 py-2.5 text-[#F5F5F5] font-normal">{match.teamACode} DNB</td>
                  <td className="px-4 py-2.5 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-[#F5F5F5] text-sm">{match.drawNoBetMarket?.home ? Math.round(match.drawNoBetMarket.home * 100) : 'N/A'}%</span>
                      <div className="w-16 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-[#34D399] rounded-full"
                          style={{ width: `${match.drawNoBetMarket?.home ? Math.round(match.drawNoBetMarket.home * 100) : 0}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      (match.drawNoBetMarket?.home || 0) >= 75 ? 'bg-[#34D399]/10 text-[#34D399]' :
                      (match.drawNoBetMarket?.home || 0) >= 60 ? 'bg-[#34D399]/5 text-[#34D399]/80' :
                      (match.drawNoBetMarket?.home || 0) >= 45 ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                      'bg-[#232B36] text-[#98A2B3]'
                    }`}>
                      {(match.drawNoBetMarket?.home || 0) >= 75 ? 'Strong' : (match.drawNoBetMarket?.home || 0) >= 60 ? 'Good' : (match.drawNoBetMarket?.home || 0) >= 45 ? 'Lean' : 'Avoid'}
                    </span>
                  </td>
                </tr>
                <tr className="border-b border-[#1C222C] hover:bg-[#1C222C]/50 transition-colors duration-250">
                  <td className="px-4 py-2.5 text-[#F5F5F5] font-normal">{match.teamBCode} DNB</td>
                  <td className="px-4 py-2.5 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-[#F5F5F5] text-sm">{match.drawNoBetMarket?.away ? Math.round(match.drawNoBetMarket.away * 100) : 'N/A'}%</span>
                      <div className="w-16 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-[#34D399] rounded-full"
                          style={{ width: `${match.drawNoBetMarket?.away ? Math.round(match.drawNoBetMarket.away * 100) : 0}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      (match.drawNoBetMarket?.away || 0) >= 75 ? 'bg-[#34D399]/10 text-[#34D399]' :
                      (match.drawNoBetMarket?.away || 0) >= 60 ? 'bg-[#34D399]/5 text-[#34D399]/80' :
                      (match.drawNoBetMarket?.away || 0) >= 45 ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                      'bg-[#232B36] text-[#98A2B3]'
                    }`}>
                      {(match.drawNoBetMarket?.away || 0) >= 75 ? 'Strong' : (match.drawNoBetMarket?.away || 0) >= 60 ? 'Good' : (match.drawNoBetMarket?.away || 0) >= 45 ? 'Lean' : 'Avoid'}
                    </span>
                  </td>
                </tr>
                <tr className="border-b border-[#1C222C] hover:bg-[#1C222C]/50 transition-colors duration-250">
                  <td className="px-4 py-2.5 text-[#F5F5F5] font-normal">{match.teamACode} Win to Nil</td>
                  <td className="px-4 py-2.5 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-[#F5F5F5] text-sm">{match.winToNilMarket?.home ? Math.round(match.winToNilMarket.home * 100) : 'N/A'}%</span>
                      <div className="w-16 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-[#34D399] rounded-full"
                          style={{ width: `${match.winToNilMarket?.home ? Math.round(match.winToNilMarket.home * 100) : 0}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      (match.winToNilMarket?.home || 0) >= 75 ? 'bg-[#34D399]/10 text-[#34D399]' :
                      (match.winToNilMarket?.home || 0) >= 60 ? 'bg-[#34D399]/5 text-[#34D399]/80' :
                      (match.winToNilMarket?.home || 0) >= 45 ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                      'bg-[#232B36] text-[#98A2B3]'
                    }`}>
                      {(match.winToNilMarket?.home || 0) >= 75 ? 'Strong' : (match.winToNilMarket?.home || 0) >= 60 ? 'Good' : (match.winToNilMarket?.home || 0) >= 45 ? 'Lean' : 'Avoid'}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-2.5 text-[#F5F5F5] font-normal">{match.teamBCode} Win to Nil</td>
                  <td className="px-4 py-2.5 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-[#F5F5F5] text-sm">{match.winToNilMarket?.away ? Math.round(match.winToNilMarket.away * 100) : 'N/A'}%</span>
                      <div className="w-16 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-[#34D399] rounded-full"
                          style={{ width: `${match.winToNilMarket?.away ? Math.round(match.winToNilMarket.away * 100) : 0}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      (match.winToNilMarket?.away || 0) >= 75 ? 'bg-[#34D399]/10 text-[#34D399]' :
                      (match.winToNilMarket?.away || 0) >= 60 ? 'bg-[#34D399]/5 text-[#34D399]/80' :
                      (match.winToNilMarket?.away || 0) >= 45 ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                      'bg-[#232B36] text-[#98A2B3]'
                    }`}>
                      {(match.winToNilMarket?.away || 0) >= 75 ? 'Strong' : (match.winToNilMarket?.away || 0) >= 60 ? 'Good' : (match.winToNilMarket?.away || 0) >= 45 ? 'Lean' : 'Avoid'}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </motion.section>

        {/* Goals Section */}
        <motion.section 
          id="section-goals" 
          className="mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Goal Markets" subtitle="Over/Under and BTTS probabilities" />
          
          <div className="bg-[#171C24] rounded-xl shadow-[0_4px_18px_rgba(0,0,0,0.16)] overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#1C222C] border-b border-[#232B36]">
                  <th className="text-left text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">Market</th>
                  <th className="text-center text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">Probability</th>
                  <th className="text-center text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">Strength</th>
                </tr>
              </thead>
              <tbody>
                {['0.5', '1.5', '2.5', '3.5', '4.5'].map((line) => (
                  <React.Fragment key={line}>
                    <tr className="border-b border-[#1C222C] hover:bg-[#1C222C]/50 transition-colors duration-250">
                      <td className="px-4 py-2.5 text-[#F5F5F5] font-normal">Over {line}</td>
                      <td className="px-4 py-2.5 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <span className="text-[#F5F5F5] text-sm">{match.overUnder?.[line]?.over ? Math.round(match.overUnder[line].over * 100) : 'N/A'}%</span>
                          <div className="w-16 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-[#34D399] rounded-full"
                              style={{ width: `${match.overUnder?.[line]?.over ? Math.round(match.overUnder[line].over * 100) : 0}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-2.5 text-center">
                        <span className={`text-xs font-semibold px-2 py-1 rounded ${
                          (match.overUnder?.[line]?.over || 0) >= 75 ? 'bg-[#34D399]/10 text-[#34D399]' :
                          (match.overUnder?.[line]?.over || 0) >= 60 ? 'bg-[#34D399]/5 text-[#34D399]/80' :
                          (match.overUnder?.[line]?.over || 0) >= 45 ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                          'bg-[#232B36] text-[#98A2B3]'
                        }`}>
                          {(match.overUnder?.[line]?.over || 0) >= 75 ? 'Strong' : (match.overUnder?.[line]?.over || 0) >= 60 ? 'Good' : (match.overUnder?.[line]?.over || 0) >= 45 ? 'Lean' : 'Avoid'}
                        </span>
                      </td>
                    </tr>
                    <tr className="border-b border-[#1C222C] hover:bg-[#1C222C]/50 transition-colors duration-250">
                      <td className="px-4 py-2.5 text-[#F5F5F5] font-normal">Under {line}</td>
                      <td className="px-4 py-2.5 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <span className="text-[#F5F5F5] text-sm">{match.overUnder?.[line]?.under ? Math.round(match.overUnder[line].under * 100) : 'N/A'}%</span>
                          <div className="w-16 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-[#34D399] rounded-full"
                              style={{ width: `${match.overUnder?.[line]?.under ? Math.round(match.overUnder[line].under * 100) : 0}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-2.5 text-center">
                        <span className={`text-xs font-semibold px-2 py-1 rounded ${
                          (match.overUnder?.[line]?.under || 0) >= 75 ? 'bg-[#34D399]/10 text-[#34D399]' :
                          (match.overUnder?.[line]?.under || 0) >= 60 ? 'bg-[#34D399]/5 text-[#34D399]/80' :
                          (match.overUnder?.[line]?.under || 0) >= 45 ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                          'bg-[#232B36] text-[#98A2B3]'
                        }`}>
                          {(match.overUnder?.[line]?.under || 0) >= 75 ? 'Strong' : (match.overUnder?.[line]?.under || 0) >= 60 ? 'Good' : (match.overUnder?.[line]?.under || 0) >= 45 ? 'Lean' : 'Avoid'}
                        </span>
                      </td>
                    </tr>
                  </React.Fragment>
                ))}
                <tr className="border-b border-[#1C222C] hover:bg-[#1C222C]/50 transition-colors duration-250">
                  <td className="px-4 py-2.5 text-[#F5F5F5] font-normal">BTTS Yes</td>
                  <td className="px-4 py-2.5 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-[#F5F5F5] text-sm">{match.bttsMarket?.yes ? Math.round(match.bttsMarket.yes * 100) : 'N/A'}%</span>
                      <div className="w-16 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-[#34D399] rounded-full"
                          style={{ width: `${match.bttsMarket?.yes ? Math.round(match.bttsMarket.yes * 100) : 0}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      (match.bttsMarket?.yes || 0) >= 75 ? 'bg-[#34D399]/10 text-[#34D399]' :
                      (match.bttsMarket?.yes || 0) >= 60 ? 'bg-[#34D399]/5 text-[#34D399]/80' :
                      (match.bttsMarket?.yes || 0) >= 45 ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                      'bg-[#232B36] text-[#98A2B3]'
                    }`}>
                      {(match.bttsMarket?.yes || 0) >= 75 ? 'Strong' : (match.bttsMarket?.yes || 0) >= 60 ? 'Good' : (match.bttsMarket?.yes || 0) >= 45 ? 'Lean' : 'Avoid'}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-2.5 text-[#F5F5F5] font-normal">BTTS No</td>
                  <td className="px-4 py-2.5 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-[#F5F5F5] text-sm">{match.bttsMarket?.no ? Math.round(match.bttsMarket.no * 100) : 'N/A'}%</span>
                      <div className="w-16 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-[#34D399] rounded-full"
                          style={{ width: `${match.bttsMarket?.no ? Math.round(match.bttsMarket.no * 100) : 0}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      (match.bttsMarket?.no || 0) >= 75 ? 'bg-[#34D399]/10 text-[#34D399]' :
                      (match.bttsMarket?.no || 0) >= 60 ? 'bg-[#34D399]/5 text-[#34D399]/80' :
                      (match.bttsMarket?.no || 0) >= 45 ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                      'bg-[#232B36] text-[#98A2B3]'
                    }`}>
                      {(match.bttsMarket?.no || 0) >= 75 ? 'Strong' : (match.bttsMarket?.no || 0) >= 60 ? 'Good' : (match.bttsMarket?.no || 0) >= 45 ? 'Lean' : 'Avoid'}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </motion.section>

        {/* Handicap Section */}
        <motion.section 
          id="section-handicap" 
          className="mb-12"
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
            
            const sortedLines = lines.sort((a, b) => b.rawLine - a.rawLine);
            
            return (
              <div className="bg-[#171C24] rounded-xl shadow-[0_4px_18px_rgba(0,0,0,0.16)] overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-[#1C222C] border-b border-[#232B36]">
                      <th className="text-left text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">Line</th>
                      <th className="text-center text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">Probability</th>
                      <th className="text-center text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">Strength</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedLines.map((item, index) => (
                      <tr key={item.line} className={index < sortedLines.length - 1 ? "border-b border-[#1C222C] hover:bg-[#1C222C]/50 transition-colors duration-250" : "hover:bg-[#1C222C]/50 transition-colors duration-250"}>
                        <td className="px-4 py-2.5 text-[#F5F5F5] font-normal">{item.line}</td>
                        <td className="px-4 py-2.5 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <span className="text-[#F5F5F5] text-sm">{item.probability}%</span>
                            <div className="w-16 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-[#34D399] rounded-full"
                                style={{ width: `${item.probability}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-2.5 text-center">
                          <span className={`text-xs font-semibold px-2 py-1 rounded ${
                            item.probability >= 75 ? 'bg-[#34D399]/10 text-[#34D399]' :
                            item.probability >= 60 ? 'bg-[#34D399]/5 text-[#34D399]/80' :
                            item.probability >= 45 ? 'bg-[#F5B301]/10 text-[#F5B301]' :
                            'bg-[#232B36] text-[#98A2B3]'
                          }`}>
                            {item.probability >= 75 ? 'Strong' : item.probability >= 60 ? 'Good' : item.probability >= 45 ? 'Lean' : 'Avoid'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          })()}
        </motion.section>

        {/* Scores Section */}
        <motion.section 
          id="section-scores" 
          className="mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Correct Scores" subtitle="Most likely scorelines" />
          
          <div className="bg-[#171C24] rounded-xl shadow-[0_4px_18px_rgba(0,0,0,0.16)] overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#1C222C] border-b border-[#232B36]">
                  <th className="text-left text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">Rank</th>
                  <th className="text-left text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">Score</th>
                  <th className="text-center text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">Probability</th>
                </tr>
              </thead>
              <tbody>
                {match.top5Scorelines?.map((score, index) => (
                  <tr key={index} className={index < (match.top5Scorelines?.length || 0) - 1 ? "border-b border-[#1C222C] hover:bg-[#1C222C]/50 transition-colors duration-250" : "hover:bg-[#1C222C]/50 transition-colors duration-250"}>
                    <td className="px-4 py-2.5 text-[#F5F5F5] font-normal">{index === 0 ? <Trophy className="w-4 h-4 text-[#F5B301]" /> : index === 1 ? <Trophy className="w-4 h-4 text-[#98A2B3]" /> : index === 2 ? <Trophy className="w-4 h-4 text-[#6B7280]" /> : `${index + 1}.`}</td>
                    <td className="px-4 py-2.5 text-[#F5F5F5] font-semibold">{score.score}</td>
                    <td className="px-4 py-2.5 text-center">
                      <div className="flex items-center justify-center gap-3">
                        <span className="text-[#F5F5F5]">{score.probability ? Math.round(score.probability * 100) : 0}%</span>
                        <div className="w-20 h-1.5 bg-[#0E1117] rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-[#34D399] rounded-full"
                            style={{ width: `${score.probability ? Math.round(score.probability * 100) : 0}%` }}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.section>

        {/* Statistics Section */}
        <motion.section 
          id="section-statistics" 
          className="mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Team Statistics" subtitle="Comparative team metrics" />
          
          <div className="bg-[#171C24] rounded-xl shadow-[0_4px_18px_rgba(0,0,0,0.16)] overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#1C222C] border-b border-[#232B36]">
                  <th className="text-left text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">Metric</th>
                  <th className="text-center text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">{match.teamA}</th>
                  <th className="text-center text-[10px] text-[#98A2B3] uppercase tracking-wider font-normal px-4 py-3">{match.teamB}</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-[#1C222C] hover:bg-[#1C222C]/50 transition-colors duration-250">
                  <td className="px-4 py-2.5 text-[#98A2B3] font-normal">FIFA Rank</td>
                  <td className="px-4 py-2.5 text-center text-[#F5F5F5]">{match.fifaRankA || 'N/A'}</td>
                  <td className="px-4 py-2.5 text-center text-[#F5F5F5]">{match.fifaRankB || 'N/A'}</td>
                </tr>
                <tr className="border-b border-[#1C222C] hover:bg-[#1C222C]/50 transition-colors duration-250">
                  <td className="px-4 py-2.5 text-[#98A2B3] font-normal">ELO Rating</td>
                  <td className="px-4 py-2.5 text-center text-[#F5F5F5]">{match.eloRankA || 'N/A'}</td>
                  <td className="px-4 py-2.5 text-center text-[#F5F5F5]">{match.eloRankB || 'N/A'}</td>
                </tr>
                <tr className="hover:bg-[#1C222C]/50 transition-colors duration-250">
                  <td className="px-4 py-2.5 text-[#98A2B3] font-normal">Squad Value</td>
                  <td className="px-4 py-2.5 text-center text-[#F5F5F5]">{match.squadValueA || 'N/A'}</td>
                  <td className="px-4 py-2.5 text-center text-[#F5F5F5]">{match.squadValueB || 'N/A'}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </motion.section>

        {/* Model Section */}
        <motion.section 
          id="section-model" 
          className="mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Model Confidence" subtitle="Prediction reliability metrics" />
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[#1C222C] rounded-lg p-4 shadow-[0_4px_18px_rgba(0,0,0,0.16)] hover:bg-[#232B36] transition-colors duration-250">
              <div className="flex items-center gap-2 mb-2">
                <Scale className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
                <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider">Calibration</span>
              </div>
              <div className="text-xl font-semibold text-[#F5F5F5]">{match.confidence || 'N/A'}</div>
            </div>
            <div className="bg-[#1C222C] rounded-lg p-4 shadow-[0_4px_18px_rgba(0,0,0,0.16)] hover:bg-[#232B36] transition-colors duration-250">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
                <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider">Agreement</span>
              </div>
              <div className="text-xl font-semibold text-[#F5F5F5]">85%</div>
            </div>
            <div className="bg-[#1C222C] rounded-lg p-4 shadow-[0_4px_18px_rgba(0,0,0,0.16)] hover:bg-[#232B36] transition-colors duration-250">
              <div className="flex items-center gap-2 mb-2">
                <ChartColumn className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
                <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider">Variance</span>
              </div>
              <div className="text-xl font-semibold text-[#F5F5F5]">Low</div>
            </div>
            <div className="bg-[#1C222C] rounded-lg p-4 shadow-[0_4px_18px_rgba(0,0,0,0.16)] hover:bg-[#232B36] transition-colors duration-250">
              <div className="flex items-center gap-2 mb-2">
                <Clock3 className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
                <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider">Freshness</span>
              </div>
              <div className="text-xl font-semibold text-[#F5F5F5]">Recent</div>
            </div>
          </div>
        </motion.section>

        {/* History Section */}
        <motion.section 
          id="section-history" 
          className="mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Head to Head" subtitle="Historical match data" />
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[#1C222C] rounded-lg p-4 shadow-[0_4px_18px_rgba(0,0,0,0.16)] hover:bg-[#232B36] transition-colors duration-250">
              <div className="flex items-center gap-2 mb-3">
                <History className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
                <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider">{match.teamA} Form</span>
              </div>
              <div className="flex gap-2">
                {match.recentFormA?.map((result, i) => (
                  <FormBadge key={i} result={result} />
                ))}
              </div>
            </div>
            <div className="bg-[#1C222C] rounded-lg p-4 shadow-[0_4px_18px_rgba(0,0,0,0.16)] hover:bg-[#232B36] transition-colors duration-250">
              <div className="flex items-center gap-2 mb-3">
                <History className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
                <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider">{match.teamB} Form</span>
              </div>
              <div className="flex gap-2">
                {match.recentFormB?.map((result, i) => (
                  <FormBadge key={i} result={result} />
                ))}
              </div>
            </div>
          </div>
        </motion.section>

        {/* Squad Health Section */}
        <motion.section 
          id="section-squad" 
          className="mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <SectionHeader title="Squad Health" subtitle="Injuries and suspensions" />
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[#1C222C] rounded-lg p-4 shadow-[0_4px_18px_rgba(0,0,0,0.16)] hover:bg-[#232B36] transition-colors duration-250">
              <div className="flex items-center gap-2 mb-3">
                <Users className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
                <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider">{match.teamA}</span>
              </div>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-[#98A2B3] text-[10px] uppercase tracking-wider font-normal">Injured</span>
                  <p className="text-[#F5F5F5] mt-1">{match.injuriesA?.join(', ') || 'None'}</p>
                </div>
                <div>
                  <span className="text-[#98A2B3] text-[10px] uppercase tracking-wider font-normal">Suspended</span>
                  <p className="text-[#F5F5F5] mt-1">{match.suspensionsA?.join(', ') || 'None'}</p>
                </div>
              </div>
            </div>
            <div className="bg-[#1C222C] rounded-lg p-4 shadow-[0_4px_18px_rgba(0,0,0,0.16)] hover:bg-[#232B36] transition-colors duration-250">
              <div className="flex items-center gap-2 mb-3">
                <Users className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
                <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider">{match.teamB}</span>
              </div>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-[#98A2B3] text-[10px] uppercase tracking-wider font-normal">Injured</span>
                  <p className="text-[#F5F5F5] mt-1">{match.injuriesB?.join(', ') || 'None'}</p>
                </div>
                <div>
                  <span className="text-[#98A2B3] text-[10px] uppercase tracking-wider font-normal">Suspended</span>
                  <p className="text-[#F5F5F5] mt-1">{match.suspensionsB?.join(', ') || 'None'}</p>
                </div>
              </div>
            </div>
          </div>
        </motion.section>

        {/* Team Goals Section */}
        {match.teamGoals && (
          <motion.section 
            id="section-team-goals" 
            className="mb-12"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5 }}
          >
            <SectionHeader title="Team Goals" subtitle="Over/Under by team" />
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#1C222C] rounded-lg p-4 shadow-[0_4px_18px_rgba(0,0,0,0.16)] hover:bg-[#232B36] transition-colors duration-250">
                <div className="flex items-center gap-2 mb-3">
                  <Goal className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
                  <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider">{match.teamA}</span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-[#F5F5F5]">Over 0.5</span>
                    <span className="text-xs text-[#F5F5F5]">{match.teamGoals.home.over_0_5 ? Math.round(match.teamGoals.home.over_0_5 * 100) : 'N/A'}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-[#F5F5F5]">Over 1.5</span>
                    <span className="text-xs text-[#F5F5F5]">{match.teamGoals.home.over_1_5 ? Math.round(match.teamGoals.home.over_1_5 * 100) : 'N/A'}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-[#F5F5F5]">Over 2.5</span>
                    <span className="text-xs text-[#F5F5F5]">{match.teamGoals.home.over_2_5 ? Math.round(match.teamGoals.home.over_2_5 * 100) : 'N/A'}%</span>
                  </div>
                </div>
              </div>
              <div className="bg-[#1C222C] rounded-lg p-4 shadow-[0_4px_18px_rgba(0,0,0,0.16)] hover:bg-[#232B36] transition-colors duration-250">
                <div className="flex items-center gap-2 mb-3">
                  <Goal className="w-[18px] h-[18px] text-[#98A2B3]" strokeWidth={1.8} />
                  <span className="text-[10px] text-[#98A2B3] uppercase tracking-wider">{match.teamB}</span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-[#F5F5F5]">Over 0.5</span>
                    <span className="text-xs text-[#F5F5F5]">{match.teamGoals.away.over_0_5 ? Math.round(match.teamGoals.away.over_0_5 * 100) : 'N/A'}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-[#F5F5F5]">Over 1.5</span>
                    <span className="text-xs text-[#F5F5F5]">{match.teamGoals.away.over_1_5 ? Math.round(match.teamGoals.away.over_1_5 * 100) : 'N/A'}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-[#F5F5F5]">Over 2.5</span>
                    <span className="text-xs text-[#F5F5F5]">{match.teamGoals.away.over_2_5 ? Math.round(match.teamGoals.away.over_2_5 * 100) : 'N/A'}%</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.section>
        )}

        {/* Final Verdict */}
        <motion.section 
          className="mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <div className="bg-[#171C24] rounded-xl p-6 shadow-[0_4px_18px_rgba(0,0,0,0.16)]">
            <div className="flex items-center gap-2 mb-6">
              <Trophy className="w-5 h-5 text-[#F5B301]" />
              <h2 className="text-xl font-bold text-[#F5F5F5] tracking-tight">Match Verdict</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div>
                <div className="text-[10px] text-[#98A2B3] uppercase tracking-wider mb-2">Top Pick</div>
                <div className="text-lg font-semibold text-[#F5F5F5]">{match.prediction || 'N/A'}</div>
              </div>
              <div>
                <div className="text-[10px] text-[#98A2B3] uppercase tracking-wider mb-2">Prediction</div>
                <div className="text-lg font-semibold text-[#F5F5F5]">{match.mostLikelyScore || 'N/A'}</div>
              </div>
              <div>
                <div className="text-[10px] text-[#98A2B3] uppercase tracking-wider mb-2">Probability</div>
                <div className="text-lg font-semibold text-[#F5F5F5]">{Math.max(probA, probB, probD)}%</div>
              </div>
              <div>
                <div className="text-[10px] text-[#98A2B3] uppercase tracking-wider mb-2">xG</div>
                <div className="text-lg font-semibold text-[#F5F5F5]">{totalXG?.toFixed(2) || 'N/A'}</div>
              </div>
            </div>
            <p className="text-[#98A2B3] text-sm leading-relaxed max-w-3xl">
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
      <div className="flex items-center gap-2 text-[#98A2B3] mb-4">
        {icon}
        <span className="text-xs font-normal uppercase tracking-wider">{title}</span>
        {isRecommended && (
          <span className="ml-auto text-[10px] font-semibold text-[#34D399] bg-[#34D399]/10 px-2 py-0.5 rounded-full">
            TOP PICK
          </span>
        )}
      </div>
      <div className="text-3xl font-bold text-[#F5F5F5] mb-2 tracking-tight">{value}</div>
      {probability !== null && (
        <div className="text-sm text-[#98A2B3] font-normal">{probability}%</div>
      )}
      {confidence && (
        <div className={`text-xs font-normal mt-3 ${
          confidence === 'High' ? 'text-[#34D399]' : 
          confidence === 'Medium' ? 'text-[#D8A31A]' : 'text-[#98A2B3]'
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
      <p className="text-sm text-[#98A2B3] font-normal">{subtitle}</p>
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
    if (prob === null) return { label: 'N/A', color: 'text-[#98A2B3]', barColor: 'bg-[#1D222A]' };
    if (prob >= 75) return { label: 'Strong', color: 'text-[#34D399]', barColor: 'bg-[#34D399]' };
    if (prob >= 60) return { label: 'Good', color: 'text-[#34D399]/80', barColor: 'bg-[#34D399]/80' };
    if (prob >= 45) return { label: 'Lean', color: 'text-[#D8A31A]', barColor: 'bg-[#D8A31A]' };
    return { label: 'Avoid', color: 'text-[#98A2B3]', barColor: 'bg-[#1D222A]' };
  };

  const strength = getStrength(probability);

  return (
    <div className="flex items-center justify-between py-3">
      <span className="text-sm text-[#98A2B3] font-normal">{label}</span>
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
          strength.label === 'Strong' ? 'bg-[#34D399]/10 text-[#34D399]' :
          strength.label === 'Good' ? 'bg-[#34D399]/5 text-[#34D399]/80' :
          strength.label === 'Lean' ? 'bg-[#D8A31A]/10 text-[#D8A31A]' :
          'bg-[#1D222A] text-[#98A2B3]'
        }`}>{strength.label}</span>
      </div>
    </div>
  );
}

function HandicapCard({ line, probability }: { line: string; probability: number }) {
  const getStrength = (prob: number) => {
    if (prob >= 75) return { bg: 'bg-[#1D222A]', textColor: 'text-[#34D399]' };
    if (prob >= 60) return { bg: 'bg-[#181C22]', textColor: 'text-[#34D399]/80' };
    if (prob >= 45) return { bg: 'bg-[#181C22]', textColor: 'text-[#D8A31A]' };
    return { bg: 'bg-[#181C22]', textColor: 'text-[#98A2B3]' };
  };

  const strength = getStrength(probability);

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className={`bg-[#181C22] rounded-2xl p-6 shadow-[0_8px_30px_rgba(0,0,0,0.18)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.24)] transition-all duration-300 ${
        probability >= 75 ? 'bg-[#1D222A]' : ''
      }`}
    >
      <div className="text-xs text-[#98A2B3] mb-3 font-normal uppercase tracking-wider">{line}</div>
      <div className="text-3xl font-bold text-[#F5F5F5] mb-3 tracking-tight">{probability}%</div>
      <div className={`text-xs font-semibold px-3 py-1.5 rounded-full inline-block ${
        strength.textColor === 'text-[#34D399]' ? 'bg-[#34D399]/10 text-[#34D399]' :
        strength.textColor === 'text-[#34D399]/80' ? 'bg-[#34D399]/5 text-[#34D399]/80' :
        strength.textColor === 'text-[#D8A31A]' ? 'bg-[#D8A31A]/10 text-[#D8A31A]' :
        'bg-[#1D222A] text-[#98A2B3]'
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
        <div className="text-sm text-[#98A2B3] font-normal mt-1">{probability}%</div>
      </div>
      <div className="w-32 h-2.5 bg-[#13171D] rounded-full overflow-hidden">
        <motion.div 
          initial={{ width: 0 }}
          whileInView={{ width: `${probability}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="h-full bg-[#34D399] rounded-full"
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
      <div className="text-xs text-[#98A2B3] mb-5 uppercase tracking-wider font-normal">{label}</div>
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <span className="text-sm text-[#F5F5F5] font-normal w-32 truncate">{labelA}</span>
          <div className="flex-1 h-2.5 bg-[#13171D] rounded-full overflow-hidden">
            <motion.div 
              initial={{ width: 0 }}
              whileInView={{ width: `${widthA}%` }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
              className="h-full bg-[#34D399] rounded-full"
            />
          </div>
          <span className="text-sm text-[#98A2B3] w-24 text-right font-normal">{valueA}</span>
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
          <span className="text-sm text-[#98A2B3] w-24 text-right font-normal">{valueB}</span>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, status }: { label: string; value: string; status: 'good' | 'warning' | 'bad' }) {
  const statusColors = {
    good: 'text-[#34D399]',
    warning: 'text-[#D8A31A]',
    bad: 'text-[#EF4444]'
  };

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="bg-[#181C22] rounded-2xl p-8 shadow-[0_8px_30px_rgba(0,0,0,0.18)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.24)] transition-all duration-300"
    >
      <div className="text-xs text-[#98A2B3] mb-4 uppercase tracking-wider font-normal">{label}</div>
      <div className={`text-2xl font-bold ${statusColors[status]}`}>{value}</div>
    </motion.div>
  );
}

function FormBadge({ result }: { result: string }) {
  const colors = {
    W: 'bg-[#34D399]/10 text-[#34D399]',
    D: 'bg-[#1D222A] text-[#98A2B3]',
    L: 'bg-[#EF4444]/10 text-[#EF4444]'
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
