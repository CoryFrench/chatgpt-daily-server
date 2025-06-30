import os
import json
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from atlassian import Jira
import msal
import requests
import psycopg2
import psycopg2.extras
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Debug mode flag
DEBUG = os.getenv('DEBUG', 'false').lower() in ('true', 'yes', '1')

# Database Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# User Authentication Setup
authorized_users = {}  # Cache for auth_id -> email mappings
last_user_refresh = None
USER_CACHE_DURATION = 300  # 5 minutes

def get_case_insensitive_header(header_name):
    """Get header value regardless of case"""
    # Check common variations of X-API-Key
    variations = [
        'X-API-Key',
        'x-api-key', 
        'X-Api-Key',
        'X-API-KEY',
        'x-API-key'
    ]
    
    for variation in variations:
        value = request.headers.get(variation)
        if value:
            return value
    return None

def connect_db():
    """Create database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return None

def load_authorized_users():
    """Load auth_id -> email mappings from database"""
    global authorized_users, last_user_refresh
    
    # Check if we need to refresh cache
    now = datetime.now()
    if last_user_refresh and (now - last_user_refresh).seconds < USER_CACHE_DURATION:
        return authorized_users
    
    try:
        conn = connect_db()
        if not conn:
            print("ERROR: Cannot connect to database for user authentication")
            return {}
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT auth_id, email, name 
            FROM utils.user_details 
            WHERE auth_id IS NOT NULL 
            AND email IS NOT NULL
            AND authorized = true
        """)
        
        users = cursor.fetchall()
        new_authorized_users = {}
        
        for user in users:
            auth_id = str(user['auth_id'])  # Convert UUID to string
            new_authorized_users[auth_id] = {
                'email': user['email'],
                'name': user['name']
            }
        
        cursor.close()
        conn.close()
        
        authorized_users = new_authorized_users
        last_user_refresh = now
        
        print(f"Loaded {len(authorized_users)} authorized users from database")
        return authorized_users
        
    except Exception as e:
        print(f"Error loading authorized users: {str(e)}")
        return {}

def get_authenticated_user():
    """Get authenticated user from API key"""
    api_key = get_case_insensitive_header('X-API-Key')
    
    if not api_key:
        return None
    
    # Load users if cache is empty or stale
    users = load_authorized_users()
    
    # Look up user by auth_id
    user_info = users.get(api_key)
    if user_info:
        return user_info
    
    return None

