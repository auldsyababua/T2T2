import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient
from unittest.mock import Mock, patch
import os
from datetime import datetime

# Override environment for testing
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_FILE"] = "/tmp/t2t2_test.log"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from main import app
from db.database import Base, get_db
from models.models import User
from utils.logging import setup_logger

# Test logger
logger = setup_logger("tests")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """Create a test database for each test function."""
    # Create test engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    TestSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator:
    """Create a test client with overridden database dependency."""
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        logger.info("Test client created")
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        tg_user_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    logger.info(f"Created test user: {user.username}")
    return user


@pytest.fixture
def mock_telegram_auth():
    """Mock Telegram authentication."""
    with patch("api.routes.auth.verify_telegram_auth") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls."""
    with patch("openai.AsyncOpenAI") as mock:
        mock_client = Mock()
        mock.return_value = mock_client
        
        # Mock embeddings
        mock_client.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 3072)]
        )
        
        # Mock chat completion
        mock_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test response"))]
        )
        
        yield mock_client


@pytest.fixture
def mock_telethon():
    """Mock Telethon client."""
    with patch("telethon.TelegramClient") as mock:
        mock_client = Mock()
        mock.return_value = mock_client
        
        # Mock methods
        mock_client.connect = Mock(return_value=asyncio.Future())
        mock_client.connect.return_value.set_result(None)
        
        mock_client.disconnect = Mock(return_value=asyncio.Future())
        mock_client.disconnect.return_value.set_result(None)
        
        yield mock_client


@pytest.fixture
def mock_upstash_redis():
    """Mock Upstash Redis client."""
    with patch("upstash_redis.Redis") as mock:
        mock_redis = Mock()
        mock.from_env.return_value = mock_redis
        
        # Mock methods
        mock_redis.get = Mock(return_value=None)
        mock_redis.set = Mock(return_value=True)
        mock_redis.delete = Mock(return_value=1)
        
        yield mock_redis


@pytest.fixture
def mock_s3():
    """Mock AWS S3 client."""
    with patch("boto3.client") as mock:
        mock_s3 = Mock()
        mock.return_value = mock_s3
        
        # Mock methods
        mock_s3.upload_fileobj = Mock()
        mock_s3.generate_presigned_url = Mock(
            return_value="https://mock-s3-url.com/test.jpg"
        )
        
        yield mock_s3