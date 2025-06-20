"""
Vercel serverless function for QR authentication
"""
import os
import json
import secrets
import base64
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.auth import ExportLoginTokenRequest
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('.env.supabase_bot')

# Configuration
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def generate_qr_token(session_id: str, user_id: str):
    """Generate QR login token"""
    client = TelegramClient(
        StringSession(),
        TELEGRAM_API_ID,
        TELEGRAM_API_HASH,
        device_model="T2T2 QR Auth",
        system_version="1.0",
        app_version="1.0"
    )
    
    await client.connect()
    
    # Export login token for QR
    result = await client(ExportLoginTokenRequest(
        api_id=TELEGRAM_API_ID,
        api_hash=TELEGRAM_API_HASH,
        except_ids=[]
    ))
    
    token_data = base64.urlsafe_b64encode(result.token).decode('utf-8')
    
    # Store in Supabase
    supabase.table('qr_sessions').insert({
        'session_id': session_id,
        'user_id': user_id,
        'token': token_data,
        'expires_at': (datetime.now() + timedelta(seconds=30)).isoformat(),
        'status': 'pending'
    }).execute()
    
    await client.disconnect()
    return token_data

def handler(request):
    """Vercel serverless handler"""
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
    
    if request.method == 'GET':
        # Return QR auth page
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': '''<!DOCTYPE html>
<html>
<head>
    <title>T2T2 Authentication</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 20px; }
        #qr-container { margin: 20px auto; padding: 20px; max-width: 400px; }
        .error { color: red; background: #ffe0e0; padding: 10px; border-radius: 5px; }
        .success { color: green; background: #e0ffe0; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>T2T2 Authentication</h1>
    <div id="qr-container">
        <p>Loading QR code...</p>
    </div>
    <script>
        const params = new URLSearchParams(window.location.search);
        const sessionId = params.get('session');
        const userId = params.get('user_id');
        
        if (!sessionId || !userId) {
            document.getElementById('qr-container').innerHTML = 
                '<div class="error">Missing session parameters</div>';
        } else {
            // Generate QR code
            fetch('/api/qr_auth', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session: sessionId, user_id: userId})
            })
            .then(res => res.json())
            .then(data => {
                if (data.token) {
                    const qrUrl = 'tg://login?token=' + data.token;
                    document.getElementById('qr-container').innerHTML = 
                        '<img src="https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=' + 
                        encodeURIComponent(qrUrl) + '" />' +
                        '<p>Scan with Telegram to authenticate</p>';
                } else {
                    document.getElementById('qr-container').innerHTML = 
                        '<div class="error">Failed to generate QR code</div>';
                }
            })
            .catch(err => {
                document.getElementById('qr-container').innerHTML = 
                    '<div class="error">Error: ' + err.message + '</div>';
            });
        }
    </script>
</body>
</html>'''
        }
    
    elif request.method == 'POST':
        # Generate QR token
        try:
            body = json.loads(request.body)
            session_id = body.get('session')
            user_id = body.get('user_id')
            
            if not session_id or not user_id:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Missing parameters'})
                }
            
            # Run async function
            import asyncio
            token = asyncio.run(generate_qr_token(session_id, user_id))
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'token': token})
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': str(e)})
            }