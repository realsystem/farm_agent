#!/bin/bash

set -e

echo "🌾 Farm Agent Local Development Setup"
echo "======================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker & Docker Compose found"
echo ""

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env"
    echo ""
    echo "📝 Edit .env and add your credentials:"
    echo "   - OPENAI_API_KEY=sk-proj-..."
    echo "   - HA_TOKEN= (leave blank, we'll add it after HA starts)"
    echo ""
    echo "   nano .env"
    echo ""
fi

# Check if OPENAI_API_KEY is set
if ! grep -q "OPENAI_API_KEY=sk" .env 2>/dev/null; then
    echo "⚠️  OPENAI_API_KEY not set in .env"
    echo "   Edit .env and add your OpenAI API key before starting"
    echo ""
fi

# Start the environment
echo "Starting Docker Compose..."
docker-compose -f docker-compose.dev.yml up -d

echo "✅ Containers started"
echo ""
echo "⏳ Waiting for Home Assistant to start (this takes 60+ seconds)..."
echo ""

# Wait for Home Assistant health check
max_attempts=120
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f docker-compose.dev.yml ps homeassistant | grep -q "healthy"; then
        echo "✅ Home Assistant is ready!"
        break
    fi

    attempt=$((attempt + 1))
    if [ $((attempt % 10)) -eq 0 ]; then
        echo "   Still waiting... ($attempt seconds elapsed)"
    fi
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo "⚠️  Home Assistant didn't report healthy status yet"
    echo "   Check logs with: docker-compose -f docker-compose.dev.yml logs homeassistant"
fi

echo ""
echo "🎯 Next steps:"
echo ""
echo "1. Open Home Assistant in your browser:"
echo "   http://localhost:8123"
echo ""
echo "2. Complete the onboarding flow"
echo ""
echo "3. Create a long-lived access token:"
echo "   Click your user icon (bottom left) → Long-lived access tokens"
echo "   Click 'Create Token' → Name: 'Farm Agent Local Dev'"
echo ""
echo "4. Add the token to .env:"
echo "   HA_TOKEN=<paste_token_here>"
echo ""
echo "5. Restart Farm Agent:"
echo "   docker-compose -f docker-compose.dev.yml restart farm-agent"
echo ""
echo "6. Test the agent:"
echo "   curl 'http://localhost:8080/ask?q=What%20is%20the%20battery%20voltage?'"
echo ""
echo "For more details, see LOCAL_DEVELOPMENT.md"
