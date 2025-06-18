#!/bin/bash
# Start QR auth with public URL using ngrok

echo "🚀 Starting T2T2 QR Authentication with public URL..."
echo ""

# Kill any existing ngrok
pkill ngrok 2>/dev/null

# Start QR server
echo "1. Starting QR authentication server..."
python t2t2_qr_auth.py > qr_server.log 2>&1 &
QR_PID=$!
echo "   QR server PID: $QR_PID"

# Wait for server to start
sleep 3

# Start ngrok
echo ""
echo "2. Starting ngrok tunnel..."
ngrok http 5000 > /dev/null 2>&1 &
NGROK_PID=$!
echo "   Ngrok PID: $NGROK_PID"

# Wait for ngrok to start
sleep 3

# Get public URL
echo ""
echo "3. Getting public URL..."
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | cut -d'"' -f4)

if [ -z "$PUBLIC_URL" ]; then
    echo "❌ Failed to get ngrok URL"
    exit 1
fi

echo "   ✅ Public URL: $PUBLIC_URL"
echo ""
echo "📝 Next steps:"
echo "1. Update t2t2_chat_indexer.py to use this URL:"
echo "   server_url = \"$PUBLIC_URL\""
echo ""
echo "2. Restart the chat indexer bot"
echo ""
echo "3. Users can now authenticate from anywhere!"
echo ""
echo "Press Ctrl+C to stop both servers"

# Keep running
wait