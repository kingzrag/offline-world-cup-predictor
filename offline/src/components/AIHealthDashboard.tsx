import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle,
  WarningCircle,
  XCircle,
  ArrowsClockwise,
  Trash,
  Spinner,
  Database,
  Cpu,
  Globe,
  Toolbox,
  Brain,
  Clock,
  Lightning
} from '@phosphor-icons/react';

const API_BASE = '/api/ai';

interface ServiceStatus {
  status: 'healthy' | 'warning' | 'offline';
  response_time_ms?: number;
  last_error?: string;
  configured?: boolean;
  loaded?: boolean;
  tool_count?: number;
  tools?: string[];
  active_sessions?: number;
  max_messages_per_session?: number;
  model?: string;
  model_versions?: Record<string, string>;
  type?: string;
  live_sync?: any;
  last_updated?: string;
  staleness?: string;
  minutes_since_update?: number;
}

interface DiagnosticsData {
  openrouter: ServiceStatus;
  prediction_model: ServiceStatus;
  database: ServiceStatus;
  odds_api: ServiceStatus;
  tool_calling: ServiceStatus;
  conversation_memory: ServiceStatus;
  cache: ServiceStatus;
  background_jobs: ServiceStatus;
  overall: {
    status: 'healthy' | 'warning';
    timestamp: number;
  };
}

interface TestResult {
  service: string;
  status: string;
  response_time_ms?: number;
  details?: any;
  error?: string;
}

const StatusIcon = ({ status }: { status: 'healthy' | 'warning' | 'offline' }) => {
  if (status === 'healthy') {
    return <CheckCircle weight="fill" className="w-5 h-5 text-green-400" />;
  } else if (status === 'warning') {
    return <WarningCircle weight="fill" className="w-5 h-5 text-yellow-400" />;
  }
  return <XCircle weight="fill" className="w-5 h-5 text-red-400" />;
};

