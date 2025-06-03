import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import subprocess
import sys

# Load environment variables
load_dotenv()

# Base URL of the API server
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')

def test_health_check():
    print("\n--- Testing Health Check API ---")
    
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        health_data = response.json()
        print(f"Health check: {health_data}")
        
        services = health_data.get('services', {})
        print("\nService Status:")
        for service, status in services.items():
            print(f"  {service}: {status}")
    else:
        print(f"Error getting health check: {response.status_code}")

def test_youtube_videos():
    print("\n--- Testing YouTube Monitor API ---")
    
    # Test with no parameters
    response = requests.get(f"{BASE_URL}/videos")
    print(f"All videos: {len(response.json())} videos returned")
    
    # Test with channel filter
    response = requests.get(f"{BASE_URL}/videos?channels=TechWorld")
    print(f"TechWorld videos: {len(response.json())} videos returned")
    
    # Test with category filter
    response = requests.get(f"{BASE_URL}/videos?categories=music")
    print(f"Music videos: {len(response.json())} videos returned")
    
    # Test with both filters
    response = requests.get(f"{BASE_URL}/videos?channels=TechWorld&categories=tech")
    print(f"TechWorld tech videos: {len(response.json())} videos returned")

def test_news_headlines():
    print("\n--- Testing News Aggregator API ---")
    
    # Test with no parameters
    response = requests.get(f"{BASE_URL}/headlines")
    print(f"All headlines: {len(response.json())} articles returned")
    
    # Test with topic filter
    response = requests.get(f"{BASE_URL}/headlines?topics=technology")
    print(f"Technology headlines: {len(response.json())} articles returned")
    
    # Test with hours filter
    response = requests.get(f"{BASE_URL}/headlines?hours=12")
    print(f"Last 12 hours: {len(response.json())} articles returned")
    
    # Test with both filters
    response = requests.get(f"{BASE_URL}/headlines?topics=economy&hours=12")
    print(f"Economy news from last 12 hours: {len(response.json())} articles returned")

def test_all_services():
    """Run specialized test scripts for services with detailed tests"""
    print("\n--- Running Specialized Service Tests ---")
    
    # Dictionary mapping service names to their test script paths
    service_tests = {
        "Jira": "test_jira.py",
        "Microsoft Graph (Email & Calendar)": "test_ms_graph.py"
    }
    
    for service_name, test_script in service_tests.items():
        print(f"\n=== Testing {service_name} ===")
        try:
            # Check if test script exists
            if not os.path.exists(test_script):
                print(f"Test script {test_script} not found, skipping...")
                continue
                
            # For Windows, use python command explicitly
            if sys.platform.startswith('win'):
                result = subprocess.run(["python", test_script], capture_output=True, text=True)
            else:
                result = subprocess.run(["python3", test_script], capture_output=True, text=True)
                
            print(result.stdout)
            if result.stderr:
                print(f"Errors: {result.stderr}")
        except Exception as e:
            print(f"Error running test script {test_script}: {str(e)}")

if __name__ == "__main__":
    print("Starting API tests...")
    
    try:
        test_health_check()
        
        # Basic API tests
        test_youtube_videos()
        test_news_headlines()
        
        # Run specialized service tests
        test_all_services()
        
        print("\nAll tests completed successfully!")
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Could not connect to the server at {BASE_URL}")
        print("Make sure the server is running before executing tests.")
    except Exception as e:
        print(f"\nERROR: {str(e)}") 