"""Simple workflow orchestrator for multi-agent system (compatible with Python 3.8)."""

from typing import Dict, Any, List
import logging

from app.agents.analyzer import QueryAnalyzer
from app.agents.retriever import GraphRAGRetriever
from app.agents.generator import ResponseGenerator

logger = logging.getLogger(__name__)


class GraphRAGState:
    """State passed between agents in workflow."""
    def __init__(self):
        self.user_query: str = ""
        self.extracted_entities: Dict[str, Any] = {}
        self.intent: str = ""
        self.urgency: str = "medium"
        self.matched_nodes: List[Dict[str, Any]] = []
        self.subgraph: Dict[str, Any] = {}
        self.graph_paths: List[List[str]] = []
        self.personalized_tips: List[Dict[str, Any]] = []
        self.context: str = ""
        self.explanation: str = ""
        self.final_response: str = ""


class GraphRAGWorkflow:
    """Simple workflow orchestrating the 3-agent system (no LangGraph dependency)."""
    
    def __init__(
        self,
        analyzer: QueryAnalyzer,
        retriever: GraphRAGRetriever,
        generator: ResponseGenerator
    ):
        """Initialize workflow with agents.
        
        Args:
            analyzer: Agent 1 - Query Analyzer
            retriever: Agent 2 - GraphRAG Retriever
            generator: Agent 3 - Response Generator
        """
        self.analyzer = analyzer
        self.retriever = retriever
        self.generator = generator
    
    async def run(self, user_message: str) -> Dict[str, Any]:
        """Run workflow on user message.
        
        Args:
            user_message: User query
        
        Returns:
            Final state with response
        """
        state = GraphRAGState()
        state.user_query = user_message
        
        # Agent 1: Query Analyzer
        logger.info("Running Agent 1: Query Analyzer")
        query_context = self.analyzer.analyze(state.user_query)
        state.extracted_entities = query_context.get("entities", {})
        state.intent = query_context.get("intent", "general_advice")
        state.urgency = query_context.get("urgency", "medium")
        
        # Agent 2: GraphRAG Retriever
        logger.info("Running Agent 2: GraphRAG Retriever")
        query_ctx = {
            "entities": state.extracted_entities,
            "intent": state.intent,
            "urgency": state.urgency
        }
        retrieval_result = self.retriever.retrieve(query_ctx, state.user_query)
        state.matched_nodes = retrieval_result.get("matched_nodes", [])
        state.subgraph = retrieval_result.get("subgraph", {})
        state.graph_paths = retrieval_result.get("graph_paths", [])
        state.personalized_tips = retrieval_result.get("personalized_tips", [])
        state.context = retrieval_result.get("context", "")
        state.explanation = retrieval_result.get("explanation", "")
        
        # Agent 3: Response Generator
        logger.info("Running Agent 3: Response Generator")
        query_ctx = {
            "entities": state.extracted_entities,
            "intent": state.intent,
            "urgency": state.urgency
        }
        retrieval_ctx = {
            "matched_nodes": state.matched_nodes,
            "subgraph": state.subgraph,
            "graph_paths": state.graph_paths,
            "personalized_tips": state.personalized_tips,
            "context": state.context,
            "explanation": state.explanation
        }
        state.final_response = self.generator.generate(
            state.user_query,
            query_ctx,
            retrieval_ctx
        )
        
        # Return as dictionary
        return {
            "user_query": state.user_query,
            "extracted_entities": state.extracted_entities,
            "intent": state.intent,
            "urgency": state.urgency,
            "matched_nodes": state.matched_nodes,
            "subgraph": state.subgraph,
            "graph_paths": state.graph_paths,
            "personalized_tips": state.personalized_tips,
            "context": state.context,
            "explanation": state.explanation,
            "final_response": state.final_response
        }
    
    async def run_with_explanation(self, user_message: str) -> Dict[str, Any]:
        """Run workflow and include explanation of graph traversal.
        
        Args:
            user_message: User query
        
        Returns:
            Final state with response and explanation
        """
        result = await self.run(user_message)
        
        # Add detailed explanation
        explanation = {
            "query_analysis": {
                "entities": result.get("extracted_entities", {}),
                "intent": result.get("intent"),
                "urgency": result.get("urgency")
            },
            "graph_traversal": {
                "matched_nodes_count": len(result.get("matched_nodes", [])),
                "subgraph_nodes": len(result.get("subgraph", {}).get("nodes", [])),
                "paths_found": len(result.get("graph_paths", [])),
                "explanation": result.get("explanation", "")
            },
            "tips_retrieved": len(result.get("personalized_tips", []))
        }
        
        result["detailed_explanation"] = explanation
        
        return result
