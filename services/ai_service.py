"""
services/ai_service.py
=====================
OpenRouter AI Service for Football Analysis

This service integrates OpenRouter AI as a football analyst that:
- Understands natural language queries
- Calls backend prediction APIs via tool calling
- Explains results naturally without inventing data
- Maintains conversation memory
"""

import os
import json
import httpx
import asyncio
from typing import Any, Dict, List, Optional, TypedDict
from dataclasses import dataclass, field
from datetime import datetime
from utils.logger import logger


class Message(TypedDict):
    role: str
    content: str


@dataclass
class ConversationMemory:
    """Stores conversation history for context awareness."""
    messages: List[Message] = field(default_factory=list)
    current_match_id: Optional[str] = None
    current_teams: Optional[tuple[str, str]] = None
    max_messages: int = 20  # Keep last 20 messages for context
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        # Keep only last 20 messages to manage context window
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def set_match_context(self, match_id: str, teams: tuple[str, str]):
        """Set the current match context for the conversation."""
        self.current_match_id = match_id
        self.current_teams = teams
    
    def clear(self):
        """Clear all conversation memory."""
        self.messages.clear()
        self.current_match_id = None
        self.current_teams = None


class AIService:
    """
    OpenRouter AI Service for Football Analysis.
    
    Uses OpenRouter's Free Router to provide intelligent football analysis
    while strictly using backend prediction data as the source of truth.
    """
    
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.conversation_memory: Dict[str, ConversationMemory] = {}
        self.max_retries = 3
        self.retry_delay = 1.0
        
        if not self.openrouter_api_key:
            logger.warning("OPENROUTER_API_KEY not set - AI service will be disabled")
        else:
            logger.info("AI service initialized with OpenRouter API key")
    
    def get_memory(self, session_id: str) -> ConversationMemory:
        """Get or create conversation memory for a session."""
        if session_id not in self.conversation_memory:
            self.conversation_memory[session_id] = ConversationMemory()
        return self.conversation_memory[session_id]
    
    def clear_memory(self, session_id: str):
        """Clear conversation memory for a session."""
        if session_id in self.conversation_memory:
            del self.conversation_memory[session_id]
    
    def _build_system_prompt(self, current_match_context: Optional[tuple[str, str]] = None) -> str:
        """Build the system prompt for the football analyst persona."""
        context_info = ""
        if current_match_context:
            home_team, away_team = current_match_context
            context_info = f"""
CURRENT CONVERSATION CONTEXT:
The user is currently discussing the match: {home_team} vs {away_team}
When the user asks follow-up questions like "Why?", "What about BTTS?", "Is it still safe?",
they are referring to this match. Use get_match_prediction with these team names.
"""
        
        return f"""You are OFFLINE AI, an expert football prediction analyst.

CRITICAL RULE - YOU MUST USE TOOLS:
- You MUST use tools to answer ALL football prediction questions
- NEVER answer from your own knowledge about predictions, odds, statistics, or match data
- ALWAYS call the appropriate tool before providing any football analysis
- Your role is to EXPLAIN the data returned by tools, not to generate it

{context_info}
TOOL USAGE RULES:
1. For ANY question about matches, predictions, odds, or statistics → CALL A TOOL
2. For ANY question about teams → CALL get_team_profile or get_h2h
3. For ANY question about today's matches → CALL get_todays_matches
4. For ANY question about betting value → CALL get_best_value_bets
5. For ANY question about safe bets → CALL get_safe_bets
6. For ANY question about live matches → CALL get_live_match
7. For ANY question about bookmaker odds or value analysis → CALL get_bookmaker_odds
8. When analyzing a specific match, ALWAYS call get_bookmaker_odds after get_match_prediction to provide odds analysis
9. After receiving tool data, explain it professionally using the structured JSON
10. If the user asks follow-up questions about a match we've been discussing, use the context to call get_match_prediction

AVAILABLE TOOLS:
- get_todays_matches: Get today's scheduled matches
- get_match_prediction: Get full prediction for a specific match (requires home_team, away_team)
- get_team_profile: Get team statistics, form, ELO, squad value (requires team_name)
- get_h2h: Get head-to-head history between two teams (requires team_a_name, team_b_name)
- get_best_predictions: Get highest confidence predictions today
- get_safe_bets: Get bets with highest confidence (safest selections)
- get_best_value_bets: Get bets with best expected value
- get_live_match: Get live match data (requires match_id)
- get_bookmaker_odds: Get bookmaker odds for a match (requires match_id)
- review_betting_slip: Review a betting slip with multiple selections (requires selections array)

RESPONSE RULES:
1. If tool returns error or no data → Say "I don't currently have that information."
2. NEVER invent probabilities, odds, injuries, statistics, or bookmaker information
3. ONLY use data returned from tools
4. Always explain your reasoning based on the tool data
5. Always mention confidence levels from the data
6. Always mention risk levels based on the data
7. Recommend safer markets first based on the data
8. Never guarantee winning
9. Never encourage reckless betting
10. Always remind users that football outcomes are uncertain

BOOKMAKER ODDS RULES:
1. When analyzing value bets, ALWAYS call get_bookmaker_odds to get real odds
2. Compare Model Probability vs Bookmaker Odds vs Implied Probability vs Expected Value
3. Expected Value (EV) = (Model Probability × Bookmaker Odds) - 1
4. Positive EV (> 0) indicates value opportunity
5. Negative EV (< 0) indicates poor value
6. Highlight positive EV opportunities clearly
7. If bookmaker odds are unavailable, clearly say "No live bookmaker odds are available"
8. Compare odds across bookmakers (Stake, Bet365, Pinnacle, 1xBet) when available
9. Recommend the bookmaker with the best odds for the selected market
10. Never invent odds or implied probabilities

STRUCTURED RESPONSE FORMAT:
You MUST use this exact structure for all match prediction responses:

---
🏆 **Prediction**
[Outcome]

📊 **Probability**
[Percentage]%

🎯 **Confidence**
[High/Medium/Low]

⚠️ **Risk Level**
[Low/Medium/High]

💰 **Bookmaker Odds Analysis** (if odds available)
| Bookmaker | Market | Odds | Implied Prob | Model Prob | EV |
|-----------|--------|------|-------------|-----------|-----|
| [Stake] | [Market] | [X.XX] | [XX%] | [XX%] | [+X.XX] |
| [Bet365] | [Market] | [X.XX] | [XX%] | [XX%] | [+X.XX] |

💰 **Recommended Markets**
- [Market 1]: [Probability]% - [Risk] - [Best Bookmaker: X.XX]
- [Market 2]: [Probability]% - [Risk] - [Best Bookmaker: X.XX]
- [Market 3]: [Probability]% - [Risk] - [Best Bookmaker: X.XX]

🧠 **Reasoning**
- [Key factor 1]: [Explanation]
- [Key factor 2]: [Explanation]
- [Key factor 3]: [Explanation]

📈 **Advanced Statistics** (expandable)
> [Detailed stats like xG, ELO, form, injuries]

✅ **Summary**
[1-2 sentence summary of the analysis]

---

If bookmaker odds are unavailable, include:
💰 **Bookmaker Odds**
No live bookmaker odds are available for this match.

For multi-match responses (like "best predictions"), use a table format:

| Match | Prediction | Probability | Confidence | Risk | Best Odds | EV |
|-------|------------|-------------|------------|------|-----------|-----|
| [Team A vs Team B] | [Outcome] | [XX]% | [High/Med/Low] | [Low/Med/High] | [X.XX] | [+X.XX] |

Then provide reasoning for each.

For betting slip reviews, use this format:

---
📋 **Betting Slip Review**

**Combined Probability**
[XX]%

**Overall Risk**
[Low/Medium/High/Very High]

**Selection Analysis**
| Selection | Probability | Confidence | Risk | Weak? |
|-----------|-------------|------------|------|-------|
| [Selection 1] | [XX%] | [High/Med/Low] | [Low/Med/High] | [Yes/No] |
| [Selection 2] | [XX%] | [High/Med/Low] | [Low/Med/High] | [Yes/No] |

**Weak Selections**
- [Selection 1]: [Reason]
- [Selection 2]: [Reason]

**Safer Replacements**
- [Original] → [Suggestion]
- [Original] → [Suggestion]

**Recommendation**
[1-2 sentence recommendation]

⚠️ **Disclaimer**
Never guarantee winnings. Remind user that football outcomes are uncertain.

---

RESPONSE STYLE:
- Use emojis for visual appeal (🏆, ⚽, 📊, ✅, ⚠️, 🎯, 💰, 🧠, 📈)
- Structure responses with clear sections using markdown headers
- Use tables for multi-match comparisons
- Use blockquotes (>) for expandable advanced statistics sections
- Be professional yet conversational
- Provide actionable insights based on the tool data
- Keep each section concise - no long paragraphs

EXAMPLE INTERACTIONS:
User: "Where should I bet today?"
→ Call get_best_predictions or get_safe_bets
→ Return structured table with top picks
→ Provide brief reasoning for each

User: "France vs Morocco"
→ Call get_match_prediction with home_team="France", away_team="Morocco"
→ Return structured response with all sections
→ Set conversation context to (France, Morocco)

User: "Why?"
→ Use context (France, Morocco)
→ Call get_match_prediction for France vs Morocco
→ Return structured response focusing on reasoning section

User: "What about BTTS?"
→ Use context (France, Morocco)
→ Call get_match_prediction for France vs Morocco
→ Return structured response with BTTS probability in recommended markets

User: "Is France still the safer bet?"
→ Use context (France, Morocco)
→ Call get_match_prediction for France vs Morocco
→ Return structured response comparing confidence and risk

REMEMBER: For ANY factual football data question, you MUST call a tool first."""
    
    def _build_tools(self) -> List[Dict[str, Any]]:
        """Build tool definitions for OpenRouter function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_todays_matches",
                    "description": "Get today's scheduled matches with basic information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "competition_code": {
                                "type": "string",
                                "description": "Competition code (default: 'WC')",
                                "default": "WC"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of matches to return (default: 30)",
                                "default": 30
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_match_prediction",
                    "description": "Get full prediction for a specific match including probabilities, xG, confidence, and all betting markets. Use this when user asks about a specific match.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "home_team": {
                                "type": "string",
                                "description": "Home team name (e.g., 'France')"
                            },
                            "away_team": {
                                "type": "string",
                                "description": "Away team name (e.g., 'Morocco')"
                            },
                            "competition_code": {
                                "type": "string",
                                "description": "Competition code (default: 'WC')",
                                "default": "WC"
                            }
                        },
                        "required": ["home_team", "away_team"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_team_profile",
                    "description": "Get team profile with statistics, recent form, ELO rating, squad value, injuries, and suspensions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "team_name": {
                                "type": "string",
                                "description": "Team name (e.g., 'France')"
                            }
                        },
                        "required": ["team_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_h2h",
                    "description": "Get head-to-head history between two teams",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "team_a_name": {
                                "type": "string",
                                "description": "First team name"
                            },
                            "team_b_name": {
                                "type": "string",
                                "description": "Second team name"
                            }
                        },
                        "required": ["team_a_name", "team_b_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_best_predictions",
                    "description": "Get today's highest confidence predictions sorted by model confidence",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "competition_code": {
                                "type": "string",
                                "description": "Competition code (default: 'WC')",
                                "default": "WC"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of predictions to return (default: 10)",
                                "default": 10
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_safe_bets",
                    "description": "Get bets with highest confidence (safest selections) - typically above 80% confidence",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "competition_code": {
                                "type": "string",
                                "description": "Competition code (default: 'WC')",
                                "default": "WC"
                            },
                            "min_confidence": {
                                "type": "number",
                                "description": "Minimum confidence threshold (default: 0.8)",
                                "default": 0.8
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of bets to return (default: 10)",
                                "default": 10
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_best_value_bets",
                    "description": "Get bets with best expected value by comparing model probabilities with bookmaker odds",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "competition_code": {
                                "type": "string",
                                "description": "Competition code (default: 'WC')",
                                "default": "WC"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of bets to return (default: 10)",
                                "default": 10
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_live_match",
                    "description": "Get live match data including current score, minute, red cards, possession, shots, and live xG",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "match_id": {
                                "type": "integer",
                                "description": "Match ID from the database"
                            }
                        },
                        "required": ["match_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_bookmaker_odds",
                    "description": "Get bookmaker odds for a specific match from multiple bookmakers (Stake, Pinnacle, Bet365, 1xBet)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "match_id": {
                                "type": "integer",
                                "description": "Match ID from the database"
                            }
                        },
                        "required": ["match_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "review_betting_slip",
                    "description": "Review a betting slip with multiple selections. Analyzes each selection, calculates combined probability, identifies weak selections, and suggests safer replacements.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selections": {
                                "type": "array",
                                "description": "List of betting selections (e.g., ['France Win', 'Spain Over 2.5', 'England BTTS'])",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "text": {
                                            "type": "string",
                                            "description": "Selection text (e.g., 'France Win')"
                                        }
                                    },
                                    "required": ["text"]
                                }
                            }
                        },
                        "required": ["selections"]
                    }
                }
            }
        ]
    
    async def _call_openrouter_with_retry(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Call OpenRouter API with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        self.openrouter_url,
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                    return response.json()
                    
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(f"OpenRouter API HTTP error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if e.response.status_code in [429, 500, 502, 503, 504]:
                    # Retry on rate limit or server errors
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                else:
                    # Don't retry on client errors (4xx except 429)
                    break
                    
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"OpenRouter API timeout (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except httpx.HTTPError as e:
                last_error = e
                logger.error(f"OpenRouter API HTTP error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
        # All retries exhausted
        raise last_error or Exception("OpenRouter API call failed after retries")

    async def chat(
        self,
        user_message: str,
        session_id: str,
        tools_data: Dict[str, Any],
        stream: bool = True
    ) -> Dict[str, Any]:
        """
        Send a message to OpenRouter AI with tool calling support.
        
        Args:
            user_message: User's message
            session_id: Session identifier for conversation memory
            tools_data: Dictionary mapping tool names to their results
            stream: Whether to stream the response
            
        Returns:
            Dictionary with response content and tool calls
        """
        if not self.openrouter_api_key:
            return {
                "error": "AI service not configured",
                "content": "AI service is not available. Please configure OPENROUTER_API_KEY."
            }
        
        memory = self.get_memory(session_id)
        memory.add_message("user", user_message)
        
        # Build messages with system prompt (including context) and conversation history
        messages: List[Message] = [
            {"role": "system", "content": self._build_system_prompt(memory.current_teams)}
        ]
        messages.extend(memory.messages)
        
        # Build tool definitions with actual data
        tools = self._build_tools()
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://offline-prediction.com",
            "X-Title": "OFFLINE AI Football Analyst"
        }
        
        # Prepare payload
        payload = {
            "model": "openrouter/free",  # Use free router
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",  # Let AI decide when to use tools
            "stream": stream  # Enable streaming
        }
        
        try:
            result = await self._call_openrouter_with_retry(payload, headers)
            
            # Process response
            assistant_message = result["choices"][0]["message"]
            
            # Check if AI wants to call tools
            tool_calls = assistant_message.get("tool_calls", [])
            
            if tool_calls:
                # AI wants to call tools - extract match context if applicable
                self._extract_match_context_from_tool_calls(tool_calls, memory)
                
                # AI wants to call tools - return the tool calls
                memory.add_message("assistant", assistant_message.get("content", ""))
                
                return {
                    "content": assistant_message.get("content", ""),
                    "tool_calls": tool_calls,
                    "requires_action": True
                }
            else:
                # AI provided final answer
                content = assistant_message.get("content", "")
                memory.add_message("assistant", content)
                
                return {
                    "content": content,
                    "tool_calls": [],
                    "requires_action": False
                }
                
        except Exception as e:
            logger.error(f"OpenRouter AI service error: {e}", exc_info=True)
            return {
                "error": "AI service error",
                "content": "I encountered an error connecting to the AI service. Please try again."
            }
    
    def _extract_match_context_from_tool_calls(self, tool_calls: List[Dict], memory: ConversationMemory):
        """Extract match context from tool calls to maintain conversation state."""
        for tool_call in tool_calls:
            function_name = tool_call.get("function", {}).get("name")
            arguments = tool_call.get("function", {}).get("arguments", "{}")
            
            try:
                args = json.loads(arguments)
                
                # If the AI is calling get_match_prediction, extract the teams
                if function_name == "get_match_prediction":
                    home_team = args.get("home_team")
                    away_team = args.get("away_team")
                    if home_team and away_team:
                        memory.set_match_context(None, (home_team, away_team))
                        logger.info(f"Set conversation context to: {home_team} vs {away_team}")
                
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse tool arguments: {arguments}")
    
    async def submit_tool_results(
        self,
        session_id: str,
        tool_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Submit tool execution results back to AI for final response.
        
        Args:
            session_id: Session identifier
            tool_results: List of tool execution results
            
        Returns:
            Final AI response with analysis
        """
        if not self.openrouter_api_key:
            return {
                "error": "AI service not configured",
                "content": "AI service is not available."
            }
        
        memory = self.get_memory(session_id)
        
        # Build messages
        messages: List[Message] = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        messages.extend(memory.messages)
        
        # Add tool results
        for result in tool_results:
            messages.append({
                "role": "tool",
                "tool_call_id": result["tool_call_id"],
                "content": json.dumps(result["content"])
            })
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://offline-prediction.com",
            "X-Title": "OFFLINE AI Football Analyst"
        }
        
        # Prepare payload
        payload = {
            "model": "openrouter/free",
            "messages": messages
        }
        
        try:
            result = await self._call_openrouter_with_retry(payload, headers)
            
            # Get final response
            assistant_message = result["choices"][0]["message"]
            content = assistant_message.get("content", "")
            
            memory.add_message("assistant", content)
            
            return {
                "content": content,
                "requires_action": False
            }
            
        except Exception as e:
            logger.error(f"OpenRouter AI service error in submit_tool_results: {e}", exc_info=True)
            return {
                "error": "AI service error",
                "content": "I encountered an error processing the tool results. Please try again."
            }


# Singleton instance
ai_service = AIService()
