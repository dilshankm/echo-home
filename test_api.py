"""Simple test script to verify the API is working."""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_graph_stats():
    """Test graph stats endpoint."""
    print("Testing graph stats endpoint...")
    response = requests.get(f"{BASE_URL}/api/graph/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_chat(query: str):
    """Test chat endpoint."""
    print(f"Testing chat endpoint with query: '{query}'...")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": query}
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {result.get('response', '')[:500]}...")
    print(f"Query Context: {json.dumps(result.get('query_context', {}), indent=2)}")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("Energy Coach GraphRAG API Test")
    print("=" * 60)
    print()
    
    # Test health
    try:
        test_health()
    except Exception as e:
        print(f"Error testing health: {e}")
        print("Make sure the server is running: uvicorn app.main:app --reload")
        exit(1)
    
    # Test graph stats
    try:
        test_graph_stats()
    except Exception as e:
        print(f"Error testing graph stats: {e}")
    
    # Test chat with demo queries
    demo_queries = [
        "How can I reduce my electricity bills?",
        "I have high heating costs in a 2-bed flat",
        "What are quick wins for saving energy?"
    ]
    
    for query in demo_queries:
        try:
            test_chat(query)
        except Exception as e:
            print(f"Error testing chat: {e}")
    
    print("=" * 60)
    print("Tests completed!")
    print("=" * 60)

