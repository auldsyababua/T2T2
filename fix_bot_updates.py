#!/usr/bin/env python3
"""
Script to clear Telegram bot update queue and fix offset issues
"""

import os
import asyncio
import logging
from telegram import Bot
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.supabase_bot')

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def clear_updates():
    """Clear all pending updates for the bot"""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    logger.info("Getting bot info...")
    bot_info = await bot.get_me()
    logger.info(f"Bot: @{bot_info.username} ({bot_info.first_name})")
    
    logger.info("Clearing webhook if any...")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook cleared with pending updates dropped")
    
    logger.info("Getting updates to check current state...")
    updates = await bot.get_updates(limit=100)
    
    if updates:
        logger.info(f"Found {len(updates)} pending updates")
        # Get the last update ID and use it to clear the queue
        last_update_id = updates[-1].update_id
        logger.info(f"Last update ID: {last_update_id}")
        
        # Clear by getting updates with offset
        logger.info("Clearing update queue...")
        await bot.get_updates(offset=last_update_id + 1, limit=1)
        logger.info("Update queue cleared!")
    else:
        logger.info("No pending updates found")
    
    logger.info("Bot is now ready to receive fresh commands")

if __name__ == "__main__":
    asyncio.run(clear_updates())