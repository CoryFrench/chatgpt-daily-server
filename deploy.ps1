# ChatGPT Daily GPT Server - Full Stack Deployment Script (PowerShell)
# This script deploys both the app and reverse proxy together

param(
    [Parameter()]
    [ValidateSet("production", "development", "stop")]
    [string]$Mode = "production"
)

Write-Host "🚀 ChatGPT Daily GPT Server - Full Stack Deployment" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker and try again." -ForegroundColor Red
    exit 1
}

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  No .env file found. Creating from template..." -ForegroundColor Yellow
    if (Test-Path "env.template") {
        Copy-Item "env.template" ".env"
        Write-Host "✅ Created .env from template. Please edit it with your API keys." -ForegroundColor Green
        Write-Host "   Required: JIRA_API_KEY, JIRA_EMAIL, TENANT_ID, CLIENT_ID, CLIENT_SECRET" -ForegroundColor Yellow
    } else {
        Write-Host "❌ No env.template found. Please create a .env file with required variables." -ForegroundColor Red
        exit 1
    }
}

# Deployment modes
switch ($Mode) {
    "production" {
        Write-Host "🏭 Starting production deployment..." -ForegroundColor Blue
        docker-compose -f docker-compose.full-stack.yml down
        docker-compose -f docker-compose.full-stack.yml up --build -d
    }
    "development" {
        Write-Host "🔧 Starting development deployment..." -ForegroundColor Blue
        docker-compose -f docker-compose.full-stack.yml --profile dev down
        docker-compose -f docker-compose.full-stack.yml --profile dev up --build -d
    }
    "stop" {
        Write-Host "🛑 Stopping all services..." -ForegroundColor Yellow
        docker-compose -f docker-compose.full-stack.yml down
        docker-compose -f docker-compose.full-stack.yml --profile dev down
        Write-Host "✅ All services stopped." -ForegroundColor Green
        exit 0
    }
}

# Wait for services to start
Write-Host ""
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Health checks
Write-Host ""
Write-Host "🩺 Checking service health..." -ForegroundColor Blue

# Check gateway
try {
    $response = Invoke-WebRequest -Uri "http://localhost/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ API Gateway: Healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ API Gateway: Not responding" -ForegroundColor Red
}

# Check app
try {
    $response = Invoke-WebRequest -Uri "http://localhost/api/chatgpt-daily/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ ChatGPT Daily App: Healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ ChatGPT Daily App: Not responding" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access your services:" -ForegroundColor Cyan
Write-Host "   Gateway Dashboard: http://localhost" -ForegroundColor White
Write-Host "   Alternative port:  http://localhost:8080" -ForegroundColor White
Write-Host "   Direct app access: http://localhost:14000 (if needed)" -ForegroundColor White
Write-Host ""
Write-Host "📋 Useful commands:" -ForegroundColor Cyan
Write-Host "   View logs:     docker-compose -f docker-compose.full-stack.yml logs -f" -ForegroundColor White
Write-Host "   Stop services: docker-compose -f docker-compose.full-stack.yml down" -ForegroundColor White
Write-Host "   Restart:       docker-compose -f docker-compose.full-stack.yml restart" -ForegroundColor White
Write-Host ""

# Usage examples
Write-Host "💡 Script usage examples:" -ForegroundColor Cyan
Write-Host "   .\deploy.ps1                    # Production mode" -ForegroundColor White
Write-Host "   .\deploy.ps1 -Mode development  # Development mode" -ForegroundColor White
Write-Host "   .\deploy.ps1 -Mode stop         # Stop all services" -ForegroundColor White
Write-Host ""

function Deploy-Standalone {
    Write-Host "🐳 Deploying AgentDirectory standalone..." -ForegroundColor Green
    docker-compose up -d --build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ AgentDirectory deployed successfully!" -ForegroundColor Green
        Write-Host "📡 Direct access: http://localhost:14100" -ForegroundColor Cyan
        Write-Host "🔐 Check your .env file or env.template for authentication details" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Deployment failed!" -ForegroundColor Red
    }
}

function Deploy-FullStack {
    Write-Host "🌐 Deploying AgentDirectory with reverse proxy..." -ForegroundColor Green
    docker-compose -f docker-compose.full-stack.yml up -d --build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Full-stack deployment successful!" -ForegroundColor Green
        Write-Host "🌐 Gateway access: http://localhost" -ForegroundColor Cyan
        Write-Host "👥 Agent Directory: http://localhost/api/agent-directory/" -ForegroundColor Cyan
        Write-Host "📡 Direct access: http://localhost:14100" -ForegroundColor Cyan
        Write-Host "🔐 Check your .env file or env.template for authentication details" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Deployment failed!" -ForegroundColor Red
    }
}

function Deploy-Development {
    Write-Host "🛠️  Deploying AgentDirectory in development mode..." -ForegroundColor Green
    
    # Create .env file if it doesn't exist
    if (-not (Test-Path ".env")) {
        Copy-Item "env.template" ".env"
        Write-Host "📄 Created .env file from template" -ForegroundColor Yellow
    }
    
    docker-compose -f docker-compose.yml --profile dev up -d --build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Development environment ready!" -ForegroundColor Green
        Write-Host "📡 Dev server: http://localhost:14100" -ForegroundColor Cyan
        Write-Host "🔄 Hot reload enabled" -ForegroundColor Yellow
        Write-Host "🔐 Check your .env file for authentication details" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Development deployment failed!" -ForegroundColor Red
    }
} 