const StatusBadge = ({ status }: { status: 'healthy' | 'warning' | 'offline' }) => {
  const colors = {
    healthy: 'bg-green-500/10 text-green-400 border-green-500/30',
    warning: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    offline: 'bg-red-500/10 text-red-400 border-red-500/30'
  };
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${colors[status]}`}>
      {status.toUpperCase()}
    </span>
  );
};

const ServiceCard = ({ 
  title, 
  icon, 
  status, 
  details, 
  onTest 
}: { 
  title: string; 
  icon: React.ReactNode; 
  status: ServiceStatus; 
  details: React.ReactNode;
  onTest?: () => void;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className="bg-zinc-800/50 border border-zinc-700/50 rounded-xl p-4 hover:border-zinc-600/50 transition-colors"
  >
    <div className="flex items-start justify-between mb-3">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-zinc-700/50 rounded-lg">
          {icon}
        </div>
        <div>
          <h3 className="text-sm font-semibold text-zinc-100">{title}</h3>
          <StatusBadge status={status.status} />
        </div>
      </div>
      {onTest && (
        <button
          onClick={onTest}
          className="p-2 hover:bg-zinc-700/50 rounded-lg transition-colors"
          title="Test Service"
        >
          <Lightning weight="bold" className="w-4 h-4 text-zinc-400" />
        </button>
      )}
    </div>
    
    {details}
    
    {status.last_error && (
      <div className="mt-3 p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
        <p className="text-xs text-red-400 font-mono">{status.last_error}</p>
      </div>
    )}
  </motion.div>
);

export default function AIHealthDashboard() {
  const [diagnostics, setDiagnostics] = useState<DiagnosticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});
  const [testing, setTesting] = useState<Record<string, boolean>>({});

  const fetchDiagnostics = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/diagnostics`);
      const data = await response.json();
      setDiagnostics(data);
    } catch (error) {
      console.error('Failed to fetch diagnostics:', error);
    } finally {
      setLoading(false);
    }
  };

  const testService = async (service: string) => {
    setTesting(prev => ({ ...prev, [service]: true }));
    try {
      const response = await fetch(`${API_BASE}/diagnostics/test/${service}`, {
        method: 'POST'
      });
      const result = await response.json();
      setTestResults(prev => ({ ...prev, [service]: result }));
    } catch (error) {
      setTestResults(prev => ({ 
        ...prev, 
        [service]: { 
          service, 
          status: 'offline', 
          error: error instanceof Error ? error.message : 'Test failed' 
        } 
      }));
    } finally {
      setTesting(prev => ({ ...prev, [service]: false }));
    }
  };

  const testAllServices = () => {
    testService('all');
  };

  const clearMemory = async () => {
    if (!confirm('Are you sure you want to clear all conversation memory?')) return;
    
    try {
      const response = await fetch(`${API_BASE}/diagnostics/clear-memory`, {
        method: 'POST'
      });
      const result = await response.json();
      alert(`Cleared ${result.cleared_sessions} sessions`);
      fetchDiagnostics();
    } catch (error) {
      alert('Failed to clear memory');
    }
  };

  useEffect(() => {
    fetchDiagnostics();
    const interval = setInterval(fetchDiagnostics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading || !diagnostics) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-950">
        <div className="flex items-center gap-3">
          <Spinner weight="bold" className="w-6 h-6 text-blue-400 animate-spin" />
          <span className="text-zinc-400">Loading diagnostics...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Spinner weight="fill" className="w-8 h-8 text-blue-400" />
              <div>
                <h1 className="text-2xl font-bold text-white">AI Health Dashboard</h1>
                <p className="text-zinc-400 text-sm">Developer-only diagnostics</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={diagnostics.overall.status} />
              <button
                onClick={fetchDiagnostics}
                className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
              >
                <ArrowsClockwise weight="bold" className="w-4 h-4 text-zinc-400" />
                <span className="text-sm text-zinc-300">Refresh</span>
              </button>
            </div>
          </div>
          
          <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-xl p-4">
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <Clock weight="bold" className="w-4 h-4 text-zinc-400" />
                <span className="text-zinc-300">
                  Last updated: {new Date(diagnostics.overall.timestamp * 1000).toLocaleTimeString()}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle weight="fill" className="w-4 h-4 text-green-400" />
                <span className="text-zinc-300">
                  Overall: {diagnostics.overall.status.toUpperCase()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mb-8 flex flex-wrap gap-3">
          <button
            onClick={testAllServices}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <Lightning weight="bold" className="w-4 h-4 text-white" />
            <span className="text-sm text-white">Test All Services</span>
          </button>
          <button
            onClick={clearMemory}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
          >
            <Trash weight="bold" className="w-4 h-4 text-white" />
            <span className="text-sm text-white">Clear Conversation Memory</span>
          </button>
        </div>

        {/* Services Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {/* OpenRouter */}
          <ServiceCard
            title="OpenRouter API"
            icon={<Globe weight="fill" className="w-5 h-5 text-blue-400" />}
            status={diagnostics.openrouter}
            onTest={() => testService('openrouter')}
            details={
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Configured:</span>
                  <span className={diagnostics.openrouter.configured ? "text-green-400" : "text-red-400"}>
                    {diagnostics.openrouter.configured ? "Yes" : "No"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Model:</span>
                  <span className="text-zinc-300">{diagnostics.openrouter.model}</span>
                </div>
                {diagnostics.openrouter.response_time_ms && (
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Response Time:</span>
                    <span className="text-zinc-300">{diagnostics.openrouter.response_time_ms}ms</span>
                  </div>
                )}
              </div>
            }
          />

          {/* Prediction Model */}
          <ServiceCard
            title="Prediction Model"
            icon={<Cpu weight="fill" className="w-5 h-5 text-purple-400" />}
            status={diagnostics.prediction_model}
            onTest={() => testService('prediction_model')}
            details={
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Loaded:</span>
                  <span className={diagnostics.prediction_model.loaded ? "text-green-400" : "text-red-400"}>
                    {diagnostics.prediction_model.loaded ? "Yes" : "No"}
                  </span>
                </div>
                {diagnostics.prediction_model.model_versions && Object.keys(diagnostics.prediction_model.model_versions).length > 0 && (
                  <div>
                    <span className="text-zinc-400">Models:</span>
                    <div className="mt-1 space-y-1">
                      {Object.entries(diagnostics.prediction_model.model_versions).map(([name, version]) => (
                        <div key={name} className="flex justify-between">
                          <span className="text-zinc-500">{name}:</span>
                          <span className="text-zinc-300">{version}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            }
          />

          {/* Database */}
          <ServiceCard
            title="Database"
            icon={<Database weight="fill" className="w-5 h-5 text-green-400" />}
            status={diagnostics.database}
            onTest={() => testService('database')}
            details={
              <div className="space-y-2 text-xs">
                {diagnostics.database.response_time_ms && (
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Response Time:</span>
                    <span className="text-zinc-300">{diagnostics.database.response_time_ms}ms</span>
                  </div>
                )}
              </div>
            }
          />

          {/* Odds API */}
          <ServiceCard
            title="Odds API"
            icon={<Lightning weight="fill" className="w-5 h-5 text-yellow-400" />}
            status={diagnostics.odds_api}
            onTest={() => testService('odds_api')}
            details={
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Configured:</span>
                  <span className={diagnostics.odds_api.configured ? "text-green-400" : "text-red-400"}>
                    {diagnostics.odds_api.configured ? "Yes" : "No"}
                  </span>
                </div>
                {diagnostics.odds_api.response_time_ms && (
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Response Time:</span>
                    <span className="text-zinc-300">{diagnostics.odds_api.response_time_ms}ms</span>
                  </div>
                )}
                {diagnostics.odds_api.last_updated && (
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Last Updated:</span>
                    <span className="text-zinc-300">
                      {new Date(diagnostics.odds_api.last_updated).toLocaleTimeString()}
                    </span>
                  </div>
                )}
                {diagnostics.odds_api.staleness && (
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Status:</span>
                    <span className={
                      diagnostics.odds_api.staleness === 'fresh' ? 'text-green-400' :
                      diagnostics.odds_api.staleness === 'no data' ? 'text-red-400' :
                      'text-yellow-400'
                    }>
                      {diagnostics.odds_api.staleness}
                    </span>
                  </div>
                )}
              </div>
            }
          />

          {/* Tool Calling */}
          <ServiceCard
            title="Tool Calling"
            icon={<Toolbox weight="fill" className="w-5 h-5 text-orange-400" />}
            status={diagnostics.tool_calling}
            onTest={() => testService('tools')}
            details={
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Tool Count:</span>
                  <span className="text-zinc-300">{diagnostics.tool_calling.tool_count}</span>
                </div>
                {diagnostics.tool_calling.tools && (
                  <div>
                    <span className="text-zinc-400">Tools:</span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {diagnostics.tool_calling.tools.slice(0, 5).map(tool => (
                        <span key={tool} className="px-1.5 py-0.5 bg-zinc-700 rounded text-zinc-300">
                          {tool}
                        </span>
                      ))}
                      {diagnostics.tool_calling.tools.length > 5 && (
                        <span className="text-zinc-500">+{diagnostics.tool_calling.tools.length - 5} more</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            }
          />

          {/* Conversation Memory */}
          <ServiceCard
            title="Conversation Memory"
            icon={<Brain weight="fill" className="w-5 h-5 text-pink-400" />}
            status={diagnostics.conversation_memory}
            details={
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Active Sessions:</span>
                  <span className="text-zinc-300">{diagnostics.conversation_memory.active_sessions}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Max Messages/Session:</span>
                  <span className="text-zinc-300">{diagnostics.conversation_memory.max_messages_per_session}</span>
                </div>
              </div>
            }
          />
        </div>

        {/* Test Results */}
        {Object.keys(testResults).length > 0 && (
          <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-zinc-100 mb-4">Test Results</h3>
            <div className="space-y-3">
              {Object.entries(testResults).map(([service, result]) => (
                <div key={service} className="p-3 bg-zinc-900/50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-zinc-300 capitalize">{service}</span>
                    <StatusBadge status={result.status as any} />
                  </div>
                  {result.response_time_ms && (
                    <div className="text-xs text-zinc-400 mb-1">
                      Response Time: {result.response_time_ms}ms
                    </div>
                  )}
                  {result.details && typeof result.details === 'object' && !Array.isArray(result.details) && (
                    <div className="text-xs text-zinc-400 space-y-1">
                      {Object.entries(result.details).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-zinc-500">{key}:</span>
                          <span className="text-zinc-300">{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {result.error && (
                    <div className="text-xs text-red-400 font-mono mt-2">{result.error}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
