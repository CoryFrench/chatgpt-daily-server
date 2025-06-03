import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Base URL of the API server
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')

def test_ms_graph_connection():
    """Test the health endpoint to check if Microsoft Graph API is configured"""
    
    print("\n=== Testing Microsoft Graph API Configuration ===")
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        services = data.get('services', {})
        ms_graph_status = services.get('microsoft_graph', 'unknown')
        
        print(f"Microsoft Graph API status: {ms_graph_status}")
        
        if ms_graph_status == "configured":
            print("✅ Microsoft Graph API is properly configured!")
        else:
            print("❌ Microsoft Graph API is not configured. Check your .env file.")
            print("Required variables:")
            print("  - TENANT_ID")
            print("  - CLIENT_ID")
            print("  - CLIENT_SECRET")
    else:
        print(f"❌ Failed to get health status: {response.status_code}")

def test_email_endpoint():
    """Test the important emails endpoint"""
    
    print("\n=== Testing Email API ===")
    
    # Test with no parameters
    response = requests.get(f"{BASE_URL}/important")
    
    if response.status_code == 200:
        emails = response.json()
        
        print(f"Retrieved {len(emails)} emails")
        
        if len(emails) > 0:
            print("\nFirst email details:")
            print(f"  Subject: {emails[0].get('subject')}")
            print(f"  From: {emails[0].get('sender')}")
            print(f"  Received: {emails[0].get('receivedAt')}")
            print(f"  Read: {emails[0].get('read')}")
            print(f"  Snippet: {emails[0].get('snippet')[:50]}...")
        else:
            print("No emails were returned. This could be normal if there are no emails in the last 24 hours.")
        
        # Test with priority contacts
        # Replace with an actual email that might be in your inbox
        test_contact = "example@company.com"
        response = requests.get(f"{BASE_URL}/important?priorityContacts={test_contact}")
        
        if response.status_code == 200:
            filtered_emails = response.json()
            print(f"\nTesting with priorityContacts={test_contact}: Retrieved {len(filtered_emails)} emails")
        else:
            print(f"❌ Failed to get emails with priority contacts: {response.status_code}")
    else:
        print(f"❌ Failed to get emails: {response.status_code}")
        print(f"Response: {response.text}")

def test_calendar_endpoint():
    """Test the calendar events endpoint"""
    
    print("\n=== Testing Calendar API ===")
    
    # Get current date and date 7 days in future
    today = datetime.now().strftime("%Y-%m-%d")
    future = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Test with date range
    response = requests.get(f"{BASE_URL}/events?startDate={today}&endDate={future}")
    
    if response.status_code == 200:
        events = response.json()
        
        print(f"Retrieved {len(events)} events for the next 7 days")
        
        if len(events) > 0:
            print("\nFirst event details:")
            print(f"  Title: {events[0].get('title')}")
            print(f"  Start: {events[0].get('start')}")
            print(f"  End: {events[0].get('end')}")
            print(f"  Location: {events[0].get('location')}")
            print(f"  Attendees: {', '.join(events[0].get('attendees', []))}")
        else:
            print("No events were returned. This could be normal if there are no events in the next 7 days.")
        
        # Test with invalid dates (should return error)
        response = requests.get(f"{BASE_URL}/events?startDate=invalid&endDate={future}")
        print(f"\nInvalid date test: {response.status_code} - {response.json() if response.status_code != 200 else 'Success'}")
    else:
        print(f"❌ Failed to get calendar events: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    print("Starting Microsoft Graph API tests...")
    
    try:
        test_ms_graph_connection()
        test_email_endpoint()
        test_calendar_endpoint()
        
        print("\nAll tests completed.")
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Could not connect to the server at {BASE_URL}")
        print("Make sure the server is running before executing tests.")
    except Exception as e:
        print(f"\nERROR: {str(e)}") 