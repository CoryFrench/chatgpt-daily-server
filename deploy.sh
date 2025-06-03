#!/bin/bash

# ChatGPT Daily GPT Server - Full Stack Deployment Script
# This script deploys both the app and reverse proxy together

set -e  # Exit on any error

echo "🚀 ChatGPT Daily GPT Server - Full Stack Deployment"
echo "=================================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    if [ -f "env.template" ]; then
        cp env.template .env
        echo "✅ Created .env from template. Please edit it with your API keys."
        echo "   Required: JIRA_API_KEY, JIRA_EMAIL, TENANT_ID, CLIENT_ID, CLIENT_SECRET"
    else
        echo "❌ No env.template found. Please create a .env file with required variables."
        exit 1
    fi
fi

# Deployment options
echo ""
echo "Choose deployment mode:"
echo "1) Production (recommended)"
echo "2) Development (with hot reload)"
echo "3) Stop all services"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "🏭 Starting production deployment..."
        docker-compose -f docker-compose.full-stack.yml down
        docker-compose -f docker-compose.full-stack.yml up --build -d
        ;;
    2)
        echo "🔧 Starting development deployment..."
        docker-compose -f docker-compose.full-stack.yml --profile dev down
        docker-compose -f docker-compose.full-stack.yml --profile dev up --build -d
        ;;
    3)
        echo "🛑 Stopping all services..."
        docker-compose -f docker-compose.full-stack.yml down
        docker-compose -f docker-compose.full-stack.yml --profile dev down
        echo "✅ All services stopped."
        exit 0
        ;;
    *)
        echo "❌ Invalid choice."
        exit 1
        ;;
esac

# Wait for services to start
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Health checks
echo ""
echo "🩺 Checking service health..."

# Check gateway
if curl -f http://localhost/health >/dev/null 2>&1; then
    echo "✅ API Gateway: Healthy"
else
    echo "❌ API Gateway: Not responding"
fi

# Check app
if curl -f http://localhost/api/chatgpt-daily/health >/dev/null 2>&1; then
    echo "✅ ChatGPT Daily App: Healthy"
else
    echo "❌ ChatGPT Daily App: Not responding"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "🌐 Access your services:"
echo "   Gateway Dashboard: http://localhost"
echo "   Alternative port:  http://localhost:8080"
echo "   Direct app access: http://localhost:14000 (if needed)"
echo ""
echo "📋 Useful commands:"
echo "   View logs:     docker-compose -f docker-compose.full-stack.yml logs -f"
echo "   Stop services: docker-compose -f docker-compose.full-stack.yml down"
echo "   Restart:       docker-compose -f docker-compose.full-stack.yml restart"
echo "" 