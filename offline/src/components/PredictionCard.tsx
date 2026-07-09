import React from 'react';
import { motion } from 'framer-motion';
import {
  Trophy,
  TrendUp,
  Shield,
  Target,
  ChartLine,
  Lightning,
  CheckCircle,
  XCircle
} from '@phosphor-icons/react';

interface PredictionCardProps {
  prediction: {
    match: string;
    prediction: string;
    probability: number;
    confidence: number;
    risk: 'Low' | 'Medium' | 'High';
    expectedGoals: {
      home: number;
      away: number;
      total: number;
    };
    recommendedMarkets: string[];
    modelEdge: number;
    expectedValue?: number;
  };
}

const PredictionCard: React.FC<PredictionCardProps> = ({ prediction }) => {
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'Low': return 'text-green-400 bg-green-500/10 border-green-500/30';
      case 'Medium': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
      case 'High': return 'text-red-400 bg-red-500/10 border-red-500/30';
      default: return 'text-zinc-400 bg-zinc-500/10 border-zinc-500/30';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-400';
    if (confidence >= 60) return 'text-blue-400';
    if (confidence >= 40) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="bg-gradient-to-br from-zinc-800/80 to-zinc-900/80 border border-zinc-700/50 rounded-2xl p-5 shadow-xl mb-4"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl border border-blue-400/20">
            <Trophy weight="fill" className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-zinc-100">Prediction</h3>
            <p className="text-xs text-zinc-400">{prediction.match}</p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-medium border ${getRiskColor(prediction.risk)}`}>
          {prediction.risk} Risk
        </div>
      </div>

      {/* Main Prediction */}
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-xl p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-zinc-400 uppercase tracking-wider">Prediction</span>
          <TrendUp weight="fill" className="w-4 h-4 text-blue-400" />
        </div>
        <p className="text-lg font-bold text-white mb-2">{prediction.prediction}</p>
        <div className="flex items-center gap-4">
          <div>
            <span className="text-xs text-zinc-400">Probability</span>
            <p className="text-xl font-bold text-white">{prediction.probability}%</p>
          </div>
          <div className="w-px h-8 bg-zinc-700" />
          <div>
            <span className="text-xs text-zinc-400">Confidence</span>
            <p className={`text-xl font-bold ${getConfidenceColor(prediction.confidence)}`}>
              {prediction.confidence}%
            </p>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {/* Expected Goals */}
        <div className="bg-zinc-700/30 border border-zinc-600/30 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <Target weight="fill" className="w-4 h-4 text-purple-400" />
            <span className="text-xs text-zinc-400">Expected Goals</span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-bold text-white">{prediction.expectedGoals.home}</span>
            <span className="text-zinc-500">-</span>
            <span className="text-lg font-bold text-white">{prediction.expectedGoals.away}</span>
          </div>
          <p className="text-xs text-zinc-500 mt-1">Total: {prediction.expectedGoals.total}</p>
        </div>

        {/* Model Edge */}
        <div className="bg-zinc-700/30 border border-zinc-600/30 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <ChartLine weight="fill" className="w-4 h-4 text-green-400" />
            <span className="text-xs text-zinc-400">Model Edge</span>
          </div>
          <p className="text-lg font-bold text-green-400">+{prediction.modelEdge}%</p>
          <p className="text-xs text-zinc-500 mt-1">vs market</p>
        </div>
      </div>

      {/* Expected Value (if available) */}
      {prediction.expectedValue !== undefined && (
        <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-lg p-3 mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Lightning weight="fill" className="w-4 h-4 text-green-400" />
              <span className="text-xs text-zinc-400">Expected Value</span>
            </div>
            <p className={`text-lg font-bold ${prediction.expectedValue > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {prediction.expectedValue > 0 ? '+' : ''}{prediction.expectedValue.toFixed(1)}%
            </p>
          </div>
        </div>
      )}

      {/* Recommended Markets */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Shield weight="fill" className="w-4 h-4 text-orange-400" />
          <span className="text-xs text-zinc-400 uppercase tracking-wider">Recommended Markets</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {prediction.recommendedMarkets.map((market, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-700/50 hover:bg-zinc-700/70 border border-zinc-600/50 rounded-lg transition-colors"
            >
              <CheckCircle weight="fill" className="w-3 h-3 text-green-400" />
              <span className="text-xs text-zinc-300 font-medium">{market}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default PredictionCard;
