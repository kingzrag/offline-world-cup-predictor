import type { MatchPrediction } from '../types';
import { predictMatch, getTeamProfile, getFixtures } from '../api';

export interface AIResponse {
  message: string;
  data?: any;
  steps?: string[];
}

export interface AIAnalysisStep {
  step: string;
  status: 'pending' | 'complete' | 'error';
}

// Cache for today's predictions to avoid repeated API calls
const predictionCache = new Map<string, any>();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

export class AIService {
  private static instance: AIService;

  private constructor() {}

  static getInstance(): AIService {
    if (!AIService.instance) {
      AIService.instance = new AIService();
    }
    return AIService.instance;
  }

  // Get cached prediction or fetch new one
  private async getCachedPrediction(matchId: string, fetchFn: () => Promise<any>): Promise<any> {
    const cached = predictionCache.get(matchId);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      return cached.data;
    }

    const data = await fetchFn();
    predictionCache.set(matchId, { data, timestamp: Date.now() });
    return data;
  }

  // Clear cache (call when new day starts)
  clearCache() {
    predictionCache.clear();
  }

  // Analyze best bet today
  async analyzeBestBetToday(matches: MatchPrediction[]): Promise<AIResponse> {
    const steps: AIAnalysisStep[] = [
      { step: 'Checking prediction model', status: 'pending' },
      { step: 'Comparing confidence scores', status: 'pending' },
      { step: 'Calculating expected value', status: 'pending' },
      { step: 'Finding safest betting market', status: 'pending' },
    ];

    try {
      steps[0].status = 'complete';
      
      // Find match with highest confidence
      const highConfidenceMatches = matches.filter(m => m.confidence === 'High');
      
      steps[1].status = 'complete';
      
      if (highConfidenceMatches.length === 0) {
        return {
          message: "I couldn't find any high-confidence matches today. The model suggests being cautious with today's fixtures as most predictions have moderate confidence levels.",
          steps: steps.map(s => s.step)
        };
      }

      // Get the highest confidence match
      const bestMatch = highConfidenceMatches[0];
      
      steps[2].status = 'complete';
      
      // Fetch detailed prediction from backend
      const prediction = await this.getCachedPrediction(
        bestMatch.id,
        () => predictMatch(bestMatch.teamA, bestMatch.teamB, bestMatch.kickoffTime)
      );

      steps[3].status = 'complete';

      const message = `Based on our prediction model analysis, the best betting opportunity today is:\n\n🏆 **${bestMatch.teamA} vs ${bestMatch.teamB}**\n\n**Prediction:** ${bestMatch.prediction}\n**Confidence:** High (${bestMatch.probA}% / ${bestMatch.probD}% / ${bestMatch.probB}%)\n\n**Why this match?**\n• Highest model confidence among today's fixtures\n• Clear probability differential\n• Strong statistical backing\n\n**Recommended markets:**\n• Match Result: ${bestMatch.prediction}\n• Expected Goals: ${prediction.goals?.total_expected_goals?.toFixed(2) || 'N/A'}\n\n⚠️ Remember: This is model-based analysis, not a guarantee. Always bet responsibly.`;

      return {
        message,
        data: { match: bestMatch, prediction },
        steps: steps.map(s => s.step)
      };
    } catch (error) {
      return {
        message: "I encountered an error analyzing today's best bet. Please try again.",
        steps: steps.map(s => s.step)
      };
    }
  }

  // Analyze specific match
  async analyzeMatch(matchId: string, matches: MatchPrediction[]): Promise<AIResponse> {
    const match = matches.find(m => m.id === matchId);
    if (!match) {
      return { message: "I couldn't find that match in today's fixtures." };
    }

    const steps: AIAnalysisStep[] = [
      { step: 'Loading match data', status: 'pending' },
      { step: 'Fetching prediction model', status: 'pending' },
      { step: 'Comparing team ELO ratings', status: 'pending' },
      { step: 'Calculating expected goals', status: 'pending' },
      { step: 'Analyzing betting markets', status: 'pending' },
    ];

    try {
      steps[0].status = 'complete';

      const prediction = await this.getCachedPrediction(
        matchId,
        () => predictMatch(match.teamA, match.teamB, match.kickoffTime)
      );

      steps[1].status = 'complete';

      // Get team profiles for ELO comparison
      const [teamAProfile, teamBProfile] = await Promise.all([
        getTeamProfile(match.teamA).catch(() => null),
        getTeamProfile(match.teamB).catch(() => null)
      ]);

      steps[2].status = 'complete';
      steps[3].status = 'complete';
      steps[4].status = 'complete';

      const eloDiff = teamAProfile?.elo_rating && teamBProfile?.elo_rating
        ? teamAProfile.elo_rating - teamBProfile.elo_rating
        : null;

      let analysis = `📊 **Match Analysis: ${match.teamA} vs ${match.teamB}**\n\n`;
      
      analysis += `**Prediction:** ${match.prediction}\n`;
      analysis += `**Confidence:** ${match.confidence}\n`;
      analysis += `**Probabilities:** ${match.teamA} ${match.probA}% | Draw ${match.probD}% | ${match.teamB} ${match.probB}%\n\n`;

      if (eloDiff !== null) {
        analysis += `**ELO Rating Difference:** ${eloDiff > 0 ? match.teamA : match.teamB} favored by ${Math.abs(eloDiff)} points\n`;
      }

      analysis += `**Expected Goals:** ${prediction.goals?.total_expected_goals?.toFixed(2) || 'N/A'}\n`;
      analysis += `**Most Likely Score:** ${prediction.markets?.most_likely_score || 'N/A'}\n\n`;

      analysis += `**Key Markets:**\n`;
      analysis += `• Over/Under 2.5: Over ${prediction.markets?.over_under?.['2.5']?.over?.toFixed(1)}% | Under ${prediction.markets?.over_under?.['2.5']?.under?.toFixed(1)}%\n`;
      analysis += `• BTTS: Yes ${prediction.markets?.btts?.yes?.toFixed(1)}% | No ${prediction.markets?.btts?.no?.toFixed(1)}%\n\n`;

      if (match.confidence === 'High') {
        analysis += `✅ This match has high model confidence, making it a relatively safer betting opportunity.\n`;
      } else {
        analysis += `⚠️ This match has moderate/low confidence. The model suggests caution as the outcome is less predictable.\n`;
      }

      analysis += `\n💡 **Why this prediction?**\nThe model considers ELO ratings, recent form, attack/defense strength, and historical performance to generate these probabilities.`;

      return {
        message: analysis,
        data: { match, prediction, teamAProfile, teamBProfile },
        steps: steps.map(s => s.step)
      };
    } catch (error) {
      return {
        message: "I encountered an error analyzing this match. The backend might be unavailable.",
        steps: steps.map(s => s.step)
      };
    }
  }

  // Find highest confidence match
  async findHighestConfidence(matches: MatchPrediction[]): Promise<AIResponse> {
    const steps: AIAnalysisStep[] = [
      { step: 'Scanning today\'s fixtures', status: 'pending' },
      { step: 'Comparing confidence levels', status: 'pending' },
      { step: 'Identifying top prediction', status: 'pending' },
    ];

    try {
      steps[0].status = 'complete';
      
      const sortedByConfidence = [...matches].sort((a, b) => {
        const confidenceOrder = { 'High': 3, 'Medium': 2, 'Low': 1 };
        return confidenceOrder[b.confidence] - confidenceOrder[a.confidence];
      });

      steps[1].status = 'complete';

      const topMatch = sortedByConfidence[0];
      
      steps[2].status = 'complete';

      if (!topMatch) {
        return { message: "No matches available for analysis.", steps: steps.map(s => s.step) };
      }

      const message = `The match with the highest model confidence today is:\n\n🏆 **${topMatch.teamA} vs ${topMatch.teamB}**\n\n**Prediction:** ${topMatch.prediction}\n**Confidence:** ${topMatch.confidence}\n**Probabilities:** ${topMatch.teamA} ${topMatch.probA}% | Draw ${topMatch.probD}% | ${topMatch.teamB} ${topMatch.probB}%\n\nThis match has the strongest statistical backing from our prediction model among today's fixtures.`;

      return {
        message,
        data: { match: topMatch },
        steps: steps.map(s => s.step)
      };
    } catch (error) {
      return {
        message: "I encountered an error finding the highest confidence match.",
        steps: steps.map(s => s.step)
      };
    }
  }

  // Find best Over 2.5 Goals
  async findBestOver25Goals(matches: MatchPrediction[]): Promise<AIResponse> {
    const steps: AIAnalysisStep[] = [
      { step: 'Loading fixture data', status: 'pending' },
      { step: 'Calculating expected goals', status: 'pending' },
      { step: 'Comparing Over 2.5 probabilities', status: 'pending' },
    ];

    try {
      steps[0].status = 'complete';

      // Fetch predictions for all matches to get expected goals
      const predictions = await Promise.all(
        matches.slice(0, 5).map(match =>
          this.getCachedPrediction(
            match.id,
            () => predictMatch(match.teamA, match.teamB, match.kickoffTime)
          ).catch(() => null)
        )
      );

      steps[1].status = 'complete';

      // Find match with highest Over 2.5 probability
      let bestMatch = null;
      let highestOver25Prob = 0;

      predictions.forEach((prediction, index) => {
        if (prediction && prediction.markets?.over_under?.['2.5']?.over) {
          const overProb = prediction.markets.over_under['2.5'].over;
          if (overProb > highestOver25Prob) {
            highestOver25Prob = overProb;
            bestMatch = { match: matches[index], prediction };
          }
        }
      });

      steps[2].status = 'complete';

      if (!bestMatch) {
        return { message: "I couldn't find suitable Over 2.5 Goals opportunities among today's fixtures.", steps: steps.map(s => s.step) };
      }

      const message = `The best Over 2.5 Goals opportunity today is:\n\n⚽ **${bestMatch.match.teamA} vs ${bestMatch.match.teamB}**\n\n**Expected Goals:** ${bestMatch.prediction.goals?.total_expected_goals?.toFixed(2) || 'N/A'}\n**Over 2.5 Probability:** ${(highestOver25Prob * 100).toFixed(1)}%\n**Most Likely Score:** ${bestMatch.prediction.markets?.most_likely_score || 'N/A'}\n\nThis match has the highest expected goals and Over 2.5 probability among today's fixtures, making it the best candidate for this market.`;

      return {
        message,
        data: bestMatch,
        steps: steps.map(s => s.step)
      };
    } catch (error) {
      return {
        message: "I encountered an error finding the best Over 2.5 Goals opportunity.",
        steps: steps.map(s => s.step)
      };
    }
  }

  // Find best BTTS prediction
  async findBestBTTS(matches: MatchPrediction[]): Promise<AIResponse> {
    const steps: AIAnalysisStep[] = [
      { step: 'Loading fixture data', status: 'pending' },
      { step: 'Analyzing team attacking strength', status: 'pending' },
      { step: 'Comparing BTTS probabilities', status: 'pending' },
    ];

    try {
      steps[0].status = 'complete';

      const predictions = await Promise.all(
        matches.slice(0, 5).map(match =>
          this.getCachedPrediction(
            match.id,
            () => predictMatch(match.teamA, match.teamB, match.kickoffTime)
          ).catch(() => null)
        )
      );

      steps[1].status = 'complete';

      let bestMatch = null;
      let highestBTTSYesProb = 0;

      predictions.forEach((prediction, index) => {
        if (prediction && prediction.markets?.btts?.yes) {
          const bttsProb = prediction.markets.btts.yes;
          if (bttsProb > highestBTTSYesProb) {
            highestBTTSYesProb = bttsProb;
            bestMatch = { match: matches[index], prediction };
          }
        }
      });

      steps[2].status = 'complete';

      if (!bestMatch) {
        return { message: "I couldn't find strong BTTS opportunities among today's fixtures.", steps: steps.map(s => s.step) };
      }

      const message = `The best BTTS (Both Teams To Score) opportunity today is:\n\n⚽ **${bestMatch.match.teamA} vs ${bestMatch.match.teamB}**\n\n**BTTS Yes Probability:** ${(highestBTTSYesProb * 100).toFixed(1)}%\n**Expected Goals:** ${bestMatch.prediction.goals?.total_expected_goals?.toFixed(2) || 'N/A'}\n\nThis match has the highest probability of both teams scoring, making it the best BTTS candidate today.`;

      return {
        message,
        data: bestMatch,
        steps: steps.map(s => s.step)
      };
    } catch (error) {
      return {
        message: "I encountered an error finding the best BTTS opportunity.",
        steps: steps.map(s => s.step)
      };
    }
  }

  // Explain why a prediction was made
  async explainPrediction(matchId: string, matches: MatchPrediction[]): Promise<AIResponse> {
    const match = matches.find(m => m.id === matchId);
    if (!match) {
      return { message: "I couldn't find that match." };
    }

    const steps: AIAnalysisStep[] = [
      { step: 'Loading prediction data', status: 'pending' },
      { step: 'Analyzing team statistics', status: 'pending' },
      { step: 'Comparing ELO ratings', status: 'pending' },
      { step: 'Generating explanation', status: 'pending' },
    ];

    try {
      steps[0].status = 'complete';

      const prediction = await this.getCachedPrediction(
        matchId,
        () => predictMatch(match.teamA, match.teamB, match.kickoffTime)
      );

      const [teamAProfile, teamBProfile] = await Promise.all([
        getTeamProfile(match.teamA).catch(() => null),
        getTeamProfile(match.teamB).catch(() => null)
      ]);

      steps[1].status = 'complete';
      steps[2].status = 'complete';

      let explanation = `🤖 **Why the model predicted ${match.prediction}**\n\n`;
      explanation += `For **${match.teamA} vs ${match.teamB}**, our prediction model chose **${match.prediction}** based on several factors:\n\n`;

      // Add ELO comparison
      if (teamAProfile?.elo_rating && teamBProfile?.elo_rating) {
        const eloDiff = teamAProfile.elo_rating - teamBProfile.elo_rating;
        explanation += `**ELO Ratings:**\n`;
        explanation += `• ${match.teamA}: ${teamAProfile.elo_rating}\n`;
        explanation += `• ${match.teamB}: ${teamBProfile.elo_rating}\n`;
        if (Math.abs(eloDiff) > 50) {
          explanation += `• ${eloDiff > 0 ? match.teamA : match.teamB} has a significant ELO advantage (${Math.abs(eloDiff)} points)\n`;
        }
        explanation += `\n`;
      }

      // Add recent form
      if (teamAProfile?.recent_form || teamBProfile?.recent_form) {
        explanation += `**Recent Form:**\n`;
        if (teamAProfile?.recent_form) {
          const recentResults = teamAProfile.recent_form.slice(-5).map(f => f.result).join(' ');
          explanation += `• ${match.teamA}: ${recentResults}\n`;
        }
        if (teamBProfile?.recent_form) {
          const recentResults = teamBProfile.recent_form.slice(-5).map(f => f.result).join(' ');
          explanation += `• ${match.teamB}: ${recentResults}\n`;
        }
        explanation += `\n`;
      }

      // Add probability breakdown
      explanation += `**Model Probabilities:**\n`;
      explanation += `• ${match.teamA} Win: ${match.probA}%\n`;
      explanation += `• Draw: ${match.probD}%\n`;
      explanation += `• ${match.teamB} Win: ${match.probB}%\n\n`;

      explanation += `**Expected Goals:** ${prediction.goals?.total_expected_goals?.toFixed(2) || 'N/A'}\n\n`;

      explanation += `**Summary:**\nThe model combines ELO ratings, recent performance, attacking/defensive strength, and historical data to generate these probabilities. The prediction with the highest probability (${match.prediction}) is selected as the most likely outcome.\n\n`;
      
      if (match.confidence === 'High') {
        explanation += `✅ High confidence indicates strong statistical backing for this prediction.`;
      } else {
        explanation += `⚠️ Moderate/low confidence suggests this match is more unpredictable - consider smaller stakes or avoiding this market.`;
      }

      steps[3].status = 'complete';

      return {
        message: explanation,
        data: { match, prediction, teamAProfile, teamBProfile },
        steps: steps.map(s => s.step)
      };
    } catch (error) {
      return {
        message: "I encountered an error generating the explanation.",
        steps: steps.map(s => s.step)
      };
    }
  }

  // General intent detection and routing
  async processQuery(query: string, matches: MatchPrediction[], contextMatchId?: string): Promise<AIResponse> {
    const lowerQuery = query.toLowerCase();

    // If context match is provided, prioritize match-specific queries
    if (contextMatchId) {
      if (lowerQuery.includes('why') || lowerQuery.includes('explain')) {
        return this.explainPrediction(contextMatchId, matches);
      }
      if (lowerQuery.includes('analyze')) {
        return this.analyzeMatch(contextMatchId, matches);
      }
      // Default to analysis if context match is provided
      return this.analyzeMatch(contextMatchId, matches);
    }

    // Intent detection for general queries
    if (lowerQuery.includes('best bet') || lowerQuery.includes('where should i bet')) {
      return this.analyzeBestBetToday(matches);
    }
    if (lowerQuery.includes('highest confidence') || lowerQuery.includes('most confident')) {
      return this.findHighestConfidence(matches);
    }
    if (lowerQuery.includes('over 2.5') || lowerQuery.includes('over/under')) {
      return this.findBestOver25Goals(matches);
    }
    if (lowerQuery.includes('btts') || lowerQuery.includes('both teams to score')) {
      return this.findBestBTTS(matches);
    }
    if (lowerQuery.includes('today') && lowerQuery.includes('match')) {
      return this.analyzeBestBetToday(matches);
    }

    // Default response
    return {
      message: `I can help you with:\n\n• 🎯 Best bet today\n• 📊 Analyze specific matches\n• 📈 Highest confidence predictions\n• ⚽ Over/Under goals\n• 💰 BTTS predictions\n• 🤖 Explain predictions\n\nTry asking "Where should I bet today?" or click "Ask AI" on any match card for detailed analysis.`
    };
  }
}

export const aiService = AIService.getInstance();
