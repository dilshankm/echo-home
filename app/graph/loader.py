"""Graph data loader - accepts multiple input formats."""

import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from app.graph.schema import Node, Edge
from app.graph.sample_data import CATEGORIES, FUELS, TIPS, HOUSE_TYPES


def load_from_dict(data: Dict[str, Any]) -> Tuple[List[Node], List[Edge]]:
    """Load graph from Python dictionary format.
    
    Expected format:
    {
        "nodes": [
            {"id": "...", "label": "...", "properties": {...}}
        ],
        "edges": [
            {"source": "...", "target": "...", "relationship": "...", "properties": {...}}
        ]
    }
    """
    nodes = [Node(**node) for node in data.get("nodes", [])]
    edges = [Edge(**edge) for edge in data.get("edges", [])]
    return nodes, edges


def load_from_json(filepath: str) -> Tuple[List[Node], List[Edge]]:
    """Load graph from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return load_from_dict(data)


def load_from_csv(nodes_csv: str, edges_csv: str) -> Tuple[List[Node], List[Edge]]:
    """Load graph from CSV files.
    
    Note: Requires pandas to be installed. If not available, this will raise ImportError.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for CSV loading. "
            "Install with: pip install pandas"
        )
    
    nodes_df = pd.read_csv(nodes_csv)
    edges_df = pd.read_csv(edges_csv)
    
    nodes = []
    for _, row in nodes_df.iterrows():
        props = {k: v for k, v in row.items() if k not in ['id', 'label']}
        nodes.append(Node(
            id=str(row['id']),
            label=row['label'],
            properties=props
        ))
    
    edges = []
    for _, row in edges_df.iterrows():
        props = {k: v for k, v in row.items() if k not in ['source', 'target', 'relationship']}
        edges.append(Edge(
            source=str(row['source']),
            target=str(row['target']),
            relationship=row['relationship'],
            properties=props if props else None
        ))
    
    return nodes, edges


def create_graph_from_sample_data() -> Tuple[List[Node], List[Edge]]:
    """Create graph structure from sample data (default implementation)."""
    nodes = []
    edges = []
    
    # Add Categories
    for cat in CATEGORIES:
        nodes.append(Node(
            id=f"category_{cat['name']}",
            label="Category",
            properties={
                "name": cat['name'],
                "kwh_per_home": cat['kwh'],
                "total_gwh": cat['gwh'],
                "percentage": cat['percentage'],
                "fuel_type": cat['fuel']
            }
        ))
        
        # Connect category to fuel
        edges.append(Edge(
            source=f"category_{cat['name']}",
            target=f"fuel_{cat['fuel']}",
            relationship="USES_FUEL"
        ))
    
    # Add Fuel Types
    for fuel in FUELS:
        nodes.append(Node(
            id=f"fuel_{fuel['name']}",
            label="FuelType",
            properties={
                "name": fuel['name'],
                "rate_gbp_kwh": fuel['rate_gbp_kwh'],
                "co2_kg_kwh": fuel['co2_kg_kwh']
            }
        ))
    
    # Add Tips
    for tip in TIPS:
        nodes.append(Node(
            id=tip['id'],
            label="Tip",
            properties={
                "action": tip['action'],
                "description": tip['description'],
                "savings_gbp": tip['savings_gbp'],
                "savings_co2": tip['savings_co2'],
                "difficulty": tip['difficulty'],
                "category": tip['category']
            }
        ))
        
        # Connect tip to category
        edges.append(Edge(
            source=tip['id'],
            target=f"category_{tip['category']}",
            relationship="IMPROVES"
        ))
    
    # Add House Types
    for house in HOUSE_TYPES:
        nodes.append(Node(
            id=f"house_{house['type']}",
            label="HouseType",
            properties={
                "type": house['type'],
                "avg_size_sqm": house['avg_size_sqm'],
                "typical_occupants": house['typical_occupants'],
                "heating_kwh_factor": house['heating_kwh_factor']
            }
        ))
    
    # Connect tips to suitable house types (simplified - all tips work for all types)
    # But some tips are more relevant for certain types
    for tip in TIPS:
        if tip['category'] == 'heating':
            # Heating tips more relevant for larger houses
            for house in HOUSE_TYPES:
                edges.append(Edge(
                    source=tip['id'],
                    target=f"house_{house['type']}",
                    relationship="SUITABLE_FOR"
                ))
        else:
            # Other tips work for all house types
            for house in HOUSE_TYPES:
                edges.append(Edge(
                    source=tip['id'],
                    target=f"house_{house['type']}",
                    relationship="SUITABLE_FOR"
                ))
    
    return nodes, edges


def load_graph_data(data_source: Optional[str] = None) -> Tuple[List[Node], List[Edge]]:
    """Main loader function - automatically detects format and loads data.
    
    Args:
        data_source: Path to data file (JSON/CSV) or None to use sample data
    
    Returns:
        Tuple of (nodes, edges)
    """
    if data_source is None:
        return create_graph_from_sample_data()
    
    path = Path(data_source)
    
    if path.suffix == '.json':
        return load_from_json(str(path))
    elif path.suffix == '.csv':
        # Assuming nodes.csv and edges.csv naming
        nodes_csv = path.parent / "nodes.csv"
        edges_csv = path.parent / "edges.csv"
        return load_from_csv(str(nodes_csv), str(edges_csv))
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