def require_auth(f):
    """Decorator to require user authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_authenticated_user()
        
        if not user:
            return jsonify({
                'error': 'Invalid or missing API key',
                'message': 'Please provide a valid X-API-Key header with your user UUID'
            }), 401
        
        # Add user info to request context
        request.authenticated_user = user
        return f(*args, **kwargs)
    
    return decorated_function

# Load authorized users on startup
print("Initializing user authentication system...")
load_authorized_users()

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

# Calendar Backend Service Configuration
CALENDAR_BACKEND_URL = os.getenv('CALENDAR_BACKEND_URL', 'http://calendar-backend:5000')
DEFAULT_PHOTOGRAPHER_EMAIL = os.getenv('DEFAULT_PHOTOGRAPHER_EMAIL', 'cory@wfpcc.com')

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
    
    # If Jira client is not initialized, return error instead of mock data
    if not jira_client:
        error_msg = "Jira client not configured or authentication failed"
        print(f"ERROR: {error_msg}")
        return {"error": error_msg}
    
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

def get_important_emails(user_email, priority_contacts=None, hours=72):
    """Get important emails using Microsoft Graph API"""
    
    # Get access token for Microsoft Graph API
    access_token = get_ms_graph_token()
    
    # If no token, return error instead of mock data
    if not access_token:
        error_msg = "Microsoft Graph API not configured or authentication failed"
        print(f"ERROR: {error_msg}")
        return {"error": error_msg}
    
    try:
        # Get emails from the specified number of hours (default 72)
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Calculate date filter for the specified hours
        now = datetime.utcnow()
        cutoff_time = (now - timedelta(hours=int(hours))).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Build the query
        query_params = {
            '$top': 50,  # Limit to 50 emails
            '$orderby': 'receivedDateTime desc',
            '$filter': f"receivedDateTime ge {cutoff_time}",
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
        
        # Make the request to MS Graph API using the authenticated user's email
        response = requests.get(
            f'https://graph.microsoft.com/v1.0/users/{user_email}/messages',
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

def get_calendar_events(user_email, start_date, end_date):
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
    
    # If no token, return error instead of mock data
    if not access_token:
        error_msg = "Microsoft Graph API not configured or authentication failed"
        print(f"ERROR: {error_msg}")
        return {"error": error_msg}
    
    try:
        # Format dates for MS Graph API
        start_str = start.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_str = end.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Query parameters for calendarView
        query_params = {
            'startDateTime': start_str,
            'endDateTime': end_str,
            '$select': 'id,subject,start,end,location,attendees',
            '$orderby': 'start/dateTime'
        }
        
        # Make the request to MS Graph API using calendarView to expand recurring events
        response = requests.get(
            f'https://graph.microsoft.com/v1.0/users/{user_email}/calendar/calendarView',
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

def create_calendar_event_via_backend(user_email, event_data):
    """Create a calendar event via the calendar-backend general calendar service"""
    
    try:
        # Map our event data to the general calendar format (no photography logic)
        backend_data = {
            "title": event_data['title'],
            "start_time": event_data['start_time'],
            "end_time": event_data['end_time'],
            "attendee_email": user_email,  # Book on the user's calendar
            "location": event_data.get('location'),
            "notes": event_data.get('notes'),
            "attendees": event_data.get('attendees', [])
        }
        
        # Remove None values to clean up the request
        backend_data = {k: v for k, v in backend_data.items() if v is not None}
        
        print(f"Creating general calendar event via backend: {CALENDAR_BACKEND_URL}/api/general-calendar/event")
        print(f"Backend data: {backend_data}")
        
        # Send request to calendar-backend general calendar endpoint
        response = requests.post(
            f"{CALENDAR_BACKEND_URL}/api/general-calendar/event",
            json=backend_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"General calendar backend response status: {response.status_code}")
        print(f"General calendar backend response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                event_info = result.get('event', {})
                return {
                    "success": True,
                    "message": result.get('message', 'Calendar event created successfully'),
                    "event": {
                        "appointment_id": event_info.get('appointment_id'),
                        "title": event_info.get('title'),
                        "start_time": event_info.get('start_time'),
                        "end_time": event_info.get('end_time'),
                        "location": event_info.get('location'),
                        "notes": event_info.get('notes'),
                        "web_link": event_info.get('web_link'),
                        "attendees": event_info.get('attendees', [])
                    }
                }
            else:
                return {
                    "error": result.get('error', 'Unknown error from general calendar backend')
                }
        else:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get('error', error_detail)
            except:
                pass
            
            return {
                "error": f"General calendar backend error (HTTP {response.status_code}): {error_detail}"
            }
    
    except requests.exceptions.RequestException as e:
        print(f"Request error to general calendar backend: {str(e)}")
        return {
            "error": f"Failed to connect to general calendar backend: {str(e)}"
        }
    except Exception as e:
        print(f"Unexpected error in general calendar creation: {str(e)}")
        return {
            "error": f"General calendar creation failed: {str(e)}"
        }

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
@require_auth
def jira_tasks():
    limit = request.args.get('limit', 5)
    
    tasks = get_jira_tasks(limit)
    return jsonify(tasks)

@app.route('/important', methods=['GET'])
@require_auth
def important_emails():
    priority_contacts = request.args.get('priorityContacts')
    hours = request.args.get('hours', 72)  # Default to 72 hours (3 days)
    user_email = request.authenticated_user['email']
    
    print(f"Email request: user={user_email}, hours={hours}, priority_contacts={priority_contacts}")
    
    emails = get_important_emails(user_email, priority_contacts, hours)
    
    # Retry logic: if we get 0 results, try once more after a brief delay
    if isinstance(emails, list) and len(emails) == 0:
        print("Emails returned 0 results, retrying in 2 seconds...")
        time.sleep(2)
        emails = get_important_emails(user_email, priority_contacts, hours)
        print(f"Email retry response: {len(emails) if isinstance(emails, list) else 'error'} emails")
    
    print(f"Email final response: {len(emails) if isinstance(emails, list) else 'error'} emails")
    
    return jsonify(emails)

@app.route('/events', methods=['GET'])
@require_auth
def calendar_events():
    user_email = request.authenticated_user['email']
    
    # Get start and end dates, with defaults for next 72 hours
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    
    # If no dates provided, default to today through next 3 days
    if not start_date:
        start_date = datetime.now().strftime('%Y-%m-%d')
    if not end_date:
        end_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    
    print(f"Calendar request: user={user_email}, start={start_date}, end={end_date}")
    
    events = get_calendar_events(user_email, start_date, end_date)
    
    # Retry logic: if we get 0 results, try once more after a brief delay
    if isinstance(events, list) and len(events) == 0:
        print("Calendar returned 0 results, retrying in 2 seconds...")
        time.sleep(2)
        events = get_calendar_events(user_email, start_date, end_date)
        print(f"Calendar retry response: {len(events) if isinstance(events, list) else 'error'} events")
    
    print(f"Calendar final response: {len(events) if isinstance(events, list) else 'error'} events")
    
    # Debug: Log first event details if we have events
    if isinstance(events, list) and len(events) > 0:
        print(f"Sample event: {events[0]}")
    
    if isinstance(events, dict) and "error" in events:
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
    
    # Check database connectivity
    db_status = "not configured"
    user_count = 0
    try:
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM utils.user_details WHERE auth_id IS NOT NULL AND authorized = true")
            user_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            db_status = "configured"
    except Exception as e:
        print(f"Health check database error: {str(e)}")
        db_status = f"error: {str(e)}"
    
    # Check calendar backend connectivity
    calendar_backend_status = "not configured"
    general_calendar_status = "not configured"
    try:
        response = requests.get(f"{CALENDAR_BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            calendar_backend_status = "configured"
        else:
            calendar_backend_status = f"error: HTTP {response.status_code}"
    except requests.exceptions.RequestException as e:
        calendar_backend_status = f"error: {str(e)}"
    except Exception as e:
        calendar_backend_status = f"error: {str(e)}"
    
    # Check general calendar endpoint
    try:
        response = requests.get(f"{CALENDAR_BACKEND_URL}/api/general-calendar/health", timeout=5)
        if response.status_code == 200:
            general_calendar_status = "configured"
        else:
            general_calendar_status = f"error: HTTP {response.status_code}"
    except requests.exceptions.RequestException as e:
        general_calendar_status = f"error: {str(e)}"
    except Exception as e:
        general_calendar_status = f"error: {str(e)}"
    
    return jsonify({
        "status": "ok", 
        "version": "2.2.0",
        "authentication": "UUID-based user authentication",
        "authorized_users": user_count,
        "services": {
            "database": db_status,
            "jira": jira_status,
            "microsoft_graph": ms_graph_status,
            "calendar_backend": calendar_backend_status,
            "general_calendar": general_calendar_status,
            "youtube": "not configured",
            "news": "not configured"
        },
        "features": {
            "read_emails": "configured",
            "read_calendar": "configured", 
            "create_calendar": "configured" if general_calendar_status == "configured" else "not configured",
            "jira_tasks": "configured" if jira_client else "not configured"
        }
    })

# Daily endpoint - handles both GET (summary) and POST (create event)
@app.route('/daily', methods=['GET', 'POST'])
@require_auth
def daily_endpoint():
    """Combined endpoint for daily calendar/email data (GET) and calendar event creation (POST)"""
    user_email = request.authenticated_user['email']
    
    if request.method == 'GET':
        # GET: Return daily summary (calendar + emails)
        # Get parameters
        priority_contacts = request.args.get('priorityContacts')
        email_hours = request.args.get('emailHours', 72)  # Default to 72 hours for emails
        
        # Calendar date range (default: today through next 3 days)
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        
        print(f"Daily summary request: user={user_email}, calendar={start_date} to {end_date}, email_hours={email_hours}")
        
        # Get calendar events
        events = get_calendar_events(user_email, start_date, end_date)
        
        # Retry logic for calendar
        if isinstance(events, list) and len(events) == 0:
            print("Calendar returned 0 results, retrying in 2 seconds...")
            time.sleep(2)
            events = get_calendar_events(user_email, start_date, end_date)
            print(f"Calendar retry response: {len(events) if isinstance(events, list) else 'error'} events")
        
        # Get emails
        emails = get_important_emails(user_email, priority_contacts, email_hours)
        
        # Retry logic for emails
        if isinstance(emails, list) and len(emails) == 0:
            print("Emails returned 0 results, retrying in 2 seconds...")
            time.sleep(2)
            emails = get_important_emails(user_email, priority_contacts, email_hours)
            print(f"Email retry response: {len(emails) if isinstance(emails, list) else 'error'} emails")
        
        # Handle errors
        calendar_error = None
        email_error = None
        
        if isinstance(events, dict) and "error" in events:
            calendar_error = events["error"]
            events = []
        
        if isinstance(emails, dict) and "error" in emails:
            email_error = emails["error"]
            emails = []
        
        # Create combined response
        response = {
            "calendar": {
                "events": events,
                "count": len(events),
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "error": calendar_error
            },
            "emails": {
                "messages": emails,
                "count": len(emails),
                "hours_back": int(email_hours),
                "priority_contacts": priority_contacts,
                "error": email_error
            },
            "summary": {
                "total_events": len(events),
                "total_emails": len(emails),
                "user": user_email,
                "generated_at": datetime.now().isoformat()
            }
        }
        
        print(f"Daily summary response: {len(events)} events, {len(emails)} emails")
        return jsonify(response)
    
    elif request.method == 'POST':
        # POST: Create new calendar event
        try:
            # Get event data from request
            event_data = request.get_json()
            
            if not event_data:
                return jsonify({"error": "No event data provided"}), 400
            
            # Validate required fields
            required_fields = ['title', 'start_time', 'end_time']
            missing_fields = [field for field in required_fields if not event_data.get(field)]
            
            if missing_fields:
                return jsonify({
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                    "required_fields": required_fields
                }), 400
            
            # Validate date format
            try:
                start_time = datetime.fromisoformat(event_data['start_time'].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(event_data['end_time'].replace('Z', '+00:00'))
                
                if end_time <= start_time:
                    return jsonify({"error": "End time must be after start time"}), 400
                    
            except ValueError as e:
                return jsonify({
                    "error": "Invalid date format. Use ISO 8601 format (e.g., '2024-01-15T10:00:00Z')",
                    "details": str(e)
                }), 400
            
            print(f"Creating calendar event via daily endpoint for user: {user_email}")
            print(f"Event data: {event_data}")
            
            # Create the event via calendar-backend
            result = create_calendar_event_via_backend(user_email, event_data)
            
            if "error" in result:
                return jsonify(result), 500
            
            print(f"Calendar event created successfully: {result}")
            return jsonify(result)
        
        except Exception as e:
            print(f"Exception in calendar event creation: {str(e)}")
            return jsonify({
                "error": "Failed to create calendar event",
                "details": str(e)
            }), 500

@app.route('/auth-test', methods=['GET'])
@require_auth
def auth_test():
    user = request.authenticated_user
    return jsonify({
        "status": "authenticated",
        "user": {
            "name": user['name'],
            "email": user['email']
        },
        "message": "Authentication successful! You can access your personal data."
    })

if __name__ == '__main__':
    # Try to get MS Graph token at startup
    get_ms_graph_token()
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug) 