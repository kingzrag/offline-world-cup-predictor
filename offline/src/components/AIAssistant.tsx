import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChatCenteredDots,
  Robot,
  Brain,
  Sparkle,
  Lightning,
  ArrowUpRight,
  X,
  Check,
  PaperPlaneRight
} from '@phosphor-icons/react';
import { aiService, AIResponse } from '../services/aiService';
import type { MatchPrediction } from '../types';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AIAssistantProps {
  onAskAboutMatch?: (matchId: string) => void;
  matches?: MatchPrediction[];
}

export default function AIAssistant({ onAskAboutMatch, matches = [] }: AIAssistantProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingSteps, setThinkingSteps] = useState<string[]>([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [selectedMatchId, setSelectedMatchId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const quickActions = [
    { icon: <Lightning weight="fill" className="w-4 h-4" />, label: 'Best Bet Today', action: 'best_bet' },
    { icon: <ChatCenteredDots weight="fill" className="w-4 h-4" />, label: "Today's Matches", action: 'today_matches' },
    { icon: <Brain weight="fill" className="w-4 h-4" />, label: 'Analyze Match', action: 'analyze_match' },
    { icon: <Sparkle weight="fill" className="w-4 h-4" />, label: 'Betting Advice', action: 'betting_advice' },
    { icon: <Robot weight="fill" className="w-4 h-4" />, label: 'Highest Confidence', action: 'highest_confidence' },
    { icon: <ChatCenteredDots weight="fill" className="w-4 h-4" />, label: 'Explain Prediction', action: 'explain_prediction' },
    { icon: <Lightning weight="fill" className="w-4 h-4" />, label: 'Live Matches', action: 'live_matches' },
  ];

  const suggestedQuestions = [
    "Where should I bet today?",
    "Which match has the highest confidence?",
    "Explain Argentina vs Brazil",
    "Why did the AI predict France?",
    "Show today's safest bet",
    "Which match should I avoid?",
    "Best over 2.5 goals today",
    "Best BTTS prediction",
  ];

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (selectedMatchId && isOpen) {
      handleMatchContext(selectedMatchId);
      setSelectedMatchId(null);
    }
  }, [selectedMatchId, isOpen]);

  const handleMatchContext = async (matchId: string) => {
    const match = matches.find(m => m.id === matchId);
    if (!match) return;

    const contextMessage: Message = {
      id: Date.now().toString(),
      role: 'assistant',
      content: `I'm ready to analyze **${match.teamA} vs ${match.teamB}**. What would you like to know about this match?`,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, contextMessage]);
    
    // Auto-trigger analysis
    setIsThinking(true);
    setCurrentStepIndex(0);
    setThinkingSteps([]);

    try {
      const response: AIResponse = await aiService.analyzeMatch(matchId, matches);

      if (response.steps && response.steps.length > 0) {
        setThinkingSteps(response.steps);
        for (let i = 0; i < response.steps.length; i++) {
          setCurrentStepIndex(i);
          await new Promise(resolve => setTimeout(resolve, 400));
        }
      }

      setIsThinking(false);

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      setIsThinking(false);
    }
  };

  const toggleOpen = () => {
    setIsOpen(!isOpen);
    if (!isOpen && messages.length === 0) {
      const welcomeMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `👋 Welcome to OFFLINE AI.\n\nI can help you analyze matches, explain predictions, find the safest betting markets, and answer football questions using our prediction model.`,
        timestamp: new Date(),
      };
      setMessages([welcomeMessage]);
    }
  };

  const handleQuickAction = async (action: string) => {
    const actionMessages: Record<string, string> = {
      best_bet: "Where should I bet today?",
      today_matches: "Show me today's matches",
      analyze_match: "Analyze today's matches",
      betting_advice: "Give me betting advice",
      highest_confidence: "Which match has the highest confidence?",
      explain_prediction: "Explain the prediction",
      live_matches: "Show live matches",
    };

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: actionMessages[action] || action,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    
    // Start thinking phase
    setIsThinking(true);
    setCurrentStepIndex(0);
    setThinkingSteps([]);

    try {
      const response: AIResponse = await aiService.processQuery(
        actionMessages[action] || action,
        matches,
        selectedMatchId || undefined
      );

      // Animate through thinking steps
      if (response.steps && response.steps.length > 0) {
        setThinkingSteps(response.steps);
        for (let i = 0; i < response.steps.length; i++) {
          setCurrentStepIndex(i);
          await new Promise(resolve => setTimeout(resolve, 400));
        }
      }

      setIsThinking(false);

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      setIsThinking(false);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I encountered an error processing your request. Please try again.",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    
    // Start thinking phase
    setIsThinking(true);
    setCurrentStepIndex(0);
    setThinkingSteps([]);

    try {
      const response: AIResponse = await aiService.processQuery(
        inputValue,
        matches,
        selectedMatchId || undefined
      );

      // Animate through thinking steps
      if (response.steps && response.steps.length > 0) {
        setThinkingSteps(response.steps);
        for (let i = 0; i < response.steps.length; i++) {
          setCurrentStepIndex(i);
          await new Promise(resolve => setTimeout(resolve, 400));
        }
      }

      setIsThinking(false);

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      setIsThinking(false);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I encountered an error processing your request. Please try again.",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    }
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
          {/* Multi-layered glow effect */}
          <motion.div
            animate={{ 
              scale: [1, 1.2, 1],
              opacity: [0.5, 0.8, 0.5]
            }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            className="absolute inset-0 bg-blue-500/30 blur-2xl rounded-full"
          />
          <motion.div
            animate={{ 
              scale: [1, 1.1, 1],
              opacity: [0.3, 0.5, 0.3]
            }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
            className="absolute inset-0 bg-purple-500/20 blur-xl rounded-full"
          />
          
          {/* Glassmorphism button */}
          <div className="relative bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-blue-500/10 backdrop-blur-2xl border border-blue-400/20 rounded-full p-4 shadow-2xl shadow-blue-500/10 ring-1 ring-white/10">
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="relative"
            >
              <Sparkle weight="fill" className="w-6 h-6 text-blue-400" />
            </motion.div>
            
            {/* Online indicator */}
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-zinc-900 shadow-lg shadow-green-500/50">
              <motion.div
                animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                className="absolute inset-0 bg-green-500 rounded-full"
              />
            </div>
          </div>

          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
            <div className="px-4 py-2 bg-zinc-900/95 backdrop-blur-xl border border-zinc-700/50 rounded-lg text-xs text-white whitespace-nowrap shadow-xl">
              <div className="flex items-center gap-2">
                <Robot weight="fill" className="w-3 h-3 text-blue-400" />
                <span>Ask OFFLINE AI</span>
              </div>
              <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-zinc-900/95" />
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
            className="fixed bottom-24 right-6 z-50 w-[400px] max-w-[calc(100vw-3rem)] max-h-[600px]"
          >
            <div className="bg-zinc-950/95 backdrop-blur-xl border border-zinc-800/50 rounded-2xl shadow-2xl shadow-blue-500/10 overflow-hidden flex flex-col max-h-[600px]">
              {/* Header */}
              <div className="bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-blue-500/5 border-b border-zinc-800/50 p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <motion.div
                        animate={{ rotate: [0, 360] }}
                        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                        className="relative"
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
                      <p className="text-[10px] text-zinc-400 font-medium tracking-wide">Football Decision Engine Assistant</p>
                    </div>
                  </div>
                  <button
                    onClick={toggleOpen}
                    className="p-2 hover:bg-zinc-800/50 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 group"
                  >
                    <X weight="bold" className="w-4 h-4 text-zinc-400 group-hover:text-white transition-colors" />
                  </button>
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
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                        message.role === 'user'
                          ? 'bg-gradient-to-br from-blue-500/20 to-blue-600/20 border border-blue-400/30 text-white shadow-lg shadow-blue-500/10'
                          : 'bg-gradient-to-br from-zinc-800/60 to-zinc-900/60 border border-zinc-700/50 text-zinc-200 shadow-lg shadow-zinc-900/20'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap leading-relaxed font-medium">{message.content}</p>
                      <p className="text-[10px] text-zinc-500 mt-2 font-mono">
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </motion.div>
                ))}
                {isThinking && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className="flex justify-start"
                  >
                    <div className="bg-gradient-to-br from-zinc-800/60 to-zinc-900/60 border border-zinc-700/50 rounded-2xl px-4 py-3 w-full max-w-[85%] shadow-lg shadow-zinc-900/20">
                      <div className="flex items-center gap-3">
                        <div className="flex gap-1.5">
                          <motion.div
                            animate={{ y: [0, -8, 0], opacity: [0.4, 1, 0.4] }}
                            transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
                            className="w-2 h-2 bg-blue-400 rounded-full"
                          />
                          <motion.div
                            animate={{ y: [0, -8, 0], opacity: [0.4, 1, 0.4] }}
                            transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut", delay: 0.2 }}
                            className="w-2 h-2 bg-blue-400 rounded-full"
                          />
                          <motion.div
                            animate={{ y: [0, -8, 0], opacity: [0.4, 1, 0.4] }}
                            transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut", delay: 0.4 }}
                            className="w-2 h-2 bg-blue-400 rounded-full"
                          />
                        </div>
                        <span className="text-xs text-zinc-400 font-medium">Thinking</span>
                      </div>
                      {thinkingSteps.length > 0 && (
                        <div className="mt-3 space-y-2">
                          {thinkingSteps.map((step, index) => (
                            <motion.div
                              key={index}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.1 }}
                              className={`flex items-center gap-2 text-[10px] ${
                                index <= currentStepIndex ? 'text-green-400' : 'text-zinc-500'
                              }`}
                            >
                              {index <= currentStepIndex ? (
                                <Check weight="fill" className="w-3 h-3" />
                              ) : (
                                <div className="w-3 h-3 border border-zinc-600 rounded-full" />
                              )}
                              <span className="font-medium">{step}</span>
                            </motion.div>
                          ))}
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Quick Actions */}
              {messages.length <= 1 && (
                <div className="px-4 pb-4">
                  <div className="flex flex-wrap gap-2">
                    {quickActions.slice(0, 4).map((action) => (
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
                    {suggestedQuestions.slice(0, 3).map((question, index) => (
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
                    disabled={!inputValue.trim() || isTyping}
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
