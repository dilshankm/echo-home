"""Agent 1: Query Analyzer - Extract intent and entities from user query.

Uses pattern matching + basic NER (NO LLM - saves API calls!).
Target: <100ms response time.
"""

import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Extracts entities and intent from user queries using pattern matching."""
    
    # Patterns for entity extraction
    HOUSE_TYPE_PATTERNS = {
        "flat": ["flat", "apartment", "studio"],
        "terraced": ["terraced", "row house", "townhouse"],
        "semi_detached": ["semi-detached", "semi detached", "semi"],
        "detached": ["detached", "house"]
    }
    
    CATEGORY_PATTERNS = {
        "heating": ["heating", "heat", "thermostat", "warm", "cold", "central heating"],
        "lighting": ["light", "lighting", "bulb", "lamp", "lights"],
        "appliances": ["appliance", "fridge", "freezer", "washing machine", "dishwasher", "dryer"],
        "water": ["water", "hot water", "shower", "bath", "tap", "boiler"],
        "cooking": ["cooking", "cook", "oven", "hob", "stove", "kettle"]
    }
    
    INTENT_PATTERNS = {
        "cost_reduction": ["reduce", "lower", "save", "cut", "cheaper", "bills", "cost", "money"],
        "environmental": ["co2", "carbon", "emission", "environment", "green", "eco"],
        "quick_wins": ["quick", "easy", "fast", "simple", "quick wins"],
        "upgrade": ["upgrade", "replace", "new", "install", "buy"],
        "general_advice": ["tips", "advice", "recommend", "help", "suggest"]
    }
    
    PROBLEM_PATTERNS = {
        "high_bills": ["high", "expensive", "too much", "costing", "bill", "spending"],
        "inefficient": ["inefficient", "waste", "wasting", "too much energy"],
        "old_equipment": ["old", "aging", "broken", "needs replacing"]
    }
    
    BEDROOM_PATTERNS = [
        r"(\d+)\s*-?\s*bed",
        r"bedroom[s]?\s*(\d+)",
        r"(\d+)\s*bedroom"
    ]
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """Analyze user query and extract entities, intent, and urgency.
        
        Args:
            query: User query text
        
        Returns:
            Structured query context
        """
        query_lower = query.lower()
        
        # Extract entities
        entities = {}
        
        # House type
        entities["house_type"] = self._extract_house_type(query_lower)
        
        # Bedrooms
        entities["bedrooms"] = self._extract_bedrooms(query_lower)
        
        # Category
        entities["category"] = self._extract_category(query_lower)
        
        # Problem
        entities["problem"] = self._extract_problem(query_lower)
        
        # Intent
        intent = self._extract_intent(query_lower)
        
        # Urgency (based on problem mentions)
        urgency = "medium"
        if entities.get("problem") in ["high_bills", "inefficient"]:
            urgency = "high"
        elif any(word in query_lower for word in ["quick", "fast", "urgent"]):
            urgency = "high"
        
        result = {
            "entities": entities,
            "intent": intent,
            "urgency": urgency,
            "original_query": query
        }
        
        logger.info(f"Query analyzed: intent={intent}, entities={entities}")
        
        return result
    
    def _extract_house_type(self, query: str) -> str:
        """Extract house type from query."""
        for house_type, patterns in self.HOUSE_TYPE_PATTERNS.items():
            if any(pattern in query for pattern in patterns):
                return house_type
        return None
    
    def _extract_bedrooms(self, query: str) -> int:
        """Extract number of bedrooms."""
        for pattern in self.BEDROOM_PATTERNS:
            match = re.search(pattern, query)
            if match:
                try:
                    return int(match.group(1))
                except:
                    pass
        return None
    
    def _extract_category(self, query: str) -> str:
        """Extract energy category."""
        matches = []
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if pattern in query:
                    matches.append(category)
                    break
        
        if matches:
            # Return first match (could be enhanced to return all)
            return matches[0]
        return None
    
    def _extract_problem(self, query: str) -> str:
        """Extract problem type."""
        for problem, patterns in self.PROBLEM_PATTERNS.items():
            if any(pattern in query for pattern in patterns):
                return problem
        return None
    
    def _extract_intent(self, query: str) -> str:
        """Extract user intent."""
        scores = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = sum(1 for pattern in patterns if pattern in query)
            if score > 0:
                scores[intent] = score
        
        if scores:
            # Return intent with highest score
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return "general_advice"  # Default intent

