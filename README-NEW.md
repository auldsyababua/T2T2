# T2T2 - Talk to Telegram 2

A web application that allows you to chat with an AI about your complete Telegram chat history. Now uses Telethon for full chat history access!

## Features

- 📱 Phone number authentication (like native Telegram)
- 💬 Access to ALL chat history (not just recent messages)
- 🤖 AI-powered chat analysis and Q&A
- 🔐 Encrypted session storage
- 📊 Full message indexing with progress tracking

## Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL (or SQLite for development)
- Telegram API credentials from [my.telegram.org](https://my.telegram.org/apps)

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/T2T2.git
cd T2T2
```

### 2. Set up environment variables
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
- `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` from my.telegram.org
- `SESSION_ENCRYPTION_KEY` - Generate with: `openssl rand -base64 32`
- `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `OPENAI_API_KEY` - Your OpenAI API key
- Database and other service credentials

### 3. Start the services

#### Backend
```bash
./start-backend.sh
```
The backend will be available at http://localhost:8000

#### Frontend
In a new terminal:
```bash
./start-frontend.sh
```
The frontend will be available at http://localhost:5173

## Manual Setup

### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the backend server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
# Navigate to UI directory
cd UI

# Install dependencies
npm install

# Start development server
npm run dev
```

## Project Structure

```
T2T2/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── phone_auth.py    # Phone authentication endpoints
│   │   │   ├── telethon_telegram.py  # Telegram operations
│   │   │   └── ...
│   │   └── dependencies.py      # Auth dependencies
│   ├── services/
│   │   ├── auth_service.py      # Telethon authentication
│   │   ├── session_service.py   # Session encryption
│   │   └── chat_service.py      # Chat operations
│   └── models/
├── UI/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PhoneLogin.tsx   # Phone auth component
│   │   │   └── ...
│   │   └── App.tsx              # Main app component
├── docs/
│   ├── development/
│   │   └── tdlib-architecture.md
│   └── refactor-summary.md
└── tests/
```

## Authentication Flow

1. User enters phone number
2. Verification code sent via Telegram
3. User enters code (and 2FA password if enabled)
4. Session created and encrypted
5. JWT token issued for API access

## API Documentation

When the backend is running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints

- `POST /api/phone-auth/send-code` - Send verification code
- `POST /api/phone-auth/verify-code` - Verify code and login
- `GET /api/telegram/chats` - Get user's chats
- `GET /api/telegram/chats/{chat_id}/history` - Get chat history
- `POST /api/telegram/index-chats` - Index selected chats

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
# Python
black backend/
ruff backend/

# TypeScript
cd UI && npm run lint
```

## Deployment

### Railway
1. Set environment variables in Railway dashboard
2. Deploy backend service pointing to `backend.main:app`
3. Deploy frontend service with build command `cd UI && npm run build`

### Vercel (Frontend only)
1. Connect GitHub repository
2. Set root directory to `UI`
3. Add environment variable `VITE_API_URL` pointing to backend

## Security Notes

- Session strings are encrypted with AES-256-GCM
- Phone numbers are masked in the UI
- All API endpoints require authentication
- Sessions expire after 30 days of inactivity

## Troubleshooting

### "No SESSION_ENCRYPTION_KEY found"
Generate a key: `openssl rand -base64 32`

### "TELEGRAM_API_ID and TELEGRAM_API_HASH must be set"
Get these from https://my.telegram.org/apps

### Rate limiting errors
Telethon has stricter rate limits than Bot API. Add delays between operations if needed.

## License

MIT