"""Mock Neo4j implementation using NetworkX - PRIMARY implementation for hackathon."""

import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
import logging

from app.graph.schema import Node, Edge
from app.graph.loader import load_graph_data

logger = logging.getLogger(__name__)


class MockNeo4j:
    """NetworkX-based mock Neo4j implementation.
    
    Provides same query interface as Neo4j but uses NetworkX for in-memory graph.
    This allows development without Neo4j running - PRIMARY for hackathon.
    """
    
    def __init__(self, data_source: Optional[str] = None):
        """Initialize mock Neo4j with graph data.
        
        Args:
            data_source: Optional path to data file, or None to use sample data
        """
        self.graph = nx.MultiDiGraph()  # MultiDiGraph supports multiple edges
        self.nodes_by_id = {}  # Quick lookup: node_id -> node_data
        self._load_data(data_source)
    
    def _load_data(self, data_source: Optional[str] = None):
        """Load graph data into NetworkX graph."""
        nodes, edges = load_graph_data(data_source)
        
        # Add nodes
        for node in nodes:
            self.graph.add_node(
                node.id,
                label=node.label,
                **node.properties
            )
            self.nodes_by_id[node.id] = {
                "id": node.id,
                "label": node.label,
                **node.properties
            }
        
        # Add edges
        for edge in edges:
            self.graph.add_edge(
                edge.source,
                edge.target,
                relationship=edge.relationship,
                **(edge.properties or {})
            )
        
        logger.info(f"Loaded {len(nodes)} nodes and {len(edges)} edges into graph")
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node by ID."""
        return self.nodes_by_id.get(node_id)
    
    def get_nodes_by_label(self, label: str) -> List[Dict[str, Any]]:
        """Get all nodes with given label."""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            if data.get("label") == label:
                nodes.append({
                    "id": node_id,
                    "label": data.get("label"),
                    **{k: v for k, v in data.items() if k != "label"}
                })
        return nodes
    
    def get_neighbors(
        self, 
        node_id: str, 
        relationship: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get neighboring nodes (1-hop).
        
        Args:
            node_id: Source node ID
            relationship: Optional relationship type filter
        
        Returns:
            List of neighbor nodes with edge info
        """
        if node_id not in self.graph:
            return []
        
        neighbors = []
        for target in self.graph.successors(node_id):
            for edge_data in self.graph.get_edge_data(node_id, target).values():
                if relationship is None or edge_data.get("relationship") == relationship:
                    neighbor = self.get_node(target)
                    if neighbor:
                        neighbors.append({
                            **neighbor,
                            "relationship": edge_data.get("relationship"),
                            "edge_properties": {k: v for k, v in edge_data.items() if k != "relationship"}
                        })
        
        return neighbors
    
    def get_k_hop_subgraph(
        self, 
        node_ids: List[str], 
        k: int = 2
    ) -> Dict[str, Any]:
        """Extract k-hop subgraph around given nodes.
        
        Args:
            node_ids: List of starting node IDs
            k: Number of hops (default: 2)
        
        Returns:
            Dictionary with nodes and edges of subgraph
        """
        subgraph_nodes = set(node_ids)
        subgraph_edges = []
        
        # Expand k hops
        current_level = set(node_ids)
        for hop in range(k):
            next_level = set()
            for node_id in current_level:
                if node_id in self.graph:
                    # Get successors
                    for target in self.graph.successors(node_id):
                        next_level.add(target)
                        for edge_key, edge_data in self.graph.get_edge_data(node_id, target).items():
                            subgraph_edges.append({
                                "source": node_id,
                                "target": target,
                                "relationship": edge_data.get("relationship"),
                                **{k: v for k, v in edge_data.items() if k != "relationship"}
                            })
                    
                    # Get predecessors (bidirectional traversal)
                    for source in self.graph.predecessors(node_id):
                        next_level.add(source)
                        for edge_key, edge_data in self.graph.get_edge_data(source, node_id).items():
                            subgraph_edges.append({
                                "source": source,
                                "target": node_id,
                                "relationship": edge_data.get("relationship"),
                                **{k: v for k, v in edge_data.items() if k != "relationship"}
                            })
            
            subgraph_nodes.update(next_level)
            current_level = next_level
        
        # Build result
        nodes = [self.get_node(node_id) for node_id in subgraph_nodes if self.get_node(node_id)]
        
        return {
            "nodes": nodes,
            "edges": subgraph_edges,
            "hop_count": k
        }
    
    def find_paths(
        self, 
        source_id: str, 
        target_id: str, 
        max_length: int = 4
    ) -> List[List[str]]:
        """Find shortest paths between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_length: Maximum path length
        
        Returns:
            List of paths (each path is list of node IDs)
        """
        if source_id not in self.graph or target_id not in self.graph:
            return []
        
        try:
            # Find all simple paths
            paths = list(nx.all_simple_paths(
                self.graph.to_directed(),
                source_id,
                target_id,
                cutoff=max_length
            ))
            return paths[:10]  # Limit to 10 paths
        except (nx.NodeNotFound, nx.NetworkXNoPath):
            return []
    
    def query_by_property(
        self, 
        label: Optional[str] = None,
        **properties
    ) -> List[Dict[str, Any]]:
        """Query nodes by properties.
        
        Args:
            label: Optional node label filter
            **properties: Property filters (e.g., category="heating")
        
        Returns:
            List of matching nodes
        """
        matches = []
        for node_id, data in self.graph.nodes(data=True):
            if label and data.get("label") != label:
                continue
            
            # Check all properties match
            match = True
            for key, value in properties.items():
                if data.get(key) != value:
                    match = False
                    break
            
            if match:
                matches.append({
                    "id": node_id,
                    "label": data.get("label"),
                    **{k: v for k, v in data.items() if k != "label"}
                })
        
        return matches
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        node_labels = {}
        relationship_types = {}
        
        # Count nodes by label
        for node_id, data in self.graph.nodes(data=True):
            label = data.get("label", "Unknown")
            node_labels[label] = node_labels.get(label, 0) + 1
        
        # Count relationships
        for source, target, data in self.graph.edges(data=True):
            rel = data.get("relationship", "Unknown")
            relationship_types[rel] = relationship_types.get(rel, 0) + 1
        
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_labels": node_labels,
            "relationship_types": relationship_types
        }
    
    def calculate_centrality(self, node_id: str) -> float:
        """Calculate PageRank centrality for a node.
        
        Args:
            node_id: Node ID
        
        Returns:
            Centrality score (0-1)
        """
        if node_id not in self.graph:
            return 0.0
        
        try:
            pagerank = nx.pagerank(self.graph.to_directed())
            return pagerank.get(node_id, 0.0)
        except:
            # If graph is too small or has issues, return default
            return 0.1

