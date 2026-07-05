import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, X, Send, ChevronRight, Check } from 'lucide-react';
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
    { icon: '🎯', label: 'Best Bet Today', action: 'best_bet' },
    { icon: '⚽', label: "Today's Matches", action: 'today_matches' },
    { icon: '📊', label: 'Analyze Match', action: 'analyze_match' },
    { icon: '💰', label: 'Betting Advice', action: 'betting_advice' },
    { icon: '📈', label: 'Highest Confidence', action: 'highest_confidence' },
    { icon: '🤖', label: 'Explain Prediction', action: 'explain_prediction' },
    { icon: '🔴', label: 'Live Matches', action: 'live_matches' },
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
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
      >
        <div className="relative">
          {/* Blue glow effect */}
          <div className="absolute inset-0 bg-blue-500/20 blur-xl rounded-full animate-pulse" />
          
          {/* Glassmorphism button */}
          <div className="relative bg-gradient-to-br from-blue-500/20 to-purple-500/20 backdrop-blur-xl border border-blue-400/30 rounded-2xl p-4 shadow-2xl shadow-blue-500/20">
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="relative"
            >
              <Sparkles className="w-6 h-6 text-blue-400" />
            </motion.div>
          </div>

          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-zinc-900/90 backdrop-blur-md border border-zinc-700/50 rounded-lg text-xs text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
            Ask OFFLINE AI
            <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-zinc-900/90" />
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
              <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-b border-zinc-800/50 p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <motion.div
                        animate={{ rotate: [0, 360] }}
                        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                      >
                        <Sparkles className="w-5 h-5 text-blue-400" />
                      </motion.div>
                      <div className="absolute -bottom-0.5 -right-0.5 w-2 h-2 bg-green-500 rounded-full border-2 border-zinc-900" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white">🤖 OFFLINE AI</h3>
                      <p className="text-[10px] text-zinc-400">Football Intelligence Assistant</p>
                    </div>
                  </div>
                  <button
                    onClick={toggleOpen}
                    className="p-1.5 hover:bg-zinc-800/50 rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4 text-zinc-400" />
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-[10px] text-green-400 font-medium">🟢 Online</span>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-xl px-4 py-3 ${
                        message.role === 'user'
                          ? 'bg-blue-500/20 border border-blue-400/30 text-white'
                          : 'bg-zinc-800/50 border border-zinc-700/50 text-zinc-200'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
                      <p className="text-[10px] text-zinc-500 mt-1">
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </motion.div>
                ))}
                {isThinking && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex justify-start"
                  >
                    <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-xl px-4 py-3 w-full max-w-[85%]">
                      <div className="text-xs text-zinc-400 mb-2">🤖 Analyzing today's fixtures...</div>
                      <div className="space-y-2">
                        {thinkingSteps.map((step, index) => (
                          <div
                            key={index}
                            className={`flex items-center gap-2 text-[10px] ${
                              index <= currentStepIndex ? 'text-green-400' : 'text-zinc-500'
                            }`}
                          >
                            {index <= currentStepIndex ? (
                              <Check className="w-3 h-3" />
                            ) : (
                              <div className="w-3 h-3 border border-zinc-600 rounded-full" />
                            )}
                            <span>{step}</span>
                          </div>
                        ))}
                      </div>
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
                        <ChevronRight className="w-3 h-3 flex-shrink-0" />
                        <span className="truncate">{question}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Input */}
              <div className="p-4 border-t border-zinc-800/50">
                <div className="flex gap-2">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask about matches, predictions, betting..."
                    className="flex-1 bg-zinc-800/50 border border-zinc-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-blue-400/50 transition-colors"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputValue.trim() || isTyping}
                    className="p-3 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-400/30 rounded-xl text-blue-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="w-4 h-4" />
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
