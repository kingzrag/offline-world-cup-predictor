import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChatCenteredDots,
  Robot,
  Sparkle,
  Lightning,
  ArrowUpRight,
  X,
  PaperPlaneRight,
  Copy,
  ArrowCounterClockwise,
  CaretDown,
  CaretUp,
  Trophy,
  ChartLine
} from '@phosphor-icons/react';
import { openRouterAIService } from '../services/openRouterAIService';
import type { MatchPrediction } from '../types';
import PredictionCard from './PredictionCard';

// Progress bar component for probabilities
const ProgressBar = ({ value, color = 'blue' }: { value: number; color?: string }) => {
  const percentage = Math.min(Math.max(value, 0), 100);
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500'
  };
  
  return (
    <div className="w-full bg-zinc-700/50 rounded-full h-2 overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${percentage}%` }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className={`h-full ${colorClasses[color as keyof typeof colorClasses] || colorClasses.blue}`}
      />
    </div>
  );
};

// Expandable section component for advanced statistics
const ExpandableSection = ({ title, children }: { title: string; children: React.ReactNode }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div className="mt-3 border border-zinc-700/50 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2 bg-zinc-800/50 hover:bg-zinc-700/50 flex items-center justify-between transition-colors"
      >
        <span className="text-xs font-medium text-zinc-300">{title}</span>
        {isExpanded ? (
          <CaretUp weight="bold" className="w-4 h-4 text-zinc-400" />
        ) : (
          <CaretDown weight="bold" className="w-4 h-4 text-zinc-400" />
        )}
      </button>
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 py-3 bg-zinc-900/30 text-xs text-zinc-400">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Typing indicator component
const TypingIndicator = () => (
  <div className="flex items-center gap-2 px-4 py-3 bg-zinc-800/60 border border-zinc-700/50 rounded-2xl w-fit">
    <div className="flex gap-1">
      <motion.div
        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 1, repeat: Infinity, ease: "easeInOut" }}
        className="w-2 h-2 bg-blue-400 rounded-full"
      />
      <motion.div
        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 1, repeat: Infinity, ease: "easeInOut", delay: 0.2 }}
        className="w-2 h-2 bg-blue-400 rounded-full"
      />
      <motion.div
        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 1, repeat: Infinity, ease: "easeInOut", delay: 0.4 }}
        className="w-2 h-2 bg-blue-400 rounded-full"
      />
    </div>
    <span className="text-xs text-zinc-400">OFFLINE AI is thinking...</span>
  </div>
);

// Quick action chip component
const QuickActionChip = ({ icon, label, onClick }: { icon: React.ReactNode; label: string; onClick: () => void }) => (
  <motion.button
    whileHover={{ scale: 1.05, y: -2 }}
    whileTap={{ scale: 0.95 }}
    onClick={onClick}
    className="flex items-center gap-2 px-3 py-2 bg-zinc-800/50 hover:bg-zinc-700/50 border border-zinc-700/50 rounded-xl transition-all duration-200"
  >
    <span className="text-blue-400">{icon}</span>
    <span className="text-xs text-zinc-300 font-medium">{label}</span>
  </motion.button>
);

