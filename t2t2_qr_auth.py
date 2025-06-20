#!/usr/bin/env python3
"""
T2T2 QR Code Authentication Server
Provides secure authentication via QR codes - no passwords needed!
"""

import asyncio
import os
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional
import qrcode
import io
from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.auth import ExportLoginTokenRequest, ImportLoginTokenRequest
from telethon.tl.types import auth
from supabase import create_client
from dotenv import load_dotenv
import logging

load_dotenv('.env.supabase_bot')

# Configuration
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Initialize
app = Flask(__name__)
CORS(app)  # Enable CORS for GitHub Pages
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store QR sessions
QR_SESSIONS = {}  # session_id -> {client, token, expires, user_id}

# HTML template for QR auth page
QR_AUTH_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>T2T2 QR Authentication</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 500px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
            text-align: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #0088cc;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        #qr-container {
            margin: 30px 0;
            min-height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        #qr-code {
            border: 2px solid #eee;
            border-radius: 10px;
            padding: 20px;
            background: white;
        }
        .status {
            margin: 20px 0;
            padding: 15px;
            border-radius: 5px;
            font-weight: 500;
        }
        .status.waiting {
            background: #e3f2fd;
            color: #1976d2;
        }
        .status.success {
            background: #e8f5e9;
            color: #388e3c;
        }
        .status.error {
            background: #ffebee;
            color: #c62828;
        }
        .instructions {
            text-align: left;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .instructions h3 {
            margin-top: 0;
            color: #333;
        }
        .instructions ol {
            margin: 10px 0;
            padding-left: 20px;
        }
        .instructions li {
            margin: 5px 0;
        }
        .countdown {
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #0088cc;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>T2T2 Authentication</h1>
        <p class="subtitle">Secure login with QR code</p>
        
        <div class="instructions">
            <h3>How to authenticate:</h3>
            <ol>
                <li>Open Telegram on your phone</li>
                <li>Go to Settings → Devices → Scan QR Code</li>
                <li>Point your camera at the QR code below</li>
                <li>Confirm the login on your phone</li>
            </ol>
        </div>
        
        <div id="qr-container">
            <div class="spinner"></div>
        </div>
        
        <div id="status" class="status waiting">
            Generating QR code...
        </div>
        
        <div id="countdown" class="countdown"></div>
    </div>
    
    <script>
        const sessionId = new URLSearchParams(window.location.search).get('session');
        const userId = new URLSearchParams(window.location.search).get('user_id');
        let countdownInterval;
        let checkInterval;
        
        if (!sessionId || !userId) {
            document.getElementById('status').className = 'status error';
            document.getElementById('status').textContent = 'Invalid session link. Please get a new link from the bot.';
        } else {
            // Start checking for QR code
            checkForQR();
        }
        
        async function checkForQR() {
            try {
                const response = await fetch(`/qr/${sessionId}`);
                const data = await response.json();
                
                if (data.qr_code) {
                    // Display QR code
                    document.getElementById('qr-container').innerHTML = 
                        `<img id="qr-code" src="${data.qr_code}" alt="QR Code" />`;
                    
                    document.getElementById('status').textContent = 
                        'Scan this QR code with Telegram on your phone';
                    
                    // Start countdown
                    startCountdown(30);
                    
                    // Start checking for authentication
                    checkInterval = setInterval(checkAuth, 2000);
                } else if (data.error) {
                    document.getElementById('status').className = 'status error';
                    document.getElementById('status').textContent = data.error;
                    document.getElementById('qr-container').innerHTML = '';
                } else {
                    // Keep checking
                    setTimeout(checkForQR, 1000);
                }
            } catch (e) {
                document.getElementById('status').className = 'status error';
                document.getElementById('status').textContent = 'Connection error. Please try again.';
            }
        }
        
        async function checkAuth() {
            try {
                const response = await fetch(`/check_auth/${sessionId}`);
                const data = await response.json();
                
                if (data.authenticated) {
                    clearInterval(checkInterval);
                    clearInterval(countdownInterval);
                    
                    document.getElementById('status').className = 'status success';
                    document.getElementById('status').innerHTML = 
                        '✅ Authentication successful!<br><br>' +
                        'You can now close this window and return to Telegram.<br>' +
                        'Use /chats in the bot to select chats to index.';
                    
                    document.getElementById('qr-container').innerHTML = 
                        '<div style="font-size: 72px;">🎉</div>';
                    
                    document.getElementById('countdown').textContent = '';
                } else if (data.expired) {
                    clearInterval(checkInterval);
                    clearInterval(countdownInterval);
                    
                    document.getElementById('status').className = 'status error';
                    document.getElementById('status').textContent = 
                        'QR code expired. Please get a new link from the bot.';
                    
                    document.getElementById('qr-container').innerHTML = '';
                    document.getElementById('countdown').textContent = '';
                }
            } catch (e) {
                // Continue checking
            }
        }
        
        function startCountdown(seconds) {
            let remaining = seconds;
            
            function update() {
                document.getElementById('countdown').textContent = 
                    `Code expires in ${remaining} seconds`;
                
                remaining--;
                if (remaining < 0) {
                    clearInterval(countdownInterval);
                    clearInterval(checkInterval);
                    
                    document.getElementById('status').className = 'status error';
                    document.getElementById('status').textContent = 
                        'QR code expired. Please get a new link from the bot.';
                    
                    document.getElementById('qr-container').innerHTML = '';
                    document.getElementById('countdown').textContent = '';
                }
            }
            
            update();
            countdownInterval = setInterval(update, 1000);
        }
    </script>
</body>
</html>
'''

class QRAuthManager:
    def __init__(self):
        self.bot_client = None
        
    async def initialize_bot(self):
        """Initialize the bot client for handling updates"""
        if not self.bot_client:
            self.bot_client = TelegramClient(
                'qr_auth_bot',
                TELEGRAM_API_ID,
                TELEGRAM_API_HASH
            )
            await self.bot_client.start(bot_token=TELEGRAM_BOT_TOKEN)
            
            # Listen for login token updates
            @self.bot_client.on(events.Raw)
            async def handle_update(update):
                if hasattr(update, 'login_token'):
                    await self.handle_login_update(update)
    
    async def create_qr_session(self, user_id: str, session_id: str):
        """Create a new QR authentication session"""
        try:
            # Create a new client for this session
            client = TelegramClient(
                StringSession(),
                TELEGRAM_API_ID,
                TELEGRAM_API_HASH,
                device_model="T2T2 QR Auth",
                system_version="1.0",
                app_version="1.0"
            )
            
            await client.connect()
            
            # Export login token
            result = await client(ExportLoginTokenRequest(
                api_id=TELEGRAM_API_ID,
                api_hash=TELEGRAM_API_HASH,
                except_ids=[]  # Don't exclude any accounts
            ))
            
            if isinstance(result, auth.LoginToken):
                # Encode token for QR
                token_bytes = result.token
                token_b64 = base64.urlsafe_b64encode(token_bytes).decode('utf-8').rstrip('=')
                
                # Create QR code
                qr = qrcode.QRCode(
                    version=None,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(f"tg://login?token={token_b64}")
                qr.make(fit=True)
                
                # Generate QR image
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convert to base64 for embedding
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                buf.seek(0)
                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                # Store session
                QR_SESSIONS[session_id] = {
                    'client': client,
                    'token': result,
                    'token_b64': token_b64,
                    'qr_data': f"data:image/png;base64,{img_b64}",
                    'expires': datetime.now() + timedelta(seconds=result.expires.timestamp() - datetime.now().timestamp()),
                    'user_id': user_id,
                    'authenticated': False
                }
                
                logger.info(f"Created QR session {session_id} for user {user_id}")
                
                # Start checking for authentication
                asyncio.create_task(self.check_authentication(session_id))
                
                return True
            else:
                logger.error(f"Unexpected result type: {type(result)}")
                await client.disconnect()
                return False
                
        except Exception as e:
            logger.error(f"Failed to create QR session: {e}")
            return False
    
    async def check_authentication(self, session_id: str):
        """Check if the QR code has been scanned and authenticated"""
        session = QR_SESSIONS.get(session_id)
        if not session:
            return
        
        client = session['client']
        max_attempts = 30  # Check for 30 seconds
        
        for _ in range(max_attempts):
            if session_id not in QR_SESSIONS:
                break
                
            try:
                # Check if authenticated by trying to get dialogs
                async for dialog in client.iter_dialogs(limit=1):
                    # If we can get dialogs, we're authenticated!
                    session['authenticated'] = True
                    
                    # Get user info
                    me = await client.get_me()
                    
                    # Save session to database
                    session_string = client.session.save()
                    
                    supabase.table('user_sessions').upsert({
                        'user_id': session['user_id'],
                        'session_string': session_string,
                        'monitored_chats': [],
                        'created_at': datetime.now().isoformat()
                    }).execute()
                    
                    # Update pending auth if exists
                    supabase.table('pending_authentications').update({
                        'status': 'completed',
                        'completed_at': datetime.now().isoformat()
                    }).eq('user_id', session['user_id']).eq('status', 'pending').execute()
                    
                    logger.info(f"User {session['user_id']} authenticated successfully via QR")
                    
                    # Clean up
                    await client.disconnect()
                    break
                    
            except Exception as e:
                # Not authenticated yet, keep checking
                pass
            
            await asyncio.sleep(1)
        
        # Clean up if not authenticated
        if session_id in QR_SESSIONS and not QR_SESSIONS[session_id]['authenticated']:
            client = QR_SESSIONS[session_id]['client']
            await client.disconnect()
            del QR_SESSIONS[session_id]

# Initialize manager
qr_manager = QRAuthManager()

@app.route('/')
def index():
    return QR_AUTH_PAGE

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

@app.route('/qr/<session_id>')
async def get_qr(session_id):
    """Get QR code for session"""
    session = QR_SESSIONS.get(session_id)
    
    if not session:
        # Try to create it
        user_id = request.args.get('user_id')
        if user_id:
            success = await qr_manager.create_qr_session(user_id, session_id)
            if success:
                session = QR_SESSIONS.get(session_id)
            else:
                return jsonify({'error': 'Failed to generate QR code'})
        else:
            return jsonify({'error': 'Session not found'})
    
    if session and not session['authenticated']:
        # Check if expired
        if datetime.now() > session['expires']:
            # Clean up
            await session['client'].disconnect()
            del QR_SESSIONS[session_id]
            return jsonify({'error': 'QR code expired', 'expired': True})
        
        return jsonify({
            'qr_code': session['qr_data'],
            'expires_in': int((session['expires'] - datetime.now()).total_seconds())
        })
    elif session and session['authenticated']:
        return jsonify({'authenticated': True})
    else:
        return jsonify({'error': 'Session not found'})

@app.route('/check_auth/<session_id>')
def check_auth(session_id):
    """Check if session is authenticated"""
    session = QR_SESSIONS.get(session_id)
    
    if not session:
        return jsonify({'error': 'Session not found', 'expired': True})
    
    if session['authenticated']:
        return jsonify({'authenticated': True})
    
    if datetime.now() > session['expires']:
        return jsonify({'expired': True})
    
    return jsonify({'authenticated': False})

async def cleanup_expired_sessions():
    """Clean up expired sessions periodically"""
    while True:
        now = datetime.now()
        expired = []
        
        for session_id, session in QR_SESSIONS.items():
            if now > session['expires'] and not session['authenticated']:
                expired.append(session_id)
        
        for session_id in expired:
            try:
                await QR_SESSIONS[session_id]['client'].disconnect()
            except:
                pass
            del QR_SESSIONS[session_id]
        
        await asyncio.sleep(60)  # Check every minute

def run_server():
    """Run the Flask server with asyncio support"""
    import nest_asyncio
    nest_asyncio.apply()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Initialize bot
    loop.run_until_complete(qr_manager.initialize_bot())
    
    # Start cleanup task
    loop.create_task(cleanup_expired_sessions())
    
    # Run Flask with Railway PORT
    port = int(os.getenv('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    print("🚀 T2T2 QR Authentication Server")
    print("📍 Access at: http://localhost:5000")
    print("\nThis provides secure QR code authentication - no passwords needed!")
    print("\nUsers will:")
    print("1. Click a link from the bot")
    print("2. Scan QR code with Telegram")
    print("3. Get authenticated automatically")
    
    run_server()