#!/usr/bin/env python3
"""
Optimized T2T2 Bot with comprehensive file processing
Supports all Telegram file types with vector storage and Redis caching
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from pathlib import Path
import hashlib
import mimetypes

# External libraries
import boto3
from botocore.exceptions import ClientError
import redis
from telegram import Update, Bot, File
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telethon import TelegramClient
from telethon.sessions import StringSession

# Supabase and AI
from supabase import create_client, Client
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.chains import RetrievalQA
from langchain.schema import Document
from dotenv import load_dotenv
import httpx

# Load environment
load_dotenv('.env.supabase_bot')

# Setup comprehensive logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID", "")

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "t2t2-images")

# Redis Configuration (if using external Redis)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Initialize services
logger.info("Initializing services...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)

# S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# Redis client (optional - can use Supabase's Redis integration)
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    redis_client.ping()
    logger.info("✅ Redis connected")
except Exception as e:
    logger.warning(f"Redis not available: {e}. Using database only.")
    redis_client = None


class OptimizedT2T2Bot:
    """Optimized bot with comprehensive file handling"""
    
    def __init__(self):
        self.bot_app = None
        self.telethon_client = None
        self.processing_stats = {
            'total_files': 0,
            'processed': 0,
            'failed': 0,
            'cached_hits': 0
        }
        
    async def handle_any_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Universal handler for all file types"""
        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        
        logger.info(f"File received from {user.username} ({user.id}) in {chat.title or 'DM'}")
        
        # Determine file type and get file info
        file_obj, file_type, file_info = self._extract_file_info(message)
        
        if not file_obj:
            await message.reply_text("❌ Could not process this file type")
            return
            
        # Quick acknowledgment
        status_msg = await message.reply_text(f"📥 Receiving {file_type}...")
        
        try:
            # Download file from Telegram
            logger.info(f"Downloading {file_type} file: {file_info['filename']}")
            telegram_file = await file_obj.get_file()
            
            # Generate S3 key
            s3_key = self._generate_s3_key(file_type, file_info['filename'], user.id, chat.id)
            
            # Download to memory
            file_data = await telegram_file.download_as_bytearray()
            
            # Upload to S3
            logger.info(f"Uploading to S3: {s3_key}")
            await self._upload_to_s3(s3_key, file_data, file_info['mime_type'])
            
            # Store file metadata in database
            file_record = await self._store_file_metadata(
                s3_key=s3_key,
                file_info=file_info,
                file_type=file_type,
                user=user,
                chat=chat,
                message=message
            )
            
            # Update status
            await status_msg.edit_text(f"✅ {file_type.capitalize()} saved! Processing...")
            
            # Trigger async processing via Edge Function
            await self._trigger_processing(file_record['id'], file_type, s3_key)
            
            # Final status
            await status_msg.edit_text(
                f"✅ {file_type.capitalize()} queued for processing!\n"
                f"📊 You can search for it once processing completes."
            )
            
            # Update stats
            self.processing_stats['total_files'] += 1
            
        except Exception as e:
            logger.error(f"Error handling file: {e}")
            await status_msg.edit_text(f"❌ Error: {str(e)}")
            self.processing_stats['failed'] += 1
    
    def _extract_file_info(self, message) -> tuple:
        """Extract file object and metadata from message"""
        file_obj = None
        file_type = 'unknown'
        file_info = {
            'filename': None,
            'file_size': 0,
            'mime_type': None,
            'file_id': None,
            'file_unique_id': None
        }
        
        # Check each file type
        if message.photo:
            file_obj = message.photo[-1]  # Largest photo
            file_type = 'photo'
            file_info['filename'] = f"photo_{message.message_id}.jpg"
            file_info['mime_type'] = 'image/jpeg'
        elif message.video:
            file_obj = message.video
            file_type = 'video'
            file_info['filename'] = message.video.file_name or f"video_{message.message_id}.mp4"
            file_info['mime_type'] = message.video.mime_type
        elif message.document:
            file_obj = message.document
            file_type = 'document'
            file_info['filename'] = message.document.file_name
            file_info['mime_type'] = message.document.mime_type
        elif message.audio:
            file_obj = message.audio
            file_type = 'audio'
            file_info['filename'] = message.audio.file_name or f"audio_{message.message_id}.mp3"
            file_info['mime_type'] = message.audio.mime_type
        elif message.voice:
            file_obj = message.voice
            file_type = 'voice'
            file_info['filename'] = f"voice_{message.message_id}.ogg"
            file_info['mime_type'] = 'audio/ogg'
        elif message.video_note:
            file_obj = message.video_note
            file_type = 'video_note'
            file_info['filename'] = f"video_note_{message.message_id}.mp4"
            file_info['mime_type'] = 'video/mp4'
        elif message.sticker:
            file_obj = message.sticker
            file_type = 'sticker'
            file_info['filename'] = f"sticker_{message.sticker.file_unique_id}.webp"
            file_info['mime_type'] = 'image/webp'
        elif message.animation:
            file_obj = message.animation
            file_type = 'animation'
            file_info['filename'] = f"animation_{message.message_id}.gif"
            file_info['mime_type'] = 'image/gif'
        
        if file_obj:
            file_info['file_id'] = file_obj.file_id
            file_info['file_unique_id'] = file_obj.file_unique_id
            file_info['file_size'] = getattr(file_obj, 'file_size', 0)
            
            # Ensure we have a mime type
            if not file_info['mime_type'] and file_info['filename']:
                file_info['mime_type'] = mimetypes.guess_type(file_info['filename'])[0]
        
        return file_obj, file_type, file_info
    
    def _generate_s3_key(self, file_type: str, filename: str, user_id: int, chat_id: int) -> str:
        """Generate organized S3 key"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = "".join(c for c in filename if c.isalnum() or c in '._-')
        
        # Organize by file type and date
        folder = {
            'photo': 'images',
            'video': 'videos',
            'audio': 'audio',
            'voice': 'voice',
            'document': 'documents',
            'animation': 'animations',
            'sticker': 'stickers',
            'video_note': 'video_notes'
        }.get(file_type, 'other')
        
        return f"{folder}/{datetime.now().strftime('%Y/%m')}/{user_id}_{timestamp}_{safe_filename}"
    
    async def _upload_to_s3(self, s3_key: str, file_data: bytes, mime_type: str):
        """Upload file to S3"""
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=file_data,
                ContentType=mime_type or 'application/octet-stream'
            )
            logger.info(f"✅ Uploaded to S3: {s3_key}")
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise
    
    async def _store_file_metadata(self, s3_key: str, file_info: dict, file_type: str, 
                                  user: Any, chat: Any, message: Any) -> dict:
        """Store file metadata in Supabase"""
        record = {
            's3_key': s3_key,
            's3_bucket': S3_BUCKET_NAME,
            'file_type': file_type,
            'file_size': file_info['file_size'],
            'mime_type': file_info['mime_type'],
            'original_filename': file_info['filename'],
            'file_extension': Path(file_info['filename']).suffix if file_info['filename'] else None,
            
            'telegram_file_id': file_info['file_id'],
            'telegram_file_unique_id': file_info['file_unique_id'],
            'telegram_chat_id': str(chat.id),
            'telegram_chat_name': chat.title or chat.username or 'DM',
            'telegram_message_id': str(message.message_id),
            'telegram_user_id': str(user.id),
            'telegram_username': user.username,
            
            'message_text': message.caption or message.text,
            'reply_to_message_id': str(message.reply_to_message.message_id) if message.reply_to_message else None,
            'telegram_date': message.date.isoformat() if message.date else None,
            
            'processing_status': 'pending'
        }
        
        result = supabase.table('telegram_files').insert(record).execute()
        logger.info(f"✅ Stored file metadata: {result.data[0]['id']}")
        
        return result.data[0]
    
    async def _trigger_processing(self, file_id: str, file_type: str, s3_key: str):
        """Trigger Edge Function for file processing"""
        try:
            # Add to processing queue
            queue_item = {
                'file_id': file_id,
                'queue_name': file_type,
                'priority': 5,  # Default priority
                'status': 'pending'
            }
            supabase.table('processing_queue').insert(queue_item).execute()
            
            # Trigger Edge Function
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SUPABASE_URL}/functions/v1/process-file",
                    json={
                        'fileId': file_id,
                        'fileType': file_type,
                        's3Key': s3_key,
                        's3Bucket': S3_BUCKET_NAME
                    },
                    headers={
                        'Authorization': f'Bearer {SUPABASE_KEY}',
                        'Content-Type': 'application/json'
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Processing triggered for {file_id}")
                else:
                    logger.error(f"Processing trigger failed: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error triggering processing: {e}")
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search through stored files"""
        user = update.effective_user
        query = ' '.join(context.args) if context.args else None
        
        if not query:
            await update.message.reply_text(
                "🔍 Usage: `/search <query>`\n"
                "Example: `/search cat photos`"
            )
            return
        
        await update.message.reply_text("🔍 Searching...")
        
        try:
            # Check Redis cache first
            cache_key = f"search:{user.id}:{hashlib.md5(query.encode()).hexdigest()}"
            cached_result = None
            
            if redis_client:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    self.processing_stats['cached_hits'] += 1
                    results = json.loads(cached_result)
                    logger.info(f"✅ Cache hit for search: {query}")
            
            if not cached_result:
                # Generate embedding for query
                query_embedding = embeddings.embed_query(query)
                
                # Search in database
                response = supabase.rpc('search_files_similarity', {
                    'query_embedding': query_embedding,
                    'match_count': 5,
                    'user_id': str(user.id),
                    'min_similarity': 0.3
                }).execute()
                
                results = response.data
                
                # Cache the results
                if redis_client and results:
                    redis_client.setex(
                        cache_key,
                        300,  # 5 minute cache
                        json.dumps(results)
                    )
            
            # Format results
            if results:
                response_text = f"🔍 Found {len(results)} results:\n\n"
                
                for i, result in enumerate(results, 1):
                    response_text += f"{i}. **{result['original_filename'] or result['file_type']}**\n"
                    response_text += f"   📊 Similarity: {result['similarity']:.0%}\n"
                    
                    if result['extracted_text']:
                        preview = result['extracted_text'][:100] + "..."
                        response_text += f"   📝 {preview}\n"
                    
                    response_text += "\n"
                
                await update.message.reply_text(response_text, parse_mode='Markdown')
            else:
                await update.message.reply_text("No results found. Try different keywords.")
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            await update.message.reply_text(f"❌ Search error: {str(e)}")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        user = update.effective_user
        
        try:
            # Get user stats
            stats = supabase.table('user_statistics').select('*').eq('user_id', str(user.id)).execute()
            
            if stats.data:
                user_stats = stats.data[0]
                
                # Format file size
                total_mb = user_stats['total_size_bytes'] / (1024 * 1024)
                
                response = f"📊 **Your Statistics**\n\n"
                response += f"📁 Total files: {user_stats['total_files']}\n"
                response += f"💾 Total size: {total_mb:.1f} MB\n"
                response += f"📅 First upload: {user_stats['first_file_date'][:10]}\n"
                response += f"🔍 Searches: {user_stats['search_count']}\n\n"
                
                # File type breakdown
                response += "**Files by type:**\n"
                for file_type, count in user_stats['files_by_type'].items():
                    response += f"• {file_type}: {count}\n"
                
                # Bot stats
                response += f"\n**Bot Stats:**\n"
                response += f"• Processed: {self.processing_stats['processed']}\n"
                response += f"• Failed: {self.processing_stats['failed']}\n"
                response += f"• Cache hits: {self.processing_stats['cached_hits']}\n"
                
                await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text("No files stored yet. Send me some files!")
                
        except Exception as e:
            logger.error(f"Stats error: {e}")
            await update.message.reply_text("❌ Error retrieving statistics")
    
    async def setup_bot(self):
        """Setup bot handlers"""
        logger.info("Setting up bot...")
        
        self.bot_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Commands
        self.bot_app.add_handler(CommandHandler("start", self.start_command))
        self.bot_app.add_handler(CommandHandler("search", self.search_command))
        self.bot_app.add_handler(CommandHandler("stats", self.stats_command))
        self.bot_app.add_handler(CommandHandler("help", self.help_command))
        
        # File handlers - handle all file types
        self.bot_app.add_handler(MessageHandler(
            filters.PHOTO | filters.VIDEO | filters.Document.ALL | 
            filters.AUDIO | filters.VOICE | filters.VIDEO_NOTE | 
            filters.Sticker.ALL | filters.ANIMATION,
            self.handle_any_file
        ))
        
        logger.info("✅ Bot setup complete")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        user = update.effective_user
        
        welcome_text = f"""
👋 Welcome {user.first_name}!

I'm T2T2 Bot - I store and index ALL your Telegram content:
📸 Photos & Videos
📄 Documents & Files
🎵 Audio & Voice messages
🎬 GIFs & Stickers

**Features:**
• 🔍 Semantic search across all content
• 🤖 AI-powered content analysis
• 📊 Usage statistics
• ⚡ Fast retrieval with caching

**Commands:**
/search <query> - Search your files
/stats - View your statistics
/help - Show help

Just send me any file and I'll process it!
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        help_text = """
**T2T2 Bot Help**

