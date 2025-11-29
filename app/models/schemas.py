"""Pydantic models for API requests and responses."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User query message")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Generated response")
    query_context: Optional[Dict[str, Any]] = Field(None, description="Query analysis context")


class AnalysisRequest(BaseModel):
    """Request model for analysis endpoint."""
    message: str = Field(..., description="User query message")


class AnalysisResponse(BaseModel):
    """Response model for analysis endpoint with graph traversal details."""
    response: str = Field(..., description="Generated response")
    explanation: Dict[str, Any] = Field(..., description="Graph traversal explanation")
    matched_nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Matched graph nodes")
    graph_paths: List[List[str]] = Field(default_factory=list, description="Graph paths found")


class GraphStatsResponse(BaseModel):
    """Response model for graph statistics."""
    total_nodes: int
    total_edges: int
    node_labels: Dict[str, int]
    relationship_types: Dict[str, int]
    mode: str = Field(..., description="Graph mode (mock_neo4j or neo4j)")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    mode: str = Field(..., description="Graph mode")

