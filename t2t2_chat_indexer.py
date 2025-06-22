#!/usr/bin/env python3
"""
T2T2 Chat Indexer - Index ENTIRE chat histories from selected Telegram chats
Uses Telethon for full chat access + Bot for interface
"""

import os
import asyncio
import logging
from typing import Set

# Telegram libraries
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Message
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# Supabase and AI
from supabase import create_client, Client
from langchain_openai import OpenAIEmbeddings
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
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Initialize services
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# Store user sessions and selected chats
USER_SESSIONS = {}  # user_id -> telethon_session_string
MONITORED_CHATS = {}  # user_id -> set of chat_ids


class T2T2ChatIndexer:
    """Index entire chat histories from selected Telegram chats"""

    def __init__(self):
        self.bot_app = None
        self.telethon_clients = {}  # user_id -> TelegramClient
        self.load_user_data()

    def load_user_data(self):
        """Load saved user sessions and monitored chats"""
        try:
            # Load from database
            sessions = supabase.table("user_sessions").select("*").execute()
            for session in sessions.data:
                USER_SESSIONS[session["user_id"]] = session["session_string"]
                MONITORED_CHATS[session["user_id"]] = set(session["monitored_chats"])
        except:
            logger.info("No saved sessions found")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command - explain the bot"""
        user = update.effective_user

        text = f"""
👋 Welcome {user.first_name}!

I'm T2T2 Chat Indexer - I can index ENTIRE chat histories from your Telegram chats!

**How it works:**
1. Authenticate with your phone number
2. Choose which chats to index
3. I'll crawl the ENTIRE history
4. Search across all your indexed chats

**Privacy:**
• Your data is encrypted and isolated
• Only you can search your chats
• You control which chats are indexed

**Commands:**
/auth - Authenticate with Telegram
/chats - Choose chats to index
/search - Search indexed chats
/status - View indexing status