**Supported Files:**
• Photos (JPG, PNG, etc.)
• Videos (MP4, AVI, etc.)
• Documents (PDF, DOC, TXT, etc.)
• Audio files (MP3, OGG, etc.)
• Voice messages
• GIFs and animations
• Stickers

**Search Tips:**
• Use natural language: "photos from last week"
• Search by content: "documents about python"
• Find by objects: "images with cats"

**Commands:**
/search <query> - Search files
/stats - Your statistics
/help - This message

**Privacy:**
All files are stored securely in your personal space.
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def run(self):
        """Run the bot"""
        await self.setup_bot()
        
        logger.info("🚀 Starting Optimized T2T2 Bot...")
        await self.bot_app.initialize()
        await self.bot_app.start()
        await self.bot_app.updater.start_polling()
        
        logger.info("✅ Bot is running!")
        
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
    bot = OptimizedT2T2Bot()
    await bot.run()


if __name__ == "__main__":
    # Verify configuration
    required = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": SUPABASE_KEY,
        "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
        "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
        "S3_BUCKET_NAME": S3_BUCKET_NAME
    }
    
    missing = [k for k, v in required.items() if not v]
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        exit(1)
    
    print("✅ All environment variables configured")
    print(f"📦 S3 Bucket: {S3_BUCKET_NAME}")
    print(f"🚀 Starting bot...")
    
    asyncio.run(main())