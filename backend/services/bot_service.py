"""
Telegram Bot service for interacting with T2T2 via Telegram.
Works alongside the web interface to provide chat-based Q&A.
"""
import os
import asyncio
from typing import Optional
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from backend.utils.logging import setup_logger
from backend.db.database import get_db
from backend.models.models import User
from backend.services.query_service import QueryService
from sqlalchemy import select

logger = setup_logger(__name__)


class TelegramBotService:
    """Telegram bot for chat-based interaction with indexed messages"""

    def __init__(self, bot_token: str):
        """Initialize the bot service"""
        self.bot_token = bot_token
        self.query_service = QueryService()
        self.application = None

        logger.info(f"[BOT_SERVICE] Initialized with token: ...{bot_token[-4:]}")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        logger.info(
            f"[BOT_SERVICE] Start command from user {user.id} (@{user.username})"
        )

        await update.message.reply_text(
            f"👋 Hello {user.first_name}!\n\n"
            "I'm T2T2 - Talk to Telegram bot. I can help you search and ask questions about your Telegram chat history.\n\n"
            "**First Time Setup:**\n"
            "1. Visit https://t2t2.vercel.app (or your web URL)\n"
            "2. Login with your phone number\n"
            "3. Select chats to index\n"
            "4. Come back here to ask questions!\n\n"
            "**Commands:**\n"
            "/help - Show this help message\n"
            "/status - Check your indexing status\n"
            "/query - Ask a question about your chats\n\n"
            "Or just send me a message to search your chats!",
            parse_mode="Markdown",
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check user's indexing status"""
        user_id = str(update.effective_user.id)
        logger.info(f"[BOT_SERVICE] Status check from user {user_id}")

        async with get_db() as db:
            # Check if user exists
            result = await db.execute(select(User).where(User.tg_user_id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                await update.message.reply_text(
                    "❌ You haven't set up T2T2 yet!\n\n"
                    "Please visit the web interface to login and select chats to index."
                )
                return

            # TODO: Get actual indexing stats
            await update.message.reply_text(
                f"✅ Your account is set up!\n\n"
                f"User ID: {user.tg_user_id}\n"
                f"Username: @{user.username or 'N/A'}\n"
                f"Account created: {user.created_at.strftime('%Y-%m-%d')}\n\n"
                f"You can now ask questions about your indexed chats!"
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages as queries"""
        user_id = str(update.effective_user.id)
        query = update.message.text

        logger.info(f"[BOT_SERVICE] Query from user {user_id}: {query[:50]}...")

        # Send typing indicator
        await update.message.chat.send_action("typing")

        async with get_db() as db:
            # Check if user exists
            result = await db.execute(select(User).where(User.tg_user_id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                await update.message.reply_text(
                    "❌ Please set up T2T2 first using /start"
                )
                return

            try:
                # Query the indexed messages
                response = await self.query_service.query_messages(
                    user_id=user.id, query=query
                )

                # Format response
                answer = response.get("answer", "No relevant information found.")
                sources = response.get("sources", [])

                # Build message
                message = f"**Answer:**\n{answer}\n\n"

                if sources:
                    message += "**Sources:**\n"
                    for i, source in enumerate(sources[:3], 1):
                        chat_title = source.get("chat_title", "Unknown")
                        timestamp = source.get("timestamp", "")
                        message += f"{i}. {chat_title} - {timestamp}\n"

                await update.message.reply_text(message, parse_mode="Markdown")

            except Exception as e:
                logger.error(f"[BOT_SERVICE] Query error: {type(e).__name__}: {str(e)}")
                await update.message.reply_text(
                    "❌ Sorry, an error occurred while searching. Please try again."
                )

    async def query_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /query command"""
        if not context.args:
            await update.message.reply_text(
                "Please provide a query after /query\n"
                "Example: /query when did we discuss the project deadline?"
            )
            return

        # Set the message text to the query and handle it
        update.message.text = " ".join(context.args)
        await self.handle_message(update, context)

    async def start(self):
        """Start the bot"""
        logger.info(f"[BOT_SERVICE] Starting Telegram bot...")

        # Create application
        self.application = Application.builder().token(self.bot_token).build()

        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("query", self.query_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        # Start polling
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

        logger.info(f"[BOT_SERVICE] Bot started successfully!")

    async def stop(self):
        """Stop the bot"""
        if self.application:
            logger.info(f"[BOT_SERVICE] Stopping bot...")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info(f"[BOT_SERVICE] Bot stopped!")


# Singleton instance
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
if bot_token:
    bot_service = TelegramBotService(bot_token)
else:
    bot_service = None
    logger.warning("[BOT_SERVICE] No TELEGRAM_BOT_TOKEN found - bot disabled")
