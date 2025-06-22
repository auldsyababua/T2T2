#!/usr/bin/env python3
"""
Traditional authentication script for T2T2
Admin runs this to authenticate users via phone/code/2FA
"""

import os
import sys
import asyncio
import getpass
from datetime import datetime
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


async def authenticate_user(user_id: str, phone_number: str):
    """Authenticate a user via traditional phone/code/2FA method"""
    print(f"\n🔐 Authenticating user {user_id} with phone {phone_number}")
    
    # Create a new client with StringSession
    client = TelegramClient(
        StringSession(),
        TELEGRAM_API_ID,
        TELEGRAM_API_HASH
    )
    
    try:
        await client.connect()
        
        # Send code request
        print(f"\n📱 Sending verification code to {phone_number}...")
        sent_code = await client.send_code_request(phone_number)
        print("✅ Code sent successfully!")
        
        # Get code from admin
        print("\n⚠️  IMPORTANT: User should receive code in their Telegram app")
        print("⚠️  They must send it to you via SMS, call, or other non-Telegram method")
        code = input("\n📝 Enter the verification code: ").strip()
        
        try:
            # Try to sign in with code
            print("\n🔄 Attempting to sign in...")
            await client.sign_in(phone_number, code)
            print("✅ Signed in successfully!")
            
        except errors.SessionPasswordNeededError:
            # 2FA is enabled, need password
            print("\n🔒 Two-factor authentication is enabled")
            print("⚠️  User must provide their 2FA password")
            password = getpass.getpass("🔑 Enter 2FA password: ")
            
            try:
                await client.sign_in(password=password)
                print("✅ 2FA authentication successful!")
            except Exception as e:
                print(f"❌ 2FA authentication failed: {e}")
                return False
                
        except errors.PhoneCodeInvalidError:
            print("❌ Invalid verification code!")
            return False
            
        except errors.PhoneCodeExpiredError:
            print("❌ Verification code has expired!")
            return False
            
        # Authentication successful - save session
        session_string = client.session.save()
        
        # Save to database
        print("\n💾 Saving session to database...")
        supabase.table("user_sessions").upsert({
            "user_id": user_id,
            "session_string": session_string,
            "monitored_chats": [],
            "created_at": datetime.now().isoformat()
        }).execute()
        
        # Update pending authentication
        supabase.table("pending_authentications").update({
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }).eq("user_id", user_id).eq("status", "pending").execute()
        
        print("✅ Session saved successfully!")
        print(f"\n🎉 User {user_id} is now authenticated!")
        
        # Get user info
        me = await client.get_me()
        print(f"📱 Authenticated as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        if client.is_connected():
            await client.disconnect()
        return False


async def main():
    """Main function to handle authentication flow"""
    print("🤖 T2T2 Traditional Authentication System")
    print("=" * 50)
    
    # Check if user_id provided as argument
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        user_id = input("\n👤 Enter Telegram User ID: ").strip()
    
    # Get pending authentication from database
    print(f"\n🔍 Looking up pending authentication for user {user_id}...")
    
    result = supabase.table("pending_authentications")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("status", "pending")\
        .execute()
    
    if not result.data:
        print(f"❌ No pending authentication found for user {user_id}")
        print("ℹ️  User must first use /auth command in the bot")
        return
    
    pending_auth = result.data[0]
    phone_number = pending_auth.get("phone_number")
    
    if not phone_number:
        print("❌ No phone number found in pending authentication")
        return
    
    print(f"✅ Found pending auth - Phone: {phone_number}")
    
    # Check if user is pre-authorized
    # You can add additional authorization checks here
    
    # Authenticate the user
    success = await authenticate_user(user_id, phone_number)
    
    if success:
        print("\n✨ Authentication completed successfully!")
    else:
        print("\n❌ Authentication failed. Please try again.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Authentication cancelled by admin")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")