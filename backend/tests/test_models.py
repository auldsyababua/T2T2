import pytest
from sqlalchemy import select
from datetime import datetime

from models.models import User, Chat, Message, MessageEmbedding, UserMessage
from utils.logging import setup_logger

logger = setup_logger(__name__)


class TestModels:
    """Test database models and operations."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, test_db):
        """Test creating a user."""
        logger.info("Testing user creation")
        
        user = User(
            tg_user_id=987654321,
            username="another_user",
            first_name="Another",
            last_name="User"
        )
        test_db.add(user)
        await test_db.commit()
        
        # Query back
        result = await test_db.execute(
            select(User).where(User.tg_user_id == 987654321)
        )
        saved_user = result.scalar_one()
        
        assert saved_user.username == "another_user"
        assert saved_user.first_name == "Another"
        
        logger.info("User creation test passed")
    
    @pytest.mark.asyncio
    async def test_create_chat_and_message(self, test_db):
        """Test creating chat and message with relationship."""
        logger.info("Testing chat and message creation")
        
        # Create chat
        chat = Chat(
            chat_id=-1001234567890,
            title="Test Chat",
            type="group"
        )
        test_db.add(chat)
        await test_db.commit()
        
        # Create message
        message = Message(
            chat_id=chat.id,
            msg_id=12345,
            sender_id=123456789,
            sender_name="Test User",
            text="Hello, this is a test message!",
            date=datetime.utcnow()
        )
        test_db.add(message)
        await test_db.commit()
        
        # Query with relationship
        result = await test_db.execute(
            select(Message).where(Message.msg_id == 12345)
        )
        saved_message = result.scalar_one()
        
        assert saved_message.text == "Hello, this is a test message!"
        assert saved_message.chat_id == chat.id
        
        logger.info("Chat and message creation test passed")
    
    @pytest.mark.asyncio
    async def test_message_deduplication(self, test_db):
        """Test that messages are deduplicated by chat_id and msg_id."""
        logger.info("Testing message deduplication")
        
        # Create chat
        chat = Chat(
            chat_id=-1001234567890,
            title="Test Chat",
            type="group"
        )
        test_db.add(chat)
        await test_db.commit()
        
        # Create first message
        message1 = Message(
            chat_id=chat.id,
            msg_id=99999,
            sender_id=123456789,
            text="First version",
            date=datetime.utcnow()
        )
        test_db.add(message1)
        await test_db.commit()
        
        # Try to create duplicate (should fail with unique constraint)
        message2 = Message(
            chat_id=chat.id,
            msg_id=99999,  # Same msg_id
            sender_id=123456789,
            text="Second version",
            date=datetime.utcnow()
        )
        test_db.add(message2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await test_db.commit()
        
        logger.info("Message deduplication test passed")
    
    @pytest.mark.asyncio
    async def test_user_message_relationship(self, test_db, test_user):
        """Test many-to-many relationship between users and messages."""
        logger.info("Testing user-message relationship")
        
        # Create chat
        chat = Chat(
            chat_id=-1009876543210,
            title="Shared Chat",
            type="group"
        )
        test_db.add(chat)
        await test_db.commit()
        
        # Create message
        message = Message(
            chat_id=chat.id,
            msg_id=55555,
            sender_id=111111111,
            text="Shared message",
            date=datetime.utcnow()
        )
        test_db.add(message)
        await test_db.commit()
        
        # Create user-message relationship
        user_message = UserMessage(
            user_id=test_user.id,
            message_id=message.id
        )
        test_db.add(user_message)
        await test_db.commit()
        
        # Query relationship
        result = await test_db.execute(
            select(UserMessage).where(UserMessage.user_id == test_user.id)
        )
        relationships = result.scalars().all()
        
        assert len(relationships) == 1
        assert relationships[0].message_id == message.id
        
        logger.info("User-message relationship test passed")
    
    @pytest.mark.asyncio
    async def test_message_embedding(self, test_db):
        """Test message embedding storage."""
        logger.info("Testing message embedding")
        
        # Create chat and message
        chat = Chat(chat_id=-1005555555555, title="Embed Chat", type="private")
        test_db.add(chat)
        await test_db.commit()
        
        message = Message(
            chat_id=chat.id,
            msg_id=77777,
            text="Text to embed",
            date=datetime.utcnow()
        )
        test_db.add(message)
        await test_db.commit()
        
        # Create embedding
        embedding = MessageEmbedding(
            message_id=message.id,
            chunk_index=0,
            chunk_text="Text to embed",
            embedding=[0.1] * 3072  # Mock embedding
        )
        test_db.add(embedding)
        await test_db.commit()
        
        # Query back
        result = await test_db.execute(
            select(MessageEmbedding).where(MessageEmbedding.message_id == message.id)
        )
        saved_embedding = result.scalar_one()
        
        assert saved_embedding.chunk_text == "Text to embed"
        assert len(saved_embedding.embedding) == 3072
        
        logger.info("Message embedding test passed")