#!/usr/bin/env python3
"""Comprehensive local API testing script.

Run this to test all API endpoints locally.
Usage: python test_api_local.py
"""

import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text: str):
    """Print a section divider."""
    print(f"\n{'─' * 70}")
    print(f"  {text}")
    print("─" * 70)


def test_health():
    """Test health endpoint."""
    print_section("1️⃣ Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Status: {data.get('status')}")
        print(f"✅ Mode: {data.get('mode')}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False


def test_graph_stats():
    """Test graph statistics endpoint."""
    print_section("2️⃣ Graph Statistics")
    try:
        response = requests.get(f"{BASE_URL}/api/graph/stats", timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Total Nodes: {data.get('total_nodes')}")
        print(f"✅ Total Edges: {data.get('total_edges')}")
        print(f"✅ Node Labels: {json.dumps(data.get('node_labels'), indent=2)}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False


def test_chat(query: str, description: str) -> bool:
    """Test chat endpoint with a query."""
    print_section(f"3️⃣ Chat Test: {description}")
    print(f"📝 Query: '{query}'")
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": query},
            timeout=TIMEOUT
        )
        elapsed = time.time() - start_time
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Response Time: {elapsed:.2f}s")
        print(f"✅ Response Length: {len(data.get('response', ''))} characters")
        
        query_context = data.get('query_context', {})
        entities = query_context.get('entities', {})
        print(f"✅ Intent: {query_context.get('intent')}")
        print(f"✅ Entities: {json.dumps(entities, indent=2)}")
        
        # Show response preview
        response_text = data.get('response', '')
        print(f"\n📄 Response Preview (first 200 chars):")
        print(f"   {response_text[:200]}...")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text[:200]}")
        return False


def test_analyze_endpoint(query: str):
    """Test analyze endpoint (shows graph traversal)."""
    print_section("4️⃣ Analyze Endpoint (Graph Traversal)")
    print(f"📝 Query: '{query}'")
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"message": query},
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        
        explanation = data.get('explanation', {})
        graph_traversal = explanation.get('graph_traversal', {})
        
        print(f"✅ Matched Nodes: {graph_traversal.get('matched_nodes_count', 0)}")
        print(f"✅ Subgraph Nodes: {graph_traversal.get('subgraph_nodes', 0)}")
        print(f"✅ Paths Found: {graph_traversal.get('paths_found', 0)}")
        print(f"✅ Tips Retrieved: {explanation.get('tips_retrieved', 0)}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False


def wait_for_server(max_attempts: int = 30):
    """Wait for server to be ready."""
    print("🔄 Waiting for server to be ready...")
    for i in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=2)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            pass
        time.sleep(1)
        if (i + 1) % 5 == 0:
            print(f"   Still waiting... ({i + 1}/{max_attempts})")
    return False


def main():
    """Run all tests."""
    print_header("🧪 Energy Coach GraphRAG API - Local Test Suite")
    
    # Check if server is running
    print("\n📍 Testing server at:", BASE_URL)
    if not wait_for_server():
        print("\n❌ Server is not responding!")
        print("   Please start the server first:")
        print("   uvicorn app.main:app --reload")
        sys.exit(1)
    
    results = []
    
    # Test 1: Health
    results.append(("Health Check", test_health()))
    
    # Test 2: Graph Stats
    results.append(("Graph Statistics", test_graph_stats()))
    
    # Test 3: Chat endpoints
    chat_tests = [
        ("How can I reduce my electricity bills?", "General query"),
        ("I have high heating costs in a 2-bed flat", "Specific context"),
        ("What are quick wins for saving energy?", "Quick wins"),
    ]
    
    for query, desc in chat_tests:
        results.append((f"Chat: {desc}", test_chat(query, desc)))
        time.sleep(1)  # Small delay between requests
    
    # Test 4: Analyze endpoint
    results.append(("Analyze Endpoint", test_analyze_endpoint("How can I save energy?")))
    
    # Summary
    print_header("📊 Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{'=' * 70}")
    print(f"  Results: {passed}/{total} tests passed")
    print(f"{'=' * 70}\n")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

