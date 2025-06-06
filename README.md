# Daily GPT Server

A Python Flask server that implements custom API endpoints to support a CustomGPT with 5 custom actions:

1. YouTube Monitor - Fetch recent videos from selected channels or categories
2. News Aggregator - Fetch news articles from preferred sources
3. Jira Service - Fetch current Jira tasks
4. Email Service - Fetch recent high-priority emails (using Microsoft Graph API)
5. Calendar Service - Retrieve calendar events for specified date ranges (using Microsoft Graph API)

## Setup

1. Clone this repository:
```
git clone <repository-url>
cd daily-gpt-server
```

2. Create a virtual environment and activate it:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following content:
```
PORT=5000
FLASK_ENV=development

# Jira configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_KEY=your-api-token
JIRA_PROJECT_KEY=PROJ

# Microsoft Graph API configuration
TENANT_ID=your-tenant-id
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
```

### Setting up Jira integration

To use the Jira integration:

1. Go to your Atlassian account: https://id.atlassian.com/manage-profile/security/api-tokens
2. Create an API token and copy it
3. Add the token to your .env file as JIRA_API_KEY
4. Set your Atlassian account email as JIRA_EMAIL
5. Set your Jira URL (e.g., https://your-domain.atlassian.net)
6. Set your project key as JIRA_PROJECT_KEY (e.g., PROJ)

### Setting up Microsoft Graph API integration

The server uses Microsoft Graph API to access email and calendar data for a specific user (cory@wfpcc.com). To set this up:

1. Register an application in the Azure Portal (https://portal.azure.com)
2. Go to Azure Active Directory > App registrations > New registration
3. Name your application and set the appropriate redirect URI
4. After registering, note the Application (client) ID and Directory (tenant) ID
5. Create a client secret: Go to Certificates & secrets > New client secret
6. Set permissions: API permissions > Add permission > Microsoft Graph > Application permissions:
   - For Email: Mail.Read
   - For Calendar: Calendars.Read
7. Click "Grant admin consent"
8. Add the following to your .env file:
   ```
   TENANT_ID=your-tenant-id
   CLIENT_ID=your-client-id
   CLIENT_SECRET=your-client-secret
   ```

**Note:** The API is configured to only access data for the email address `cory@wfpcc.com`. This is hardcoded into the application for security purposes.

## Running the Server

Start the development server:
```
python app.py
```

The server will run on http://localhost:5000

## Endpoints

### 1. YouTube Monitor
```
GET /videos?channels=TechWorld,MusicTrends&categories=tech,music
```

### 2. News Aggregator
```
GET /headlines?topics=technology,economy&hours=24
```

### 3. Jira Service
```
GET /tasks?limit=5
```
Returns your Jira tasks marked as To Do or In Progress, sorted by most recently updated.

### 4. Email Service
```
GET /important?priorityContacts=boss@company.com,client@company.com
```
Returns important emails from the last 24 hours. If priorityContacts are specified, only emails from those addresses will be returned.

### 5. Calendar Service
```
GET /events?startDate=2023-12-01&endDate=2023-12-05
```
Returns calendar events within the specified date range.

## Health Check
```
GET /health
```
The health check endpoint now shows which services are configured.

## Production Deployment

For production deployment, consider using Gunicorn:
```
gunicorn app:app
```

## Note

This server currently has real integration with Jira and Microsoft Graph API (for email and calendar) and uses mock data for the other services. As you implement more integrations, you'll need to add the appropriate API keys and configuration to your .env file. 