// Daily briefing dashboard component
const DailyBriefingDashboard = ({ briefing, onClose }: { briefing: any; onClose: () => void }) => {
  if (!briefing) return null;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="mb-4 bg-gradient-to-br from-zinc-800/80 to-zinc-900/80 border border-zinc-700/50 rounded-2xl p-4 shadow-xl"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkle weight="fill" className="w-5 h-5 text-yellow-400" />
          <h3 className="text-sm font-bold text-zinc-100">Daily Football Briefing</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-zinc-700/50 rounded transition-colors"
        >
          <X weight="bold" className="w-4 h-4 text-zinc-400" />
        </button>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="bg-zinc-700/30 rounded-lg p-3 border border-zinc-600/30">
          <p className="text-[10px] text-zinc-400 uppercase tracking-wider mb-1">Today's Matches</p>
          <p className="text-xl font-bold text-zinc-100">{briefing.today_matches}</p>
        </div>
        <div className="bg-zinc-700/30 rounded-lg p-3 border border-zinc-600/30">
          <p className="text-[10px] text-zinc-400 uppercase tracking-wider mb-1">Live Matches</p>
          <p className="text-xl font-bold text-green-400">{briefing.live_matches?.length || 0}</p>
        </div>
        <div className="bg-zinc-700/30 rounded-lg p-3 border border-zinc-600/30">
          <p className="text-[10px] text-zinc-400 uppercase tracking-wider mb-1">Model Accuracy</p>
          <p className="text-xl font-bold text-blue-400">{briefing.model_updates?.accuracy || 'N/A'}</p>
        </div>
        <div className="bg-zinc-700/30 rounded-lg p-3 border border-zinc-600/30">
          <p className="text-[10px] text-zinc-400 uppercase tracking-wider mb-1">Model Version</p>
          <p className="text-xl font-bold text-purple-400">{briefing.model_updates?.version || 'N/A'}</p>
        </div>
      </div>
      
      <div className="space-y-3">
        {briefing.highest_confidence && (
          <div className="bg-gradient-to-r from-green-500/10 to-green-600/10 border border-green-500/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <Trophy weight="fill" className="w-4 h-4 text-green-400" />
              <p className="text-xs font-medium text-green-400">Highest Confidence</p>
            </div>
            <p className="text-sm text-zinc-200">
              {briefing.highest_confidence.home_team?.name} vs {briefing.highest_confidence.away_team?.name}
            </p>
            <p className="text-xs text-zinc-400">
              Confidence: {(briefing.highest_confidence.prediction?.confidence * 100).toFixed(0)}%
            </p>
          </div>
        )}
        
        {briefing.best_value_bet && (
          <div className="bg-gradient-to-r from-blue-500/10 to-blue-600/10 border border-blue-500/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <Lightning weight="fill" className="w-4 h-4 text-blue-400" />
              <p className="text-xs font-medium text-blue-400">Best Value Bet</p>
            </div>
            <p className="text-sm text-zinc-200">
              {briefing.best_value_bet.home_team?.name} vs {briefing.best_value_bet.away_team?.name}
            </p>
            <p className="text-xs text-zinc-400">
              EV: {(briefing.best_value_bet.expected_value * 100).toFixed(1)}% | Odds: {briefing.best_value_bet.odds?.toFixed(2)}
            </p>
          </div>
        )}
        
        {briefing.biggest_upset && (
          <div className="bg-gradient-to-r from-yellow-500/10 to-yellow-600/10 border border-yellow-500/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <ArrowUpRight weight="fill" className="w-4 h-4 text-yellow-400" />
              <p className="text-xs font-medium text-yellow-400">Upset Alert</p>
            </div>
            <p className="text-sm text-zinc-200">
              {briefing.biggest_upset.home_team?.name} vs {briefing.biggest_upset.away_team?.name}
            </p>
            <p className="text-xs text-zinc-400">
              Underdog chance: {briefing.biggest_upset.upset_team === 'home' 
                ? (briefing.biggest_upset.prediction?.outcome?.home_win_prob * 100).toFixed(0)
                : (briefing.biggest_upset.prediction?.outcome?.away_win_prob * 100).toFixed(0)}%
            </p>
          </div>
        )}
        
        {briefing.best_over_25 && (
          <div className="bg-gradient-to-r from-purple-500/10 to-purple-600/10 border border-purple-500/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <ChartLine weight="fill" className="w-4 h-4 text-purple-400" />
              <p className="text-xs font-medium text-purple-400">Best Over 2.5</p>
            </div>
            <p className="text-sm text-zinc-200">
              {briefing.best_over_25.home_team?.name} vs {briefing.best_over_25.away_team?.name}
            </p>
            <p className="text-xs text-zinc-400">
              Probability: {(briefing.best_over_25.prediction?.goals?.markets?.over_under?.['2.5']?.over * 100).toFixed(0)}%
            </p>
          </div>
        )}
        
        {briefing.best_btts && (
          <div className="bg-gradient-to-r from-pink-500/10 to-pink-600/10 border border-pink-500/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <ChatCenteredDots weight="fill" className="w-4 h-4 text-pink-400" />
              <p className="text-xs font-medium text-pink-400">Best BTTS</p>
            </div>
            <p className="text-sm text-zinc-200">
              {briefing.best_btts.home_team?.name} vs {briefing.best_btts.away_team?.name}
            </p>
            <p className="text-xs text-zinc-400">
              Probability: {(briefing.best_btts.prediction?.goals?.markets?.btts?.yes * 100).toFixed(0)}%
            </p>
          </div>
        )}
        
        {briefing.model_updates && (
          <div className="bg-zinc-700/20 border border-zinc-600/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <Robot weight="fill" className="w-4 h-4 text-zinc-400" />
              <p className="text-xs font-medium text-zinc-400">Model Updates</p>
            </div>
            <p className="text-xs text-zinc-300">
              Last updated: {briefing.model_updates.last_updated}
            </p>
            <p className="text-xs text-zinc-400 mt-1">
              {briefing.model_updates.notes}
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
};

// Structured response component for rendering AI responses
const StructuredResponse = ({ content }: { content: string }) => {
  const lines = content.split('\n');
  const sections: React.ReactNode[] = [];
  let currentSection: string[] = [];
  let inBlockquote = false;
  let inTable = false;
  let tableRows: string[][] = [];
  let inPredictionBlock = false;
  let predictionData: any = null;

  const parsePredictionBlock = (text: string) => {
    const prediction: any = {
      match: '',
      prediction: '',
      probability: 0,
      confidence: 0,
      risk: 'Medium',
      expectedGoals: { home: 0, away: 0, total: 0 },
      recommendedMarkets: [],
      modelEdge: 0,
      expectedValue: undefined
    };

    // Parse match
    const matchMatch = text.match(/Match:\s*(.+)/i);
    if (matchMatch) prediction.match = matchMatch[1].trim();

    // Parse prediction
    const predMatch = text.match(/Prediction:\s*(.+)/i);
    if (predMatch) prediction.prediction = predMatch[1].trim();

    // Parse probability
    const probMatch = text.match(/Probability:\s*(\d+)%/i);
    if (probMatch) prediction.probability = parseInt(probMatch[1]);

    // Parse confidence
    const confMatch = text.match(/Confidence:\s*(\d+)%/i);
    if (confMatch) prediction.confidence = parseInt(confMatch[1]);

    // Parse risk
    const riskMatch = text.match(/Risk:\s*(Low|Medium|High)/i);
    if (riskMatch) prediction.risk = riskMatch[1];

    // Parse expected goals
    const xgMatch = text.match(/Expected Goals:\s*(\d+\.?\d*)\s*-\s*(\d+\.?\d*)/i);
    if (xgMatch) {
      prediction.expectedGoals.home = parseFloat(xgMatch[1]);
      prediction.expectedGoals.away = parseFloat(xgMatch[2]);
      prediction.expectedGoals.total = prediction.expectedGoals.home + prediction.expectedGoals.away;
    }

    // Parse recommended markets
    const marketsMatch = text.match(/Recommended Markets:\s*(.+)/i);
    if (marketsMatch) {
      prediction.recommendedMarkets = marketsMatch[1].split(',').map(m => m.trim());
    }

    // Parse model edge
    const edgeMatch = text.match(/Model Edge:\s*\+?(\d+)%/i);
    if (edgeMatch) prediction.modelEdge = parseInt(edgeMatch[1]);

    // Parse expected value
    const evMatch = text.match(/Expected Value:\s*([+-]?\d+\.?\d*)%/i);
    if (evMatch) prediction.expectedValue = parseFloat(evMatch[1]);

    return prediction;
  };

  const processSection = () => {
    if (currentSection.length === 0) return;
    
    const sectionText = currentSection.join('\n');
    
    // Check if this is a prediction block
    if (sectionText.includes('🏆') || sectionText.includes('PREDICTION') || 
        (sectionText.includes('Match:') && sectionText.includes('Prediction:'))) {
      const parsedPrediction = parsePredictionBlock(sectionText);
      if (parsedPrediction.match && parsedPrediction.prediction) {
        sections.push(<PredictionCard key={sections.length} prediction={parsedPrediction} />);
        currentSection = [];
        return;
      }
    }
    
    // Check if this is a probability section with percentage
    const probMatch = sectionText.match(/(\d+)%/);
    if (probMatch && sectionText.includes('📊')) {
      const percentage = parseInt(probMatch[1]);
      const color = percentage >= 80 ? 'green' : percentage >= 60 ? 'blue' : percentage >= 40 ? 'yellow' : 'red';
      sections.push(
        <div key={sections.length} className="mb-3">
          <p className="text-sm font-medium text-zinc-200 mb-1">{sectionText}</p>
          <ProgressBar value={percentage} color={color} />
        </div>
      );
    }
    // Check if this is a blockquote (expandable section)
    else if (sectionText.startsWith('>')) {
      const title = sectionText.replace(/^>\s*/, '').replace(/\(expandable\)/, '').trim();
      sections.push(
        <ExpandableSection key={sections.length} title={title}>
          <p>Detailed statistics would appear here</p>
        </ExpandableSection>
      );
    }
    // Check if this is a table
    else if (sectionText.includes('|')) {
      const rows = sectionText.split('\n').filter(row => row.includes('|'));
      if (rows.length > 1) {
        sections.push(
          <div key={sections.length} className="overflow-x-auto mb-3">
            <table className="w-full text-xs">
              <tbody>
                {rows.map((row, idx) => (
                  <tr key={idx} className={idx === 0 ? "border-b border-zinc-700" : ""}>
                    {row.split('|').filter(cell => cell.trim()).map((cell, cellIdx) => (
                      <td key={cellIdx} className={`px-2 py-1 ${idx === 0 ? "font-medium text-zinc-200" : "text-zinc-400"}`}>
                        {cell.trim()}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      } else {
        sections.push(<p key={sections.length} className="text-sm whitespace-pre-wrap leading-relaxed">{sectionText}</p>);
      }
    }
    // Regular text
    else {
      sections.push(<p key={sections.length} className="text-sm whitespace-pre-wrap leading-relaxed">{sectionText}</p>);
    }
    
    currentSection = [];
  };

  lines.forEach((line, idx) => {
    if (line.startsWith('---') || line.startsWith('🏆') || line.startsWith('📊') || line.startsWith('🎯') || 
        line.startsWith('⚠️') || line.startsWith('💰') || line.startsWith('🧠') || line.startsWith('📈') || line.startsWith('✅')) {
      processSection();
      currentSection = [line];
    } else {
      currentSection.push(line);
    }
  });

  processSection();

  return <div className="space-y-2">{sections}</div>;
};

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  error?: boolean;
}

interface AIAssistantProps {
  onAskAboutMatch?: (matchId: string) => void;
  matches?: MatchPrediction[];
}

export default function AIAssistantNew({ onAskAboutMatch, matches = [] }: AIAssistantProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [dailyBriefing, setDailyBriefing] = useState<any>(null);
  const [showBriefing, setShowBriefing] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const quickActions = [
    { icon: <Lightning weight="fill" className="w-4 h-4" />, label: "Today's Brief", action: "Give me today's football brief" },
    { icon: <ChatCenteredDots weight="fill" className="w-4 h-4" />, label: 'Match Scout', action: 'Analyze France vs Morocco' },
    { icon: <Sparkle weight="fill" className="w-4 h-4" />, label: 'Value Bets', action: 'Find the best value bets today' },
    { icon: <Robot weight="fill" className="w-4 h-4" />, label: 'Safest Bets', action: 'Show only bets above 80% confidence' },
  ];

  const suggestedQuestions = [
    "Where should I bet today?",
    "Which match has the highest confidence?",
    "Explain France vs Morocco",
    "What are the safest betting markets?",
    "Best over 2.5 goals today",
    "Explain Asian Handicap",
    "Compare France and Brazil",
    "Which bookmaker has the best odds?",
  ];

  // Load conversation from localStorage
  useEffect(() => {
    const savedMessages = localStorage.getItem('ai_conversation');
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        setMessages(parsed);
      } catch (e) {
        console.error('Failed to load conversation:', e);
      }
    }
  }, []);

  // Save conversation to localStorage
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('ai_conversation', JSON.stringify(messages));
    }
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load daily briefing on mount
  useEffect(() => {
    const loadDailyBriefing = async () => {
      try {
        const briefing = await openRouterAIService.getDailyBriefing();
        if (!briefing.error) {
          setDailyBriefing(briefing);
        }
      } catch (error) {
        console.error('Failed to load daily briefing:', error);
      }
    };
    
    loadDailyBriefing();
  }, []);

  const toggleOpen = () => {
    setIsOpen(!isOpen);
    if (!isOpen && messages.length === 0) {
      const welcomeMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `👋 Welcome to OFFLINE AI.\n\nI'm your football prediction analyst. I can help you with:\n\n• 🏆 Today's Football Brief\n• ⚽ Match Analysis\n• 💰 Value Betting\n• 📊 Risk Assessment\n• 📚 Football Concepts\n\nAsk me anything about today's matches, predictions, or betting markets!`,
        timestamp: new Date(),
      };
      setMessages([welcomeMessage]);
    }
  };

  const handleQuickAction = async (action: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: action,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsThinking(true);

    try {
      const response = await openRouterAIService.processMessage(action);
      
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I encountered an error processing your request. Please try again.",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isThinking) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsThinking(true);

    // Add streaming message placeholder
    const streamingId = `streaming-${Date.now()}`;
    setMessages(prev => [...prev, {
      id: streamingId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true
    }]);

    try {
      // Use streaming chat
      await openRouterAIService.chatStream(
        inputValue.trim(),
        // onChunk - update message content as it arrives
        (chunk: string) => {
          setMessages(prev => prev.map(msg => 
            msg.id === streamingId 
              ? { ...msg, content: msg.content + chunk }
              : msg
          ));
        },
        // onDone - finalize the message
        (response: any) => {
          setMessages(prev => prev.map(msg => 
            msg.id === streamingId 
              ? { 
                  ...msg, 
                  content: response.content,
                  isStreaming: false,
                  tool_calls: response.tool_calls,
                  requires_action: response.requires_action
                }
              : msg
          ));
        },
        // onError - handle streaming errors
        (error: string) => {
          setMessages(prev => prev.map(msg => 
            msg.id === streamingId 
              ? { 
                  ...msg, 
                  content: 'Sorry, I encountered an error. Please try again.',
                  isStreaming: false,
                  error: true
                }
              : msg
          ));
        }
      );
    } catch (error) {
      // Fallback to non-streaming if streaming fails completely
      console.error('Streaming failed, falling back to regular chat:', error);
      
      try {
        const response = await openRouterAIService.processMessage(inputValue.trim());
        
        setMessages(prev => prev.map(msg => 
          msg.id === streamingId 
            ? { 
                ...msg, 
                content: response,
                isStreaming: false
              }
            : msg
        ));
      } catch (fallbackError) {
        setMessages(prev => prev.map(msg => 
          msg.id === streamingId 
            ? { 
                ...msg, 
                content: 'Sorry, I encountered an error. Please try again.',
                isStreaming: false,
                error: true
              }
            : msg
        ));
      }
    } finally {
      setIsThinking(false);
    }
  };

  const handleRetry = async (messageId: string) => {
    const messageIndex = messages.findIndex(m => m.id === messageId);
    if (messageIndex === -1) return;

    const userMessage = messages[messageIndex];
    if (userMessage.role !== 'user') return;

    // Remove the failed assistant response
    setMessages(prev => prev.slice(0, messageIndex + 1));
    setIsThinking(true);

    try {
      const response = await openRouterAIService.processMessage(userMessage.content);
      
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I encountered an error processing your request. Please try again.",
        timestamp: new Date(),
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  const handleClearConversation = async () => {
    // Clear local state
    setMessages([]);
    localStorage.removeItem('ai_conversation');
    
    // Clear backend memory (this will reset the session)
    await openRouterAIService.clearMemory();
    
    // Start fresh with welcome message
    const welcomeMessage: Message = {
      id: Date.now().toString(),
      role: 'assistant',
      content: `👋 Welcome to OFFLINE AI.\n\nI'm your football prediction analyst. How can I help you today?`,
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <>
      {/* Floating AI Button */}
      <motion.button
        onClick={toggleOpen}
        className="fixed bottom-6 right-6 z-50 group"
        whileHover={{ scale: 1.08, y: -4 }}
        whileTap={{ scale: 0.95 }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1, type: "spring", stiffness: 200, damping: 20 }}
      >
        <div className="relative">
          <motion.div
            animate={{ 
              scale: [1, 1.2, 1],
              opacity: [0.5, 0.8, 0.5]
            }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            className="absolute inset-0 bg-blue-500/30 blur-2xl rounded-full"
          />
          <div className="relative bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-blue-500/10 backdrop-blur-2xl border border-blue-400/20 rounded-full p-4 shadow-2xl shadow-blue-500/10 ring-1 ring-white/10">
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            >
              <Sparkle weight="fill" className="w-6 h-6 text-blue-400" />
            </motion.div>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-zinc-900 shadow-lg shadow-green-500/50">
              <motion.div
                animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                className="absolute inset-0 bg-green-500 rounded-full"
              />
            </div>
          </div>
        </div>
      </motion.button>

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-24 right-6 z-50 w-[420px] max-w-[calc(100vw-3rem)] max-h-[650px]"
          >
            <div className="bg-zinc-950/95 backdrop-blur-xl border border-zinc-800/50 rounded-2xl shadow-2xl shadow-blue-500/10 overflow-hidden flex flex-col max-h-[650px]">
              {/* Header */}
              <div className="bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-blue-500/5 border-b border-zinc-800/50 p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <motion.div
                        animate={{ rotate: [0, 360] }}
                        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                      >
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl border border-blue-400/20 flex items-center justify-center backdrop-blur-sm">
                          <Robot weight="fill" className="w-5 h-5 text-blue-400" />
                        </div>
                      </motion.div>
                      <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-zinc-900 shadow-lg shadow-green-500/50">
                        <motion.div
                          animate={{ scale: [1, 1.3, 1], opacity: [1, 0.6, 1] }}
                          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                          className="absolute inset-0 bg-green-500 rounded-full"
                        />
                      </div>
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white tracking-tight">OFFLINE AI</h3>
                      <p className="text-[10px] text-zinc-400 font-medium tracking-wide">Football Intelligence Assistant</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleClearConversation}
                      className="p-2 hover:bg-zinc-800/50 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 group"
                      title="Clear conversation"
                    >
                      <ArrowCounterClockwise weight="bold" className="w-4 h-4 text-zinc-400 group-hover:text-white transition-colors" />
                    </button>
                    <button
                      onClick={toggleOpen}
                      className="p-2 hover:bg-zinc-800/50 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 group"
                    >
                      <X weight="bold" className="w-4 h-4 text-zinc-400 group-hover:text-white transition-colors" />
                    </button>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5 px-2.5 py-1 bg-green-500/10 border border-green-500/20 rounded-full">
                    <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                    <span className="text-[10px] text-green-400 font-semibold tracking-wide">ONLINE</span>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Daily Briefing Dashboard */}
                <AnimatePresence>
                  {showBriefing && dailyBriefing && (
                    <DailyBriefingDashboard 
                      briefing={dailyBriefing} 
                      onClose={() => setShowBriefing(false)} 
                    />
                  )}
                </AnimatePresence>
                
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {message.isStreaming && message.role === 'assistant' ? (
                      <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-gradient-to-br from-zinc-800/60 to-zinc-900/60 border border-zinc-700/50 text-zinc-200 shadow-lg shadow-zinc-900/20">
                        <div className="flex items-center gap-2">
                          <StructuredResponse content={message.content} />
                          <motion.span
                            animate={{ opacity: [1, 0, 1] }}
                            transition={{ duration: 0.8, repeat: Infinity }}
                            className="w-2 h-4 bg-blue-400 rounded-sm"
                          />
                        </div>
                      </div>
                    ) : message.isStreaming ? (
                      <TypingIndicator />
                    ) : (
                      <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                        message.role === 'user'
                          ? 'bg-gradient-to-br from-blue-500/20 to-blue-600/20 border border-blue-400/30 text-white shadow-lg shadow-blue-500/10'
                          : 'bg-gradient-to-br from-zinc-800/60 to-zinc-900/60 border border-zinc-700/50 text-zinc-200 shadow-lg shadow-zinc-900/20'
                      }`}>
                        <StructuredResponse content={message.content} />
                        <div className="flex items-center justify-between mt-2 pt-2 border-t border-zinc-700/30">
                          <p className="text-[10px] text-zinc-500 font-mono">
                            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                          {message.role === 'assistant' && (
                            <div className="flex items-center gap-1">
                              {message.error && (
                                <button
                                  onClick={() => handleRetry(message.id)}
                                  className="p-1 hover:bg-zinc-700/30 rounded transition-colors"
                                  title="Retry"
                                >
                                  <ArrowCounterClockwise weight="bold" className="w-3 h-3 text-zinc-400" />
                                </button>
                              )}
                              <button
                                onClick={() => handleCopy(message.content)}
                                className="p-1 hover:bg-zinc-700/30 rounded transition-colors"
                                title="Copy"
                              >
                                <Copy weight="bold" className="w-3 h-3 text-zinc-500 hover:text-white" />
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* Quick Actions */}
              {!isThinking && messages.length === 0 && (
                <div className="px-4 pb-2">
                  <div className="flex flex-wrap gap-2">
                    <QuickActionChip 
                      icon={<Lightning weight="fill" className="w-4 h-4" />} 
                      label="Today's Brief" 
                      onClick={() => handleQuickAction("Give me today's football brief")} 
                    />
                    <QuickActionChip 
                      icon={<ChatCenteredDots weight="fill" className="w-4 h-4" />} 
                      label="Match Scout" 
                      onClick={() => handleQuickAction("Analyze France vs Morocco")} 
                    />
                    <QuickActionChip 
                      icon={<Sparkle weight="fill" className="w-4 h-4" />} 
                      label="Value Bets" 
                      onClick={() => handleQuickAction("Find the best value bets today")} 
                    />
                    <QuickActionChip 
                      icon={<Robot weight="fill" className="w-4 h-4" />} 
                      label="Safest Bets" 
                      onClick={() => handleQuickAction("Show only bets above 80% confidence")} 
                    />
                  </div>
                </div>
              )}

              {/* Quick Actions */}
              {messages.length <= 1 && (
                <div className="px-4 pb-4">
                  <div className="flex flex-wrap gap-2">
                    {quickActions.map((action) => (
                      <button
                        key={action.action}
                        onClick={() => handleQuickAction(action.action)}
                        className="flex items-center gap-2 px-3 py-2 bg-zinc-800/50 hover:bg-zinc-700/50 border border-zinc-700/50 rounded-lg text-xs text-zinc-300 transition-colors"
                      >
                        <span>{action.icon}</span>
                        <span>{action.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Suggested Questions */}
              {messages.length <= 1 && (
                <div className="px-4 pb-4">
                  <p className="text-[10px] text-zinc-500 mb-2">Suggested questions:</p>
                  <div className="space-y-1">
                    {suggestedQuestions.slice(0, 4).map((question, index) => (
                      <button
                        key={index}
                        onClick={() => setInputValue(question)}
                        className="w-full text-left px-3 py-2 bg-zinc-800/30 hover:bg-zinc-800/50 border border-zinc-700/30 rounded-lg text-[11px] text-zinc-400 hover:text-zinc-300 transition-colors flex items-center gap-2"
                      >
                        <ArrowUpRight className="w-3 h-3 flex-shrink-0" />
                        <span className="truncate">{question}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Input */}
              <div className="p-4 border-t border-zinc-800/50 bg-gradient-to-t from-zinc-900/50 to-transparent">
                <div className="flex gap-2">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask about matches, predictions, betting..."
                    className="flex-1 bg-zinc-800/60 backdrop-blur-sm border border-zinc-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10 transition-all duration-200"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputValue.trim() || isThinking}
                    className="p-3 bg-gradient-to-br from-blue-500/20 to-blue-600/20 hover:from-blue-500/30 hover:to-blue-600/30 border border-blue-400/30 rounded-xl text-blue-400 transition-all duration-200 hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-lg shadow-blue-500/10"
                  >
                    <PaperPlaneRight weight="fill" className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
