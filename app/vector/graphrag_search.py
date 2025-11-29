"""GraphRAG similarity search - THE CORE INNOVATION!

Combines vector similarity, graph structure, and personalization.
This is what makes it GraphRAG vs simple RAG.
"""

import numpy as np
import faiss
from typing import List, Dict, Any, Tuple, Optional
import logging

from app.config import config
from app.vector.embeddings import get_embedding_model, create_node_embedding_text
from app.graph.mock_neo4j import MockNeo4j
# Neo4jConnector has the same interface as MockNeo4j, so it works here too
from typing import Union

logger = logging.getLogger(__name__)


class GraphRAGSearch:
    """GraphRAG search engine combining vector similarity and graph traversal."""
    
    def __init__(self, graph: Union[MockNeo4j, Any]):
        """Initialize GraphRAG search with graph.
        
        Args:
            graph: MockNeo4j or Neo4jConnector instance
        """
        self.graph = graph
        self.embedding_model = get_embedding_model()
        self.index = None
        self.node_ids = []
        self.node_embeddings = []
        self._build_index()
    
    def _build_index(self):
        """
        Build FAISS index for all graph nodes.
        
        GraphRAG Flow:
        STEP 1: Get KG structure from Neo4j (get_all_nodes)
        STEP 2: Create embeddings and build vector index (this method)
        STEP 3: Vector similarity search (cosine) - search()
        STEP 4: Graph traversal with Cypher - get_k_hop_subgraph()
        """
        logger.info("STEP 2: Building FAISS vector index from KG nodes...")
        
        # STEP 1: Get all nodes from graph (works for both MockNeo4j and Neo4jConnector)
        if hasattr(self.graph, 'nodes_by_id'):
            # MockNeo4j has nodes_by_id attribute
            nodes_dict = self.graph.nodes_by_id
            logger.info(f"Got {len(nodes_dict)} nodes from MockNeo4j")
        else:
            # Neo4jConnector - STEP 1: Get KG from Neo4j
            nodes_dict = self.graph.get_all_nodes()
            logger.info(f"Got {len(nodes_dict)} nodes from Neo4j KG")
        
        if not nodes_dict:
            logger.warning("No nodes found in graph")
            return
        
        # Get all nodes from graph and create embeddings
        all_nodes = []
        for node_id, node_data in nodes_dict.items():
            # Get graph context (1-hop neighbors)
            neighbors = self.graph.get_neighbors(node_id)
            neighbor_texts = []
            for neighbor in neighbors[:5]:  # Limit to top 5 neighbors
                rel = neighbor.get("relationship", "")
                neighbor_label = neighbor.get("label", "")
                neighbor_id = neighbor.get("id", "")
                neighbor_name = neighbor.get("name") or neighbor.get("action") or neighbor.get("type") or neighbor_id
                neighbor_texts.append(f"{rel} {neighbor_label}: {neighbor_name}")
            
            graph_context = "; ".join(neighbor_texts) if neighbor_texts else None
            
            # Create embedding text
            embedding_text = create_node_embedding_text(node_data, graph_context)
            all_nodes.append((node_id, embedding_text))
        
        if not all_nodes:
            logger.warning("No nodes found in graph for indexing")
            return
        
        # Generate embeddings
        texts = [text for _, text in all_nodes]
        embeddings = self.embedding_model.embed_batch(texts)
        
        # Store for later lookup
        self.node_ids = [node_id for node_id, _ in all_nodes]
        self.node_embeddings = embeddings
        
        # STEP 2: Build FAISS index with cosine similarity
        dimension = embeddings.shape[1]
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        # Use InnerProduct for cosine similarity (after normalization, dot product = cosine)
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings.astype('float32'))
        
        logger.info(f"STEP 2: Indexed {len(self.node_ids)} nodes in FAISS with cosine similarity")
    
    def search(
        self, 
        query: str, 
        k: Optional[int] = None,
        min_score: Optional[float] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        STEP 3: Vector Similarity Search (Cosine Similarity)
        
        GraphRAG retrieval combining:
        1. Vector similarity (cosine similarity on embeddings)
        2. Graph structure (relationships and paths) - done in retrieve_subgraph
        3. Personalization (user context) - done in retriever agent
        
        Args:
            query: User query text
            k: Number of results (default from config)
            min_score: Minimum similarity score (default from config)
        
        Returns:
            List of (node_dict, similarity_score) tuples
        """
        if self.index is None or len(self.node_ids) == 0:
            logger.warning("Index not built, returning empty results")
            return []
        
        k = k or config.VECTOR_SIMILARITY_TOP_K
        min_score = min_score or config.MIN_SIMILARITY_SCORE
        
        # STEP 3: Vector Similarity Search using Cosine Similarity
        query_embedding = self.embedding_model.embed(query)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        # Normalize query embedding for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Get more candidates for re-ranking
        search_k = min(k * 2, len(self.node_ids))
        similarities, indices = self.index.search(query_embedding, search_k)
        
        # STEP 2: Graph-Based Re-ranking
        # Combine vector similarity with graph importance
        scored_nodes = []
        for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
            node_id = self.node_ids[idx]
            node = self.graph.get_node(node_id)
            
            if not node:
                continue
            
            # Cosine similarity is already in range [-1, 1], normalize to [0, 1]
            vector_similarity = (similarity + 1.0) / 2.0
            
            # Calculate graph centrality
            centrality = self.graph.calculate_centrality(node_id)
            
            # Combined score: 70% vector similarity, 30% graph centrality
            final_score = (vector_similarity * 0.7) + (centrality * 0.3)
            
            if final_score >= min_score:
                scored_nodes.append((node, final_score, vector_similarity, centrality))
        
        # Sort by final score
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k
        results = [(node, score) for node, score, _, _ in scored_nodes[:k]]
        
        logger.info(f"GraphRAG search returned {len(results)} results for query: {query[:50]}")
        
        return results
    
    def retrieve_subgraph(
        self,
        query: str,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Full GraphRAG retrieval pipeline.
        
        GraphRAG Flow:
        STEP 1: Get KG from Neo4j (done in _build_index)
        STEP 2: Build vector index (done in _build_index)
        STEP 3: Vector similarity search - cosine similarity (search)
        STEP 4: Graph traversal with Cypher queries (this method)
        
        Args:
            query: User query
            k: Number of top nodes to start traversal from
        
        Returns:
            Complete GraphRAG result with subgraph and paths
        """
        # STEP 3: Vector Similarity Search (Cosine Similarity)
        top_nodes_scores = self.search(query, k=k)
        top_node_ids = [node['id'] for node, _ in top_nodes_scores]
        
        if not top_node_ids:
            return {
                'top_nodes': [],
                'scores': [],
                'subgraph': {'nodes': [], 'edges': []},
                'paths': [],
                'context_text': '',
                'explanation': 'No matching nodes found'
            }
        
        logger.info(f"STEP 3: Vector search found {len(top_node_ids)} relevant nodes")
        
        # STEP 4: Graph Traversal using Cypher queries
        # Extract subgraph around matched nodes
        logger.info(f"STEP 4: Traversing graph with Cypher queries (k-hop: {config.SUBGRAPH_HOPS})...")
        subgraph = self.graph.get_k_hop_subgraph(
            top_node_ids,
            k=config.SUBGRAPH_HOPS
        )
        
        # STEP 4b: Path Finding with Cypher
        # Find meaningful paths between matched nodes
        paths = []
        logger.info(f"STEP 4b: Finding paths between {len(top_node_ids)} matched nodes...")
        for i, node1_id in enumerate(top_node_ids):
            for node2_id in top_node_ids[i+1:]:
                found_paths = self.graph.find_paths(node1_id, node2_id, max_length=4)
                for path in found_paths:
                    if len(path) <= 4:  # Only short, meaningful paths
                        paths.append(path)
        
        logger.info(f"STEP 4: Graph traversal found {len(subgraph.get('nodes', []))} nodes, {len(subgraph.get('edges', []))} edges, {len(paths)} paths")
        
        # STEP 4: Context Serialization
        context_text = self._serialize_subgraph_with_paths(subgraph, paths, top_nodes_scores)
        
        # STEP 5: Explanation
        explanation = self._generate_traversal_explanation(paths, top_nodes_scores)
        
        return {
            'top_nodes': [node for node, _ in top_nodes_scores],
            'scores': [score for _, score in top_nodes_scores],
            'subgraph': subgraph,
            'paths': paths,
            'context_text': context_text,
            'explanation': explanation
        }
    
    def _serialize_subgraph_with_paths(
        self,
        subgraph: Dict[str, Any],
        paths: List[List[str]],
        top_nodes: List[Tuple[Dict[str, Any], float]]
    ) -> str:
        """Convert subgraph and paths to text for LLM."""
        parts = []
        
        parts.append("Graph analysis results:")
        parts.append(f"\nTop matched nodes ({len(top_nodes)}):")
        for node, score in top_nodes[:5]:
            label = node.get("label", "")
            name = node.get("name") or node.get("action") or node.get("type") or node.get("id")
            parts.append(f"- {label}: {name} (score: {score:.3f})")
        
        parts.append(f"\nSubgraph contains {len(subgraph['nodes'])} nodes and {len(subgraph['edges'])} edges.")
        
        # Add key relationships
        parts.append("\nKey relationships:")
        for edge in subgraph['edges'][:10]:  # Limit to 10 edges
            rel = edge.get("relationship", "")
            parts.append(f"- {edge['source']} --[{rel}]--> {edge['target']}")
        
        # Add paths
        if paths:
            parts.append(f"\nFound {len(paths)} meaningful paths:")
            for path in paths[:5]:  # Show top 5 paths
                parts.append(f"- Path: {' -> '.join(path)}")
        
        return "\n".join(parts)
    
    def _generate_traversal_explanation(
        self,
        paths: List[List[str]],
        top_nodes: List[Tuple[Dict[str, Any], float]]
    ) -> str:
        """Generate human-readable explanation of graph traversal."""
        if not top_nodes:
            return "No nodes matched the query."
        
        explanation_parts = []
        explanation_parts.append(f"GraphRAG found {len(top_nodes)} relevant nodes:")
        
        for i, (node, score) in enumerate(top_nodes[:3], 1):
            label = node.get("label", "")
            name = node.get("name") or node.get("action") or node.get("type") or node.get("id")
            explanation_parts.append(f"{i}. {label} '{name}' (relevance: {score:.2f})")
        
        if paths:
            explanation_parts.append(f"\nDiscovered {len(paths)} connections between concepts, showing how energy-saving tips relate to categories and fuel types.")
        
        return " ".join(explanation_parts)

