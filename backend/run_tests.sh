#!/bin/bash

# Run tests with coverage and logging
echo "🧪 Running T2T2 Backend Tests..."

# Set test environment variables
export ENVIRONMENT=test
export LOG_LEVEL=DEBUG
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export JWT_SECRET_KEY="test_secret_key"
export TELEGRAM_BOT_TOKEN="test_bot_token"
export TELEGRAM_API_ID="12345"
export TELEGRAM_API_HASH="test_api_hash"
export OPENAI_API_KEY="test_openai_key"

# Run linting first
echo "🎨 Running code formatting checks..."
black --check . || (echo "❌ Code formatting issues found. Run 'black .' to fix." && exit 1)

echo "🔍 Running linting..."
ruff check . || (echo "❌ Linting issues found." && exit 1)

# Run tests
echo "🧪 Running tests..."
pytest -v --cov=. --cov-report=term-missing --cov-report=html

echo "✅ Tests complete! Coverage report available in htmlcov/index.html"