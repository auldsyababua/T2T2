#!/usr/bin/env python3
"""
Multi-user T2T2 Bot with isolated vector databases and bot memory

Features:
1. Each user has their own isolated vector database
2. Bot conversations are indexed and searchable (bot memory)
3. Complete data isolation between users
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
import json
from pathlib import Path

# Telegram libraries
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# AI/ML libraries
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Initialize services
embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
llm = ChatOpenAI(temperature=0, api_key=OPENAI_API_KEY)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# User data directory
USER_DATA_DIR = Path("./user_data")
USER_DATA_DIR.mkdir(exist_ok=True)


class UserSession:
    """Manages a single user's vector database and chat history"""
    
    def __init__(self, user_id: str, username: str = None):
        self.user_id = user_id
        self.username = username
        self.user_dir = USER_DATA_DIR / user_id
        self.user_dir.mkdir(exist_ok=True)
        
        # User-specific paths
        self.vectorstore_path = self.user_dir / "chroma_db"
        self.session_file = self.user_dir / "telethon_session.txt"
        self.bot_history_file = self.user_dir / "bot_conversations.jsonl"
        
        self.vectorstore = None
        self.qa_chain = None
        
        logger.info(f"[USER_{user_id}] Initialized session for {username or 'Unknown'}")
        
    def load_or_create_vectorstore(self):
        """Load existing vector store or create new one"""
        if self.vectorstore_path.exists():
            logger.info(f"[USER_{self.user_id}] Loading existing vector store")
            self.vectorstore = Chroma(
                persist_directory=str(self.vectorstore_path),
                embedding_function=embeddings
            )
        else:
            logger.info(f"[USER_{self.user_id}] Creating new vector store")
            self.vectorstore = Chroma(
                persist_directory=str(self.vectorstore_path),
                embedding_function=embeddings
            )
            
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True
        )
        
    def add_bot_conversation(self, user_message: str, bot_response: str):
        """Add bot conversation to vector store and history file"""
        timestamp = datetime.now().isoformat()
        
        # Create document for vector store
        conversation_text = f"User: {user_message}\nBot: {bot_response}"
        metadata = {
            "type": "bot_conversation",
            "timestamp": timestamp,
            "user_message": user_message,
            "bot_response": bot_response
        }
        
        # Add to vector store
        self.vectorstore.add_documents([
            Document(page_content=conversation_text, metadata=metadata)
        ])
        self.vectorstore.persist()
        
        # Also save to history file for backup
        with open(self.bot_history_file, 'a') as f:
            json.dump({
                "timestamp": timestamp,
                "user": user_message,
                "bot": bot_response
            }, f)
            f.write('\n')
            
        logger.info(f"[USER_{self.user_id}] Added conversation to memory")
        
    async def index_telegram_history(self, telethon_session: str, limit_per_chat: int = 1000):
        """Index user's Telegram history into their vector store"""
        logger.info(f"[USER_{self.user_id}] Starting Telegram history indexing")
        
        # Save session for future use
        with open(self.session_file, 'w') as f:
            f.write(telethon_session)
            
        # Create Telethon client
        session = StringSession(telethon_session)
        client = TelegramClient(session, API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            logger.error(f"[USER_{self.user_id}] Telethon session not authorized")
            return False
            
        # Get all dialogs
        dialogs = await client.get_dialogs()
        logger.info(f"[USER_{self.user_id}] Found {len(dialogs)} chats")
        
        documents = []
        
        for dialog in dialogs:
            chat_title = dialog.title or f"Chat {dialog.id}"
            logger.info(f"[USER_{self.user_id}] Processing: {chat_title}")
            
            # Get messages
            message_count = 0
            async for message in client.iter_messages(dialog, limit=limit_per_chat):
                if message.text:
                    metadata = {
                        "type": "telegram_message",
                        "chat": chat_title,
                        "chat_id": str(dialog.id),
                        "date": message.date.isoformat(),
                        "sender_id": str(message.sender_id),
                        "message_id": str(message.id)
                    }
                    
                    # Add sender name if available
                    if message.sender:
                        if hasattr(message.sender, 'first_name'):
                            metadata['sender_name'] = f"{message.sender.first_name or ''} {message.sender.last_name or ''}".strip()
                        elif hasattr(message.sender, 'title'):
                            metadata['sender_name'] = message.sender.title
                            
                    documents.append(
                        Document(page_content=message.text, metadata=metadata)
                    )
                    message_count += 1
                    
            logger.info(f"[USER_{self.user_id}]   Indexed {message_count} messages from {chat_title}")
            
        # Add all documents to vector store
        if documents:
            logger.info(f"[USER_{self.user_id}] Adding {len(documents)} documents to vector store")
            self.vectorstore.add_documents(documents)
            self.vectorstore.persist()
            
        await client.disconnect()
        logger.info(f"[USER_{self.user_id}] Indexing complete!")
        return True
        
    async def query(self, question: str) -> tuple[str, list]:
        """Query the user's vector store"""
        if not self.qa_chain:
            self.load_or_create_vectorstore()
            
        result = self.qa_chain({"query": question})
        answer = result['result']
        sources = result.get('source_documents', [])
        
        return answer, sources


class MultiUserBot:
    """Main bot that manages multiple user sessions"""
    
    def __init__(self):
        self.user_sessions: Dict[str, UserSession] = {}
        self.bot_app = None
        
    def get_user_session(self, user_id: str, username: str = None) -> UserSession:
        """Get or create user session"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession(user_id, username)
            self.user_sessions[user_id].load_or_create_vectorstore()
        return self.user_sessions[user_id]
        
    # Bot command handlers
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        session = self.get_user_session(str(user.id), user.username)
        
        await update.message.reply_text(
            f"👋 Welcome {user.first_name}!\n\n"
            "I'm your personal T2T2 bot with memory!\n\n"
            "**Features:**\n"
            "• I remember all our conversations\n"
            "• I can search your Telegram history (after setup)\n"
            "• Your data is completely isolated from other users\n\n"
            "**Commands:**\n"
            "/setup - Connect your Telegram account\n"
            "/ask <question> - Ask me anything\n"
            "/memory - Show what I remember about you\n"
            "/help - Show this message\n\n"
            "Just send me a message and I'll remember it!",
            parse_mode='Markdown'
        )
        
    async def setup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setup command for Telegram indexing"""
        user = update.effective_user
        session = self.get_user_session(str(user.id), user.username)
        
        await update.message.reply_text(
            "To index your Telegram history, I need you to:\n\n"
            "1. Get your phone authentication code\n"
            "2. Use the web interface to authenticate\n"
            "3. Or provide your Telethon session string\n\n"
            "For now, I'll just remember our conversations!"
        )
        
    async def memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user what bot remembers"""
        user = update.effective_user
        session = self.get_user_session(str(user.id), user.username)
        
        # Query for bot's memory about the user
        answer, sources = await session.query(f"What do you know about user {user.first_name}?")
        
        response = f"**My memory about you:**\n\n{answer}\n\n"
        
        # Add source count
        bot_convos = sum(1 for s in sources if s.metadata.get('type') == 'bot_conversation')
        telegram_msgs = sum(1 for s in sources if s.metadata.get('type') == 'telegram_message')
        
        response += f"_Based on {bot_convos} bot conversations and {telegram_msgs} Telegram messages_"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask command"""
        if not context.args:
            await update.message.reply_text("Please provide a question after /ask")
            return
            
        question = ' '.join(context.args)
        await self.handle_query(update, question)
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user_message = update.message.text
        await self.handle_query(update, user_message)
        
    async def handle_query(self, update: Update, question: str):
        """Process a query and remember the conversation"""
        user = update.effective_user
        session = self.get_user_session(str(user.id), user.username)
        
        logger.info(f"[USER_{user.id}] Query: {question}")
        
        # Send typing indicator
        await update.message.chat.send_action("typing")
        
        try:
            # Get answer from RAG
            answer, sources = await session.query(question)
            
            # Send response
            await update.message.reply_text(answer)
            
            # Add this conversation to memory
            session.add_bot_conversation(question, answer)
            
            # Log source types
            source_types = {}
            for source in sources:
                stype = source.metadata.get('type', 'unknown')
                source_types[stype] = source_types.get(stype, 0) + 1
            logger.info(f"[USER_{user.id}] Sources used: {source_types}")
            
        except Exception as e:
            logger.error(f"[USER_{user.id}] Error: {e}")
            error_msg = "Sorry, I encountered an error. Please try again."
            await update.message.reply_text(error_msg)
            
            # Still save the failed interaction
            session.add_bot_conversation(question, f"[Error: {str(e)}]")
            
    async def setup_bot(self):
        """Setup Telegram bot"""
        logger.info("Setting up bot...")
        
        self.bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        self.bot_app.add_handler(CommandHandler("start", self.start_command))
        self.bot_app.add_handler(CommandHandler("help", self.start_command))
        self.bot_app.add_handler(CommandHandler("setup", self.setup_command))
        self.bot_app.add_handler(CommandHandler("memory", self.memory_command))
        self.bot_app.add_handler(CommandHandler("ask", self.ask_command))
        self.bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Bot setup complete!")
        
    async def run(self):
        """Run the bot"""
        await self.setup_bot()
        
        logger.info("Starting bot...")
        await self.bot_app.initialize()
        await self.bot_app.start()
        await self.bot_app.updater.start_polling()
        
        logger.info("Multi-user bot is running! Press Ctrl+C to stop.")
        
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info("Stopping bot...")
            await self.bot_app.updater.stop()
            await self.bot_app.stop()
            await self.bot_app.shutdown()


async def main():
    """Main entry point"""
    bot = MultiUserBot()
    await bot.run()


if __name__ == "__main__":
    # Check required environment variables
    if not all([BOT_TOKEN, OPENAI_API_KEY]):
        print("Missing required environment variables!")
        print("Please set: TELEGRAM_BOT_TOKEN, OPENAI_API_KEY")
        print("Optional: TELEGRAM_API_ID, TELEGRAM_API_HASH (for history indexing)")
        exit(1)
        
    asyncio.run(main())