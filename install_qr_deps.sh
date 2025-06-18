#!/bin/bash
# Install dependencies for QR authentication

echo "📦 Installing QR authentication dependencies..."

# QR code generation
pip install qrcode[pil]

# Web server support
pip install flask flask-cors

# Async support for Flask
pip install nest_asyncio

echo "✅ QR authentication dependencies installed!"
echo ""
echo "To use QR authentication:"
echo "1. Start the QR server: python t2t2_qr_auth.py"
echo "2. Start the chat indexer: python t2t2_chat_indexer.py"
echo "3. Users can authenticate by scanning QR codes!"