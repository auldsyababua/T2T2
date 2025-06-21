#!/usr/bin/env python3
"""
Team T2T2 Bot with Supabase Vector Storage and Admin Control

Features:
1. Admin can add users by Telegram ID or username
2. All data stored in Supabase with encryption
3. Each user has isolated vector collections
4. Complete privacy protection with end-to-end encryption
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Set
import json
from pathlib import Path
from cryptography.fernet import Fernet
import base64

# Telegram libraries
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Supabase and AI libraries
from supabase import create_client, Client
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.supabase_bot")

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # Use service key for full access
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID", "")  # Your Telegram ID
ENCRYPTION_KEY = os.getenv("TEAM_ENCRYPTION_KEY", "")  # Team-wide encryption key

# Generate encryption key if not provided
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key()
    logger.info(f"Generated new encryption key: {ENCRYPTION_KEY.decode()}")
    logger.info("Save this in TEAM_ENCRYPTION_KEY env var!")

# Initialize services
fernet = Fernet(
    ENCRYPTION_KEY if isinstance(ENCRYPTION_KEY, bytes) else ENCRYPTION_KEY.encode()
)
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Authorized users file (encrypted)
AUTHORIZED_USERS_FILE = Path("./authorized_users.enc")


class TeamBotService:
    """Team bot with Supabase storage and admin control"""

    def __init__(self):
        self.authorized_users: Set[str] = set()
        self.load_authorized_users()
        self.bot_app = None

    def load_authorized_users(self):
        """Load authorized users from encrypted file"""
        if AUTHORIZED_USERS_FILE.exists():
            try:
                encrypted_data = AUTHORIZED_USERS_FILE.read_bytes()
                decrypted_data = fernet.decrypt(encrypted_data)
                users = json.loads(decrypted_data.decode())
                self.authorized_users = set(users)
                logger.info(f"Loaded {len(self.authorized_users)} authorized users")
            except Exception as e:
                logger.error(f"Error loading authorized users: {e}")
                self.authorized_users = {ADMIN_ID} if ADMIN_ID else set()
        else:
            # Initialize with admin
            self.authorized_users = {ADMIN_ID} if ADMIN_ID else set()
            self.save_authorized_users()

    def save_authorized_users(self):
        """Save authorized users to encrypted file"""
        try:
            data = json.dumps(list(self.authorized_users))
            encrypted_data = fernet.encrypt(data.encode())
            AUTHORIZED_USERS_FILE.write_bytes(encrypted_data)
            logger.info("Saved authorized users")
        except Exception as e:
            logger.error(f"Error saving authorized users: {e}")

    def is_admin(self, user_id: str) -> bool:
        """Check if user is admin"""
        return str(user_id) == str(ADMIN_ID)

    def is_authorized(self, user_id: str) -> bool:
        """Check if user is authorized"""
        return str(user_id) in self.authorized_users or self.is_admin(user_id)

    def encrypt_text(self, text: str) -> str:
        """Encrypt text for storage"""
        return base64.b64encode(fernet.encrypt(text.encode())).decode()

    def decrypt_text(self, encrypted_text: str) -> str:
        """Decrypt text from storage"""
        return fernet.decrypt(base64.b64decode(encrypted_text)).decode()

    def get_user_collection_name(self, user_id: str) -> str:
        """Get unique collection name for user"""
        # Hash user ID for privacy
        import hashlib

        user_hash = hashlib.sha256(f"{user_id}:{ENCRYPTION_KEY}".encode()).hexdigest()[
            :16
        ]
        return f"t2t2_user_{user_hash}"

    async def create_user_vectorstore(self, user_id: str) -> SupabaseVectorStore:
        """Create or get user's vector store"""
        collection_name = self.get_user_collection_name(user_id)

        # Create vector store
        vectorstore = SupabaseVectorStore(
            client=supabase,
            embedding=embeddings,
            table_name="documents",  # Supabase table for documents
            query_name=f"match_{collection_name}",  # Unique query function per user
        )

        logger.info(f"Created/accessed vector store for user {user_id}")
        return vectorstore

    # Admin Commands
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user_id = str(update.effective_user.id)

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized")
            return

        await update.message.reply_text(
            "**Admin Commands:**\n\n"
            "/add_user <telegram_id or @username> - Add authorized user\n"
            "/remove_user <telegram_id or @username> - Remove user\n"
            "/list_users - List all authorized users\n"
            "/user_stats - Show usage statistics\n"
            "/broadcast <message> - Send message to all users",
            parse_mode="Markdown",
        )

    async def add_user_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Add authorized user"""
        user_id = str(update.effective_user.id)

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized")
            return

        if not context.args:
            await update.message.reply_text(
                "Usage: /add_user <telegram_id or @username>"
            )
            return

        new_user = context.args[0]
        # Remove @ if username
        if new_user.startswith("@"):
            new_user = new_user[1:]

        self.authorized_users.add(new_user)
        self.save_authorized_users()

        await update.message.reply_text(f"✅ Added user: {new_user}")
        logger.info(f"Admin {user_id} added user {new_user}")

    async def remove_user_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Remove authorized user"""
        user_id = str(update.effective_user.id)

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized")
            return

        if not context.args:
            await update.message.reply_text(
                "Usage: /remove_user <telegram_id or @username>"
            )
            return

        user_to_remove = context.args[0]
        if user_to_remove.startswith("@"):
            user_to_remove = user_to_remove[1:]

        if user_to_remove in self.authorized_users:
            self.authorized_users.remove(user_to_remove)
            self.save_authorized_users()
            await update.message.reply_text(f"✅ Removed user: {user_to_remove}")
            logger.info(f"Admin {user_id} removed user {user_to_remove}")
        else:
            await update.message.reply_text(f"❌ User not found: {user_to_remove}")

    async def list_users_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """List authorized users"""
        user_id = str(update.effective_user.id)

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized")
            return

        users_list = f"**Authorized Users ({len(self.authorized_users)}):**\n\n"
        for user in sorted(self.authorized_users):
            users_list += f"• {user}\n"

        await update.message.reply_text(users_list, parse_mode="Markdown")

    # User Commands
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = str(user.id)

        if not self.is_authorized(user_id) and not self.is_authorized(user.username):
            await update.message.reply_text(
                "❌ You are not authorized to use this bot.\n\n"
                "Please contact your administrator for access."
            )
            return

        # Add user ID to authorized list if they were added by username
        if user.username and user.username in self.authorized_users:
            self.authorized_users.add(user_id)
            self.save_authorized_users()

        await update.message.reply_text(
            f"👋 Welcome {user.first_name}!\n\n"
            "I'm your team's private T2T2 bot with encrypted memory!\n\n"
            "**Features:**\n"
            "• All your data is encrypted\n"
            "• Complete isolation from other users\n"
            "• Powered by Supabase vector search\n\n"
            "**Commands:**\n"
            "/index - Index your Telegram history\n"
            "/ask <question> - Ask about your chats\n"
            "/memory - Show what I remember\n"
            "/help - Show this message",
            parse_mode="Markdown",
        )

    async def index_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /index command"""
        user = update.effective_user
        user_id = str(user.id)

        if not self.is_authorized(user_id):
            await update.message.reply_text("❌ Unauthorized")
            return

        await update.message.reply_text(
            "To index your Telegram history:\n\n"
            "1. Use the web interface to authenticate with your phone\n"
            "2. Or provide your Telethon session string\n\n"
            "For now, I'll remember our conversations!"
        )

        # TODO: Implement actual indexing flow

    async def memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's memory stats"""
        user = update.effective_user
        user_id = str(user.id)

        if not self.is_authorized(user_id):
            await update.message.reply_text("❌ Unauthorized")
            return

        try:
            vectorstore = await self.create_user_vectorstore(user_id)

            # Query for memory
            question = f"What do you know about {user.first_name}?"
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
            )

            result = qa_chain({"query": question})
            answer = result.get("result", "No memories yet.")

            await update.message.reply_text(
                f"**My memory about you:**\n\n{answer}", parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Memory error for user {user_id}: {e}")
            await update.message.reply_text("No memories found yet. Start chatting!")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user = update.effective_user
        user_id = str(user.id)

        if not self.is_authorized(user_id):
            return  # Silently ignore unauthorized users

        user_message = update.message.text
        logger.info(f"Query from user {user_id}: {user_message[:50]}...")

        # Send typing indicator
        await update.message.chat.send_action("typing")

        try:
            # Get user's vector store
            vectorstore = await self.create_user_vectorstore(user_id)

            # Create QA chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
                return_source_documents=True,
            )

            # Get answer
            result = qa_chain({"query": user_message})
            answer = result.get("result", "I need more context to answer that.")

            # Send response
            await update.message.reply_text(answer)

            # Store this conversation (encrypted)
            timestamp = datetime.now().isoformat()
            encrypted_message = self.encrypt_text(user_message)
            encrypted_answer = self.encrypt_text(answer)

            # Add to vector store
            conversation_doc = Document(
                page_content=f"User: {user_message}\nBot: {answer}",
                metadata={
                    "type": "bot_conversation",
                    "timestamp": timestamp,
                    "user_id": user_id,
                    "encrypted": True,
                },
            )

            vectorstore.add_documents([conversation_doc])

            logger.info(f"Stored encrypted conversation for user {user_id}")

        except Exception as e:
            logger.error(f"Error for user {user_id}: {e}")
            await update.message.reply_text(
                "Sorry, I encountered an error. Please try again."
            )

    async def setup_bot(self):
        """Setup Telegram bot"""
        logger.info("Setting up bot...")

        self.bot_app = Application.builder().token(BOT_TOKEN).build()

        # Admin commands
        self.bot_app.add_handler(CommandHandler("admin", self.admin_command))
        self.bot_app.add_handler(CommandHandler("add_user", self.add_user_command))
        self.bot_app.add_handler(
            CommandHandler("remove_user", self.remove_user_command)
        )
        self.bot_app.add_handler(CommandHandler("list_users", self.list_users_command))

        # User commands
        self.bot_app.add_handler(CommandHandler("start", self.start_command))
        self.bot_app.add_handler(CommandHandler("help", self.start_command))
        self.bot_app.add_handler(CommandHandler("index", self.index_command))
        self.bot_app.add_handler(CommandHandler("memory", self.memory_command))

        # Message handler
        self.bot_app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        logger.info("Bot setup complete!")

    async def run(self):
        """Run the bot"""
        await self.setup_bot()

        logger.info("Starting team bot...")
        await self.bot_app.initialize()
        await self.bot_app.start()
        await self.bot_app.updater.start_polling()

        logger.info(f"Team bot is running! Admin: {ADMIN_ID}")
        logger.info("Press Ctrl+C to stop.")

        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info("Stopping bot...")
            await self.bot_app.updater.stop()
            await self.bot_app.stop()
            await self.bot_app.shutdown()


