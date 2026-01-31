#!/usr/bin/env python3
"""
Complete test script for Neptune backend setup
Tests Ollama connection, LLM service, knowledge graph generation, and visualization
"""

import sys
import os
import asyncio
from typing import Dict, List, Any

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_ollama_connection():
    """Test if Ollama server is accessible"""
    print("=" * 50)
    print("Testing Ollama Connection")
    print("=" * 50)
    
    try:
        import requests
        
        # Test connection to your server
        ollama_url = "http://100.122.73.92:11434"
        print(f"Connecting to: {ollama_url}")
        
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            print("Ollama server is running.")
            print(f"Available models: {[m['name'] for m in models]}")
            return True
        else:
            print(f"Ollama server responded with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Cannot connect to Ollama: {e}")
        print("Make sure your server is running and accessible")
        return False

def test_llm_service():
    """Test the LLM service functionality"""
    print("\n" + "=" * 50)
    print("Testing LLM Service")
    print("=" * 50)
    
    try:
        from services.llm_service import extract_topics_from_notes, get_llm_response
        
        # Test basic LLM response
        print("Testing basic LLM response...")
        response = get_llm_response("What is 2+2?")
        print(f"LLM Response: {response}")
        
        # Use your existing test data from test_llm.py
        test_notes = [
            {
                "id": "note1", 
                "content": "Calculus is the mathematical study of continuous change. It involves derivatives and integrals."
            },
            {
                "id": "note2", 
                "content": "Linear algebra deals with vector spaces and linear mappings between these spaces."
            },
            {
                "id": "note3", 
                "content": "Physics explains how the universe behaves through mathematical models and experiments."
            }
        ]
        
        print(f"\nTesting topic extraction with {len(test_notes)} sample notes...")
        topics = extract_topics_from_notes(test_notes)
        
        print("Topic extraction successful.")
        print("Extracted topics:")
        for topic_data in topics:
            print(f"  - {topic_data['topic']}: {len(topic_data['note_ids'])} notes")
        
        return True
        
    except Exception as e:
        print(f"LLM service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_existing_llm_tests():
    """Run your existing LLM tests"""
    print("\n" + "=" * 50)
    print("Running Existing LLM Tests")
    print("=" * 50)
    
    try:
        # Try to run your existing test file
        print("Running app/services/test_llm.py...")
        
        # Import and run the existing test
        import subprocess
        result = subprocess.run([
            sys.executable, 
            'app/services/test_llm.py'
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("Existing LLM tests passed.")
            print("Output:", result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout)
        else:
            print("Existing LLM test had issues:")
            print("Error:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Could not run existing LLM tests: {e}")
        return False

def test_database_connection():
    """Test database connection and models"""
    print("\n" + "=" * 50)
    print("Testing Database Connection")
    print("=" * 50)
    
    try:
        from db.database import engine, SessionLocal
        from sqlalchemy import text
        
        # Test basic connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Database connection successful.")
        
        # Test session
        db = SessionLocal()
        try:
            # Try to query the database
            with db.begin():
                result = db.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
                table_count = result.scalar()
                print(f"Found {table_count} tables in database")
        except Exception as e:
            print(f"Database query issue: {e}")
            print("You might need to run migrations: alembic upgrade head")
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"Database test failed: {e}")
        print("Make sure PostgreSQL is running and DATABASE_URL is correct in .env")
        return False

def test_api_routes():
    """Test if API routes can be imported"""
    print("\n" + "=" * 50)
    print("Testing API Routes")
    print("=" * 50)
    
    try:
        # Check if main app files exist
        if os.path.exists('app/main.py'):
            from main import app
            print("FastAPI app imported successfully.")
        else:
            print("app/main.py not found.")
        
        # Check for API routes
        api_files = []
        if os.path.exists('app/api'):
            api_files = [f for f in os.listdir('app/api') if f.endswith('.py')]
            print(f"Found API files: {api_files}")
        
        return True
        
    except Exception as e:
        print(f"API routes test failed: {e}")
        return False

def test_visualizations():
    """Test visualization capabilities"""
    print("\n" + "=" * 50)
    print("Testing Visualizations")
    print("=" * 50)
    
    try:
        import networkx as nx
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        
        print("NetworkX imported successfully.")
        print("Matplotlib imported successfully.")
        
        # Check for existing visualization files
        viz_files = [f for f in os.listdir('.') if f.startswith('knowledge_graph_') and f.endswith('.png')]
        if viz_files:
            print(f"Found {len(viz_files)} existing visualization files")
            print(f"Latest: {sorted(viz_files)[-1]}")
        
        # Test basic graph creation
        G = nx.Graph()
        G.add_node("test1")
        G.add_node("test2")
        G.add_edge("test1", "test2")
        
        print("Basic graph creation works.")
        
        try:
            import plotly
            print("Plotly available for interactive visualizations.")
        except ImportError:
            print("Plotly not available (not critical).")
        
        return True
        
    except Exception as e:
        print(f"Visualization test failed: {e}")
        return False

def test_environment_config():
    """Test environment configuration"""
    print("\n" + "=" * 50)
    print("Testing Environment Configuration")
    print("=" * 50)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = [
            'DATABASE_URL',
            'OLLAMA_URL', 
            'OLLAMA_MODEL'
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if value:
                print(f"{var}: {value[:30]}..." if len(value) > 30 else f"{var}: {value}")
            else:
                missing_vars.append(var)
                print(f"{var}: Not set")
        
        if not missing_vars:
            print("All required environment variables are set.")
            return True
        else:
            print(f"Missing environment variables: {missing_vars}")
            return False
            
    except Exception as e:
        print(f"Environment config test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Neptune Backend Setup Test Suite")
    print("=" * 60)
    
    tests = [
        ("Environment Config", test_environment_config),
        ("Ollama Connection", test_ollama_connection),
        ("Database Connection", test_database_connection),
        ("LLM Service", test_llm_service),
        ("Existing LLM Tests", test_existing_llm_tests),
        ("API Routes", test_api_routes),
        ("Visualizations", test_visualizations),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"{test_name} test crashed: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests PASSED. Neptune backend is ready.")
        print("\nNext steps:")
        print("1. Run: uvicorn app.main:app --reload")
        print("2. Visit: http://localhost:8000/docs")
        print("3. Test your API endpoints")
    else:
        print("\nSome tests failed. Check the issues above.")
        print("Most critical: Environment Config, Ollama Connection, Database Connection")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
