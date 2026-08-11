/**
 * services/openRouterAIService.ts
 * ================================
 * Frontend service for OpenRouter AI integration with tool calling
 * 
 * This service handles:
 * - Chat with AI
 * - Tool execution (calling prediction APIs)
 * - Conversation memory management
 */

import { API_BASE as MAIN_API_BASE } from '../api';

const API_BASE = `${MAIN_API_BASE}/ai`;

export interface Message {
  role: 'user' | 'assistant' | 'tool';
  content: string;
  timestamp?: Date;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface ChatResponse {
  content: string;
  tool_calls: ToolCall[];
  requires_action: boolean;
  error?: string;
}

export interface ToolResult {
  tool_call_id: string;
  content: any;
}

class OpenRouterAIService {
  private sessionId: string;
  private maxRetries: number = 3;
  private retryDelay: number = 1000;

  constructor() {
    // Generate or retrieve session ID
    this.sessionId = this.getOrCreateSessionId();
  }

  private getOrCreateSessionId(): string {
    let sessionId = localStorage.getItem('ai_session_id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('ai_session_id', sessionId);
    }
    return sessionId;
  }

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private async fetchWithRetry(
    url: string,
    options: RequestInit,
    attempt: number = 0
  ): Promise<Response> {
    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        
        // Retry on rate limit (429) or server errors (5xx)
        if ((response.status === 429 || response.status >= 500) && attempt < this.maxRetries - 1) {
          console.warn(`API error ${response.status}, retrying (${attempt + 1}/${this.maxRetries})...`);
          await this.delay(this.retryDelay * (attempt + 1));
          return this.fetchWithRetry(url, options, attempt + 1);
        }
        
        throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
      
      return response;
    } catch (error) {
      if (attempt < this.maxRetries - 1 && error instanceof Error) {
        console.warn(`Fetch error, retrying (${attempt + 1}/${this.maxRetries}):`, error.message);
        await this.delay(this.retryDelay * (attempt + 1));
        return this.fetchWithRetry(url, options, attempt + 1);
      }
      throw error;
    }
  }

