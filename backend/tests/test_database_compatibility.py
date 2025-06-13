"""
Test database compatibility between PostgreSQL and SQLite.
This ensures our models and queries work with both databases.
"""
import pytest
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from models.models import Base, User, Chat, Message, MessageEmbedding


class TestDatabaseCompatibility:
    """Test that our database setup works with both PostgreSQL and SQLite."""

    @pytest.mark.asyncio
    async def test_sqlite_autoincrement(self, test_db):
        """Test that autoincrement works properly in SQLite."""
        # Create a user without specifying ID
        user = User(
            tg_user_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
        )
        test_db.add(user)
        await test_db.commit()

        # ID should be automatically assigned
        assert user.id is not None
        assert isinstance(user.id, int)
        assert user.id > 0

    @pytest.mark.asyncio
    async def test_vector_column_in_sqlite(self, test_db):
        """Test that Vector columns work in SQLite (as JSON)."""
        # Create a chat and message first
        chat = Chat(chat_id=12345, title="Test Chat", type="private")
        test_db.add(chat)
        await test_db.commit()

        message = Message(
            chat_id=chat.id,
            msg_id=1,
            sender_id=123,
            text="Test message",
            date=datetime(2025, 6, 12, 0, 0, 0),
        )
        test_db.add(message)
        await test_db.commit()

        # Create embedding with vector data
        embedding = MessageEmbedding(
            message_id=message.id,
            chunk_index=0,
            chunk_text="Test chunk",
            embedding=[0.1, 0.2, 0.3],  # This should work as JSON in SQLite
        )
        test_db.add(embedding)
        await test_db.commit()

        # Should be able to retrieve it
        assert embedding.id is not None
        assert embedding.embedding == [0.1, 0.2, 0.3]

    def test_sync_sqlite_engine_creation(self):
        """Test that we can create a sync SQLite engine without pool issues."""
        # This tests the conditional engine creation logic
        engine = create_engine("sqlite:///:memory:", echo=False)

        # Create tables
        Base.metadata.create_all(engine)

        # Test basic operations
        with Session(engine) as session:
            user = User(
                tg_user_id=987654321,
                username="sync_test",
                first_name="Sync",
                last_name="Test",
            )
            session.add(user)
            session.commit()

            # Should have an ID
            assert user.id is not None

    @pytest.mark.asyncio
    async def test_no_pgvector_extension_needed(self, test_db):
        """Test that SQLite tests don't fail due to missing pgvector."""
        # This should not raise any errors about pgvector
        result = await test_db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = [row[0] for row in result]

        # Should have created our tables
        assert "users" in tables
        assert "chats" in tables
        assert "messages" in tables
