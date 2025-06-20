#!/usr/bin/env python3

import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

load_dotenv('.env.supabase_bot')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    logger.info(f"Received /start from {update.effective_user.id}")
    await update.message.reply_text('Hi! Debug bot is working!')

async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /auth command"""
    logger.info(f"Received /auth from {update.effective_user.id}")
    await update.message.reply_text('Auth command received!')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo any text message"""
    logger.info(f"Received text: {update.message.text} from {update.effective_user.id}")
    await update.message.reply_text(f'You said: {update.message.text}')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    print(f"Starting debug bot...")
    print(f"Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("auth", auth))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Add error handler
    application.add_error_handler(error_handler)

    print("Bot handlers registered, starting polling...")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()