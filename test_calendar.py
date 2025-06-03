import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Base URL of the API server
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')

def test_calendar_valid_dates():
    """Test calendar with valid dates in different formats"""
    print("\n=== Testing Calendar API with Valid Dates ===")
    
    # Test 1: Current date to 7 days ahead (ISO format)
    today = datetime.now().strftime("%Y-%m-%d")
    future = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    print(f"\nTest 1: Using date-only format ({today} to {future})")
    response = requests.get(f"{BASE_URL}/events?startDate={today}&endDate={future}")
    
    if response.status_code == 200:
        events = response.json()
        print(f"Success! Retrieved {len(events)} events")
        
        if len(events) > 0:
            print("First event details:")
            print(f"  Title: {events[0].get('title')}")
            print(f"  Start: {events[0].get('start')}")
            print(f"  End: {events[0].get('end')}")
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test 2: Current date to 7 days ahead (ISO timestamp format)
    today_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    future_ts = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    
    print(f"\nTest 2: Using timestamp format ({today_ts} to {future_ts})")
    response = requests.get(f"{BASE_URL}/events?startDate={today_ts}&endDate={future_ts}")
    
    if response.status_code == 200:
        events = response.json()
        print(f"Success! Retrieved {len(events)} events")
        
        if len(events) > 0:
            print("First event details:")
            print(f"  Title: {events[0].get('title')}")
            print(f"  Start: {events[0].get('start')}")
            print(f"  End: {events[0].get('end')}")
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test 3: Next month range
    next_month_start = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    next_month_end = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    
    print(f"\nTest 3: Next month ({next_month_start} to {next_month_end})")
    response = requests.get(f"{BASE_URL}/events?startDate={next_month_start}&endDate={next_month_end}")
    
    if response.status_code == 200:
        events = response.json()
        print(f"Success! Retrieved {len(events)} events")
        
        if len(events) > 0:
            print("First event details:")
            print(f"  Title: {events[0].get('title')}")
            print(f"  Start: {events[0].get('start')}")
            print(f"  End: {events[0].get('end')}")
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")

def test_calendar_error_cases():
    """Test calendar API error handling"""
    print("\n=== Testing Calendar API Error Handling ===")
    
    # Test 1: Invalid date format
    print("\nTest 1: Invalid date format")
    today = datetime.now().strftime("%Y-%m-%d")
    response = requests.get(f"{BASE_URL}/events?startDate=invalid&endDate={today}")
    
    if response.status_code == 400:
        print(f"✓ Correctly rejected invalid date (Status: {response.status_code})")
        print(f"Error message: {response.json().get('error')}")
    else:
        print(f"✗ Unexpected response for invalid date: {response.status_code}")
    
    # Test 2: Missing date
    print("\nTest 2: Missing date parameter")
    response = requests.get(f"{BASE_URL}/events?startDate={today}")
    
    if response.status_code == 400:
        print(f"✓ Correctly rejected missing date (Status: {response.status_code})")
        print(f"Error message: {response.json().get('error')}")
    else:
        print(f"✗ Unexpected response for missing date: {response.status_code}")
    
    # Test 3: End date before start date
    print("\nTest 3: End date before start date")
    end_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    response = requests.get(f"{BASE_URL}/events?startDate={today}&endDate={end_date}")
    
    # Note: This might not be an error in our current implementation
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        events = response.json()
        print(f"Retrieved {len(events)} events (expected 0 since end date is before start date)")
    else:
        print(f"Error message: {response.json().get('error')}")

if __name__ == "__main__":
    print("Starting Calendar API tests...")
    
    try:
        test_calendar_valid_dates()
        test_calendar_error_cases()
        
        print("\nAll calendar tests completed.")
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Could not connect to the server at {BASE_URL}")
        print("Make sure the server is running before executing tests.")
    except Exception as e:
        print(f"\nERROR: {str(e)}") 