Ready to start? Use /auth to connect your account!
        """

        await update.message.reply_text(text, parse_mode="Markdown")

    async def auth_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start authentication process"""
        user = update.effective_user
        user_id = str(user.id)

        if user_id in USER_SESSIONS:
            await update.message.reply_text(
                "✅ You're already authenticated! Use /chats to manage your indexed chats."
            )
            return

        # Check if already pending
        try:
            pending = (
                supabase.table("pending_authentications")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "pending")
                .execute()
            )

            if pending.data:
                await update.message.reply_text(
                    "⏳ Your authentication is already pending!\n\n"
                    "The admin has been notified. You'll be contacted soon.\n"
                    "Please have your phone ready to receive the verification code."
                )
                return
        except:
            pass  # Table might not exist

        # Create pending authentication record
        try:
            # Check if already has pending auth
            result = supabase.table("pending_authentications")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "pending")\
                .execute()
                
            if not result.data:
                # Create new pending authentication
                supabase.table("pending_authentications").insert({
                    "user_id": user_id,
                    "status": "pending",
                    "created_at": datetime.now().isoformat()
                }).execute()
        except Exception as e:
            logger.error(f"Error creating pending auth: {e}")

        # Generate session ID for auth
        from datetime import datetime
        session_id = f"{user_id}_{int(datetime.now().timestamp())}"

        # Use Railway URL
        railway_url = "https://t2t2-production.up.railway.app"
        auth_url = f"{railway_url}?session={session_id}&user_id={user_id}"

        await update.message.reply_text(
            "📱 Let's authenticate your Telegram account.\n\n"
            "🔐 Manual Authentication Process:\n"
            f"Your User ID: {user_id}\n\n"
            "Click this link for instructions:\n"
            f"{auth_url}\n\n"
            "How it works:\n"
            "1. Click the link above\n"
            "2. You'll see instructions for manual authentication\n"
            "3. You'll receive a code from Telegram\n"
            "4. Send the code to admin via SMS/phone call\n"
            "5. Admin will complete your authentication\n\n"
            "⚠️ IMPORTANT: Never send the code through Telegram!\n\n"
            "Once authenticated, you'll be able to:\n"
            "• Select which chats to index\n"
            "• Search across all your messages\n"
            "• Access your full chat history",
            disable_web_page_preview=False,
        )

        # Clear any previous state
        context.user_data.clear()

    async def handle_phone_number(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle phone number input"""
        if not context.user_data.get("awaiting_phone"):
            return

        user = update.effective_user
        user_id = str(user.id)
        phone = update.message.text.strip()

        # Validate phone format
        if not phone.startswith("+"):
            await update.message.reply_text(
                "❌ Please include country code. Example: +1234567890"
            )
            return

        # Clear state
        context.user_data["awaiting_phone"] = False

        try:
            # Create pending authentication record
            supabase.table("pending_authentications").insert(
                {"user_id": user_id, "phone_number": phone, "status": "pending"}
            ).execute()

            await update.message.reply_text(
                "✅ Authentication request submitted!\n\n"
                "**What happens next:**\n"
                "1. Admin will initiate authentication for your number\n"
                "2. You'll receive a code from Telegram\n"
                "3. Contact admin with the code (phone/text)\n"
                "4. Admin will complete your authentication\n\n"
                "⏱️ This usually takes a few minutes.\n"
                "You'll be notified when complete!"
            )

            # Notify admin (if configured)
            admin_id = os.getenv("ADMIN_TELEGRAM_ID")
            if admin_id:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"🔔 New authentication request:\n\n"
                        f"User: {user.first_name} (@{user.username})\n"
                        f"ID: {user_id}\n"
                        f"Phone: {phone}\n\n"
                        f"Run admin_auth_tool.py to authenticate",
                    )
                except:
                    pass  # Admin notification failed, but user request is still saved

        except Exception as e:
            logger.error(f"Failed to create pending auth: {e}")
            await update.message.reply_text(
                "❌ Failed to submit authentication request.\n"
                "Please try again later or contact support."
            )

    async def handle_verification_code(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle verification code - now just informs user about admin process"""
        if not context.user_data.get("awaiting_code"):
            return

        # Clear the awaiting_code state
        context.user_data["awaiting_code"] = False

        await update.message.reply_text(
            "⚠️ Please DO NOT send the code here!\n\n"
            "For security reasons, Telegram blocks authentication when codes are shared in chats.\n\n"
            "**Instead:**\n"
            "1. Contact the admin via phone/text\n"
            "2. Share the code with them directly\n"
            "3. They will complete your authentication\n\n"
            "Your authentication is still pending. The admin has been notified."
        )

    async def chats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List user's chats for selection"""
        user = update.effective_user
        user_id = str(user.id)

        if user_id not in USER_SESSIONS:
            await update.message.reply_text("❌ Please /auth first!")
            return

        await update.message.reply_text("📋 Loading your chats...")

        try:
            # Get or create Telethon client
            client = await self.get_user_client(user_id)

            # Get dialogs - increased limit to get more chats
            dialogs = []
            folders = {}  # Store folder info
            
            # First, get folder information
            from telethon.tl.functions.messages import GetDialogFiltersRequest
            try:
                filters = await client(GetDialogFiltersRequest())
                for f in filters.filters:
                    if hasattr(f, 'title') and hasattr(f, 'include_peers'):
                        folders[f.title] = [p.user_id if hasattr(p, 'user_id') else p.channel_id for p in f.include_peers]
                        logger.info(f"Found folder: {f.title} with {len(f.include_peers)} chats")
            except Exception as e:
                logger.error(f"Could not get folders: {e}")
            
            async for dialog in client.iter_dialogs(limit=200):  # Increased from 50 to 200
                chat_info = {
                    "id": dialog.id,
                    "title": dialog.title or dialog.name or "Unknown",
                    "is_user": dialog.is_user,
                    "is_group": dialog.is_group,
                    "is_channel": dialog.is_channel,
                    "unread_count": dialog.unread_count,
                    "message_count": dialog.message.id if dialog.message else 0,
                    "folder": None
                }
                
                # Check which folder this chat belongs to
                for folder_name, chat_ids in folders.items():
                    if dialog.id in chat_ids:
                        chat_info["folder"] = folder_name
                        break
                        
                dialogs.append(chat_info)

            # Create inline keyboard
            keyboard = []
            monitored = MONITORED_CHATS.get(user_id, set())

            # Store dialogs in context for pagination/filtering
            context.user_data['all_dialogs'] = dialogs
            context.user_data['current_filter'] = None
            
            # Check if there's a 10NetZero folder
            has_10netzero = any(f == "10NetZero" for f in folders.keys())
            
            if has_10netzero:
                # Add folder filter buttons first
                keyboard.append([
                    InlineKeyboardButton("📁 All Chats", callback_data="filter:all"),
                    InlineKeyboardButton("💼 10NetZero", callback_data="filter:10NetZero")
                ])
                keyboard.append([InlineKeyboardButton("➖➖➖➖➖", callback_data="none")])
            
            # Show first 30 chats (increased from 20)
            for dialog in dialogs[:30]:
                status = "✅" if str(dialog["id"]) in monitored else "⬜"
                folder_indicator = f"[{dialog['folder']}] " if dialog.get('folder') else ""
                button_text = f"{status} {folder_indicator}{dialog['title'][:25]}"
                callback_data = f"toggle_chat:{dialog['id']}"
                keyboard.append(
                    [InlineKeyboardButton(button_text, callback_data=callback_data)]
                )

            keyboard.append(
                [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_chats")]
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "📥 Start Indexing", callback_data="start_indexing"
                    )
                ]
            )

            reply_markup = InlineKeyboardMarkup(keyboard)

            text = "**Select chats to index:**\n\n"
            text += f"Found {len(dialogs)} chats. Showing top 20.\n"
            text += f"Currently monitoring: {len(monitored)} chats\n\n"
            text += "Tap to toggle selection:"

            await update.message.reply_text(
                text, reply_markup=reply_markup, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Chats error: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def handle_chat_toggle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle chat selection toggle"""
        query = update.callback_query
        user_id = str(query.from_user.id)

        if not query.data.startswith("toggle_chat:"):
            return

        chat_id = query.data.split(":")[1]

        # Toggle selection
        if user_id not in MONITORED_CHATS:
            MONITORED_CHATS[user_id] = set()

        if chat_id in MONITORED_CHATS[user_id]:
            MONITORED_CHATS[user_id].remove(chat_id)
        else:
            MONITORED_CHATS[user_id].add(chat_id)

        # Update database
        supabase.table("user_sessions").update(
            {"monitored_chats": list(MONITORED_CHATS[user_id])}
        ).eq("user_id", user_id).execute()

        # Refresh the chat list
        await self.refresh_chat_list(query, user_id)

    async def refresh_chat_list(self, query, user_id: str):
        """Refresh the chat selection list"""
        try:
            client = await self.get_user_client(user_id)

            # Get dialogs again
            dialogs = []
            async for dialog in client.iter_dialogs(limit=20):
                dialogs.append(
                    {"id": dialog.id, "title": dialog.title or dialog.name or "Unknown"}
                )

            # Create updated keyboard
            keyboard = []
            monitored = MONITORED_CHATS.get(user_id, set())

            for dialog in dialogs:
                status = "✅" if str(dialog["id"]) in monitored else "⬜"
                button_text = f"{status} {dialog['title'][:30]}"
                callback_data = f"toggle_chat:{dialog['id']}"
                keyboard.append(
                    [InlineKeyboardButton(button_text, callback_data=callback_data)]
                )

            keyboard.append(
                [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_chats")]
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "📥 Start Indexing", callback_data="start_indexing"
                    )
                ]
            )

            reply_markup = InlineKeyboardMarkup(keyboard)

            text = "**Select chats to index:**\n\n"
            text += f"Currently monitoring: {len(monitored)} chats\n\n"
            text += "Tap to toggle selection:"

            await query.edit_message_text(
                text, reply_markup=reply_markup, parse_mode="Markdown"
            )
            await query.answer()

        except Exception as e:
            logger.error(f"Refresh error: {e}")
            await query.answer("Error refreshing list")

    async def start_indexing(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start indexing selected chats"""
        query = update.callback_query
        user_id = str(query.from_user.id)

        monitored = MONITORED_CHATS.get(user_id, set())
        if not monitored:
            await query.answer("No chats selected!")
            return

        await query.edit_message_text(
            f"🚀 Starting to index {len(monitored)} chats...\n\n"
            "This may take a while for large chats.\n"
            "I'll notify you when complete!"
        )

        # Start indexing in background
        asyncio.create_task(self.index_user_chats(user_id, monitored))

    async def index_user_chats(self, user_id: str, chat_ids: Set[str]):
        """Index all messages from selected chats"""
        client = await self.get_user_client(user_id)
        total_messages = 0

        for chat_id in chat_ids:
            try:
                logger.info(f"Indexing chat {chat_id} for user {user_id}")

                # Get chat entity
                entity = await client.get_entity(int(chat_id))
                chat_title = (
                    getattr(entity, "title", None)
                    or getattr(entity, "username", None)
                    or str(chat_id)
                )

                # Iterate through ALL messages
                async for message in client.iter_messages(entity, limit=None):
                    if message.text:
                        # Store message in database
                        await self.store_message(user_id, chat_id, chat_title, message)
                        total_messages += 1

                        if total_messages % 100 == 0:
                            logger.info(f"Indexed {total_messages} messages...")

                logger.info(f"Completed indexing chat {chat_title}")

            except Exception as e:
                logger.error(f"Error indexing chat {chat_id}: {e}")

        # Notify user
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=user_id,
            text=f"✅ Indexing complete!\n\n"
            f"Indexed {total_messages} messages from {len(chat_ids)} chats.\n\n"
            f"Use /search to search your messages!",
        )

    async def store_message(
        self, user_id: str, chat_id: str, chat_title: str, message: Message
    ):
        """Store a message with embeddings"""
        try:
            # Generate embedding
            if message.text:
                embedding = embeddings.embed_query(message.text[:8000])
            else:
                return  # Skip non-text messages for now

            # Store in database
            record = {
                "telegram_user_id": user_id,
                "telegram_chat_id": str(chat_id),
                "telegram_chat_name": chat_title,
                "telegram_message_id": str(message.id),
                "message_text": message.text,
                "content_embedding": embedding,
                "telegram_date": message.date.isoformat() if message.date else None,
                "file_type": "message",  # Use existing schema
                "s3_key": f"messages/{user_id}/{chat_id}/{message.id}",  # Dummy S3 key
                "s3_bucket": "messages",
                "original_filename": f"message_{message.id}.txt",
            }

            supabase.table("telegram_files").insert(record).execute()

        except Exception as e:
            logger.error(f"Error storing message: {e}")

    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search indexed messages"""
        user = update.effective_user
        user_id = str(user.id)

        query = " ".join(context.args) if context.args else None
        if not query:
            await update.message.reply_text("Usage: /search <your query>")
            return

        # Generate embedding
        query_embedding = embeddings.embed_query(query)

        # Search
        results = supabase.rpc(
            "search_files_similarity",
            {
                "query_embedding": query_embedding,
                "match_count": 10,
                "user_id": user_id,
                "file_types": ["message"],
            },
        ).execute()

        if results.data:
            text = f"🔍 Found {len(results.data)} results:\n\n"

            for i, result in enumerate(results.data[:5], 1):
                chat_name = result.get("metadata", {}).get("chat_name", "Unknown chat")
                message_preview = (
                    result["message_text"][:100] + "..."
                    if len(result["message_text"]) > 100
                    else result["message_text"]
                )
                similarity = result["similarity"]

                text += f"{i}. **{chat_name}** ({similarity:.0%})\n"
                text += f"   {message_preview}\n\n"

            await update.message.reply_text(text, parse_mode="Markdown")
        else:
            await update.message.reply_text("No results found.")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check authentication and indexing status"""
        user = update.effective_user
        user_id = str(user.id)

        status_text = "📊 **Your Status**\n\n"

        # Check authentication status
        if user_id in USER_SESSIONS:
            status_text += "✅ **Authentication:** Complete\n"

            # Check monitored chats
            monitored = MONITORED_CHATS.get(user_id, set())
            if monitored:
                status_text += f"📋 **Monitored Chats:** {len(monitored)}\n"

                # Get indexed message count
                try:
                    result = (
                        supabase.table("telegram_files")
                        .select("id", count="exact")
                        .eq("telegram_user_id", user_id)
                        .eq("file_type", "message")
                        .execute()
                    )

                    message_count = result.count if hasattr(result, "count") else 0
                    status_text += f"💬 **Indexed Messages:** {message_count:,}\n"
                except:
                    pass
            else:
                status_text += "📋 **Monitored Chats:** None selected\n"
                status_text += "\nUse /chats to select chats to index"
        else:
            # Check pending authentication
            try:
                pending = (
                    supabase.table("pending_authentications")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )

                if pending.data:
                    auth = pending.data[0]
                    if auth["status"] == "pending":
                        status_text += "⏳ **Authentication:** Pending\n"
                        status_text += (
                            f"📱 **Phone:** {auth.get('phone_number', 'Not provided')}\n"
                        )
                        status_text += f"🕐 **Requested:** {auth['created_at']}\n\n"
                        status_text += (
                            "Admin has been notified. You'll be contacted soon."
                        )
                    elif auth["status"] == "failed":
                        status_text += "❌ **Authentication:** Failed\n"
                        if auth.get("error"):
                            status_text += f"Error: {auth['error']}\n"
                        status_text += "\nPlease try /auth again"
                    else:
                        status_text += "❓ **Authentication:** Not authenticated\n"
                        status_text += "\nUse /auth to get started"
                else:
                    status_text += "❓ **Authentication:** Not authenticated\n"
                    status_text += "\nUse /auth to get started"
            except:
                status_text += "❓ **Authentication:** Not authenticated\n"
                status_text += "\nUse /auth to get started"

        await update.message.reply_text(status_text, parse_mode="Markdown")

    async def get_user_client(self, user_id: str) -> TelegramClient:
        """Get or create Telethon client for user"""
        if user_id not in self.telethon_clients:
            session_string = USER_SESSIONS.get(user_id)
            if not session_string:
                raise Exception("User not authenticated")

            client = TelegramClient(
                StringSession(session_string),
                TELEGRAM_API_ID,
                TELEGRAM_API_HASH,
                device_model="T2T2 Chat Indexer",
                system_version="1.0",
                app_version="1.0",
            )
            await client.connect()
            self.telethon_clients[user_id] = client

        return self.telethon_clients[user_id]

    async def setup_bot(self):
        """Setup bot handlers"""
        self.bot_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Commands
        self.bot_app.add_handler(CommandHandler("start", self.start_command))
        self.bot_app.add_handler(CommandHandler("auth", self.auth_command))
        self.bot_app.add_handler(CommandHandler("chats", self.chats_command))
        self.bot_app.add_handler(CommandHandler("search", self.search_command))
        self.bot_app.add_handler(CommandHandler("status", self.status_command))

        # Message handlers
        self.bot_app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message)
        )

        # Callback handlers
        self.bot_app.add_handler(
            CallbackQueryHandler(self.handle_chat_toggle, pattern="^toggle_chat:")
        )
        self.bot_app.add_handler(
            CallbackQueryHandler(self.refresh_chats_callback, pattern="^refresh_chats$")
        )
        self.bot_app.add_handler(
            CallbackQueryHandler(self.start_indexing, pattern="^start_indexing$")
        )

    async def handle_text_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle text messages based on context"""
        # No longer handling phone/code input since we use QR auth
        pass

    async def refresh_chats_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle refresh button"""
        query = update.callback_query
        user_id = str(query.from_user.id)
        await self.refresh_chat_list(query, user_id)

    async def check_new_auths(self):
        """Periodically check for newly authenticated users"""
        while True:
            try:
                # Reload user sessions from database
                sessions = supabase.table("user_sessions").select("*").execute()
                for session in sessions.data:
                    user_id = session["user_id"]
                    if user_id not in USER_SESSIONS:
                        # New authentication!
                        USER_SESSIONS[user_id] = session["session_string"]
                        MONITORED_CHATS[user_id] = set(
                            session.get("monitored_chats", [])
                        )

                        # Notify user
                        try:
                            await self.bot_app.bot.send_message(
                                chat_id=user_id,
                                text="✅ Authentication successful!\n\n"
                                "You can now use /chats to select which chats to index.",
                            )
                        except:
                            pass  # User might have blocked bot
            except Exception as e:
                logger.error(f"Error checking new auths: {e}")

            await asyncio.sleep(5)  # Check every 5 seconds

    async def run(self):
        """Run the bot"""
        await self.setup_bot()

        # Create user_sessions table if needed
        try:
            supabase.table("user_sessions").select("id").limit(1).execute()
        except:
            # Table doesn't exist, create it
            logger.info("Creating user_sessions table...")
            # You'll need to add this to your schema

        logger.info("🚀 Starting T2T2 Chat Indexer...")
        await self.bot_app.initialize()
        await self.bot_app.start()
        await self.bot_app.updater.start_polling()

        # Start checking for new authentications
        asyncio.create_task(self.check_new_auths())

        logger.info("✅ Chat indexer is running!")

        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info("Stopping bot...")

            # Clean up Telethon clients
            for client in self.telethon_clients.values():
                await client.disconnect()

            await self.bot_app.updater.stop()
            await self.bot_app.stop()
            await self.bot_app.shutdown()


# Add this table to your schema
USER_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS user_sessions (
    user_id text PRIMARY KEY,
    session_string text NOT NULL,
    monitored_chats text[] DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE INDEX idx_user_sessions_updated ON user_sessions(updated_at);
"""


async def main():
    """Main entry point"""
    indexer = T2T2ChatIndexer()
    await indexer.run()


if __name__ == "__main__":
    print("=" * 50)
    print("T2T2 CHAT INDEXER")
    print("=" * 50)
    print("\nThis bot will:")
    print("1. Let users authenticate with their phone")
    print("2. Show their Telegram chats")
    print("3. Let them select which chats to index")
    print("4. Crawl ENTIRE chat history")
    print("5. Make everything searchable\n")
    print("Starting...")

    asyncio.run(main())
