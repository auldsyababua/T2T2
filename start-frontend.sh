#!/bin/bash
# Start the frontend development server

echo "🚀 Starting T2T2 Frontend..."
echo "================================"

# Check if node_modules exists
if [ ! -d "UI/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd UI && npm install
    cd ..
fi

# Start the development server
echo "🌐 Starting Vite development server..."
cd UI && npm run dev