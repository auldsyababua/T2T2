# TDLib/Telethon Architecture Refactor

## Overview

This document outlines the architecture for refactoring T2T2 from using Telegram Bot API to Telethon (MTProto), which provides full access to chat history.

## Key Changes

### From Bot API to User Client
- **Before**: Bot API with limited message visibility
- **After**: Telethon client acting as user account with full chat history access

### Authentication Flow
- **Before**: Bot token + Mini App authentication
- **After**: Phone number + verification code (like Telegram login)

## Architecture Components

### 1. Authentication Service
```python
# backend/services/auth_service.py
class TelegramAuthService:
    """Handles phone number authentication and session management"""
    
    async def send_code(phone: str) -> str:
        """Send verification code to phone"""
        
    async def verify_code(phone: str, code: str, phone_code_hash: str) -> User:
        """Verify code and create user session"""
        
    async def get_session(user_id: str) -> StringSession:
        """Retrieve encrypted session from database"""
```

### 2. Session Management
```python
# backend/services/session_service.py
class SessionService:
    """Manages encrypted Telethon sessions"""
    
    def encrypt_session(session: StringSession) -> str:
        """Encrypt session string for database storage"""
        
    def decrypt_session(encrypted: str) -> StringSession:
        """Decrypt session string from database"""
```

### 3. Chat Service (Replaces TelegramService)
```python
# backend/services/chat_service.py
class TelethonChatService:
    """Handles all chat operations using Telethon"""
    
    async def get_user_chats(session: StringSession) -> List[Chat]:
        """Get all user's chats with full details"""
        
    async def get_chat_history(session: StringSession, chat_id: int, limit: int = None) -> List[Message]:
        """Get full chat history - the main advantage!"""
        
    async def index_chat(session: StringSession, chat_id: int):
        """Index all messages from a chat"""
```

### 4. Database Schema Updates

```sql
-- Update users table
ALTER TABLE users ADD COLUMN phone_number VARCHAR(20) UNIQUE;
ALTER TABLE users ADD COLUMN session_string TEXT;  -- Encrypted
ALTER TABLE users ADD COLUMN session_created_at TIMESTAMP;
ALTER TABLE users ADD COLUMN last_auth_at TIMESTAMP;

-- Remove bot-specific columns
ALTER TABLE users DROP COLUMN session_file;  -- Was for bot sessions
```

### 5. API Endpoints

#### Authentication Endpoints
- `POST /api/auth/send-code` - Send verification code
- `POST /api/auth/verify-code` - Verify code and create session
- `POST /api/auth/logout` - Destroy session
- `GET /api/auth/status` - Check auth status

#### Chat Endpoints (Updated)
- `GET /api/chats` - Get all user chats
- `GET /api/chats/{chat_id}/history` - Get full chat history
- `POST /api/chats/{chat_id}/index` - Index chat messages

### 6. Frontend Changes

#### Login Flow
```typescript
// UI/src/components/PhoneLogin.tsx
interface PhoneLoginProps {
  onSuccess: (user: User) => void;
}

const PhoneLogin: React.FC<PhoneLoginProps> = ({ onSuccess }) => {
  // Step 1: Phone number input
  // Step 2: Verification code input
  // Step 3: Success callback
};
```

#### Remove Mini App Dependencies
- Remove Telegram Web App script
- Remove Bot-specific authentication
- Add phone number authentication UI

### 7. Security Considerations

1. **Session Encryption**
   - Use AES-256-GCM for session string encryption
   - Store encryption keys in environment variables
   - Never log session strings

2. **Rate Limiting**
   - Limit code requests per phone number
   - Implement exponential backoff for failed attempts

3. **Session Management**
   - Sessions expire after 30 days of inactivity
   - One session per user (no concurrent sessions)
   - Clear sessions on logout

4. **API Security**
   - All endpoints require JWT authentication
   - Session strings never exposed to frontend
   - HTTPS required for all communications

### 8. Migration Plan

1. **Phase 1**: Set up Telethon infrastructure
   - Add Telethon to requirements
   - Create session management services
   - Update database schema

2. **Phase 2**: Implement authentication
   - Phone number authentication flow
   - Session storage and encryption
   - JWT integration

3. **Phase 3**: Replace chat services
   - Migrate from Bot API to Telethon
   - Update all chat-related endpoints
   - Test with real chat data

4. **Phase 4**: Frontend updates
   - Remove Mini App code
   - Add phone authentication UI
   - Update API integration

### 9. Environment Variables

```env
# Telegram API (from my.telegram.org)
TELEGRAM_API_ID=
TELEGRAM_API_HASH=

# Session encryption
SESSION_ENCRYPTION_KEY=  # 32-byte key for AES-256

# Remove old bot variables
# TELEGRAM_BOT_TOKEN=  # No longer needed
```

### 10. Benefits

1. **Full Chat History**: Access all messages, not just recent ones
2. **Better User Experience**: Native Telegram-like functionality
3. **More Features**: File downloads, user info, etc.
4. **No Bot Limitations**: Act as a real user client

### 11. Monitoring and Logging

Add extensive logging at every step:
- Authentication attempts
- Session creation/destruction
- API calls to Telegram
- Error tracking
- Performance metrics

```python
logger.info(f"[AUTH] Code sent to phone: {phone[:3]}...{phone[-2:]}")
logger.info(f"[AUTH] User {user_id} authenticated successfully")
logger.info(f"[CHAT] Fetching history for chat {chat_id}, limit: {limit}")
logger.error(f"[SESSION] Failed to decrypt session for user {user_id}")
```

## Next Steps

1. Install Telethon and dependencies
2. Create authentication service
3. Implement session management
4. Update database schema
5. Build new API endpoints
6. Update frontend
7. Test thoroughly
8. Deploy