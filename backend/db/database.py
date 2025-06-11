from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        # Create pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Enable RLS on user_messages table
        await conn.execute(text("""
            ALTER TABLE user_messages ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY IF NOT EXISTS per_user ON user_messages
            USING (user_id = current_setting('app.user_id')::bigint);
        """))