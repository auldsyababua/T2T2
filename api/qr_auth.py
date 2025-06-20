"""
Vercel serverless function for QR authentication
"""
from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET request - return simple HTML page"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>T2T2 Authentication</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .error { color: red; background: #ffe0e0; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>T2T2 Authentication</h1>
        <div class="error">
            <h2>QR Authentication is being updated</h2>
            <p>The QR authentication system is currently being migrated to a new infrastructure.</p>
            <p>Please use the admin authentication option in the bot for now.</p>
            <p>We apologize for the inconvenience.</p>
        </div>
    </div>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
        return
    
    def do_POST(self):
        """Handle POST request"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'status': 'error',
            'message': 'QR authentication is being updated. Please use admin authentication.'
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_OPTIONS(self):
        """Handle OPTIONS request for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return