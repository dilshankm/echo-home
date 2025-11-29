"""Neo4j Aurora connector - Ready for production Neo4j database.

This module provides a Neo4j connector that implements the same interface
as MockNeo4j, allowing seamless switching between mock and real Neo4j.
"""

from typing import List, Dict, Any, Optional, Tuple
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
        
        # Create driver with connection timeout and retry settings
        # Try neo4j+ssc:// if SSL certificate verification fails
        try:
            # Enable debug logging for troubleshooting
            try:
                from neo4j.debug import watch
                watch("neo4j")
                logger.info("Neo4j debug logging enabled")
            except ImportError:
                pass
            
            # Try the connection URI as-is first
            # If neo4j+s:// fails, we'll try neo4j+ssc:// (self-signed cert)
            original_uri = uri
            
            # For Neo4j Aura (cloud), use driver configuration
            self.driver = GraphDatabase.driver(
                uri, 
                auth=(user, password),
                max_connection_lifetime=30 * 60,  # 30 minutes
                max_connection_pool_size=50,
                connection_acquisition_timeout=15,  # 15 seconds (longer for Aura)
                connection_timeout=15,
                keep_alive=True
            )
            self.database = database
            self.uri = uri
            
            # Verify connection with timeout
            try:
                self.verify_connection()
                logger.info(f"✅ Connected to Neo4j at {uri}")
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"⚠️ Connection failed with {uri}: {error_msg}")
                
                # Try neo4j+ssc:// if neo4j+s:// fails (for SSL cert issues)
                if "neo4j+s://" in uri and "routing information" in error_msg.lower():
                    logger.info("🔄 Trying neo4j+ssc:// (self-signed cert bypass)...")
                    ssc_uri = uri.replace("neo4j+s://", "neo4j+ssc://")
                    try:
                        self.driver.close()
                        self.driver = GraphDatabase.driver(
                            ssc_uri,
                            auth=(user, password),
                            max_connection_lifetime=30 * 60,
                            max_connection_pool_size=50,
                            connection_acquisition_timeout=15,
                            connection_timeout=15,
                            keep_alive=True
                        )
                        self.uri = ssc_uri
                        self.verify_connection()
                        logger.info(f"✅ Connected to Neo4j using {ssc_uri} (self-signed cert)")
                        return
                    except Exception as e2:
                        logger.error(f"❌ Also failed with neo4j+ssc://: {e2}")
                
                logger.error(f"❌ Failed to verify Neo4j connection: {e}")
                logger.error("   Check: 1) Network connectivity, 2) URI format, 3) Credentials, 4) Neo4j Aura instance status")
                self.driver.close()
                raise
        except Exception as e:
            logger.error(f"❌ Failed to create Neo4j driver: {e}")
            raise
    
    def verify_connection(self):
        """Verify Neo4j connection."""
        try:
            # Try to get server info first (more robust than simple query)
            with self.driver.session(database=self.database) as session:
                # Test query
                result = session.run("RETURN 1 as test")
                record = result.single()
                if record:
                    logger.info("Neo4j connection verified successfully")
                    return True
        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            raise
    
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
            node_id: Source node ID (can be property value or internal ID)
            relationship: Optional relationship type filter
        
        Returns:
            List of neighbor nodes with edge info
        """
        # More flexible query - try id property first, then other common properties
        # Note: Handle both string and numeric IDs
        if relationship:
            query = f"""
            MATCH (source)-[r:{relationship}]->(target)
            WHERE (source.id = $node_id OR toString(source.id) = $node_id)
               OR (source.value = $node_id OR toString(source.value) = $node_id)
               OR (source.name = $node_id OR toString(source.name) = $node_id)
            RETURN target, type(r) as relationship, labels(target) as labels, id(target) as target_internal_id
            """
        else:
            query = """
            MATCH (source)-[r]->(target)
            WHERE (source.id = $node_id OR toString(source.id) = $node_id)
               OR (source.value = $node_id OR toString(source.value) = $node_id)
               OR (source.name = $node_id OR toString(source.name) = $node_id)
            RETURN target, type(r) as relationship, labels(target) as labels, id(target) as target_internal_id
            """
        
        neighbors = []
        with self.driver.session(database=self.database) as session:
            result = session.run(query, node_id=node_id)
            for record in result:
                neighbor_data = dict(record["target"])
                labels_list = record["labels"] or []
                neighbor_data["label"] = labels_list[0] if labels_list else "Node"
                
                # Ensure node has an ID
                if "id" not in neighbor_data:
                    neighbor_data["id"] = neighbor_data.get("value") or neighbor_data.get("name") or str(record["target_internal_id"])
                
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
    
    def get_all_nodes(self) -> Dict[str, Dict[str, Any]]:
        """Get all nodes from Neo4j (similar to MockNeo4j.nodes_by_id).
        
        This is STEP 1 of GraphRAG: Get the knowledge graph structure.
        
        Returns:
            Dictionary mapping node_id -> node_data
        """
        query = """
        MATCH (n)
        RETURN n, labels(n) as labels, id(n) as internal_id
        """
        
        nodes_by_id = {}
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            for record in result:
                node_data = dict(record["n"])
                labels_list = record["labels"] or []
                label = labels_list[0] if labels_list else "Node"
                
                # Try to get ID from properties first, then use internal Neo4j ID as fallback
                node_id = node_data.get("id") or node_data.get("value") or node_data.get("name") or str(record["internal_id"])
                
                # Create a consistent node representation
                node_data["id"] = str(node_id)
                node_data["label"] = label
                
                nodes_by_id[str(node_id)] = node_data
        
        logger.info(f"STEP 1: Retrieved {len(nodes_by_id)} nodes from Neo4j KG")
        return nodes_by_id
    
    def vector_similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        label: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """STEP 2: Vector similarity search using Neo4j vector index (if available) or fallback.
        
        This uses cosine similarity to find relevant nodes.
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of results
            label: Optional node label filter
        
        Returns:
            List of (node, similarity_score) tuples
        """
        # First, try to use Neo4j vector index if available
        # This requires nodes to have an 'embedding' property
        try:
            label_filter = f":{label}" if label else ""
            query = f"""
            MATCH (n{label_filter})
            WHERE n.embedding IS NOT NULL
            WITH n, gds.similarity.cosine(n.embedding, $query_embedding) AS similarity
            ORDER BY similarity DESC
            LIMIT $top_k
            RETURN n, labels(n) as labels, similarity
            """
            
            with self.driver.session(database=self.database) as session:
                result = session.run(query, query_embedding=query_embedding, top_k=top_k)
                nodes = []
                for record in result:
                    node_data = dict(record["n"])
                    labels_list = record["labels"] or []
                    node_data["label"] = labels_list[0] if labels_list else label or "Node"
                    node_id = node_data.get("id") or node_data.get("value") or node_data.get("name")
                    if not node_id:
                        node_id = str(id(record["n"]))
                    node_data["id"] = str(node_id)
                    similarity = float(record["similarity"])
                    nodes.append((node_data, similarity))
                
                if nodes:
                    logger.info(f"STEP 2: Vector similarity search found {len(nodes)} nodes using Neo4j vector index")
                    return nodes
        except Exception as e:
            logger.debug(f"Neo4j vector index not available or GDS not enabled: {e}. Using fallback method.")
        
        # Fallback: Return empty list (will be handled by FAISS in GraphRAGSearch)
        logger.info("STEP 2: Vector similarity will use FAISS (Neo4j vector index not available)")
        return []
    
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

