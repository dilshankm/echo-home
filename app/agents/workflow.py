"""LangGraph-based multi-agent workflow orchestrator."""

from __future__ import annotations
from typing import TypedDict, Dict, Any, List, Annotated
import logging

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None

from app.agents.analyzer import QueryAnalyzer
from app.agents.retriever import GraphRAGRetriever
from app.agents.generator import ResponseGenerator

logger = logging.getLogger(__name__)


class GraphRAGState(TypedDict):
    """State passed between agents in LangGraph workflow."""
    user_query: str
    extracted_entities: Dict[str, Any]
    intent: str
    urgency: str
    matched_nodes: List[Dict[str, Any]]
    subgraph: Dict[str, Any]
    graph_paths: List[List[str]]
    personalized_tips: List[Dict[str, Any]]
    context: str
    explanation: str
    final_response: str


class GraphRAGWorkflow:
    """Multi-agent workflow orchestrated with LangGraph."""
    
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
        
        # Build LangGraph workflow if available
        if LANGGRAPH_AVAILABLE:
            self.graph = self._build_workflow()
        else:
            logger.warning("LangGraph not available, using simple sequential workflow")
            self.graph = None
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow with 3 agents.
        
        Flow: analyze -> retrieve -> generate -> END
        """
        workflow = StateGraph(GraphRAGState)
        
        # Add nodes (agents)
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("generate", self._generate_node)
        
        # Define edges
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        
        # Compile workflow
        return workflow.compile()
    
    def _analyze_node(self, state: GraphRAGState) -> GraphRAGState:
        """Agent 1: Query Analyzer node."""
        logger.info("🔍 Agent 1: Analyzing query...")
        
        query_context = self.analyzer.analyze(state["user_query"])
        
        state["extracted_entities"] = query_context.get("entities", {})
        state["intent"] = query_context.get("intent", "general_advice")
        state["urgency"] = query_context.get("urgency", "medium")
        
        logger.info(f"   Intent: {state['intent']}, Entities: {list(state['extracted_entities'].keys())}")
        return state
    
    def _retrieve_node(self, state: GraphRAGState) -> GraphRAGState:
        """Agent 2: GraphRAG Retriever node."""
        logger.info("🔎 Agent 2: Retrieving with GraphRAG...")
        
        query_ctx = {
            "entities": state["extracted_entities"],
            "intent": state["intent"],
            "urgency": state["urgency"]
        }
        
        retrieval_result = self.retriever.retrieve(query_ctx, state["user_query"])
        
        state["matched_nodes"] = retrieval_result.get("matched_nodes", [])
        state["subgraph"] = retrieval_result.get("subgraph", {})
        state["graph_paths"] = retrieval_result.get("graph_paths", [])
        state["personalized_tips"] = retrieval_result.get("personalized_tips", [])
        state["context"] = retrieval_result.get("context", "")
        state["explanation"] = retrieval_result.get("explanation", "")
        
        logger.info(f"   Matched {len(state['matched_nodes'])} nodes, {len(state['graph_paths'])} paths")
        return state
    
    def _generate_node(self, state: GraphRAGState) -> GraphRAGState:
        """Agent 3: Response Generator node."""
        logger.info("✨ Agent 3: Generating response...")
        
        query_ctx = {
            "entities": state["extracted_entities"],
            "intent": state["intent"],
            "urgency": state["urgency"]
        }
        
        retrieval_ctx = {
            "matched_nodes": state["matched_nodes"],
            "subgraph": state["subgraph"],
            "graph_paths": state["graph_paths"],
            "personalized_tips": state["personalized_tips"],
            "context": state["context"],
            "explanation": state["explanation"]
        }
        
        state["final_response"] = self.generator.generate(
            state["user_query"],
            query_ctx,
            retrieval_ctx
        )
        
        logger.info("   Response generated successfully")
        return state
    
    async def run(self, user_message: str) -> Dict[str, Any]:
        """Run LangGraph workflow on user message.
        
        Args:
            user_message: User query
        
        Returns:
            Final state with response
        """
        # Initial state
        initial_state: GraphRAGState = {
            "user_query": user_message,
            "extracted_entities": {},
            "intent": "general_advice",
            "urgency": "medium",
            "matched_nodes": [],
            "subgraph": {},
            "graph_paths": [],
            "personalized_tips": [],
            "context": "",
            "explanation": "",
            "final_response": ""
        }
        
        if self.graph:
            # Use LangGraph workflow
            logger.info("🚀 Running LangGraph workflow...")
            result = await self.graph.ainvoke(initial_state)
        else:
            # Fallback to simple sequential workflow
            logger.info("🔄 Running simple sequential workflow (LangGraph not available)...")
            result = await self._run_simple(initial_state)
        
        # Return as dictionary
        return {
            "user_query": result["user_query"],
            "extracted_entities": result["extracted_entities"],
            "intent": result["intent"],
            "urgency": result["urgency"],
            "matched_nodes": result["matched_nodes"],
            "subgraph": result["subgraph"],
            "graph_paths": result["graph_paths"],
            "personalized_tips": result["personalized_tips"],
            "context": result["context"],
            "explanation": result["explanation"],
            "final_response": result["final_response"]
        }
    
    async def _run_simple(self, state: GraphRAGState) -> GraphRAGState:
        """Simple sequential workflow fallback (if LangGraph not available)."""
        state = self._analyze_node(state)
        state = self._retrieve_node(state)
        state = self._generate_node(state)
        return state
    
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
            "workflow_type": "LangGraph" if self.graph else "Sequential",
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
