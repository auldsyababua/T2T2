#!/bin/bash
# Start the backend development server

echo "🚀 Starting T2T2 Backend..."
echo "================================"

# Check environment variables
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "📝 Copy .env.example to .env and fill in your credentials:"
    echo "   cp .env.example .env"
    echo ""
fi

# Check if required environment variables are set
if [ -f ".env" ]; then
    source .env
    
    if [ -z "$TELEGRAM_API_ID" ] || [ -z "$TELEGRAM_API_HASH" ]; then
        echo "❌ Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set!"
        echo "📱 Get these from https://my.telegram.org/apps"
        exit 1
    fi
    
    if [ -z "$SESSION_ENCRYPTION_KEY" ]; then
        echo "⚠️  Warning: SESSION_ENCRYPTION_KEY not set!"
        echo "🔐 Generate one with: openssl rand -base64 32"
    fi
    
    if [ -z "$SECRET_KEY" ]; then
        echo "⚠️  Warning: SECRET_KEY not set!"
        echo "🔐 Generate one with: openssl rand -hex 32"
    fi
fi

# Install dependencies if needed
if ! python -c "import telethon" 2>/dev/null; then
    echo "📦 Installing backend dependencies..."
    pip install -r requirements.txt
fi

# Run database migrations if alembic is configured
if [ -f "alembic.ini" ]; then
    echo "🗄️  Running database migrations..."
    alembic upgrade head
fi

# Start the backend server
echo "🌐 Starting Uvicorn server on http://0.0.0.0:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload