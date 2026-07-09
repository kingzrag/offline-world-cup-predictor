import React from 'react';
import { motion } from 'framer-motion';
import {
  Calendar,
  Clock,
  TrendUp,
  TrendDown,
  Minus,
  ChartLine,
  Target,
  Shield,
  Warning,
  Star,
  Flag
} from '@phosphor-icons/react';

interface Team {
  name: string;
  flag?: string;
  elo?: number;
  form?: ('W' | 'D' | 'L')[];
}

interface MatchCardProps {
  homeTeam: Team;
  awayTeam: Team;
  kickoffTime: string;
  prediction?: {
    winner: 'home' | 'away' | 'draw';
    confidence: number;
    homeWinProb: number;
    drawProb: number;
    awayWinProb: number;
  };
  expectedGoals?: {
    home: number;
    away: number;
    total: number;
  };
  topMarkets?: string[];
  injuries?: {
    home: string[];
    away: string[];
  };
  compact?: boolean;
  onClick?: () => void;
}

const MatchCard: React.FC<MatchCardProps> = ({
  homeTeam,
  awayTeam,
  kickoffTime,
  prediction,
  expectedGoals,
  topMarkets,
  injuries,
  compact = false,
  onClick
}) => {
  const getFormIcon = (result: 'W' | 'D' | 'L') => {
    switch (result) {
      case 'W': return <TrendUp weight="fill" className="w-3 h-3 text-green-400" />;
      case 'D': return <Minus weight="fill" className="w-3 h-3 text-yellow-400" />;
      case 'L': return <TrendDown weight="fill" className="w-3 h-3 text-red-400" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-400';
    if (confidence >= 60) return 'text-blue-400';
    if (confidence >= 40) return 'text-yellow-400';
    return 'text-red-400';
  };

  const formatKickoffTime = (time: string) => {
    try {
      const date = new Date(time);
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      });
    } catch {
      return time;
    }
  };

  const formatDate = (time: string) => {
    try {
      const date = new Date(time);
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    } catch {
      return '';
    }
  };

  if (compact) {
    return (
      <motion.div
        whileHover={{ scale: 1.02, y: -2 }}
        whileTap={{ scale: 0.98 }}
        onClick={onClick}
        className="bg-zinc-800/50 border border-zinc-700/50 rounded-xl p-4 cursor-pointer hover:border-zinc-600/50 transition-all"
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Calendar weight="bold" className="w-4 h-4 text-zinc-400" />
            <span className="text-xs text-zinc-400">{formatDate(kickoffTime)}</span>
            <Clock weight="bold" className="w-4 h-4 text-zinc-400 ml-2" />
            <span className="text-xs text-zinc-400">{formatKickoffTime(kickoffTime)}</span>
          </div>
          {prediction && (
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(prediction.confidence)}`}>
              {prediction.confidence}%
            </div>
          )}
        </div>

        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              {homeTeam.flag && <span className="text-lg">{homeTeam.flag}</span>}
              <span className="text-sm font-semibold text-zinc-100">{homeTeam.name}</span>
            </div>
            {homeTeam.form && (
              <div className="flex gap-1">
                {homeTeam.form.map((result, idx) => (
                  <span key={idx} className="p-1 bg-zinc-700/50 rounded">{getFormIcon(result)}</span>
                ))}
              </div>
            )}
          </div>

          <div className="px-3 text-center">
            <span className="text-lg font-bold text-zinc-500">vs</span>
          </div>

          <div className="flex-1 text-right">
            <div className="flex items-center justify-end gap-2 mb-1">
              <span className="text-sm font-semibold text-zinc-100">{awayTeam.name}</span>
              {awayTeam.flag && <span className="text-lg">{awayTeam.flag}</span>}
            </div>
            {awayTeam.form && (
              <div className="flex gap-1 justify-end">
                {awayTeam.form.map((result, idx) => (
                  <span key={idx} className="p-1 bg-zinc-700/50 rounded">{getFormIcon(result)}</span>
                ))}
              </div>
            )}
          </div>
        </div>

        {prediction && (
          <div className="mt-3 pt-3 border-t border-zinc-700/50">
            <div className="flex items-center justify-between text-xs">
              <span className="text-zinc-400">Prediction: </span>
              <span className={`font-semibold ${
                prediction.winner === 'home' ? 'text-blue-400' : 
                prediction.winner === 'away' ? 'text-purple-400' : 'text-yellow-400'
              }`}>
                {prediction.winner === 'home' ? homeTeam.name : 
                 prediction.winner === 'away' ? awayTeam.name : 'Draw'}
              </span>
            </div>
          </div>
        )}
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      whileHover={{ scale: 1.01, y: -2 }}
      whileTap={{ scale: 0.99 }}
      onClick={onClick}
      className="bg-gradient-to-br from-zinc-800/80 to-zinc-900/80 border border-zinc-700/50 rounded-2xl p-5 cursor-pointer hover:border-zinc-600/50 transition-all shadow-xl"
    >
      {/* Header with time and confidence */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-zinc-700/50 rounded-lg">
            <Calendar weight="bold" className="w-4 h-4 text-zinc-400" />
          </div>
          <div>
            <p className="text-xs text-zinc-400">{formatDate(kickoffTime)}</p>
            <p className="text-sm font-semibold text-zinc-100">{formatKickoffTime(kickoffTime)}</p>
          </div>
        </div>
        {prediction && (
          <div className="flex items-center gap-2">
            <Star weight="fill" className="w-4 h-4 text-yellow-400" />
            <div className={`px-3 py-1 rounded-full text-sm font-bold ${getConfidenceColor(prediction.confidence)}`}>
              {prediction.confidence}%
            </div>
          </div>
        )}
      </div>

      {/* Teams */}
      <div className="flex items-center justify-between mb-4">
        {/* Home Team */}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {homeTeam.flag && <span className="text-2xl">{homeTeam.flag}</span>}
            <div>
              <h3 className="text-base font-bold text-zinc-100">{homeTeam.name}</h3>
              {homeTeam.elo && (
                <p className="text-xs text-zinc-400">ELO: {homeTeam.elo}</p>
              )}
            </div>
          </div>
          {homeTeam.form && (
            <div className="flex gap-1">
              {homeTeam.form.map((result, idx) => (
                <span key={idx} className="p-1.5 bg-zinc-700/50 rounded-lg">{getFormIcon(result)}</span>
              ))}
            </div>
          )}
        </div>

        {/* VS */}
        <div className="px-4">
          <span className="text-xl font-bold text-zinc-600">VS</span>
        </div>

        {/* Away Team */}
        <div className="flex-1 text-right">
          <div className="flex items-center justify-end gap-2 mb-2">
            <div>
              <h3 className="text-base font-bold text-zinc-100">{awayTeam.name}</h3>
              {awayTeam.elo && (
                <p className="text-xs text-zinc-400">ELO: {awayTeam.elo}</p>
              )}
            </div>
            {awayTeam.flag && <span className="text-2xl">{awayTeam.flag}</span>}
          </div>
          {awayTeam.form && (
            <div className="flex gap-1 justify-end">
              {awayTeam.form.map((result, idx) => (
                <span key={idx} className="p-1.5 bg-zinc-700/50 rounded-lg">{getFormIcon(result)}</span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Prediction Bar */}
      {prediction && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <ChartLine weight="fill" className="w-4 h-4 text-blue-400" />
            <span className="text-xs text-zinc-400 uppercase tracking-wider">Win Probability</span>
          </div>
          <div className="h-2 bg-zinc-700/50 rounded-full overflow-hidden flex">
            <div 
              className="bg-blue-500 transition-all duration-500"
              style={{ width: `${prediction.homeWinProb}%` }}
            />
            <div 
              className="bg-yellow-500 transition-all duration-500"
              style={{ width: `${prediction.drawProb}%` }}
            />
            <div 
              className="bg-purple-500 transition-all duration-500"
              style={{ width: `${prediction.awayWinProb}%` }}
            />
          </div>
          <div className="flex justify-between mt-1 text-xs">
            <span className="text-blue-400">{prediction.homeWinProb}%</span>
            <span className="text-yellow-400">{prediction.drawProb}%</span>
            <span className="text-purple-400">{prediction.awayWinProb}%</span>
          </div>
        </div>
      )}

      {/* Expected Goals */}
      {expectedGoals && (
        <div className="mb-4 bg-zinc-700/30 border border-zinc-600/30 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <Target weight="fill" className="w-4 h-4 text-green-400" />
            <span className="text-xs text-zinc-400 uppercase tracking-wider">Expected Goals</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="text-center">
              <p className="text-lg font-bold text-white">{expectedGoals.home}</p>
              <p className="text-xs text-zinc-500">Home</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold text-zinc-400">{expectedGoals.total}</p>
              <p className="text-xs text-zinc-500">Total</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold text-white">{expectedGoals.away}</p>
              <p className="text-xs text-zinc-500">Away</p>
            </div>
          </div>
        </div>
      )}

      {/* Top Markets */}
      {topMarkets && topMarkets.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Shield weight="fill" className="w-4 h-4 text-orange-400" />
            <span className="text-xs text-zinc-400 uppercase tracking-wider">Top Markets</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {topMarkets.slice(0, 4).map((market, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="px-3 py-1.5 bg-zinc-700/50 hover:bg-zinc-700/70 border border-zinc-600/50 rounded-lg text-xs text-zinc-300 font-medium"
              >
                {market}
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Injuries */}
      {injuries && (injuries.home.length > 0 || injuries.away.length > 0) && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <Warning weight="fill" className="w-4 h-4 text-red-400" />
            <span className="text-xs text-zinc-400 uppercase tracking-wider">Injuries</span>
          </div>
          <div className="space-y-1">
            {injuries.home.length > 0 && (
              <div className="text-xs">
                <span className="text-zinc-500">{homeTeam.name}:</span>
                <span className="text-red-400 ml-1">{injuries.home.join(', ')}</span>
              </div>
            )}
            {injuries.away.length > 0 && (
              <div className="text-xs">
                <span className="text-zinc-500">{awayTeam.name}:</span>
                <span className="text-red-400 ml-1">{injuries.away.join(', ')}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default MatchCard;
