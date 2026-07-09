OpenRouter AI Integration Setup Guide
=====================================

Overview
--------
The OFFLINE AI chat assistant has been upgraded to use OpenRouter's Free Router as a tool-calling agent. The AI now:
- NEVER answers football prediction questions from its own knowledge
- ALWAYS calls backend tools to get prediction data
- Explains results naturally using structured JSON from the backend
- Maintains conversation memory for context-aware responses (last 20 messages)
- Provides structured, premium football analyst reports
- Integrates bookmaker odds for value analysis

Architecture
------------
User Query → OpenRouter AI → Tool Selection → Backend API → Structured Data → AI Analysis → Structured Response

Available Tools
--------------
1. get_todays_matches() - Get today's scheduled matches
2. get_match_prediction(home_team, away_team) - Get full prediction for a specific match
3. get_team_profile(team_name) - Get team statistics, form, ELO, squad value
4. get_h2h(team_a_name, team_b_name) - Get head-to-head history
5. get_best_predictions() - Get highest confidence predictions today
6. get_safe_bets(min_confidence) - Get bets with highest confidence (safest selections)
7. get_best_value_bets() - Get bets with best expected value
8. get_live_match(match_id) - Get live match data
9. get_bookmaker_odds(match_id) - Get bookmaker odds from multiple bookmakers
10. review_betting_slip(selections) - Review a betting slip with multiple selections

Bookmaker Odds Integration
--------------------------
The AI now integrates bookmaker odds for value analysis:

Supported Bookmakers:
- Stake
- Bet365
- Pinnacle
- 1xBet

Value Analysis:
- Compares Model Probability vs Bookmaker Odds
- Calculates Implied Probability (1 / Odds)
- Calculates Expected Value (EV) = (Model Probability × Odds) - 1
- Highlights positive EV opportunities (> 5% threshold)
- Recommends best bookmaker for each market
- Clearly states when odds are unavailable

Response Format
---------------
All match predictions follow this structured format:

🏆 Prediction
📊 Probability (with progress bar)
🎯 Confidence
⚠️ Risk Level
💰 Bookmaker Odds Analysis (table with EV comparison)
💰 Recommended Markets (with best odds)
🧠 Reasoning
📈 Advanced Statistics (expandable)
✅ Summary

Betting Slip Review Format:
📋 Betting Slip Review
- Combined Probability
- Overall Risk
- Selection Analysis (table)
- Weak Selections
- Safer Replacements
- Recommendation
- Disclaimer

Conversation Memory
-------------------
- Last 20 messages kept per session
- Match context automatically tracked
- Follow-up questions use context (e.g., "Why?" refers to current match)
- Memory reset only when user clears conversation

Setup Instructions
-----------------

1. Backend Setup
   a. Add OpenRouter API Key to .env:
      OPENROUTER_API_KEY=your_openrouter_api_key_here
   
   b. Install dependencies:
      pip install -r requirements.txt
      (httpx is already included)

2. Frontend Setup
   a. Enable OpenRouter AI by setting environment variable:
      VITE_USE_OPENROUTER_AI=true
   
   b. The new AI component (AIAssistantNew) will be used instead of the old one

3. Testing
   a. Start the backend server:
      uvicorn api.main:app --reload
   
   b. Check AI health endpoint:
      GET /api/ai/health
   
   Expected response:
   {
     "status": "healthy",
     "models_loaded": true,
     "openrouter_configured": true,
     "max_retries": 3
   }

4. Usage
   - Open the chat interface
   - Ask questions like:
     * "Where should I bet today?"
     * "France vs Morocco"
     * "Show me the safest bets"
     * "What are the best value bets?"
     * "Which bookmaker has the best odds?"
     * "Review my betting slip: France Win, Spain Over 2.5, England BTTS"
   - The AI will automatically call the appropriate tools
   - Responses include bookmaker odds analysis when available
   - Betting slip reviews analyze combined probability and risk

Feature Flag
------------
To switch between old and new AI assistant:
- Set VITE_USE_OPENROUTER_AI=true to use OpenRouter AI
- Set VITE_USE_OPENROUTER_AI=false or omit to use the old keyword-based AI

Error Handling
--------------
- If OPENROUTER_API_KEY is not set, the AI will return a configuration error
- If the backend API fails, the AI will retry up to 3 times with exponential backoff
- If tools return no data, the AI will say "I don't currently have that information."
- If bookmaker odds are unavailable, the AI will say "No live bookmaker odds are available."
- All errors are logged for debugging

Files Modified
--------------
Backend:
- services/ai_service.py (new file)
- api/routes/ai.py (new file)
- api/main.py (added AI router)
- requirements.txt (added httpx)

Frontend:
- offline/src/services/openRouterAIService.ts (new file)
- offline/src/components/AIAssistantNew.tsx (new file)
- offline/src/App.tsx (added feature flag)

Configuration
-------------
- Max retries: 3
- Retry delay: 1s (exponential backoff)
- Timeout: 60s per API call
- Conversation memory: Last 20 messages per session
- EV threshold: 5% for value bets

Important Notes
---------------
- The AI NEVER invents probabilities, odds, or statistics
- All football data comes from the prediction engine
- The prediction engine remains the single source of truth
- Bookmaker odds are only used if available from the database
- If data is unavailable, the AI clearly states it
- Conversation context is maintained for follow-up questions
- Responses are structured with visual elements (progress bars, tables, expandable sections)
