#!/usr/bin/env python3
"""
Test calendar creation via the updated general calendar service
This tests the new approach that avoids photography-specific travel time logic.
"""

import requests
import json
from datetime import datetime, timedelta
import sys

# Configuration
API_BASE_URL = "http://localhost:14000"  # Change if different
API_KEY = "your-uuid-here"  # Replace with actual UUID

def test_calendar_creation():
    """Test creating calendar events with the new general calendar approach"""
    
    print("🧪 Testing General Calendar Creation (No Travel Time Logic)")
    print("=" * 60)
    
    # Test 1: Simple meeting
    simple_event = {
        "title": "Team Meeting",
        "start_time": (datetime.now() + timedelta(hours=2)).isoformat() + "Z",
        "end_time": (datetime.now() + timedelta(hours=3)).isoformat() + "Z",
        "notes": "Weekly team sync meeting"
    }
    
    # Test 2: Meeting with location
    location_event = {
        "title": "Client Meeting",
        "start_time": (datetime.now() + timedelta(days=1, hours=10)).isoformat() + "Z",
        "end_time": (datetime.now() + timedelta(days=1, hours=11)).isoformat() + "Z",
        "location": "Conference Room A",
        "notes": "Meeting with ABC Corp"
    }
    
    # Test 3: Meeting with attendees
    attendee_event = {
        "title": "Project Kickoff",
        "start_time": (datetime.now() + timedelta(days=2, hours=14)).isoformat() + "Z",
        "end_time": (datetime.now() + timedelta(days=2, hours=15, minutes=30)).isoformat() + "Z",
        "location": "Zoom",
        "notes": "Kickoff meeting for new project",
        "attendees": ["john@example.com", "jane@example.com"]
    }
    
    test_events = [
        ("Simple Meeting", simple_event),
        ("Meeting with Location", location_event),
        ("Meeting with Attendees", attendee_event)
    ]
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    results = []
    
    for test_name, event_data in test_events:
        print(f"\n📅 Test: {test_name}")
        print(f"   Title: {event_data['title']}")
        print(f"   Time: {event_data['start_time']} to {event_data['end_time']}")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/daily",
                json=event_data,
                headers=headers,
                timeout=15
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    event_info = result.get('event', {})
                    print(f"   ✅ SUCCESS")
                    print(f"   📋 Event ID: {event_info.get('appointment_id')}")
                    print(f"   🔗 Web Link: {event_info.get('web_link', 'N/A')}")
                    
                    # Verify no travel events were created
                    if 'travel_to_id' not in event_info and 'travel_from_id' not in event_info:
                        print(f"   ✅ No travel time complications (as expected)")
                    else:
                        print(f"   ⚠️  Travel events detected (unexpected)")
                    
                    results.append(("PASS", test_name))
                else:
                    print(f"   ❌ API Error: {result.get('error')}")
                    results.append(("FAIL", test_name))
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                except:
                    error_msg = response.text
                print(f"   ❌ HTTP {response.status_code}: {error_msg}")
                results.append(("FAIL", test_name))
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            results.append(("ERROR", test_name))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    pass_count = sum(1 for status, _ in results if status == "PASS")
    fail_count = sum(1 for status, _ in results if status == "FAIL")
    error_count = sum(1 for status, _ in results if status == "ERROR")
    
    for status, test_name in results:
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{icon} {status}: {test_name}")
    
    print(f"\nResults: {pass_count} passed, {fail_count} failed, {error_count} errors")
    
    if pass_count == len(test_events):
        print("🎉 All tests passed! General calendar creation is working properly.")
        return 0
    else:
        print("❌ Some tests failed. Check the logs above for details.")
        return 1

def test_health_check():
    """Test the health check to verify general calendar service is available"""
    print("\n🏥 Testing Health Check")
    print("-" * 30)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            general_calendar_status = health_data.get('services', {}).get('general_calendar', 'unknown')
            create_calendar_status = health_data.get('features', {}).get('create_calendar', 'unknown')
            
            print(f"General Calendar Service: {general_calendar_status}")
            print(f"Create Calendar Feature: {create_calendar_status}")
            
            if general_calendar_status == "configured" and create_calendar_status == "configured":
                print("✅ Health check passed - General calendar service is ready")
                return True
            else:
                print("❌ Health check failed - General calendar service not ready")
                return False
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

if __name__ == "__main__":
    if API_KEY == "your-uuid-here":
        print("❌ Please set your actual UUID in API_KEY")
        sys.exit(1)
    
    # Test health first
    if not test_health_check():
        print("\n❌ Health check failed. Make sure services are running.")
        sys.exit(1)
    
    # Run calendar creation tests
    exit_code = test_calendar_creation()
    sys.exit(exit_code) 