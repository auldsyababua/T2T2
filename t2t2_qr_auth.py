#!/usr/bin/env python3
"""
T2T2 Traditional Authentication Server
Provides authentication instructions for manual verification
"""

import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
from dotenv import load_dotenv
import logging

# Load environment variables - Railway will provide these
load_dotenv('.env.supabase_bot')  # Primary file with Supabase config
load_dotenv('.env', override=False)  # Fallback for missing vars

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


# HTML template for auth instruction page
AUTH_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>T2T2 Authentication</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
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
        .status {
            margin: 20px 0;
            padding: 20px;
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
            padding: 25px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .instructions h3 {
            margin-top: 0;
            color: #333;
            font-size: 20px;
        }
        .instructions ol {
            margin: 15px 0;
            padding-left: 25px;
            line-height: 1.8;
        }
        .instructions li {
            margin: 10px 0;
            font-size: 16px;
        }
        .warning {
            background: #fff3cd;
            color: #856404;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            text-align: left;
        }
        .warning h4 {
            margin-top: 0;
        }
        .phone-number {
            font-size: 24px;
            font-weight: bold;
            color: #0088cc;
            margin: 20px 0;
            padding: 15px;
            background: #f0f8ff;
            border-radius: 5px;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #0088cc;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
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
        <p class="subtitle">Manual verification process</p>
        
        <div class="instructions">
            <h3>🔐 Authentication Steps:</h3>
            <ol>
                <li>📱 You will receive a verification code in your Telegram app</li>
                <li>📝 Send this code to the admin via SMS, WhatsApp, Signal, or phone call</li>
                <li>⏳ Wait for the admin to complete your authentication</li>
                <li>✅ You'll see a success message here when complete</li>
            </ol>
        </div>
        
        <div class="warning">
            <h4>⚠️ Important Security Notice:</h4>
            <p><strong>NEVER</strong> send your verification code through Telegram! This will invalidate the code for security reasons.</p>
            <p>Only share the code through non-Telegram channels (SMS, phone call, etc.)</p>
        </div>
        
        <div id="phone-container"></div>
        
        <div id="status" class="status waiting">
            <div class="spinner"></div>
            <p>Waiting for authentication...</p>
            <p>The admin will process your request shortly.</p>
        </div>
    </div>
    
    <script>
        const sessionId = new URLSearchParams(window.location.search).get('session');
        const userId = new URLSearchParams(window.location.search).get('user_id');
        let checkInterval;
        
        if (!sessionId || !userId) {
            document.getElementById('status').className = 'status error';
            document.getElementById('status').innerHTML = 
                '<p>❌ Invalid session link.</p>' +
                '<p>Please get a new link from the bot.</p>';
        } else {
            // Start checking for authentication status
            checkAuth();
            checkInterval = setInterval(checkAuth, 3000); // Check every 3 seconds
        }
        
        async function checkAuth() {
            try {
                const response = await fetch(`/check_auth/${sessionId}`);
                const data = await response.json();
                
                if (data.authenticated) {
                    clearInterval(checkInterval);
                    
                    document.getElementById('status').className = 'status success';
                    document.getElementById('status').innerHTML = 
                        '<h2>✅ Authentication Successful!</h2>' +
                        '<p>You are now authenticated with T2T2.</p>' +
                        '<p>You can close this window and return to Telegram.</p>' +
                        '<p>Use <strong>/chats</strong> in the bot to select chats to index.</p>';
                    
                    // Remove instructions since they're no longer needed
                    document.querySelector('.instructions').style.display = 'none';
                    document.querySelector('.warning').style.display = 'none';
                } else if (data.error) {
                    document.getElementById('status').className = 'status error';
                    document.getElementById('status').innerHTML = 
                        '<p>❌ ' + data.error + '</p>';
                }
            } catch (e) {
                // Continue checking
                console.error('Check auth error:', e);
            }
        }
    </script>
</body>
</html>
"""





@app.route("/")
def index():
    return AUTH_PAGE


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "T2T2 Traditional Auth"})




@app.route("/create_session")
def create_session():
    """Create a new authentication session"""
    try:
        user_id = request.args.get("user_id")
        phone_number = request.args.get("phone_number")
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
            
        # Check if user already has a pending authentication
        result = supabase.table("pending_authentications")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("status", "pending")\
            .execute()
            
        if result.data:
            # Already has pending auth, update it with phone number if provided
            if phone_number:
                supabase.table("pending_authentications").update({
                    "phone_number": phone_number,
                    "updated_at": datetime.now().isoformat()
                }).eq("user_id", user_id).eq("status", "pending").execute()
        else:
            # Create new pending authentication
            supabase.table("pending_authentications").insert({
                "user_id": user_id,
                "phone_number": phone_number,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }).execute()
        
        session_id = f"{user_id}_{int(datetime.now().timestamp())}"
        return jsonify({"session_id": session_id})
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({"error": "Failed to create session"}), 500


@app.route("/check_auth/<session_id>")
def check_auth(session_id):
    """Check if session is authenticated"""
    try:
        # Extract user_id from session_id (format: user_id_timestamp)
        parts = session_id.split('_')
        if len(parts) < 2:
            return jsonify({"error": "Invalid session format"}), 400
            
        user_id = parts[0]
        
        # Check pending authentication status
        result = supabase.table("pending_authentications")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
            
        if not result.data:
            return jsonify({"error": "No authentication request found"}), 404
            
        auth_request = result.data[0]
        status = auth_request.get("status", "pending")
        
        if status == "completed":
            return jsonify({"authenticated": True})
        elif status == "failed":
            return jsonify({"error": "Authentication failed"}), 403
        else:
            return jsonify({"authenticated": False})
            
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return jsonify({"error": "Internal server error"}), 500




def run_server():
    """Run the Flask server"""
    # Run Flask with Railway PORT
    port = int(os.getenv("PORT", "5000"))
    logger.info(f"Starting T2T2 Traditional Auth Server on port {port}")
    logger.info("Server configured and ready for traditional authentication")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    print("🚀 T2T2 Traditional Authentication Server")
    print(f"📍 Starting on port {os.getenv('PORT', '5000')}")
    print("\nThis provides authentication instructions for manual verification")
    print("\nUsers will:")
    print("1. Click a link from the bot")
    print("2. See instructions for manual authentication")
    print("3. Send verification code to admin via non-Telegram method")
    print("4. Admin completes authentication using traditional_auth.py script")

    run_server()
