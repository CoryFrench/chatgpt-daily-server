import requests
import os
from dotenv import load_dotenv
import json
from atlassian import Jira

# Load environment variables
load_dotenv()

# Base URL of the API server
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')

# Debug mode flag
DEBUG = os.getenv('DEBUG', 'false').lower() in ('true', 'yes', '1')

# Jira credentials for direct testing
JIRA_URL = os.getenv('JIRA_URL')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_KEY = os.getenv('JIRA_API_KEY')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'WFPCC')

def test_jira_connection():
    """Test the health endpoint to check if Jira is configured"""
    
    print("\n=== Testing Jira Configuration ===")
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        services = data.get('services', {})
        jira_status = services.get('jira', 'unknown')
        
        print(f"Jira status: {jira_status}")
        
        if jira_status == "configured":
            print("✅ Jira is properly configured!")
        else:
            print("❌ Jira is not configured. Check your .env file.")
            print("Required variables:")
            print("  - JIRA_URL")
            print("  - JIRA_EMAIL")
            print("  - JIRA_API_KEY")
            print("  - JIRA_PROJECT_KEY")
    else:
        print(f"❌ Failed to get health status: {response.status_code}")

def direct_jira_diagnostics():
    """Run direct Jira diagnostics without using the API server"""
    if not DEBUG:
        return  # Skip diagnostics unless in debug mode
        
    print("\n=== DIRECT JIRA DIAGNOSTICS ===")
    
    if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_KEY]):
        print("Missing Jira credentials in .env file")
        return
    
    print(f"Jira URL: {JIRA_URL}")
    print(f"Jira Email: {JIRA_EMAIL}")
    print(f"Project Key: {JIRA_PROJECT_KEY}")
    
    try:
        # Try direct connection
        print("\nConnecting directly to Jira...")
        jira = Jira(
            url=JIRA_URL,
            username=JIRA_EMAIL,
            password=JIRA_API_KEY,
            cloud=True
        )
        
        # List accessible projects
        print("\nListing accessible projects:")
        projects = jira.projects()
        print(f"Found {len(projects)} projects")
        
        for project in projects:
            print(f"  - {project.get('key')}: {project.get('name')}")
        
        # Check if our project exists
        project_keys = [p.get('key') for p in projects]
        if JIRA_PROJECT_KEY in project_keys:
            print(f"\n✅ Project '{JIRA_PROJECT_KEY}' found!")
            
            # Get project information
            try:
                project_info = jira.project(JIRA_PROJECT_KEY)
                print(f"Project name: {project_info.get('name')}")
            except Exception as e:
                print(f"Error getting project info: {str(e)}")
        else:
            print(f"\n❌ Project '{JIRA_PROJECT_KEY}' not found in accessible projects!")
            print(f"Available projects: {', '.join(project_keys)}")
        
        # Get all statuses
        try:
            print("\nAvailable statuses:")
            statuses = jira.get_all_statuses()
            for status in statuses:
                print(f"  - {status.get('name')} (id: {status.get('id')})")
        except Exception as e:
            print(f"Error getting statuses: {str(e)}")
        
        # Try to get any issues from the project
        print(f"\nTrying to get any issues from project {JIRA_PROJECT_KEY}:")
        
        try:
            # Simple query - should return all issues in the project
            issues = jira.jql(f"project = {JIRA_PROJECT_KEY}", limit=10)
            total = issues.get('total', 0)
            print(f"Total issues found: {total}")
            
            if total > 0:
                print("\nFirst few issues:")
                for issue in issues.get('issues', [])[:5]:
                    key = issue.get('key')
                    fields = issue.get('fields', {})
                    summary = fields.get('summary', 'No summary')
                    status = fields.get('status', {}).get('name', 'Unknown')
                    print(f"  - {key}: {summary} (Status: {status})")
                
                # Extract status names from actual issues
                statuses = set()
                for issue in issues.get('issues', []):
                    fields = issue.get('fields', {})
                    if fields.get('status') and fields['status'].get('name'):
                        statuses.add(fields['status'].get('name'))
                
                print(f"\nStatuses used in this project: {', '.join(statuses)}")
                
                # Now try to get TO DO and IN PROGRESS issues
                todo_in_progress_query = f"project = {JIRA_PROJECT_KEY} AND status in ('TO DO', 'IN PROGRESS')"
                print(f"\nFetching TO DO and IN PROGRESS issues: {todo_in_progress_query}")
                todo_issues = jira.jql(todo_in_progress_query, limit=10)
                print(f"Found {len(todo_issues.get('issues', []))} issues with status TO DO or IN PROGRESS")
                
                if len(todo_issues.get('issues', [])) > 0:
                    print("\nIssues in TO DO or IN PROGRESS:")
                    for issue in todo_issues.get('issues', []):
                        key = issue.get('key')
                        fields = issue.get('fields', {})
                        summary = fields.get('summary', 'No summary')
                        status = fields.get('status', {}).get('name', 'Unknown')
                        print(f"  - {key}: {summary} (Status: {status})")
                
                # Try each status individually
                for status_name in statuses:
                    if "do" in status_name.lower() or "progress" in status_name.lower():
                        single_status_query = f"project = {JIRA_PROJECT_KEY} AND status = '{status_name}'"
                        print(f"\nTrying with status '{status_name}': {single_status_query}")
                        status_issues = jira.jql(single_status_query, limit=5)
                        print(f"Found {len(status_issues.get('issues', []))} issues with status '{status_name}'")
            else:
                print("No issues found in this project!")
        except Exception as e:
            print(f"Error querying issues: {str(e)}")
            
    except Exception as e:
        print(f"Failed to connect to Jira: {str(e)}")
    
    print("\n=== END DIRECT JIRA DIAGNOSTICS ===")

def test_jira_tasks():
    """Test the tasks endpoint to fetch Jira tasks"""
    
    print("\n=== Testing Jira Tasks API ===")
    
    # Test with default limit
    response = requests.get(f"{BASE_URL}/tasks")
    
    if response.status_code == 200:
        tasks = response.json()
        
        print(f"Retrieved {len(tasks)} tasks")
        
        if len(tasks) > 0:
            print("\nFirst task details:")
            print(f"  ID: {tasks[0].get('id')}")
            print(f"  Title: {tasks[0].get('title')}")
            print(f"  Status: {tasks[0].get('status')}")
            print(f"  Priority: {tasks[0].get('priority')}")
            print(f"  Assignee: {tasks[0].get('assignee')}")
        else:
            print("No tasks were returned. This could be normal if you have no tasks in To Do or In Progress status.")
        
        # Test with custom limit
        limit = 2
        response = requests.get(f"{BASE_URL}/tasks?limit={limit}")
        
        if response.status_code == 200:
            limited_tasks = response.json()
            print(f"\nTesting with limit={limit}: Retrieved {len(limited_tasks)} tasks")
            
            # Check if limit was applied
            if len(limited_tasks) <= limit:
                print(f"✅ Limit of {limit} was correctly applied")
            else:
                print(f"❌ Limit of {limit} was not correctly applied")
        else:
            print(f"❌ Failed to get tasks with limit: {response.status_code}")
    else:
        print(f"❌ Failed to get tasks: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    print("Starting Jira API tests...")
    
    try:
        test_jira_connection()
        
        # Only run diagnostics if DEBUG is enabled
        direct_jira_diagnostics()
        
        test_jira_tasks()
        
        print("\nAll tests completed.")
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Could not connect to the server at {BASE_URL}")
        print("Make sure the server is running before executing tests.")
    except Exception as e:
        print(f"\nERROR: {str(e)}") 