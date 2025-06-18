#!/usr/bin/env python3
"""
Simple T2T2 Bot - Talk to your Telegram history via Telegram

This is a standalone script that:
1. Uses Telethon to crawl your entire Telegram history (one-time)
2. Chunks and embeds messages into a vector database
3. Provides a Telegram bot interface for RAG-based Q&A
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

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

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration from environment
API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SESSION_STRING = os.getenv("TELETHON_SESSION", "")  # Store this after first auth

# Initialize services
embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
llm = ChatOpenAI(temperature=0, api_key=OPENAI_API_KEY)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)


class T2T2Bot:
    def __init__(self):
        self.vectorstore = None
        self.qa_chain = None
        self.telethon_client = None
        self.bot_app = None
        
    async def setup_telethon(self):
        """Setup Telethon client for crawling"""
        logger.info("Setting up Telethon client...")
        
        # Use existing session or create new one
        session = StringSession(SESSION_STRING) if SESSION_STRING else StringSession()
        self.telethon_client = TelegramClient(session, API_ID, API_HASH)
        
        await self.telethon_client.connect()
        
        if not await self.telethon_client.is_user_authorized():
            logger.info("Not authorized, need to login...")
            phone = input("Enter phone number: ")
            await self.telethon_client.send_code_request(phone)
            code = input("Enter verification code: ")
            await self.telethon_client.sign_in(phone, code)
            
            # Save session for future use
            new_session = self.telethon_client.session.save()
            logger.info(f"New session created! Save this in TELETHON_SESSION env var:")
            logger.info(new_session)
            
        logger.info("Telethon client ready!")
        
    async def crawl_and_index(self, limit_per_chat: int = 1000):
        """Crawl all chats and index into vector database"""
        logger.info("Starting chat crawl and indexing...")
        
        # Get all dialogs (chats)
        dialogs = await self.telethon_client.get_dialogs()
        logger.info(f"Found {len(dialogs)} chats")
        
        all_documents = []
        
        for dialog in dialogs:
            chat_title = dialog.title or f"Chat {dialog.id}"
            logger.info(f"Processing: {chat_title}")
            
            # Get messages from this chat
            messages = []
            async for message in self.telethon_client.iter_messages(dialog, limit=limit_per_chat):
                if message.text:
                    messages.append({
                        'text': message.text,
                        'date': message.date.isoformat(),
                        'sender': message.sender_id,
                        'chat': chat_title,
                        'chat_id': dialog.id
                    })
            
            logger.info(f"  Found {len(messages)} messages")
            
            # Create documents for this chat
            for msg in messages:
                metadata = {
                    'chat': msg['chat'],
                    'date': msg['date'],
                    'sender': str(msg['sender']),
                    'chat_id': str(msg['chat_id'])
                }
                
                # Split long messages into chunks
                chunks = text_splitter.split_text(msg['text'])
                for i, chunk in enumerate(chunks):
                    doc = {
                        'page_content': chunk,
                        'metadata': {**metadata, 'chunk_index': i}
                    }
                    all_documents.append(doc)
        
        logger.info(f"Total documents to index: {len(all_documents)}")
        
        # Create vector store
        logger.info("Creating vector store...")
        self.vectorstore = Chroma.from_documents(
            documents=all_documents,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )
        self.vectorstore.persist()
        
        # Create QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 5})
        )
        
        logger.info("Indexing complete!")
        
    async def load_existing_index(self):
        """Load existing vector database"""
        logger.info("Loading existing index...")
        
        self.vectorstore = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 5})
        )
        
        logger.info("Index loaded!")
        
    # Telegram Bot Handlers
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "👋 Welcome to T2T2!\n\n"
            "I can answer questions about your Telegram chat history.\n\n"
            "Just send me a question and I'll search through your indexed messages!\n\n"
            "Commands:\n"
            "/search <query> - Search for specific text\n"
            "/help - Show this help message"
        )
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)
        
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        if not context.args:
            await update.message.reply_text("Please provide a search query!")
            return
            
        query = ' '.join(context.args)
        await self.handle_query(update, query)
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages as queries"""
        query = update.message.text
        await self.handle_query(update, query)
        
    async def handle_query(self, update: Update, query: str):
        """Process a query using RAG"""
        logger.info(f"Query from {update.effective_user.id}: {query}")
        
        # Send typing indicator
        await update.message.chat.send_action("typing")
        
        try:
            # Get answer from QA chain
            result = self.qa_chain.run(query)
            
            # Send response
            await update.message.reply_text(result)
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            await update.message.reply_text(
                "Sorry, an error occurred while searching. Please try again."
            )
            
    async def setup_bot(self):
        """Setup Telegram bot"""
        logger.info("Setting up Telegram bot...")
        
        self.bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        self.bot_app.add_handler(CommandHandler("start", self.start_command))
        self.bot_app.add_handler(CommandHandler("help", self.help_command))
        self.bot_app.add_handler(CommandHandler("search", self.search_command))
        self.bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Bot setup complete!")
        
    async def run(self):
        """Run the bot"""
        # Check if we need to crawl or just load existing index
        if os.path.exists("./chroma_db"):
            logger.info("Found existing index")
            await self.load_existing_index()
        else:
            logger.info("No existing index found, need to crawl")
            await self.setup_telethon()
            await self.crawl_and_index()
            await self.telethon_client.disconnect()
            
        # Setup and run bot
        await self.setup_bot()
        
        logger.info("Starting bot...")
        await self.bot_app.initialize()
        await self.bot_app.start()
        await self.bot_app.updater.start_polling()
        
        # Keep running
        logger.info("Bot is running! Press Ctrl+C to stop.")
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
    bot = T2T2Bot()
    await bot.run()


if __name__ == "__main__":
    # Check required environment variables
    if not all([API_ID, API_HASH, BOT_TOKEN, OPENAI_API_KEY]):
        print("Missing required environment variables!")
        print("Please set: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN, OPENAI_API_KEY")
        exit(1)
        
    asyncio.run(main())