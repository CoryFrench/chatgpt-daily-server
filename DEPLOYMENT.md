# 🚀 ChatGPT Daily GPT Server - Full Stack Deployment

This package contains everything needed to deploy your ChatGPT Daily GPT Server with reverse proxy on any Docker-enabled machine.

## 📦 What's Included

```
📁 ChatGPT Daily GPT Server/
├── 🐳 Docker Configuration
│   ├── Dockerfile                     # Production container
│   ├── Dockerfile.dev                 # Development container  
│   ├── docker-compose.yml             # Single app deployment
│   └── docker-compose.full-stack.yml  # Complete stack deployment
│
├── 🌐 Reverse Proxy
│   ├── reverse-proxy/nginx.conf       # External proxy config
│   ├── reverse-proxy/nginx-internal.conf  # Unified stack config
│   └── reverse-proxy/docker-compose.yml   # Standalone proxy
│
├── 🚀 Deployment Scripts
│   ├── deploy.sh                      # Linux/Mac deployment
│   ├── deploy.ps1                     # Windows PowerShell deployment
│   └── env.template                   # Environment variables template
│
├── 📱 Application Code
│   ├── app.py                         # Main Flask application
│   ├── requirements.txt               # Python dependencies
│   └── *.py                          # Supporting files
│
└── 📚 Documentation
    ├── DEPLOYMENT.md                  # This file
    ├── DOCKER_README.md              # Docker-specific docs
    └── README.md                      # Application docs
```

## 🎯 Deployment Options

### Option 1: Standalone Deployment
**Best for**: Testing individual service, development

```powershell
# Using script
.\deploy.ps1 standalone

# Or manually
docker-compose up -d --build
```

**Access Points**:
- 📡 **Direct Access**: `http://localhost:14100`
- 🔐 **Authentication**: Check `.env` file or `env.template` for credentials

### Option 2: Full-Stack with Reverse Proxy
**Best for**: Production, integration with other services

```powershell
# Using script
.\deploy.ps1 fullstack

# Or manually
docker-compose -f docker-compose.full-stack.yml up -d --build
```

**Access Points**:
- 🌐 **Gateway Dashboard**: `http://localhost`
- 👥 **Agent Directory**: `http://localhost/api/agent-directory/`
- 📡 **Direct Access**: `http://localhost:14100`
- 🔐 **Authentication**: Check `.env` file or `env.template` for credentials

### Option 3: Development Mode
**Best for**: Active development, debugging

```powershell
# Using script
.\deploy.ps1 dev

# Or manually
cp env.template .env
docker-compose --profile dev up -d --build
```

**Features**:
- 🔄 **Hot Reload**: Automatic restart on code changes
- 📊 **Development Logging**: Enhanced debugging output
- 🛠️ **Dev Dependencies**: Includes nodemon and debugging tools

## ⚙️ Quick Setup

### Prerequisites
- ✅ Docker installed and running
- ✅ Docker Compose available
- ✅ Ports 80 and 14000 available

### Setup Steps

1. **Copy this entire folder** to your target machine

2. **Configure environment variables:**
   ```bash
   # Copy template and edit with your API keys
   cp env.template .env
   
   # Edit .env with your actual values:
   # - JIRA_API_KEY, JIRA_EMAIL, JIRA_URL
   # - TENANT_ID, CLIENT_ID, CLIENT_SECRET (for Microsoft Graph)
   ```

3. **Deploy using scripts:**
   ```bash
   # Windows
   .\deploy.ps1

   # Linux/Mac  
   ./deploy.sh
   ```

4. **Access your services:**
   - 🌐 **Gateway Dashboard**: http://localhost
   - 🔧 **Alternative port**: http://localhost:8080
   - 📊 **Direct app**: http://localhost:14000 (if needed)

## 🌍 URLs & Endpoints

### Via Reverse Proxy (Recommended)
```
🏠 Dashboard:           http://localhost/
🔧 Gateway Health:      http://localhost/health

📊 ChatGPT Daily:
├── Health:             http://localhost/api/chatgpt-daily/health
├── Videos:             http://localhost/api/chatgpt-daily/videos
├── Tasks:              http://localhost/api/chatgpt-daily/tasks
├── Headlines:          http://localhost/api/chatgpt-daily/headlines
└── Events:             http://localhost/api/chatgpt-daily/events?startDate=2025-01-01&endDate=2025-01-31

🔮 Future Apps:
├── App2:               http://localhost/api/app2/*
└── App3:               http://localhost/api/app3/*
```

### Direct Access (Fallback)
```
📊 ChatGPT Daily:       http://localhost:14000/*
```

## 📋 Management Commands

