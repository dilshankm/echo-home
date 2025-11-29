"""Agent 2: GraphRAG Retriever - THE CORE INNOVATION!

Intelligent graph traversal with vector similarity.
This is what makes this GraphRAG vs simple RAG.
"""

from typing import Dict, Any, List, Optional
import logging

from app.vector.graphrag_search import GraphRAGSearch
from app.graph.mock_neo4j import MockNeo4j
from app.graph.sample_data import HOUSE_TYPES

logger = logging.getLogger(__name__)


class GraphRAGRetriever:
    """GraphRAG retriever agent - combines vector search with graph traversal."""
    
    def __init__(self, graph: MockNeo4j, graphrag_search: GraphRAGSearch):
        """Initialize retriever with graph and search engine.
        
        Args:
            graph: MockNeo4j graph instance
            graphrag_search: GraphRAGSearch instance
        """
        self.graph = graph
        self.graphrag_search = graphrag_search
    
    def retrieve(
        self,
        query_context: Dict[str, Any],
        original_query: str
    ) -> Dict[str, Any]:
        """Retrieve relevant information using GraphRAG.
        
        Process:
        1. Vector Similarity Search
        2. Graph Traversal (2-3 hops)
        3. Context Enrichment
        4. Personalization based on house type
        
        Args:
            query_context: Output from Agent 1 (Query Analyzer)
            original_query: Original user query
        
        Returns:
            Enriched retrieval result
        """
        # Build enhanced query with context
        enhanced_query = self._build_enhanced_query(query_context, original_query)
        
        # STEP 1-4: Full GraphRAG retrieval
        graphrag_result = self.graphrag_search.retrieve_subgraph(
            enhanced_query,
            k=5
        )
        
        # STEP 5: Personalization
        personalized_tips = self._personalize_tips(
            graphrag_result["subgraph"],
            query_context.get("entities", {})
        )
        
        # STEP 6: Context Enrichment
        matched_nodes = graphrag_result.get("top_nodes", [])
        context_text = self._build_enriched_context(
            matched_nodes,
            graphrag_result,
            query_context,
            personalized_tips
        )
        
        return {
            "matched_nodes": matched_nodes,
            "subgraph": graphrag_result["subgraph"],
            "personalized_tips": personalized_tips,
            "graph_paths": graphrag_result["paths"],
            "context": context_text,
            "explanation": graphrag_result["explanation"]
        }
    
    def _build_enhanced_query(
        self,
        query_context: Dict[str, Any],
        original_query: str
    ) -> str:
        """Build enhanced query with extracted entities."""
        parts = [original_query]
        
        entities = query_context.get("entities", {})
        
        if entities.get("category"):
            parts.append(f"energy category: {entities['category']}")
        
        if entities.get("house_type"):
            parts.append(f"house type: {entities['house_type']}")
        
        if entities.get("problem"):
            parts.append(f"problem: {entities['problem']}")
        
        return " ".join(parts)
    
    def _personalize_tips(
        self,
        subgraph: Dict[str, Any],
        entities: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Personalize tips based on user's house type and context."""
        house_type_name = entities.get("house_type")
        
        # Get house type factor
        house_type_data = None
        if house_type_name:
            for ht in HOUSE_TYPES:
                if ht["type"] == house_type_name:
                    house_type_data = ht
                    break
        
        personalized_tips = []
        
        # Extract tips from subgraph
        tip_nodes = [
            node for node in subgraph.get("nodes", [])
            if node.get("label") == "Tip"
        ]
        
        for tip_node in tip_nodes:
            tip = {
                "id": tip_node.get("id"),
                "action": tip_node.get("action"),
                "description": tip_node.get("description"),
                "savings_gbp": tip_node.get("savings_gbp", 0),
                "savings_co2": tip_node.get("savings_co2", 0),
                "difficulty": tip_node.get("difficulty"),
                "category": tip_node.get("category")
            }
            
            # Adjust savings based on house type
            if house_type_data and tip["category"] == "heating":
                factor = house_type_data.get("heating_kwh_factor", 1.0)
                tip["personalized_savings_gbp"] = int(tip["savings_gbp"] * factor)
                tip["personalized_savings_co2"] = int(tip["savings_co2"] * factor)
            else:
                tip["personalized_savings_gbp"] = tip["savings_gbp"]
                tip["personalized_savings_co2"] = tip["savings_co2"]
            
            # Calculate ROI (savings / difficulty score)
            difficulty_scores = {"easy": 1, "medium": 2, "hard": 3}
            difficulty_score = difficulty_scores.get(tip["difficulty"], 2)
            tip["roi"] = tip["personalized_savings_gbp"] / difficulty_score
            
            personalized_tips.append(tip)
        
        # Sort by ROI (highest first)
        personalized_tips.sort(key=lambda x: x["roi"], reverse=True)
        
        return personalized_tips
    
    def _build_enriched_context(
        self,
        matched_nodes: List[Dict[str, Any]],
        graphrag_result: Dict[str, Any],
        query_context: Dict[str, Any],
        personalized_tips: List[Dict[str, Any]]
    ) -> str:
        """Build enriched context text for LLM."""
        parts = []
        
        entities = query_context.get("entities", {})
        
        parts.append("Graph analysis results:")
        
        # Add matched category info
        category_nodes = [
            node for node in matched_nodes
            if node.get("label") == "Category"
        ]
        
        if category_nodes:
            for cat_node in category_nodes[:1]:  # Top category
                name = cat_node.get("name", "")
                kwh = cat_node.get("kwh_per_home", 0)
                pct = cat_node.get("percentage", 0)
                fuel = cat_node.get("fuel_type", "")
                parts.append(
                    f"- Matched category: {name} ({kwh} kWh/year avg, {pct}% of home energy)"
                )
                parts.append(f"- Fuel type: {fuel}")
        
        # Add house type context
        if entities.get("house_type"):
            house_type_name = entities["house_type"]
            parts.append(f"- User's house type: {house_type_name}")
            
            # Get house type info
            for ht in HOUSE_TYPES:
                if ht["type"] == house_type_name:
                    parts.append(
                        f"  Typical size: {ht['avg_size_sqm']} sqm, "
                        f"occupants: {ht['typical_occupants']}"
                    )
                    if ht.get("heating_kwh_factor"):
                        avg_heating = 744 * ht["heating_kwh_factor"]
                        parts.append(
                            f"  Typical heating consumption: {avg_heating:.0f} kWh/year "
                            f"(vs UK average 744 kWh/year)"
                        )
                    break
        
        # Add tips
        if personalized_tips:
            parts.append(f"\nConnected tips ({len(personalized_tips)}):")
            for tip in personalized_tips[:5]:  # Top 5
                parts.append(
                    f"- {tip['action']}: "
                    f"£{tip['personalized_savings_gbp']}/year, "
                    f"{tip['personalized_savings_co2']} kg CO2/year, "
                    f"difficulty: {tip['difficulty']}"
                )
        
        # Add graph path explanation
        if graphrag_result.get("paths"):
            parts.append(f"\nGraph path: Discovered {len(graphrag_result['paths'])} connections between concepts.")
        
        return "\n".join(parts)

