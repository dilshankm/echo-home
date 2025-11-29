"""Vector embeddings using OpenAI API (no PyTorch needed!)."""

import numpy as np
from typing import List, Dict, Any, Optional
import logging
import openai
from app.config import config

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Manages OpenAI embeddings (no local model needed)."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingModel, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set - required for embeddings")
        try:
            # Initialize OpenAI client without proxies to avoid compatibility issues
            self.client = openai.OpenAI(
                api_key=config.OPENAI_API_KEY,
                timeout=30.0,
                max_retries=3
            )
            logger.info("OpenAI embedding client initialized (using text-embedding-3-small)")
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {e}")
    
    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for a single text using OpenAI."""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts using OpenAI."""
        try:
            # OpenAI API expects input to be a list of strings
            # Handle empty list
            if not texts:
                return np.array([], dtype=np.float32)
            
            # Ensure all items are strings and filter out empty/None
            clean_texts = [str(text) if text else "" for text in texts if text]
            if not clean_texts:
                logger.warning("No valid texts to embed")
                return np.array([], dtype=np.float32)
            
            # Batch process in chunks of 100 (OpenAI limit)
            all_embeddings = []
            chunk_size = 100
            for i in range(0, len(clean_texts), chunk_size):
                chunk = clean_texts[i:i + chunk_size]
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=chunk  # List of strings
                )
                chunk_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(chunk_embeddings)
            
            return np.array(all_embeddings, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            logger.error(f"Input type: {type(texts)}, Length: {len(texts) if isinstance(texts, list) else 'N/A'}")
            if isinstance(texts, list) and len(texts) > 0:
                logger.error(f"First item type: {type(texts[0])}, Sample: {str(texts[0])[:100]}")
            raise


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

