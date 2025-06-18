#!/bin/bash
# Setup script for T2T2 Team Bot

echo "🤖 T2T2 Team Bot Setup"
echo "====================="
echo ""

# Check if service key is set
if grep -q "your_service_key_here" .env.supabase_bot; then
    echo "⚠️  You need to add your Supabase service_role key!"
    echo ""
    echo "To get your service_role key:"
    echo "1. Go to: https://supabase.com/dashboard/project/tzsfkbwpgklwvsyypacc/settings/api"
    echo "2. Copy the 'service_role' key (starts with 'eyJ...')"
    echo "3. Edit .env.supabase_bot and replace 'your_service_key_here'"
    echo ""
    echo "Press Enter after adding your key..."
    read
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install telethon python-telegram-bot langchain-openai langchain-community chromadb supabase cryptography python-dotenv

# Test Supabase connection
echo ""
echo "🔗 Testing Supabase connection..."
python test_supabase_connection.py

echo ""
echo "✅ Setup complete! Run: python supabase_team_bot.py"