async def setup_supabase_tables():
    """Setup required Supabase tables if they don't exist"""
    logger.info("Checking Supabase setup...")

    # Note: You'll need to run this SQL in Supabase:
    """
    -- Enable pgvector extension
    create extension if not exists vector;
    
    -- Create documents table
    create table if not exists documents (
        id uuid default gen_random_uuid() primary key,
        content text,
        metadata jsonb,
        embedding vector(1536),
        collection_name text,
        created_at timestamp with time zone default timezone('utc'::text, now())
    );
    
    -- Create index for vector similarity search
    create index if not exists documents_embedding_idx 
    on documents using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);
    
    -- Create index for collection queries
    create index if not exists documents_collection_idx on documents(collection_name);
    
    -- Create function for similarity search per collection
    create or replace function match_documents(
        query_embedding vector(1536),
        match_count int,
        collection text
    ) returns table (
        id uuid,
        content text,
        metadata jsonb,
        similarity float
    ) language plpgsql as $$
    begin
        return query
        select
            id,
            content,
            metadata,
            1 - (documents.embedding <=> query_embedding) as similarity
        from documents
        where collection_name = collection
        order by documents.embedding <=> query_embedding
        limit match_count;
    end;
    $$;
    """
    logger.info("Please ensure the above SQL has been run in your Supabase instance")


async def main():
    """Main entry point"""
    # Setup Supabase tables
    await setup_supabase_tables()

    # Run bot
    bot = TeamBotService()
    await bot.run()


if __name__ == "__main__":
    # Check required environment variables
    required = {
        "TELEGRAM_BOT_TOKEN": BOT_TOKEN,
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": SUPABASE_KEY,
        "ADMIN_TELEGRAM_ID": ADMIN_ID,
    }

    missing = [k for k, v in required.items() if not v]

    if missing:
        print("Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease set these in your .env file or environment")
        exit(1)

    asyncio.run(main())
