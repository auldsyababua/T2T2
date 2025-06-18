"""
Telegram Mini App authentication utilities
"""
import hashlib
import hmac
import json
import time
from typing import Dict, Optional
from urllib.parse import unquote

def verify_telegram_webapp_data(init_data: str, bot_token: str, max_age: int = 86400) -> Optional[Dict]:
    """
    Verify Telegram Mini App init data
    
    Args:
        init_data: The initData string from Telegram.WebApp
        bot_token: Your bot's token
        max_age: Maximum age of the data in seconds (default: 24 hours)
    
    Returns:
        Parsed user data if valid, None otherwise
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Force debug level
    
    try:
        # Check if init_data is None or empty
        if not init_data:
            logger.error("[AUTH] init_data is None or empty")
            return None
            
        logger.info(f"[AUTH] Verifying init data length: {len(init_data)}")
        logger.debug(f"[AUTH] Init data first 100 chars: {init_data[:100]}...")
        # Parse the init data
        parsed_data = {}
        data_check_string_parts = []
        
        for part in init_data.split('&'):
            if '=' not in part:
                continue
                
            key, value = part.split('=', 1)
            value = unquote(value)
            
            if key == 'hash':
                received_hash = value
            else:
                parsed_data[key] = value
                data_check_string_parts.append(f"{key}={value}")
        
        # Ensure we captured the received hash
        if 'received_hash' not in locals():
            return None
        
        # Sort and create data check string
        data_check_string_parts.sort()
        data_check_string = '\n'.join(data_check_string_parts)
        
        # Create secret key
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Verify hash
        if calculated_hash != received_hash:
            logger.warning(f"[AUTH] Hash mismatch - calculated: {calculated_hash[:20]}..., received: {received_hash[:20]}...")
            logger.warning(f"[AUTH] Full calculated hash: {calculated_hash}")
            logger.warning(f"[AUTH] Full received hash: {received_hash}")
            logger.warning(f"[AUTH] Data check string: {data_check_string[:200]}...")
            logger.warning(f"[AUTH] Bot token last 4 chars: ...{bot_token[-4:]}")
            logger.warning(f"[AUTH] All parsed params: {list(parsed_data.keys())}")
            return None
        
        # Check auth_date (prevent replay attacks)
        if 'auth_date' in parsed_data:
            auth_date = int(parsed_data['auth_date'])
            if time.time() - auth_date > max_age:
                return None
        
        # Parse user data if present
        if 'user' in parsed_data:
            parsed_data['user'] = json.loads(parsed_data['user'])
        
        return parsed_data
        
    except Exception as e:
        logger.error(f"[AUTH] Exception in verify_telegram_webapp_data: {type(e).__name__}: {str(e)}")
        logger.error(f"[AUTH] init_data type: {type(init_data)}, value: {repr(init_data)[:100] if init_data else 'None'}")
        logger.error(f"[AUTH] bot_token present: {bool(bot_token)}")
        return None

def extract_user_from_init_data(init_data_dict: Dict) -> Optional[Dict]:
    """
    Extract user information from verified init data
    
    Args:
        init_data_dict: Verified init data dictionary
    
    Returns:
        User information dictionary
    """
    if not init_data_dict or 'user' not in init_data_dict:
        return None
    
    user = init_data_dict['user']
    
    return {
        'telegram_id': str(user.get('id', '')),
        'username': user.get('username', ''),
        'first_name': user.get('first_name', ''),
        'last_name': user.get('last_name', ''),
        'language_code': user.get('language_code', 'en'),
        'is_premium': user.get('is_premium', False),
    }