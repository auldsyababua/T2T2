#!/usr/bin/env python3
"""
Simple Telegram bot handler for T2T2
This bot provides the /start command and menu button to open the Mini App
"""
import os
import logging
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8165476295:AAGKAYjWGOPw1XKTnglbDSBWC38Dg0PDjlA")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://emails-cookbook-constant-wish.trycloudflare.com")  # Change this to your deployed URL

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with a button to open the Mini App"""
    user = update.effective_user
    
    # Create keyboard with Web App button
    keyboard = [
        [InlineKeyboardButton(
            text="🚀 Open T2T2 App", 
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
👋 Welcome {user.first_name}!

I'm T2T2 (Talk to Telegram 2), your AI-powered Telegram chat assistant.

I can help you:
• 🔍 Search through your chat history using natural language
• 💬 Find specific conversations or messages
• 📊 Generate timelines and summaries
• 🤖 Answer questions about your chats

Click the button below to open the app and get started!
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
📚 **T2T2 Help**

**How to use T2T2:**
1. Click "Open T2T2 App" or use the menu button
2. Select which chats you want to index
3. Wait for the indexing to complete
4. Start asking questions about your chats!

**Example queries:**
• "What did John say about the project?"
• "Find messages about vacation plans"
• "Show me funny messages from last week"
• "What restaurants were recommended?"

**Features:**
• 🔐 Secure: Your data never leaves your control
• 🚀 Fast: AI-powered search across all messages
• 📱 Easy: Natural language queries
• 🎯 Accurate: Advanced embeddings for better results

**Privacy:**
Your messages are processed securely and are only accessible to you. We use end-to-end encryption and never store your messages on our servers.

Need more help? Contact @your_support_username
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def app_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the Mini App button"""
    keyboard = [
        [InlineKeyboardButton(
            text="🚀 Open T2T2 App", 
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Click below to open T2T2:",
        reply_markup=reply_markup
    )

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("app", app_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main()