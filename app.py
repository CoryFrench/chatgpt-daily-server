import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from atlassian import Jira
import msal
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Debug mode flag
DEBUG = os.getenv('DEBUG', 'false').lower() in ('true', 'yes', '1')

# Jira Connection Setup
JIRA_API_KEY = os.getenv('JIRA_API_KEY')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY')
JIRA_URL = os.getenv('JIRA_URL', 'https://your-domain.atlassian.net')

# Microsoft Graph API Setup
MS_TENANT_ID = os.getenv('TENANT_ID')
MS_CLIENT_ID = os.getenv('CLIENT_ID')
MS_CLIENT_SECRET = os.getenv('CLIENT_SECRET')
MS_USER_EMAIL = 'cory@wfpcc.com'  # Hardcoded to only allow this specific user
MS_GRAPH_SCOPES = ['https://graph.microsoft.com/.default']

# Initialize Jira client if credentials are available
jira_client = None
if JIRA_API_KEY and JIRA_EMAIL:
    try:
        jira_client = Jira(
            url=JIRA_URL,
            username=JIRA_EMAIL,
            password=JIRA_API_KEY,
            cloud=True
        )
        print("Jira client initialized successfully")
    except Exception as e:
        print(f"Error initializing Jira client: {str(e)}")

# Initialize Microsoft Graph access
ms_graph_token = None
ms_graph_configured = False

def get_ms_graph_token():
    """Get a Microsoft Graph API access token"""
    global ms_graph_token, ms_graph_configured
    
    # Check if we already have credentials
    if not all([MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET]):
        ms_graph_configured = False
        return None
    
    # Check if we have a valid token
    if ms_graph_token and datetime.now() < ms_graph_token['expires_at']:
        return ms_graph_token['access_token']
    
    try:
        # Create an MSAL app
        app = msal.ConfidentialClientApplication(
            client_id=MS_CLIENT_ID,
            client_credential=MS_CLIENT_SECRET,
            authority=f"https://login.microsoftonline.com/{MS_TENANT_ID}"
        )
        
        # Acquire token via client credentials grant
        result = app.acquire_token_for_client(scopes=MS_GRAPH_SCOPES)
        
        if "access_token" in result:
            # Calculate expiration time (token expires_in is in seconds)
            expires_at = datetime.now() + timedelta(seconds=result['expires_in'] - 300)  # 5 min buffer
            
            ms_graph_token = {
                'access_token': result['access_token'],
                'expires_at': expires_at
            }
            
            ms_graph_configured = True
            print("Microsoft Graph API token acquired successfully")
            return result['access_token']
        else:
            print(f"Error acquiring Microsoft Graph token: {result.get('error')}")
            print(f"Error description: {result.get('error_description')}")
            ms_graph_configured = False
            return None
    
    except Exception as e:
        print(f"Exception while acquiring Microsoft Graph token: {str(e)}")
        ms_graph_configured = False
        return None

# Mock data providers
def get_youtube_videos(channels=None, categories=None):
    videos = [
        {
            "id": "video1",
            "title": "Latest Tech Trends 2023",
            "channel": "TechWorld",
            "publishedAt": (datetime.now() - timedelta(hours=3)).isoformat(),
            "url": "https://youtube.com/watch?v=abc123",
            "thumbnail": "https://i.ytimg.com/vi/abc123/hqdefault.jpg",
            "category": "tech"
        },
        {
            "id": "video2",
            "title": "Breaking News: Market Update",
            "channel": "FinanceToday",
            "publishedAt": (datetime.now() - timedelta(hours=5)).isoformat(),
            "url": "https://youtube.com/watch?v=def456",
            "thumbnail": "https://i.ytimg.com/vi/def456/hqdefault.jpg",
            "category": "finance"
        },
        {
            "id": "video3",
            "title": "New Music Release Roundup",
            "channel": "MusicTrends",
            "publishedAt": (datetime.now() - timedelta(hours=8)).isoformat(),
            "url": "https://youtube.com/watch?v=ghi789",
            "thumbnail": "https://i.ytimg.com/vi/ghi789/hqdefault.jpg",
            "category": "music"
        }
    ]
    
    filtered_videos = videos
    
    if channels:
        channel_list = [ch.strip() for ch in channels.split(",")]
        filtered_videos = [v for v in filtered_videos if v["channel"] in channel_list]
    
    if categories:
        category_list = [cat.strip() for cat in categories.split(",")]
        filtered_videos = [v for v in filtered_videos if v["category"] in category_list]
    
    return filtered_videos

