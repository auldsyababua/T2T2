#!/usr/bin/env python3
"""
T2T2 Web-Based Authentication Server
Provides a secure way to authenticate without sending codes through Telegram
"""

import asyncio
import os
import secrets
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession
from supabase import create_client
from dotenv import load_dotenv
import logging

load_dotenv('.env.supabase_bot')

# Configuration
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Initialize
app = Flask(__name__)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
logging.basicConfig(level=logging.INFO)

# Store temporary auth sessions
AUTH_SESSIONS = {}  # token -> {user_id, client, phone, phone_code_hash, expires}

# HTML template for auth page
AUTH_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>T2T2 Authentication</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 400px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #0088cc;
            text-align: center;
        }
        .step {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #0088cc;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
        }
        button:hover {
            background: #0077bb;
        }
        .error {
            color: #dc3545;
            margin: 10px 0;
        }
        .success {
            color: #28a745;
            margin: 10px 0;
        }
        .hidden {
            display: none;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>T2T2 Authentication</h1>
        
        <div id="step1" class="step">
            <h3>Step 1: Enter Phone Number</h3>
            <input type="tel" id="phone" placeholder="+1234567890" />
            <button onclick="sendCode()">Send Code</button>
            <div id="phone-error" class="error"></div>
        </div>
        
        <div id="step2" class="step hidden">
            <h3>Step 2: Enter Verification Code</h3>
            <div class="warning">
                ⚠️ DO NOT send this code in any Telegram chat!<br>
                Enter it ONLY in this secure form.
            </div>
            <input type="text" id="code" placeholder="12345" maxlength="6" />
            <button onclick="verifyCode()">Verify</button>
            <div id="code-error" class="error"></div>
        </div>
        
        <div id="success" class="hidden">
            <div class="success">
                <h3>✅ Authentication Successful!</h3>
                <p>You can now close this window and return to Telegram.</p>
                <p>Use /chats in the bot to select chats to index.</p>
            </div>
        </div>
    </div>
    
    <script>
        const token = new URLSearchParams(window.location.search).get('token');
        const userId = new URLSearchParams(window.location.search).get('user_id');
        
        if (!token || !userId) {
            document.body.innerHTML = '<div class="container"><h1>Invalid Link</h1><p>Please get a new authentication link from the bot.</p></div>';
        }
        
        async function sendCode() {
            const phone = document.getElementById('phone').value;
            const errorDiv = document.getElementById('phone-error');
            
            if (!phone.startsWith('+')) {
                errorDiv.textContent = 'Phone number must start with + and country code';
                return;
            }
            
            errorDiv.textContent = '';
            
            try {
                const response = await fetch('/send_code', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token, phone})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('step1').classList.add('hidden');
                    document.getElementById('step2').classList.remove('hidden');
                } else {
                    errorDiv.textContent = data.error || 'Failed to send code';
                }
            } catch (e) {
                errorDiv.textContent = 'Network error. Please try again.';
            }
        }
        
        async function verifyCode() {
            const code = document.getElementById('code').value;
            const errorDiv = document.getElementById('code-error');
            
            if (!code) {
                errorDiv.textContent = 'Please enter the code';
                return;
            }
            
            errorDiv.textContent = '';
            
            try {
                const response = await fetch('/verify_code', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token, code, user_id: userId})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('step2').classList.add('hidden');
                    document.getElementById('success').classList.remove('hidden');
                } else {
                    errorDiv.textContent = data.error || 'Invalid code';
                }
            } catch (e) {
                errorDiv.textContent = 'Network error. Please try again.';
            }
        }
        
        // Auto-focus
        document.getElementById('phone').focus();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return AUTH_PAGE

@app.route('/auth/<token>')
def auth_page(token):
    if token not in AUTH_SESSIONS:
        return "Invalid or expired link", 404
    return AUTH_PAGE

@app.route('/send_code', methods=['POST'])
async def send_code():
    data = request.json
    token = data.get('token')
    phone = data.get('phone')
    
    if token not in AUTH_SESSIONS:
        return jsonify({'success': False, 'error': 'Invalid token'})
    
    session = AUTH_SESSIONS[token]
    
    try:
        client = TelegramClient(
            StringSession(),
            TELEGRAM_API_ID,
            TELEGRAM_API_HASH,
            device_model="T2T2 Web Auth",
            system_version="1.0",
            app_version="1.0"
        )
        
        await client.connect()
        result = await client.send_code_request(phone)
        
        # Update session
        session['client'] = client
        session['phone'] = phone
        session['phone_code_hash'] = result.phone_code_hash
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Send code error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/verify_code', methods=['POST'])
async def verify_code():
    data = request.json
    token = data.get('token')
    code = data.get('code')
    user_id = data.get('user_id')
    
    if token not in AUTH_SESSIONS:
        return jsonify({'success': False, 'error': 'Invalid token'})
    
    session = AUTH_SESSIONS[token]
    client = session.get('client')
    
    if not client:
        return jsonify({'success': False, 'error': 'No active session'})
    
    try:
        await client.sign_in(
            phone=session['phone'],
            code=code,
            phone_code_hash=session['phone_code_hash']
        )
        
        # Save session
        session_string = client.session.save()
        
        # Store in database
        supabase.table('user_sessions').upsert({
            'user_id': user_id,
            'session_string': session_string,
            'monitored_chats': [],
            'created_at': datetime.now().isoformat()
        }).execute()
        
        # Clean up
        await client.disconnect()
        del AUTH_SESSIONS[token]
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Verify code error: {e}")
        return jsonify({'success': False, 'error': str(e)})

def create_auth_token(user_id: str) -> str:
    """Create a secure temporary token for web auth"""
    token = secrets.token_urlsafe(32)
    AUTH_SESSIONS[token] = {
        'user_id': user_id,
        'expires': datetime.now() + timedelta(minutes=10)
    }
    return token

def cleanup_expired_tokens():
    """Remove expired tokens"""
    now = datetime.now()
    expired = [k for k, v in AUTH_SESSIONS.items() if v.get('expires', now) < now]
    for token in expired:
        if 'client' in AUTH_SESSIONS[token]:
            # Clean up Telethon client if exists
            pass
        del AUTH_SESSIONS[token]

if __name__ == '__main__':
    print("🌐 Starting T2T2 Web Authentication Server")
    print("📍 Access at: http://localhost:5000")
    print("\nThis provides a secure way to authenticate without sending codes through Telegram")
    
    # Run periodic cleanup
    import threading
    def periodic_cleanup():
        while True:
            cleanup_expired_tokens()
            threading.Event().wait(60)  # Every minute
    
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    
    app.run(debug=True, port=5000)