### Using Full Stack
```bash
# Start production
docker-compose -f docker-compose.full-stack.yml up -d

# Start development (with hot reload)
docker-compose -f docker-compose.full-stack.yml --profile dev up -d

# View logs
docker-compose -f docker-compose.full-stack.yml logs -f

# Stop everything
docker-compose -f docker-compose.full-stack.yml down

# Restart services
docker-compose -f docker-compose.full-stack.yml restart
```

### Using Scripts
```bash
# Windows PowerShell
.\deploy.ps1 -Mode production   # Start production
.\deploy.ps1 -Mode development  # Start development  
.\deploy.ps1 -Mode stop         # Stop all services

# Linux/Mac Bash
./deploy.sh                     # Interactive mode
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Flask Configuration
FLASK_ENV=production
DEBUG=false
PORT=14000

# Jira Configuration (optional)
JIRA_API_KEY=your_jira_api_key_here
JIRA_EMAIL=your_jira_email@example.com
JIRA_PROJECT_KEY=YOUR_PROJECT_KEY
JIRA_URL=https://your-domain.atlassian.net

# Microsoft Graph API Configuration (optional)
TENANT_ID=your_azure_tenant_id
CLIENT_ID=your_azure_client_id
CLIENT_SECRET=your_azure_client_secret
```

### Port Configuration
- **Port 80**: Reverse proxy (public access)
- **Port 8080**: Alternative reverse proxy port
- **Port 14000**: ChatGPT Daily app (internal)
- **Port 14100**: Reserved for future App2
- **Port 14200**: Reserved for future App3

## 🚀 Adding New Applications

1. **Deploy your new app** on the next port (14100, 14200, etc.)

2. **Update reverse proxy** (if using external setup):
   ```bash
   # Edit reverse-proxy/nginx.conf
   # Add new upstream and location blocks
   
   # Restart proxy
   cd reverse-proxy
   docker-compose restart
   ```

3. **For full stack**: Apps should be added to `docker-compose.full-stack.yml`

## 🔍 Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker info

# Check what's using ports
# Windows
netstat -an | findstr :80
netstat -an | findstr :14000

# Linux/Mac
lsof -i :80
lsof -i :14000

# View container logs
docker-compose -f docker-compose.full-stack.yml logs
```

### Health checks failing
```bash
# Test direct app access
curl http://localhost:14000/health

# Test gateway
curl http://localhost/health

# Check container status
docker-compose -f docker-compose.full-stack.yml ps
```

### Gateway shows 502 errors
- ✅ Make sure your app is running and healthy
- ✅ Check firewall settings
- ✅ Verify .env configuration

## 📈 Production Considerations

### Security
- [ ] Change default ports if needed
- [ ] Set up SSL certificates in nginx
- [ ] Configure proper firewall rules
- [ ] Use secrets management for API keys

### Monitoring
- [ ] Set up log aggregation
- [ ] Configure health check alerts
- [ ] Monitor resource usage
- [ ] Set up backup procedures

### Scaling
- [ ] Use external load balancer for multiple instances
- [ ] Configure horizontal scaling
- [ ] Set up database clustering (if applicable)
- [ ] Implement CI/CD pipelines

## 🎯 Migration Instructions

### From Development to Production
1. Copy this entire folder to production server
2. Update `.env` with production API keys
3. Run: `docker-compose -f docker-compose.full-stack.yml up -d`

### To Different Server
1. Stop services: `docker-compose -f docker-compose.full-stack.yml down`
2. Copy entire project folder
3. Start on new server: `./deploy.sh` or `.\deploy.ps1`

### Backup & Restore
```bash
# Create backup
tar -czf chatgpt-daily-backup.tar.gz .

# Restore
tar -xzf chatgpt-daily-backup.tar.gz
./deploy.sh
```

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs: `docker-compose logs -f`
3. Verify your `.env` configuration
4. Ensure all required ports are available
5. Check Docker and Docker Compose versions

**Tested Environments:**
- ✅ Windows 10/11 with Docker Desktop
- ✅ macOS with Docker Desktop  
- ✅ Ubuntu 20.04+ with Docker CE
- ✅ CentOS 8+ with Docker CE 

## 🔒 Security Features

- **🛡️ Helmet.js**: Security headers and CSP protection
- **🍪 Secure Sessions**: Encrypted session management
- **🔐 Password Protection**: Authentication required for directory access
- **👤 Non-root User**: Container runs with restricted privileges
- **🚫 CSRF Protection**: Built-in request validation

### 🔐 Checking Authentication Credentials

To view your current authentication settings (without logging them):

```bash
# Check what environment variables are set
cat .env | grep -E "(DIRECTORY_PASSWORD|SESSION_SECRET)"

# Or check the template for defaults
cat env.template | grep -E "(DIRECTORY_PASSWORD|SESSION_SECRET)"
```

**⚠️ Security Best Practices:**
- Never log or display passwords in console output
- Always change default credentials in production
- Use strong, randomly generated session secrets
- Enable secure cookies when using HTTPS 