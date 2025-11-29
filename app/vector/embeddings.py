"""Vector embeddings using Sentence Transformers."""

import numpy as np
from typing import List, Dict, Any, Optional
import logging
from sentence_transformers import SentenceTransformer

from app.config import config

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Manages sentence transformer embeddings."""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingModel, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
            self._model = SentenceTransformer(config.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")
    
    @property
    def model(self) -> SentenceTransformer:
        """Get the embedding model."""
        return self._model
    
    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        return self._model.encode(text, convert_to_numpy=True)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts."""
        return self._model.encode(texts, convert_to_numpy=True)


def get_embedding_model() -> EmbeddingModel:
    """Get singleton embedding model instance."""
    return EmbeddingModel()


def create_node_embedding_text(node: Dict[str, Any], graph_context: Optional[str] = None) -> str:
    """Create rich text representation of node for embedding.
    
    Includes node properties and graph context (connected nodes).
    This creates graph-enhanced embeddings.
    
    Args:
        node: Node dictionary with id, label, and properties
        graph_context: Optional additional context from graph relationships
    
    Returns:
        Text representation for embedding
    """
    parts = []
    
    # Add node type and basic info
    label = node.get("label", "Node")
    node_id = node.get("id", "")
    
    if label == "Category":
        name = node.get("name", "")
        kwh = node.get("kwh_per_home", 0)
        pct = node.get("percentage", 0)
        fuel = node.get("fuel_type", "")
        parts.append(
            f"Energy category: {name}. "
            f"Consumes {kwh} kWh per home annually ({pct}% of total). "
            f"Uses fuel type: {fuel}."
        )
    
    elif label == "FuelType":
        name = node.get("name", "")
        rate = node.get("rate_gbp_kwh", 0)
        co2 = node.get("co2_kg_kwh", 0)
        parts.append(
            f"Fuel type: {name}. "
            f"Rate: £{rate:.2f}/kWh. "
            f"CO2 emissions: {co2} kg CO2/kWh."
        )
    
    elif label == "Tip":
        action = node.get("action", "")
        desc = node.get("description", "")
        savings_gbp = node.get("savings_gbp", 0)
        savings_co2 = node.get("savings_co2", 0)
        difficulty = node.get("difficulty", "")
        category = node.get("category", "")
        parts.append(
            f"Energy saving tip: {action}. "
            f"{desc} "
            f"Saves £{savings_gbp}/year and {savings_co2} kg CO2/year. "
            f"Difficulty: {difficulty}. "
            f"Improves category: {category}."
        )
    
    elif label == "HouseType":
        house_type = node.get("type", "")
        size = node.get("avg_size_sqm", 0)
        occupants = node.get("typical_occupants", 0)
        parts.append(
            f"House type: {house_type}. "
            f"Average size: {size} sqm. "
            f"Typical occupants: {occupants}."
        )
    
    # Add graph context if provided
    if graph_context:
        parts.append(f"Graph context: {graph_context}")
    
    return " ".join(parts)

