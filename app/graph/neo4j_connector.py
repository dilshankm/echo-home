"""Neo4j Aurora connector - Ready for production Neo4j database.

This module provides a Neo4j connector that implements the same interface
as MockNeo4j, allowing seamless switching between mock and real Neo4j.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import Neo4j driver
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("Neo4j driver not installed. Install with: pip install neo4j")


class Neo4jConnector:
    """Neo4j connector for Aurora/Cloud Neo4j.
    
    Implements the same interface as MockNeo4j for easy switching.
    Supports Neo4j Aura and self-hosted Neo4j instances.
    """
    
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j"
    ):
        """Initialize Neo4j connection.
        
        Args:
            uri: Neo4j connection URI (e.g., 'bolt://localhost:7687' or 'neo4j+s://xxx.databases.neo4j.io')
            user: Neo4j username
            password: Neo4j password
            database: Database name (default: 'neo4j')
        """
        if not NEO4J_AVAILABLE:
            raise ImportError(
                "Neo4j driver not installed. "
                "Install with: pip install neo4j"
            )
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self.uri = uri
        
        # Verify connection
        try:
            self.verify_connection()
            logger.info(f"Connected to Neo4j at {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def verify_connection(self):
        """Verify Neo4j connection."""
        with self.driver.session(database=self.database) as session:
            result = session.run("RETURN 1 as test")
            result.single()
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node by ID.
        
        Args:
            node_id: Node ID
        
        Returns:
            Node dictionary or None if not found
        """
        query = """
        MATCH (n {id: $node_id})
        RETURN n, labels(n) as labels
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, node_id=node_id)
            record = result.single()
            
            if record:
                node_data = dict(record["n"])
                node_data["id"] = node_id
                node_data["label"] = record["labels"][0] if record["labels"] else "Node"
                return node_data
        
        return None
    
    def get_nodes_by_label(self, label: str) -> List[Dict[str, Any]]:
        """Get all nodes with given label.
        
        Args:
            label: Node label
        
        Returns:
            List of node dictionaries
        """
        query = f"""
        MATCH (n:{label})
        RETURN n, labels(n) as labels
        """
        
        nodes = []
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            for record in result:
                node_data = dict(record["n"])
                node_data["label"] = record["labels"][0] if record["labels"] else label
                nodes.append(node_data)
        
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
        if relationship:
            query = """
            MATCH (source {id: $node_id})-[r:%s]->(target)
            RETURN target, type(r) as relationship, labels(target) as labels
            """ % relationship
        else:
            query = """
            MATCH (source {id: $node_id})-[r]->(target)
            RETURN target, type(r) as relationship, labels(target) as labels
            """
        
        neighbors = []
        with self.driver.session(database=self.database) as session:
            result = session.run(query, node_id=node_id)
            for record in result:
                neighbor_data = dict(record["target"])
                neighbor_data["label"] = record["labels"][0] if record["labels"] else "Node"
                neighbors.append({
                    **neighbor_data,
                    "relationship": record["relationship"]
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
        # Build Cypher query for k-hop traversal
        query = f"""
        MATCH path = (start)-[*1..{k}]-(connected)
        WHERE start.id IN $node_ids
        WITH nodes(path) as nodes_in_path, relationships(path) as rels_in_path
        UNWIND nodes_in_path as node
        UNWIND rels_in_path as rel
        WITH DISTINCT node, type(rel) as rel_type, startNode(rel) as source, endNode(rel) as target
        RETURN DISTINCT node, labels(node) as labels, 
               id(source) as source_id, source.id as source_node_id,
               id(target) as target_id, target.id as target_node_id,
               rel_type
        LIMIT 1000
        """
        
        nodes_dict = {}
        edges = []
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, node_ids=node_ids)
            for record in result:
                # Add node
                node_data = dict(record["node"])
                node_id = node_data.get("id", str(record.get("node")))
                if node_id not in nodes_dict:
                    nodes_dict[node_id] = {
                        "id": node_id,
                        "label": record["labels"][0] if record["labels"] else "Node",
                        **node_data
                    }
                
                # Add edge
                if record["source_node_id"] and record["target_node_id"]:
                    edges.append({
                        "source": record["source_node_id"],
                        "target": record["target_node_id"],
                        "relationship": record["rel_type"]
                    })
        
        return {
            "nodes": list(nodes_dict.values()),
            "edges": edges,
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
        query = f"""
        MATCH path = shortestPath((source {{id: $source_id}})-[*1..{max_length}]-(target {{id: $target_id}}))
        RETURN [node in nodes(path) | node.id] as path
        LIMIT 10
        """
        
        paths = []
        with self.driver.session(database=self.database) as session:
            result = session.run(query, source_id=source_id, target_id=target_id)
            for record in result:
                path = record["path"]
                if path:
                    paths.append(path)
        
        return paths
    
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
        if label:
            match_clause = f"MATCH (n:{label})"
        else:
            match_clause = "MATCH (n)"
        
        where_clauses = [f"n.{key} = ${key}" for key in properties.keys()]
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
        {match_clause}
        {where_clause}
        RETURN n, labels(n) as labels
        """
        
        nodes = []
        with self.driver.session(database=self.database) as session:
            result = session.run(query, **properties)
            for record in result:
                node_data = dict(record["n"])
                node_data["label"] = record["labels"][0] if record["labels"] else label or "Node"
                nodes.append(node_data)
        
        return nodes
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        node_label_query = """
        CALL db.labels() YIELD label
        CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {}) YIELD value
        RETURN label, value.count as count
        """
        
        rel_type_query = """
        CALL db.relationshipTypes() YIELD relationshipType
        CALL apoc.cypher.run('MATCH ()-[r:' + relationshipType + ']->() RETURN count(r) as count', {}) YIELD value
        RETURN relationshipType, value.count as count
        """
        
        # Fallback query if APOC not available
        simple_node_query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        """
        
        simple_rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as relationshipType, count(r) as count
        """
        
        node_labels = {}
        relationship_types = {}
        total_nodes = 0
        total_edges = 0
        
        try:
            with self.driver.session(database=self.database) as session:
                # Get node counts by label
                result = session.run(simple_node_query)
                for record in result:
                    label = record["label"] or "Unknown"
                    count = record["count"]
                    node_labels[label] = count
                    total_nodes += count
                
                # Get relationship counts
                result = session.run(simple_rel_query)
                for record in result:
                    rel_type = record["relationshipType"] or "Unknown"
                    count = record["count"]
                    relationship_types[rel_type] = count
                    total_edges += count
        except Exception as e:
            logger.warning(f"Error getting statistics: {e}")
        
        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
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
        # Simple implementation - can be enhanced with GDS library
        query = """
        MATCH (n {id: $node_id})
        MATCH (n)-[r]->()
        WITH n, count(r) as out_degree
        MATCH ()-[r2]->(n)
        WITH n, out_degree, count(r2) as in_degree
        RETURN (out_degree + in_degree) / 10.0 as centrality
        LIMIT 1
        """
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, node_id=node_id)
                record = result.single()
                if record:
                    return min(float(record["centrality"]), 1.0)
        except Exception as e:
            logger.warning(f"Error calculating centrality: {e}")
        
        return 0.1
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        self.close()

