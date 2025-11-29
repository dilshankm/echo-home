# Neo4j Aurora Setup Guide

This guide explains how to switch from the mock Neo4j (NetworkX) to real Neo4j Aurora.

## Current Setup: Mock Neo4j (NetworkX)

**Currently Active**: The system uses `MockNeo4j` which uses NetworkX for in-memory graph storage. This works perfectly for development and the hackathon demo.

## Switching to Neo4j Aurora (Production)

### Step 1: Install Neo4j Driver

```bash
pip install neo4j
```

### Step 2: Get Neo4j Aurora Connection Details

From your Neo4j Aura dashboard, you'll get:
- **URI**: `neo4j+s://xxxxx.databases.neo4j.io` (secure connection)
- **Username**: Usually `neo4j`
- **Password**: Your database password

### Step 3: Update `.env` File

Edit your `.env` file:

```bash
# Switch to real Neo4j
USE_MOCK_NEO4J=false

# Neo4j Aurora Connection
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
```

### Step 4: Load Data to Neo4j

You'll need to load your knowledge graph data into Neo4j. Use the `app/graph/loader.py` functions to convert your data and then import it.

**Option A: Use Neo4j Browser**

1. Connect to your Neo4j Aura instance via browser
2. Run Cypher commands to create nodes and relationships

**Option B: Create Import Script**

Create a script to import data:

```python
from app.graph.neo4j_connector import Neo4jConnector
from app.graph.loader import load_graph_data
from app.config import config

# Connect to Neo4j
connector = Neo4jConnector(
    uri=config.NEO4J_URI,
    user=config.NEO4J_USER,
    password=config.NEO4J_PASSWORD
)

# Load data
nodes, edges = load_graph_data()

# Import nodes
for node in nodes:
    properties_str = ", ".join([f"{k}: ${k}" for k in node.properties.keys()])
    query = f"""
    CREATE (n:{node.label} {{id: $id, {properties_str}}})
    """
    with connector.driver.session() as session:
        session.run(query, id=node.id, **node.properties)

# Import edges
for edge in edges:
    query = f"""
    MATCH (source {{id: $source}}), (target {{id: $target}})
    CREATE (source)-[r:{edge.relationship}]->(target)
    """
    with connector.driver.session() as session:
        session.run(query, source=edge.source, target=edge.target)

connector.close()
```

### Step 5: Restart Application

```bash
# Restart the server
python3 -m uvicorn app.main:app --reload
```

The application will now connect to Neo4j Aurora instead of using the mock.

## Graph Schema in Neo4j

Your Neo4j database should have:

**Node Labels:**
- `Category` - Energy categories
- `FuelType` - Fuel types (gas, electricity)
- `Tip` - Energy-saving tips
- `HouseType` - House types

**Relationships:**
- `USES_FUEL` - Category → FuelType
- `IMPROVES` - Tip → Category
- `SUITABLE_FOR` - Tip → HouseType

**Required Properties:**
- All nodes must have an `id` property for lookups

## Testing the Connection

After switching, check the logs:

```
INFO - Connecting to Neo4j at neo4j+s://xxxxx.databases.neo4j.io
INFO - Connected to Neo4j at neo4j+s://xxxxx.databases.neo4j.io
INFO - Graph loaded successfully
```

And test the API:

```bash
curl http://localhost:8000/api/graph/stats
```

## Switching Back to Mock

If you want to switch back to mock Neo4j (for development):

```bash
# In .env file
USE_MOCK_NEO4J=true
```

## Troubleshooting

### Connection Issues

- **Check URI format**: Must be `neo4j+s://` for Aura or `bolt://` for self-hosted
- **Verify credentials**: Username and password must be correct
- **Check network**: Ensure your IP is whitelisted in Aura

### Import Issues

- **Verify node IDs**: All nodes must have unique `id` properties
- **Check relationships**: Source and target nodes must exist before creating relationships

### Performance

- **Index creation**: Create indexes on `id` property for faster lookups:
  ```cypher
  CREATE INDEX node_id_index FOR (n) ON (n.id)
  ```

## Notes

- The `Neo4jConnector` implements the same interface as `MockNeo4j`, so no code changes are needed when switching
- Both connectors return the same data structure
- The GraphRAG search works identically with both implementations

