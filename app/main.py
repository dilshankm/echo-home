"""FastAPI application for Energy Coach GraphRAG system."""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import config
from app.graph.mock_neo4j import MockNeo4j
try:
    from app.graph.neo4j_connector import Neo4jConnector
    NEO4J_CONNECTOR_AVAILABLE = True
except ImportError:
    NEO4J_CONNECTOR_AVAILABLE = False
from app.vector.graphrag_search import GraphRAGSearch
from app.agents.analyzer import QueryAnalyzer
from app.agents.retriever import GraphRAGRetriever
from app.agents.generator import ResponseGenerator
from app.agents.workflow import GraphRAGWorkflow
from app.models.schemas import (
    ChatRequest, ChatResponse,
    AnalysisRequest, AnalysisResponse,
    GraphStatsResponse, HealthResponse
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances (initialized in lifespan)
graph: MockNeo4j = None
graphrag_search: GraphRAGSearch = None
workflow: GraphRAGWorkflow = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources."""
    global graph, graphrag_search, workflow
    
    logger.info("Starting Energy Coach GraphRAG application...")
    logger.info(f"Using mock Neo4j: {config.USE_MOCK_NEO4J}")
    
    # Initialize graph - switch between mock and real Neo4j
    if config.USE_MOCK_NEO4J:
        logger.info("Using MockNeo4j (NetworkX) for development")
        graph = MockNeo4j()
    else:
        if not NEO4J_CONNECTOR_AVAILABLE:
            logger.error("Neo4j connector not available. Install neo4j package or set USE_MOCK_NEO4J=true")
            raise ImportError("Neo4j connector requires neo4j package. Install with: pip install neo4j")
        
        if not config.NEO4J_URI:
            logger.error("NEO4J_URI not set in environment. Please set it in .env file")
            raise ValueError("NEO4J_URI required when USE_MOCK_NEO4J=false")
        
        logger.info(f"Connecting to Neo4j at {config.NEO4J_URI}")
        try:
            graph = Neo4jConnector(
                uri=config.NEO4J_URI,
                user=config.NEO4J_USER or "neo4j",
                password=config.NEO4J_PASSWORD or ""
            )
        except Exception as e:
            logger.error(f"❌ CRITICAL: Failed to connect to Neo4j: {e}")
            logger.error("❌ Cannot proceed without Neo4j connection. Check credentials and network.")
            raise
    
    logger.info("Graph loaded successfully")
    
    # Initialize GraphRAG search (this builds the FAISS index)
    logger.info("Building vector index...")
    graphrag_search = GraphRAGSearch(graph)
    logger.info("Vector index built successfully")
    
    # Initialize agents
    analyzer = QueryAnalyzer()
    retriever = GraphRAGRetriever(graph, graphrag_search)
    generator = ResponseGenerator()
    
    # Initialize workflow
    workflow = GraphRAGWorkflow(analyzer, retriever, generator)
    logger.info("Workflow initialized successfully")
    
    logger.info("Application ready!")
    
    yield
    
    # Cleanup (if needed)
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="Energy Coach GraphRAG API",
    description="AI-powered home energy coach using GraphRAG",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint - returns personalized recommendations via GraphRAG.
    
    Args:
        request: Chat request with user message
    
    Returns:
        Chat response with personalized recommendations
    """
    try:
        if not workflow:
            raise HTTPException(status_code=503, detail="Workflow not initialized")
        
        # Run workflow
        result = await workflow.run(request.message)
        
        return ChatResponse(
            response=result.get("final_response", "I couldn't generate a response."),
            query_context={
                "entities": result.get("extracted_entities", {}),
                "intent": result.get("intent"),
                "urgency": result.get("urgency")
            }
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """Analysis endpoint - shows graph traversal details.
    
    Useful for debugging and demo visualization.
    
    Args:
        request: Analysis request with user message
    
    Returns:
        Analysis response with graph traversal explanation
    """
    try:
        if not workflow:
            raise HTTPException(status_code=503, detail="Workflow not initialized")
        
        # Run workflow with explanation
        result = await workflow.run_with_explanation(request.message)
        
        return AnalysisResponse(
            response=result.get("final_response", "I couldn't generate a response."),
            explanation=result.get("detailed_explanation", {}),
            matched_nodes=result.get("matched_nodes", [])[:10],  # Limit to 10
            graph_paths=result.get("graph_paths", [])[:10]  # Limit to 10
        )
    
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/graph/stats", response_model=GraphStatsResponse)
async def graph_stats():
    """Get graph statistics.
    
    Returns:
        Graph statistics including node count, edge count, categories
    """
    try:
        if not graph:
            raise HTTPException(status_code=503, detail="Graph not initialized")
        
        stats = graph.get_statistics()
        
        return GraphStatsResponse(
            total_nodes=stats["total_nodes"],
            total_edges=stats["total_edges"],
            node_labels=stats["node_labels"],
            relationship_types=stats["relationship_types"],
            mode="mock_neo4j" if config.USE_MOCK_NEO4J else "neo4j"
        )
    
    except Exception as e:
        logger.error(f"Error in graph_stats endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """System health check.
    
    Returns:
        Health status and configuration
    """
    return HealthResponse(
        status="healthy",
        mode="mock_neo4j" if config.USE_MOCK_NEO4J else "neo4j"
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Energy Coach GraphRAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

