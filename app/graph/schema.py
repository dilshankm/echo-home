"""Graph schema definitions for knowledge graph."""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class Node:
    """Represents a node in the knowledge graph."""
    id: str
    label: str
    properties: Dict[str, Any]


@dataclass
class Edge:
    """Represents an edge (relationship) in the knowledge graph."""
    source: str
    target: str
    relationship: str
    properties: Dict[str, Any] = None


# Node Labels
NODE_LABELS = {
    "CATEGORY": "Category",
    "FUEL_TYPE": "FuelType",
    "TIP": "Tip",
    "HOUSE_TYPE": "HouseType"
}

# Relationship Types
RELATIONSHIPS = {
    "USES_FUEL": "USES_FUEL",
    "IMPROVES": "IMPROVES",
    "SUITABLE_FOR": "SUITABLE_FOR",
    "REQUIRES": "REQUIRES",
    "HAS_CATEGORY": "HAS_CATEGORY"
}

