# API cURL Examples

Complete cURL examples for testing the Energy Coach GraphRAG API.

## 🌐 Base URL

**Local Docker Container:**
- Port: `8000` (container) → `8001` (host) or `8080` (if you change it)
- Base URL: `http://localhost:8001` (or `http://localhost:8080`)

## 📋 API Endpoints

### 1️⃣ Health Check

```bash
curl http://localhost:8001/api/health
```

**Pretty formatted:**
```bash
curl http://localhost:8001/api/health | python3 -m json.tool
```

**Expected Response:**
```json
{
  "status": "healthy",
  "mode": "mock_neo4j"
}
```

---

### 2️⃣ Graph Statistics

```bash
curl http://localhost:8001/api/graph/stats
```

**Pretty formatted:**
```bash
curl http://localhost:8001/api/graph/stats | python3 -m json.tool
```

**Expected Response:**
```json
{
  "total_nodes": 39,
  "total_edges": 145,
  "node_labels": {
    "Category": 5,
    "FuelType": 2,
    "Tip": 28,
    "HouseType": 4
  },
  "relationship_types": {
    "USES_FUEL": 5,
    "IMPROVES": 28,
    "SUITABLE_FOR": 112
  },
  "mode": "mock_neo4j"
}
```

---

### 3️⃣ Chat Endpoint (Main API)

#### Example 1: General Query
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How can I reduce my electricity bills?"}'
```

#### Example 2: Specific House Type
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I have high heating costs in a 2-bed flat"}'
```

#### Example 3: Quick Wins
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are quick wins for saving energy?"}'
```

#### Example 4: Appliance Upgrade
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "My appliances are old, what should I upgrade first?"}'
```

**Pretty formatted:**
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How can I reduce my electricity bills?"}' \
  | python3 -m json.tool
```

**Expected Response:**
```json
{
  "response": "Based on UK ECUK 2025 data, here are personalized recommendations:\n\n1. Air dry clothes...",
  "query_context": {
    "entities": {
      "house_type": null,
      "bedrooms": null,
      "category": null,
      "problem": "high_bills"
    },
    "intent": "cost_reduction",
    "urgency": "high"
  }
}
```

---

### 4️⃣ Analyze Endpoint (Graph Traversal Details)

```bash
curl -X POST http://localhost:8001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "How can I save energy?"}'
```

**Pretty formatted:**
```bash
curl -X POST http://localhost:8001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "How can I save energy?"}' \
  | python3 -m json.tool
```

---

## 🐳 Running Docker Container on Port 8080

If you want to run on port 8080 instead:

```bash
# Stop existing container
docker stop echo-home-api
docker rm echo-home-api

# Run on port 8080
docker run -d --name echo-home-api \
  -e OPENAI_API_KEY="your-key-here" \
  -e USE_MOCK_NEO4J=true \
  -p 8080:8000 \
  echo-home:latest
```

Then use `http://localhost:8080` in all curl commands above.

---

## 🧪 Quick Test Script

Test all endpoints at once:

```bash
# Health check
echo "1. Health:" && curl -s http://localhost:8001/api/health | python3 -m json.tool

# Graph stats
echo -e "\n2. Graph Stats:" && curl -s http://localhost:8001/api/graph/stats | python3 -m json.tool

# Chat
echo -e "\n3. Chat:" && curl -s -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' | python3 -m json.tool
```

---

## 📚 Interactive API Docs

Once the container is running, visit:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

