#!/bin/bash

echo "🚀 AI Image Restoration App - Production Deployment"
echo "=================================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run as root"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ .env file created from template"
        echo "📝 Please edit .env and add your API keys:"
        echo "   - OPENAI_API_KEY"
        echo "   - REPLICATE_API_TOKEN"
        echo ""
        echo "After editing .env, run this script again."
        exit 0
    else
        echo "❌ .env.example not found"
        exit 1
    fi
fi

# Check if API keys are set
if ! grep -q "OPENAI_API_KEY=your_openai_api_key_here" .env && ! grep -q "REPLICATE_API_TOKEN=your_replicate_api_token_here" .env; then
    echo "✅ API keys appear to be configured"
else
    echo "⚠️  Please configure your API keys in .env file"
    echo "   - OPENAI_API_KEY"
    echo "   - REPLICATE_API_TOKEN"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads outputs temp

# Build and start the application
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting application..."
docker-compose up -d

# Wait for application to start
echo "⏳ Waiting for application to start..."
sleep 10

# Check if application is running
if curl -f http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ Application is running successfully!"
    echo ""
    echo "🌐 Access your application at: http://localhost:3000"
    echo "📊 Health check: http://localhost:3000/health"
    echo ""
    echo "📋 Useful commands:"
    echo "   - View logs: docker-compose logs -f"
    echo "   - Stop app: docker-compose down"
    echo "   - Restart app: docker-compose restart"
    echo "   - Update app: ./deploy.sh"
else
    echo "❌ Application failed to start"
    echo "📋 Check logs with: docker-compose logs"
    exit 1
fi