  async chat(message: string): Promise<ChatResponse> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          session_id: this.sessionId
        })
      });

      return response.json();
    } catch (error) {
      console.error('Chat error:', error);
      return {
        content: error instanceof Error ? error.message : 'An error occurred',
        tool_calls: [],
        requires_action: false,
        error: error instanceof Error ? error.message : 'An error occurred'
      };
    }
  }

  async chatStream(message: string, onChunk: (chunk: string) => void, onDone: (response: ChatResponse) => void, onError: (error: string) => void): Promise<void> {
    try {
      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          session_id: this.sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      let toolCalls: any[] = [];
      let requiresAction = false;

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data.trim() === '') continue;

            try {
              const parsed = JSON.parse(data);
              
              if (parsed.error) {
                onError(parsed.error);
                return;
              }
              
              if (parsed.chunk) {
                fullContent += parsed.chunk;
                onChunk(parsed.chunk);
              }
              
              if (parsed.done) {
                onDone({
                  content: fullContent,
                  tool_calls: parsed.tool_calls || [],
                  requires_action: parsed.requires_action || false
                });
                return;
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Stream chat error:', error);
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      onError(errorMessage);
      
      // Fallback to non-streaming
      console.log('Falling back to non-streaming chat');
      const fallbackResponse = await this.chat(message);
      onDone(fallbackResponse);
    }
  }

  async submitToolResults(toolResults: ToolResult[]): Promise<ChatResponse> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/submit-tools`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: this.sessionId,
          tool_results: toolResults
        })
      });

      return response.json();
    } catch (error) {
      console.error('Submit tools error:', error);
      return {
        content: error instanceof Error ? error.message : 'An error occurred',
        tool_calls: [],
        requires_action: false,
        error: error instanceof Error ? error.message : 'An error occurred'
      };
    }
  }

  async executeTool(toolCall: ToolCall): Promise<any> {
    const { name, arguments: args } = toolCall.function;
    const parsedArgs = JSON.parse(args);

    switch (name) {
      case 'get_todays_matches':
        return this.getTodaysMatches(parsedArgs);
      case 'get_match_prediction':
        return this.getMatchPrediction(parsedArgs);
      case 'get_team_profile':
        return this.getTeamProfile(parsedArgs);
      case 'get_h2h':
        return this.getH2h(parsedArgs);
      case 'get_best_predictions':
        return this.getBestPredictions(parsedArgs);
      case 'get_safe_bets':
        return this.getSafeBets(parsedArgs);
      case 'get_best_value_bets':
        return this.getBestValueBets(parsedArgs);
      case 'get_live_match':
        return this.getLiveMatch(parsedArgs);
      case 'get_bookmaker_odds':
        return this.getBookmakerOdds(parsedArgs);
      case 'review_betting_slip':
        return this.reviewBettingSlip(parsedArgs);
      case 'get_today_brief':
        return this.getTodayBrief(parsedArgs);
      case 'get_fixtures':
        return this.getFixtures(parsedArgs);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  private async getTodaysMatches(args: any): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/tools/get-todays-matches`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      });
      return response.json();
    } catch (error) {
      console.error('getTodaysMatches error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch today matches' };
    }
  }

  private async getBestPredictions(args: any): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/tools/get-best-predictions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      });
      return response.json();
    } catch (error) {
      console.error('getBestPredictions error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch best predictions' };
    }
  }

  private async getSafeBets(args: any): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/tools/get-safe-bets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      });
      return response.json();
    } catch (error) {
      console.error('getSafeBets error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch safe bets' };
    }
  }

  private async getBestValueBets(args: any): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/tools/get-best-value-bets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      });
      return response.json();
    } catch (error) {
      console.error('getBestValueBets error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch value bets' };
    }
  }

  private async getLiveMatch(args: any): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/tools/get-live-match`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      });
      return response.json();
    } catch (error) {
      console.error('getLiveMatch error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch live match data' };
    }
  }

  private async reviewBettingSlip(args: any): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/tools/review-betting-slip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      });
      return response.json();
    } catch (error) {
      console.error('reviewBettingSlip error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to review betting slip' };
    }
  }

  private async getTodayBrief(args: any): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/tools/today-brief`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      });
      return response.json();
    } catch (error) {
      console.error('getTodayBrief error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch today brief' };
    }
  }

  private async getMatchPrediction(args: any): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/tools/match-prediction`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      });
      return response.json();
    } catch (error) {
      console.error('getMatchPrediction error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch match prediction' };
    }
  }

  private async getTeamProfile(args: any): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/tools/team-profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      });
      return response.json();
    } catch (error) {
      console.error('getTeamProfile error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch team profile' };
    }
  }

  private async getH2h(args: any): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/tools/h2h`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      });
      return response.json();
    } catch (error) {
      console.error('getH2h error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch H2H data' };
    }
  }

  private async getBookmakerOdds(args: any): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/tools/bookmaker-odds`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      });
      return response.json();
    } catch (error) {
      console.error('getBookmakerOdds error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch bookmaker odds' };
    }
  }

  private async getLiveMatchData(args: any): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/tools/live-match-data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      });
      return response.json();
    } catch (error) {
      console.error('getLiveMatchData error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch live match data' };
    }
  }

  private async getFixtures(args: any): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/tools/fixtures`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      });
      return response.json();
    } catch (error) {
      console.error('getFixtures error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch fixtures' };
    }
  }

  async clearMemory(): Promise<void> {
    await fetch(`${API_BASE}/memory/${this.sessionId}`, {
      method: 'DELETE'
    });
    // Generate new session ID
    this.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('ai_session_id', this.sessionId);
  }

  async getDailyBriefing(): Promise<any> {
    try {
      const response = await this.fetchWithRetry(`${API_BASE}/daily-briefing`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      return response.json();
    } catch (error) {
      console.error('getDailyBriefing error:', error);
      return { error: error instanceof Error ? error.message : 'Failed to fetch daily briefing' };
    }
  }

  async processMessage(message: string): Promise<string> {
    // Step 1: Send message to AI
    const chatResponse = await this.chat(message);
    
    if (chatResponse.error) {
      return chatResponse.content;
    }

    // Step 2: If AI wants to call tools, execute them
    if (chatResponse.requires_action && chatResponse.tool_calls.length > 0) {
      const toolResults: ToolResult[] = [];
      
      for (const toolCall of chatResponse.tool_calls) {
        try {
          const result = await this.executeTool(toolCall);
          toolResults.push({
            tool_call_id: toolCall.id,
            content: result
          });
        } catch (error) {
          toolResults.push({
            tool_call_id: toolCall.id,
            content: { error: String(error) }
          });
        }
      }

      // Step 3: Submit tool results and get final response
      const finalResponse = await this.submitToolResults(toolResults);
      return finalResponse.content;
    }

    // AI provided direct response
    return chatResponse.content;
  }
}

export const openRouterAIService = new OpenRouterAIService();