def get_news_headlines(topics=None, hours=24):
    news = [
        {
            "id": "news1",
            "title": "New AI Breakthrough Announced",
            "source": "Tech Times",
            "publishedAt": (datetime.now() - timedelta(hours=2)).isoformat(),
            "url": "https://techtimes.com/ai-breakthrough",
            "topic": "technology"
        },
        {
            "id": "news2",
            "title": "Housing Market Shows Signs of Recovery",
            "source": "Economy Daily",
            "publishedAt": (datetime.now() - timedelta(hours=6)).isoformat(),
            "url": "https://economydaily.com/housing-recovery",
            "topic": "real estate"
        },
        {
            "id": "news3",
            "title": "Central Bank Announces New Interest Rates",
            "source": "Financial Post",
            "publishedAt": (datetime.now() - timedelta(hours=10)).isoformat(),
            "url": "https://financialpost.com/interest-rates",
            "topic": "economy"
        }
    ]
    
    # Filter by publication time
    cutoff_time = datetime.now() - timedelta(hours=int(hours))
    filtered_news = [n for n in news if datetime.fromisoformat(n["publishedAt"]) > cutoff_time]
    
    # Filter by topics if provided
    if topics:
        topic_list = [t.strip() for t in topics.split(",")]
        filtered_news = [n for n in filtered_news if n["topic"] in topic_list]
    
    return filtered_news

