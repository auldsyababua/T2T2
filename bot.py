#!/usr/bin/env python3
"""
Telegram bot handler for T2T2 with whitelist authentication
"""
import os
import sys
import logging
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from config.authorized_users import is_user_authorized, get_unauthorized_message

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8165476295:AAGKAYjWGOPw1XKTnglbDSBWC38Dg0PDjlA")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://t2t2-app.vercel.app")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")  # Will be Railway URL in production

async def check_authorization(update: Update) -> bool:
    """Check if user is authorized to use the bot."""
    user = update.effective_user
    username = user.username
    
    if not username:
        await update.message.reply_text(
            "❌ You need to have a Telegram username to use this bot.\n"
            "Please set one in your Telegram settings and try again."
        )
        return False
    
    if not is_user_authorized(username):
        await update.message.reply_text(get_unauthorized_message())
        logger.warning(f"Unauthorized access attempt by @{username} (ID: {user.id})")
        return False
    
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with a button to open the Mini App"""
    if not await check_authorization(update):
        return
    
    user = update.effective_user
    
    # Create keyboard with Web App button
    keyboard = [
        [InlineKeyboardButton(
            text="🚀 Open T2T2 App", 
            web_app=WebAppInfo(url=f"{WEBAPP_URL}?user_id={user.id}")
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

Click the button below to configure which chats to index!
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup
    )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle search queries directly in the bot."""
    if not await check_authorization(update):
        return
    
    # Get the search query
    query = ' '.join(context.args) if context.args else None
    
    if not query:
        await update.message.reply_text(
            "Please provide a search query.\n"
            "Example: `/search did we fix the pump?`"
        )
        return
    
    # For now, direct them to the web app
    # TODO: Implement direct API call to backend
    await update.message.reply_text(
        f"🔍 Searching for: *{query}*\n\n"
        "Feature coming soon! For now, please use the web app.",
        parse_mode='Markdown'
    )

async def timeline_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a timeline from the user's query."""
    if not await check_authorization(update):
        return
    
    query = ' '.join(context.args) if context.args else None
    
    if not query:
        await update.message.reply_text(
            "Please provide a timeline query.\n"
            "Example: `/timeline pump maintenance over last month`"
        )
        return
    
    # For now, direct them to the web app
    # TODO: Implement direct API call to backend
    await update.message.reply_text(
        f"📊 Generating timeline for: *{query}*\n\n"
        "Feature coming soon! For now, please use the web app.",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if not await check_authorization(update):
        return
        
    help_text = """
📚 **T2T2 Help**

**Commands:**
• `/start` - Start the bot and open configuration
• `/search [query]` - Search your indexed chats
• `/timeline [query]` - Generate a timeline
• `/help` - Show this help message

**How to use T2T2:**
1. Click "Open T2T2 App" to configure
2. Select which chats you want to index
3. Wait for the indexing to complete
4. Start asking questions!

**Example queries:**
• "What did John say about the project?"
• "Did we fix the valve on pump 5?"
• "Timeline of generator delays"
• "Messages about safety incidents"

**Privacy:**
Your messages are only accessible to you. Each user's data is completely isolated.

Need help? Contact the admin.
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular messages as search queries."""
    if not await check_authorization(update):
        return
    
    message_text = update.message.text
    
    # Treat the message as a search query
    await update.message.reply_text(
        f"🔍 Searching for: *{message_text}*\n\n"
        "Direct message search coming soon! For now, please:\n"
        "1. Use `/search {message_text}` command, or\n"
        "2. Open the web app with /start",
        parse_mode='Markdown'
    )

async def post_init(application: Application) -> None:
    """Initialize the bot commands."""
    await application.bot.set_my_commands([
        ("start", "Configure and start using T2T2"),
        ("search", "Search your indexed chats"),
        ("timeline", "Generate a timeline from your chats"),
        ("help", "Get help on using the bot")
    ])

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("timeline", timeline_command))
    
    # Handle regular messages as search queries
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot started with whitelist authentication enabled")
    application.run_polling()

if __name__ == '__main__':
    main()