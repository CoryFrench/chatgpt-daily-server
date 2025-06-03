# Docker Setup Guide

This guide will help you run your ChatGPT Daily GPT Server using Docker.

## Quick Start

1. **Copy environment template**
   ```bash
   cp env.template .env
   ```

2. **Edit your environment variables**
   Open `.env` and configure your API keys and credentials:
   - Jira API credentials
   - Microsoft Graph API credentials
   - Other configuration options

3. **Build and run with Docker Compose**
   ```bash
   # For production
   docker-compose up --build

   # For development (with hot reloading)
   docker-compose --profile dev up --build
   ```

## Available Commands

### Production Mode
```bash
# Build and start the application
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop the application
docker-compose down

# View logs
docker-compose logs -f web
```

### Development Mode
```bash
# Start development environment with hot reloading
docker-compose --profile dev up --build

# Run in background
docker-compose --profile dev up -d --build

# Stop development environment
docker-compose --profile dev down

# View development logs
docker-compose logs -f web-dev
```

### Direct Docker Commands
```bash
# Build the image
docker build -t chatgpt-daily-gpt-server .

# Run the container
docker run -p 14000:14000 --env-file .env chatgpt-daily-gpt-server

# Run with environment variables
docker run -p 14000:14000 \
  -e JIRA_API_KEY=your_key \
  -e JIRA_EMAIL=your_email \
  chatgpt-daily-gpt-server
```

## Environment Variables

Create a `.env` file based on `env.template` with the following variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `FLASK_ENV` | Flask environment (development/production) | Yes |
| `DEBUG` | Enable debug mode (true/false) | Yes |
| `PORT` | Port to run the application on | No (default: 14000) |
| `JIRA_API_KEY` | Your Jira API key | No |
| `JIRA_EMAIL` | Your Jira email address | No |
| `JIRA_PROJECT_KEY` | Your Jira project key | No |
| `JIRA_URL` | Your Jira instance URL | No |
| `TENANT_ID` | Azure tenant ID for Microsoft Graph | No |
| `CLIENT_ID` | Azure client ID for Microsoft Graph | No |
| `CLIENT_SECRET` | Azure client secret for Microsoft Graph | No |

## Health Check

The application includes a health check endpoint at `/health` that verifies:
- Application status
- Jira configuration
- Microsoft Graph configuration
- Service availability

Access it at: `http://localhost:14000/health`

## Ports

- **14000**: Main application port

## Multi-Container Setup

This configuration uses a safe, scalable port scheme optimized for multi-container deployments:

- **Port 14000**: ChatGPT Daily GPT Server (this app)
- **Port 14100**: Available for your next app
- **Port 14200**: Available for another app
- **Port 14300**: Available for another app
- **etc.**

**Benefits of the 14000+ range:**
- ✅ No conflicts with system services
- ✅ Not on browser blacklists (unlike 6000, 6666, etc.)
- ✅ 100-port increments give room for growth
- ✅ Easy to organize and remember

### Example Reverse Proxy Configuration

**Nginx:**
```nginx
upstream chatgpt_daily {
    server localhost:14000;
}

upstream app2 {
    server localhost:14100;
}

upstream app3 {
    server localhost:14200;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location /api/chatgpt-daily/ {
        proxy_pass http://chatgpt_daily/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/app2/ {
        proxy_pass http://app2/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/app3/ {
        proxy_pass http://app3/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Traefik (docker-compose labels):**
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.chatgpt-daily.rule=PathPrefix(`/api/chatgpt-daily`)"
  - "traefik.http.routers.chatgpt-daily.entrypoints=web"
  - "traefik.http.services.chatgpt-daily.loadbalancer.server.port=14000"
```

## Volumes

### Production
- No volumes mounted (for security and performance)

### Development
- Current directory mounted to `/app` for hot reloading

## Security Features

- Non-root user execution
- Minimal base image (Python slim)
- Environment variable based configuration
- Health checks for monitoring

## Troubleshooting

### Container won't start
1. Check your `.env` file configuration
2. Verify all required environment variables are set
3. Check logs: `docker-compose logs web`

### Permission errors
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
```

### Port already in use
```bash
# Change port in docker-compose.yml or stop conflicting service
sudo lsof -i :14000
```

### Memory issues
```bash
# Increase Docker memory limit in Docker Desktop settings
# Or use smaller worker count in Dockerfile
```

## Production Deployment

For production deployment:

1. Use the production Docker Compose profile
2. Set strong passwords and API keys
3. Use a reverse proxy (nginx/traefik) in front of the containers
4. Enable SSL/TLS termination at the reverse proxy level
5. Set up log aggregation
6. Configure monitoring and alerts

## Development Tips

- Use the development profile for hot reloading
- Check application logs regularly
- Test API endpoints using the health check
- Use environment variables for all configuration
- Keep your `.env` file secure and never commit it
- For multi-container development, consider using different compose files or override files 