def get_jira_tasks(limit=5):
    """Get Jira tasks that are To Do or In Progress"""
    
    # If Jira client is not initialized, return mock data
    if not jira_client:
        if DEBUG:
            print("Using mock Jira data as Jira client is not initialized")
        tasks = [
            {
                "id": "PROJ-123",
                "title": "Implement new user authentication flow",
                "status": "In Progress",
                "priority": "High",
                "assignee": "John Smith",
                "updated": (datetime.now() - timedelta(days=1)).isoformat()
            },
            {
                "id": "PROJ-124",
                "title": "Fix payment processing bug",
                "status": "To Do",
                "priority": "Critical",
                "assignee": "John Smith",
                "updated": (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                "id": "PROJ-125",
                "title": "Update documentation for API v2",
                "status": "To Do",
                "priority": "Medium",
                "assignee": "John Smith",
                "updated": (datetime.now() - timedelta(hours=12)).isoformat()
            },
            {
                "id": "PROJ-126",
                "title": "Optimize database queries",
                "status": "In Progress",
                "priority": "High",
                "assignee": "John Smith",
                "updated": (datetime.now() - timedelta(hours=6)).isoformat()
            },
            {
                "id": "PROJ-127",
                "title": "Implement dark mode for mobile app",
                "status": "To Do",
                "priority": "Low",
                "assignee": "John Smith",
                "updated": (datetime.now() - timedelta(days=3)).isoformat()
            }
        ]
        
        # Only return tasks that are To Do or In Progress
        filtered_tasks = [t for t in tasks if t["status"] in ["To Do", "In Progress"]]
        
        # Limit the number of tasks returned
        return filtered_tasks[:int(limit)]
    
    try:
        if DEBUG:
            print("=== JIRA DIAGNOSTIC INFORMATION ===")
            print(f"Jira URL: {JIRA_URL}")
            print(f"Project Key: {JIRA_PROJECT_KEY}")
            
            # Check if we can get a simple list of projects
            try:
                print("\nChecking accessible projects...")
                projects = jira_client.projects()
                print(f"Number of accessible projects: {len(projects)}")
                for proj in projects:
                    print(f"  - {proj.get('key', 'Unknown')} ({proj.get('name', 'Unknown')})")
            except Exception as e:
                print(f"Error getting projects: {str(e)}")
            
            # Get all issues with simplest query to verify basic access
            try:
                print("\nTrying to get any issues from the project...")
                simple_jql = f"project = {JIRA_PROJECT_KEY}"
                print(f"Query: {simple_jql}")
                simple_issues = jira_client.jql(simple_jql, limit=5)
                print(f"Number of issues found: {len(simple_issues.get('issues', []))}")
                
                if len(simple_issues.get('issues', [])) > 0:
                    print("First issue details:")
                    first_issue = simple_issues['issues'][0]
                    print(f"  Key: {first_issue.get('key')}")
                    fields = first_issue.get('fields', {})
                    print(f"  Summary: {fields.get('summary', 'No summary')}")
                    if fields.get('status'):
                        print(f"  Status: {fields['status'].get('name', 'Unknown')}")
                    
                    # Collect all statuses from returned issues
                    statuses = set()
                    for issue in simple_issues.get('issues', []):
                        fields = issue.get('fields', {})
                        if fields.get('status') and fields['status'].get('name'):
                            statuses.add(fields['status'].get('name'))
                    
                    print(f"Statuses found in results: {', '.join(statuses)}")
                else:
                    print("No issues found with simple query - there might be an access issue.")
            except Exception as e:
                print(f"Error with simple query: {str(e)}")
            
            # Get all statuses from the instance
            try:
                statuses = jira_client.get_all_statuses()
                print("\nAll available statuses in Jira:")
                for status in statuses:
                    print(f"  - {status.get('name')} (id: {status.get('id')})")
            except Exception as e:
                print(f"Error getting statuses: {str(e)}")
            
            # Try different capitalization and variations on status names
            status_variations = [
                "('TO DO', 'IN PROGRESS')", 
                "('To Do', 'In Progress')",
                "('TODO', 'INPROGRESS')",
                "('To-Do', 'In-Progress')",
                "('ToDo', 'InProgress')"
            ]
            
            print("\nTrying different status name variations...")
            for status_var in status_variations:
                test_jql = f"project = {JIRA_PROJECT_KEY} AND status in {status_var} ORDER BY updated DESC"
                print(f"Testing: {test_jql}")
                try:
                    test_issues = jira_client.jql(test_jql, limit=5)
                    count = len(test_issues.get('issues', []))
                    print(f"  Results: {count} issues found")
                    if count > 0:
                        print("  SUCCESS! Found issues with this variation.")
                        print(f"  First issue: {test_issues['issues'][0].get('key')}")
                        # Use this variation for our actual query
                        jql = test_jql
                        break
                except Exception as e:
                    print(f"  Error: {str(e)}")
            
            print("\n=== END DIAGNOSTIC INFORMATION ===\n")
        
        # JQL to get all tasks in the project that are To Do or In Progress
        jql = f"project = {JIRA_PROJECT_KEY} AND status in ('TO DO', 'IN PROGRESS') ORDER BY updated DESC"
        
        if DEBUG:
            print(f"Executing Jira JQL query: {jql}")
        
        # Get issues from Jira
        issues = jira_client.jql(jql, limit=int(limit))
        
        if DEBUG:
            print(f"Jira returned {len(issues.get('issues', []))} issues")
        
        # If no issues found, try with a more permissive query
        if len(issues.get('issues', [])) == 0 and DEBUG:
            print("No issues found. Checking Jira project and status names...")
            
            # Check if the project exists
            try:
                project_data = jira_client.project(JIRA_PROJECT_KEY)
                print(f"Project {JIRA_PROJECT_KEY} exists: {project_data.get('name', 'Unknown')}")
            except Exception as e:
                print(f"Error getting project: {str(e)}")
            
            # Get available statuses
            try:
                statuses = jira_client.get_all_statuses()
                print("Available statuses in Jira:")
                for status in statuses:
                    print(f"  - {status.get('name')} (id: {status.get('id')})")
                
                # Try more permissive query
                jql_permissive = f"project = {JIRA_PROJECT_KEY}"
                print(f"Trying more permissive query: {jql_permissive}")
                issues_permissive = jira_client.jql(jql_permissive, limit=10)
                
                if len(issues_permissive.get('issues', [])) > 0:
                    print(f"Found {len(issues_permissive.get('issues', []))} issues with permissive query")
                    # Extract status names from actual issues
                    statuses_in_project = set()
                    for issue in issues_permissive.get('issues', []):
                        fields = issue.get('fields', {})
                        if fields.get('status') and fields['status'].get('name'):
                            statuses_in_project.add(fields['status']['name'])
                    
                    print(f"Statuses used in this project: {', '.join(statuses_in_project)}")
                    
                    # Try with exact status names found
                    if statuses_in_project:
                        status_clause = " OR ".join([f"status = '{status}'" for status in statuses_in_project 
                                                 if "do" in status.lower() or "progress" in status.lower()])
                        if status_clause:
                            jql_fixed = f"project = {JIRA_PROJECT_KEY} AND ({status_clause}) ORDER BY updated DESC"
                            print(f"Trying with exact status names: {jql_fixed}")
                            issues = jira_client.jql(jql_fixed, limit=int(limit))
                            print(f"Found {len(issues.get('issues', []))} issues with fixed status query")
            except Exception as e:
                print(f"Error getting statuses: {str(e)}")
        
        # Transform Jira issues to our response format
        tasks = []
        for issue in issues.get('issues', []):
            # Extract fields from the Jira issue
            issue_key = issue.get('key')
            fields = issue.get('fields', {})
            
            # Get priority
            priority = "Medium"
            if fields.get('priority'):
                priority = fields['priority'].get('name', "Medium")
            
            # Get assignee
            assignee = "Unassigned"
            if fields.get('assignee'):
                assignee = fields['assignee'].get('displayName', "Unassigned")
            
            # Get status
            status = "To Do"
            if fields.get('status'):
                status = fields['status'].get('name', "To Do")
            
            # Get updated date - handle date format
            updated = datetime.now().isoformat()
            if fields.get('updated'):
                try:
                    # Jira uses format like "2023-10-23T15:23:30.123+0000"
                    updated_str = fields['updated']
                    # Convert to datetime and back to ISO format
                    updated = datetime.fromisoformat(updated_str.replace('Z', '+00:00')).isoformat()
                except:
                    pass
            
            # Create task object
            task = {
                "id": issue_key,
                "title": fields.get('summary', 'No Title'),
                "status": status,
                "priority": priority,
                "assignee": assignee,
                "updated": updated
            }
            
            tasks.append(task)
        
        return tasks
    
    except Exception as e:
        if DEBUG:
            print(f"Error fetching Jira tasks: {str(e)}")
        # Return empty list if there's an error
        return []

def get_important_emails(priority_contacts=None):
    """Get important emails using Microsoft Graph API"""
    
    # Get access token for Microsoft Graph API
    access_token = get_ms_graph_token()
    
    # If no token, return mock data
    if not access_token:
        print("Using mock email data as Microsoft Graph is not configured")
        emails = [
            {
                "id": "email1",
                "subject": "Urgent: Project Deadline Update",
                "sender": "boss@company.com",
                "receivedAt": (datetime.now() - timedelta(hours=2)).isoformat(),
                "read": False,
                "snippet": "We need to move up the deadline for the project. Please update your timelines accordingly."
            },
            {
                "id": "email2",
                "subject": "Invoice #12345 Due",
                "sender": "accounting@supplier.com",
                "receivedAt": (datetime.now() - timedelta(hours=5)).isoformat(),
                "read": True,
                "snippet": "This is a reminder that invoice #12345 is due for payment in 3 days."
            },
            {
                "id": "email3",
                "subject": "Meeting Rescheduled",
                "sender": "colleague@company.com",
                "receivedAt": (datetime.now() - timedelta(hours=8)).isoformat(),
                "read": False,
                "snippet": "The team meeting has been rescheduled to tomorrow at 2pm."
            }
        ]
        
        # Only show emails from the last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        filtered_emails = [e for e in emails if datetime.fromisoformat(e["receivedAt"]) > cutoff_time]
        
        # Filter by priority contacts if provided
        if priority_contacts:
            contact_list = [contact.strip() for contact in priority_contacts.split(",")]
            filtered_emails = [e for e in filtered_emails if e["sender"] in contact_list]
        
        return filtered_emails
    
    try:
        # Get emails from the last 24 hours
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Calculate date filter for last 24 hours
        now = datetime.utcnow()
        yesterday = (now - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Build the query
        query_params = {
            '$top': 50,  # Limit to 50 emails
            '$orderby': 'receivedDateTime desc',
            '$filter': f"receivedDateTime ge {yesterday}",
            '$select': 'id,subject,receivedDateTime,isRead,bodyPreview,from'
        }
        
        # Handle priority contacts filter if provided
        if priority_contacts:
            contact_list = [contact.strip() for contact in priority_contacts.split(",")]
            contact_filters = []
            for contact in contact_list:
                contact_filters.append(f"from/emailAddress/address eq '{contact}'")
            
            if contact_filters:
                contact_filter = " or ".join(contact_filters)
                query_params['$filter'] = f"({query_params['$filter']}) and ({contact_filter})"
        
        # Make the request to MS Graph API
        response = requests.get(
            f'https://graph.microsoft.com/v1.0/users/{MS_USER_EMAIL}/messages',
            headers=headers,
            params=query_params
        )
        
        if response.status_code == 200:
            data = response.json()
            emails = []
            
            for msg in data.get('value', []):
                # Get sender email
                sender_email = None
                if msg.get('from') and msg['from'].get('emailAddress'):
                    sender_email = msg['from']['emailAddress'].get('address')
                
                # Create email object
                email = {
                    "id": msg.get('id'),
                    "subject": msg.get('subject', '(No Subject)'),
                    "sender": sender_email,
                    "receivedAt": msg.get('receivedDateTime'),
                    "read": msg.get('isRead', False),
                    "snippet": msg.get('bodyPreview', '')
                }
                
                emails.append(email)
            
            return emails
        else:
            print(f"Error fetching emails: {response.status_code}")
            print(f"Response: {response.text}")
            return []
    
    except Exception as e:
        print(f"Exception while fetching emails: {str(e)}")
        return []

def get_calendar_events(start_date, end_date):
    """Get calendar events using Microsoft Graph API"""
    
    # Parse input dates
    try:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError:
        # Try parsing as date only format (YYYY-MM-DD)
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format. Use ISO 8601 format (e.g., 2023-12-25 or 2023-12-25T14:30:00)."}
    
    # Get access token for Microsoft Graph API
    access_token = get_ms_graph_token()
    
    # If no token, return mock data
    if not access_token:
        print("Using mock calendar data as Microsoft Graph is not configured")
        events = [
            {
                "id": "event1",
                "title": "Team Stand-up",
                "start": datetime(start.year, start.month, start.day, 10, 0).isoformat(),
                "end": datetime(start.year, start.month, start.day, 10, 30).isoformat(),
                "location": "Conference Room A",
                "attendees": ["john@company.com", "mary@company.com"]
            },
            {
                "id": "event2",
                "title": "Client Meeting",
                "start": datetime(start.year, start.month, start.day, 14, 0).isoformat(),
                "end": datetime(start.year, start.month, start.day, 15, 30).isoformat(),
                "location": "Virtual",
                "attendees": ["client@example.com", "manager@company.com"]
            },
            {
                "id": "event3",
                "title": "Project Review",
                "start": datetime(end.year, end.month, end.day, 11, 0).isoformat(),
                "end": datetime(end.year, end.month, end.day, 12, 0).isoformat(),
                "location": "Conference Room B",
                "attendees": ["team@company.com"]
            }
        ]
        
        # Filter events within the date range
        filtered_events = [
            e for e in events if 
            datetime.fromisoformat(e["start"]) >= start and 
            datetime.fromisoformat(e["end"]) <= end
        ]
        
        return filtered_events
    
    try:
        # Format dates for MS Graph API
        start_str = start.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_str = end.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Query parameters
        query_params = {
            '$select': 'id,subject,start,end,location,attendees',
            '$orderby': 'start/dateTime',
            '$filter': f"start/dateTime ge '{start_str}' and end/dateTime le '{end_str}'"
        }
        
        # Make the request to MS Graph API
        response = requests.get(
            f'https://graph.microsoft.com/v1.0/users/{MS_USER_EMAIL}/calendar/events',
            headers=headers,
            params=query_params
        )
        
        if response.status_code == 200:
            data = response.json()
            events = []
            
            for event in data.get('value', []):
                # Get attendees
                attendee_emails = []
                for attendee in event.get('attendees', []):
                    if attendee.get('emailAddress') and attendee['emailAddress'].get('address'):
                        attendee_emails.append(attendee['emailAddress']['address'])
                
                # Get location
                location = "No location"
                if event.get('location') and event['location'].get('displayName'):
                    location = event['location']['displayName']
                
                # Create event object
                calendar_event = {
                    "id": event.get('id'),
                    "title": event.get('subject', '(No Title)'),
                    "start": event.get('start', {}).get('dateTime'),
                    "end": event.get('end', {}).get('dateTime'),
                    "location": location,
                    "attendees": attendee_emails
                }
                
                events.append(calendar_event)
            
            return events
        else:
            print(f"Error fetching calendar events: {response.status_code}")
            print(f"Response: {response.text}")
            return []
    
    except Exception as e:
        print(f"Exception while fetching calendar events: {str(e)}")
        return []

# API Routes
@app.route('/videos', methods=['GET'])
def youtube_videos():
    channels = request.args.get('channels')
    categories = request.args.get('categories')
    
    videos = get_youtube_videos(channels, categories)
    return jsonify(videos)

@app.route('/headlines', methods=['GET'])
def news_headlines():
    topics = request.args.get('topics')
    hours = request.args.get('hours', 24)
    
    headlines = get_news_headlines(topics, hours)
    return jsonify(headlines)

@app.route('/tasks', methods=['GET'])
def jira_tasks():
    limit = request.args.get('limit', 5)
    
    tasks = get_jira_tasks(limit)
    return jsonify(tasks)

@app.route('/important', methods=['GET'])
def important_emails():
    priority_contacts = request.args.get('priorityContacts')
    
    emails = get_important_emails(priority_contacts)
    return jsonify(emails)

@app.route('/events', methods=['GET'])
def calendar_events():
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    
    if not start_date or not end_date:
        return jsonify({"error": "startDate and endDate parameters are required"}), 400
    
    events = get_calendar_events(start_date, end_date)
    
    if "error" in events:
        return jsonify(events), 400
    
    return jsonify(events)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    jira_status = "configured" if jira_client else "not configured"
    ms_graph_status = "configured" if ms_graph_configured else "not configured"
    
    # Test MS Graph token if not already checked
    if not ms_graph_configured:
        get_ms_graph_token()
    
    return jsonify({
        "status": "ok", 
        "version": "1.0.0",
        "services": {
            "jira": jira_status,
            "microsoft_graph": ms_graph_status,
            "youtube": "not configured",
            "news": "not configured"
        }
    })

if __name__ == '__main__':
    # Try to get MS Graph token at startup
    get_ms_graph_token()
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug) 