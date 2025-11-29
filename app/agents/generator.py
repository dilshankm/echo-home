"""Agent 3: Response Generator - Generate natural language using ChatGPT."""

from typing import Dict, Any, List
import logging
import openai

from app.config import config

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Generates personalized responses using ChatGPT."""
    
    def __init__(self):
        """Initialize with OpenAI client."""
        if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "sk-your-key-here":
            raise ValueError("OPENAI_API_KEY not set in environment. Please set it in .env file")
        
        try:
            # Initialize OpenAI client (v1.x API style) without proxies
            self.client = openai.OpenAI(
                api_key=config.OPENAI_API_KEY,
                timeout=30.0,
                max_retries=3
            )
            self.model = config.LLM_MODEL
            logger.info(f"OpenAI client initialized with model: {self.model}")
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {e}")
    
    def generate(
        self,
        original_query: str,
        query_context: Dict[str, Any],
        retrieval_result: Dict[str, Any]
    ) -> str:
        """Generate natural language response.
        
        Args:
            original_query: Original user query
            query_context: Output from Agent 1
            retrieval_result: Output from Agent 2
        
        Returns:
            Natural language response
        """
        # Build prompt
        prompt = self._build_prompt(
            original_query,
            query_context,
            retrieval_result
        )
        
        try:
            # Call ChatGPT (openai v1.x API style)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.MAX_TOKENS
            )
            
            generated_text = response.choices[0].message.content
            
            logger.info(f"Generated response ({len(generated_text)} chars)")
            
            return generated_text
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._fallback_response(retrieval_result)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for ChatGPT."""
        return """You are an expert energy efficiency coach for UK homes. 
You provide personalized, actionable advice based on official UK ECUK 2025 government data.
Your responses should be:
- Specific with actual £/year and kg CO2 savings
- Personalized to the user's house type
- Prioritized by impact (high/medium/low)
- Include difficulty ratings
- Cite data sources (ECUK 2025)
- Friendly and encouraging

Format recommendations with emojis and clear sections."""
    
    def _build_prompt(
        self,
        original_query: str,
        query_context: Dict[str, Any],
        retrieval_result: Dict[str, Any]
    ) -> str:
        """Build prompt for ChatGPT."""
        parts = []
        
        parts.append(f"User Query: {original_query}\n")
        
        # Add context
        entities = query_context.get("entities", {})
        if entities:
            parts.append("User Context:")
            if entities.get("house_type"):
                parts.append(f"- House type: {entities['house_type']}")
            if entities.get("bedrooms"):
                parts.append(f"- Bedrooms: {entities['bedrooms']}")
            if entities.get("category"):
                parts.append(f"- Energy category of interest: {entities['category']}")
            parts.append("")
        
        # Add graph analysis results
        parts.append("Graph Analysis Results:")
        parts.append(retrieval_result.get("context", ""))
        parts.append("")
        
        # Add personalized tips
        tips = retrieval_result.get("personalized_tips", [])
        if tips:
            parts.append("Personalized Recommendations (from graph):")
            for i, tip in enumerate(tips[:5], 1):  # Top 5
                parts.append(
                    f"{i}. {tip['action']} - "
                    f"Saves £{tip['personalized_savings_gbp']}/year, "
                    f"{tip['personalized_savings_co2']} kg CO2/year, "
                    f"Difficulty: {tip['difficulty']}, "
                    f"Category: {tip['category']}"
                )
            parts.append("")
        
        parts.append(
            "Generate a personalized, friendly response with specific recommendations. "
            "Include percentages vs UK average, specific savings, and prioritize by impact. "
            "Use emojis and clear formatting."
        )
        
        return "\n".join(parts)
    
    def _fallback_response(self, retrieval_result: Dict[str, Any]) -> str:
        """Fallback response if ChatGPT fails."""
        tips = retrieval_result.get("personalized_tips", [])
        
        if not tips:
            return (
                "I apologize, but I couldn't generate recommendations at this time. "
                "Please try rephrasing your question."
            )
        
        response_parts = [
            "Based on UK ECUK 2025 data, here are personalized recommendations:\n"
        ]
        
        for i, tip in enumerate(tips[:5], 1):
            impact = "HIGH" if tip["personalized_savings_gbp"] > 50 else "MEDIUM" if tip["personalized_savings_gbp"] > 20 else "LOW"
            response_parts.append(
                f"{i}. {tip['action']}\n"
                f"   Saves: £{tip['personalized_savings_gbp']}/year, "
                f"{tip['personalized_savings_co2']} kg CO2/year\n"
                f"   Difficulty: {tip['difficulty']}, Impact: {impact}"
            )
        
        return "\n".join(response_parts)

