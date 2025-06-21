#!/usr/bin/env python3
"""
T2T2 Authentication Bot
A simple bot that helps users generate Telegram session strings
No web server, no localhost, no password sharing required!
"""

import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# Load environment
load_dotenv(".env.supabase_bot")

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
AUTH_BOT_TOKEN = os.getenv(
    "AUTH_BOT_TOKEN", ""
)  # You'll need to create a new bot for this

# Active auth sessions
ACTIVE_SESSIONS = {}  # user_id -> TelegramClient


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user = update.effective_user

    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n"
        "I'm the T2T2 Auth Bot. I help you generate a session string "
        "that you can use with the T2T2 Chat Indexer.\n\n"
        "🔐 **How it works:**\n"
        "1. Send me your phone number with /auth +1234567890\n"
        "2. I'll send you a verification code\n"
        "3. Send me the code\n"
        "4. I'll give you a session string\n"
        "5. Use this string with the main T2T2 bot\n\n"
        "⚠️ **Important:** Never share your session string publicly!",
        parse_mode="Markdown",
    )


async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start authentication process"""
    user_id = str(update.effective_user.id)

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide your phone number:\n" "Example: /auth +1234567890"
        )
        return

    phone = context.args[0]
    if not phone.startswith("+"):
        await update.message.reply_text(
            "❌ Phone number must include country code (e.g., +1234567890)"
        )
        return

    # Create a new Telethon client with StringSession
    client = TelegramClient(
        StringSession(),
        TELEGRAM_API_ID,
        TELEGRAM_API_HASH,
        device_model="T2T2 Auth Bot",
        system_version="1.0",
        app_version="1.0",
    )

    ACTIVE_SESSIONS[user_id] = {"client": client, "phone": phone, "state": "connecting"}

    try:
        await client.connect()

        # Send code request
        await update.message.reply_text("📱 Sending verification code...")
        sent = await client.send_code_request(phone)

        ACTIVE_SESSIONS[user_id]["phone_code_hash"] = sent.phone_code_hash
        ACTIVE_SESSIONS[user_id]["state"] = "awaiting_code"

        await update.message.reply_text(
            "✅ Code sent! Please send me the verification code you received.\n\n"
            "The code should be 5 digits, like: 12345"
        )

    except Exception as e:
        logger.error(f"Auth error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
        if user_id in ACTIVE_SESSIONS:
            await ACTIVE_SESSIONS[user_id]["client"].disconnect()
            del ACTIVE_SESSIONS[user_id]


async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verification code"""
    user_id = str(update.effective_user.id)

    if user_id not in ACTIVE_SESSIONS:
        return

    session = ACTIVE_SESSIONS[user_id]
    if session["state"] != "awaiting_code":
        return

    code = update.message.text.strip()

    # Validate code format
    if not code.isdigit() or len(code) != 5:
        await update.message.reply_text("❌ Code should be 5 digits. Please try again.")
        return

    client = session["client"]

    try:
        # Try to sign in
        await client.sign_in(
            phone=session["phone"],
            code=code,
            phone_code_hash=session["phone_code_hash"],
        )

        # Success! Get session string
        session_string = client.session.save()

        await update.message.reply_text(
            "✅ **Authentication successful!**\n\n"
            "Here's your session string (tap to copy):\n\n"
            f"`{session_string}`\n\n"
            "📋 **What to do next:**\n"
            "1. Copy this entire string\n"
            "2. Go to @talk2telegrambot\n"
            "3. Send /session followed by your string\n"
            "4. You'll be authenticated!\n\n"
            "⚠️ **Security:** Keep this string secret!",
            parse_mode="Markdown",
        )

        # Clean up
        await client.disconnect()
        del ACTIVE_SESSIONS[user_id]

    except SessionPasswordNeededError:
        # 2FA is enabled
        session["state"] = "awaiting_2fa"
        await update.message.reply_text(
            "🔐 Two-factor authentication is enabled.\n"
            "Please send your 2FA password.\n\n"
            "⚠️ This is only stored temporarily and deleted after auth."
        )
    except Exception as e:
        logger.error(f"Sign in error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
        await client.disconnect()
        del ACTIVE_SESSIONS[user_id]


async def handle_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 2FA password"""
    user_id = str(update.effective_user.id)

    if user_id not in ACTIVE_SESSIONS:
        return

    session = ACTIVE_SESSIONS[user_id]
    if session["state"] != "awaiting_2fa":
        return

    password = update.message.text
    client = session["client"]

    try:
        # Delete the message with password for security
        await update.message.delete()

        # Sign in with 2FA
        await client.sign_in(password=password)

        # Success! Get session string
        session_string = client.session.save()

        await update.message.reply_text(
            "✅ **Authentication successful!**\n\n"
            "Here's your session string (tap to copy):\n\n"
            f"`{session_string}`\n\n"
            "📋 **What to do next:**\n"
            "1. Copy this entire string\n"
            "2. Go to @talk2telegrambot\n"
            "3. Send /session followed by your string\n"
            "4. You'll be authenticated!\n\n"
            "⚠️ **Security:** Keep this string secret!",
            parse_mode="Markdown",
        )

        # Clean up
        await client.disconnect()
        del ACTIVE_SESSIONS[user_id]

    except Exception as e:
        logger.error(f"2FA error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
        await client.disconnect()
        del ACTIVE_SESSIONS[user_id]


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current authentication"""
    user_id = str(update.effective_user.id)

    if user_id in ACTIVE_SESSIONS:
        await ACTIVE_SESSIONS[user_id]["client"].disconnect()
        del ACTIVE_SESSIONS[user_id]
        await update.message.reply_text("❌ Authentication cancelled.")
    else:
        await update.message.reply_text("No active authentication to cancel.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages based on state"""
    user_id = str(update.effective_user.id)

    if user_id not in ACTIVE_SESSIONS:
        return

    state = ACTIVE_SESSIONS[user_id]["state"]

    if state == "awaiting_code":
        await handle_code(update, context)
    elif state == "awaiting_2fa":
        await handle_2fa(update, context)


def main():
    """Start the bot"""
    if not AUTH_BOT_TOKEN:
        print("❌ Please set AUTH_BOT_TOKEN in .env.supabase_bot")
        print("You need to create a new bot with @BotFather for authentication")
        return

    # Create application
    app = Application.builder().token(AUTH_BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("auth", auth))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 T2T2 Auth Bot is running!")
    print("Users can authenticate and get session strings")
    print("No localhost, no QR codes, no password sharing!")

    # Run the bot
    app.run_polling()


if __name__ == "__main__":
    main()
