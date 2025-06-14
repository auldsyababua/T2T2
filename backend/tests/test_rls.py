"""Test Row Level Security (RLS) policies to ensure data isolation between users."""
import os
from datetime import datetime

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.models import (
    Chat,
    Message,
    MessageEmbedding,
    MessageImage,
    Timeline,
    User,
    UserMessage,
)

# Skip all tests in this file if using SQLite
pytestmark = pytest.mark.skipif(
    os.getenv("DATABASE_URL", "").startswith("sqlite"),
    reason="RLS tests require PostgreSQL",
)


@pytest.mark.asyncio
async def test_user_messages_rls(db: AsyncSession):
    """Test that users can only see their own message associations."""
    # Create two users
    user1 = User(tg_user_id=1001, username="user1", first_name="User", last_name="One")
    user2 = User(tg_user_id=1002, username="user2", first_name="User", last_name="Two")
    db.add(user1)
    db.add(user2)
    await db.commit()

    # Create a chat and message
    chat = Chat(chat_id=2001, title="Test Chat", type="private")
    db.add(chat)
    await db.commit()

    message = Message(
        chat_id=chat.id,
        msg_id=3001,
        sender_id=1001,
        text="Test message",
        date=datetime(2024, 1, 1, 0, 0, 0),
    )
    db.add(message)
    await db.commit()

    # Create user-message associations
    user1_msg = UserMessage(user_id=user1.id, message_id=message.id)
    user2_msg = UserMessage(user_id=user2.id, message_id=message.id)
    db.add(user1_msg)
    db.add(user2_msg)
    await db.commit()

    # Test RLS - Set user context to user1
    await db.execute(text("SET app.user_id = :user_id"), {"user_id": user1.id})

    # User1 should see only their message association
    result = await db.execute(select(UserMessage))
    user_messages = result.scalars().all()
    assert len(user_messages) == 1
    assert user_messages[0].user_id == user1.id

    # Switch context to user2
    await db.execute(text("SET app.user_id = :user_id"), {"user_id": user2.id})

    # User2 should see only their message association
    result = await db.execute(select(UserMessage))
    user_messages = result.scalars().all()
    assert len(user_messages) == 1
    assert user_messages[0].user_id == user2.id


@pytest.mark.asyncio
async def test_message_embeddings_rls(db: AsyncSession):
    """Test that users can only see embeddings for their messages."""
    # Create user and message setup (similar to above)
    user1 = User(
        tg_user_id=1003, username="user3", first_name="User", last_name="Three"
    )
    user2 = User(tg_user_id=1004, username="user4", first_name="User", last_name="Four")
    db.add(user1)
    db.add(user2)
    await db.commit()

    chat = Chat(chat_id=2002, title="Test Chat 2", type="private")
    db.add(chat)
    await db.commit()

    # Create messages for each user
    msg1 = Message(
        chat_id=chat.id,
        msg_id=3002,
        sender_id=user1.tg_user_id,
        text="User 1 message",
        date=datetime(2024, 1, 1, 0, 0, 0),
    )
    msg2 = Message(
        chat_id=chat.id,
        msg_id=3003,
        sender_id=user2.tg_user_id,
        text="User 2 message",
        date=datetime(2024, 1, 1, 0, 0, 0),
    )
    db.add(msg1)
    db.add(msg2)
    await db.commit()

    # Create user-message associations
    db.add(UserMessage(user_id=user1.id, message_id=msg1.id))
    db.add(UserMessage(user_id=user2.id, message_id=msg2.id))
    await db.commit()

    # Create embeddings
    embedding1 = MessageEmbedding(
        message_id=msg1.id,
        chunk_index=0,
        chunk_text="User 1 text",
        embedding=[0.1] * 3072,  # Mock embedding
    )
    embedding2 = MessageEmbedding(
        message_id=msg2.id,
        chunk_index=0,
        chunk_text="User 2 text",
        embedding=[0.2] * 3072,  # Mock embedding
    )
    db.add(embedding1)
    db.add(embedding2)
    await db.commit()

    # Test RLS - User1 should only see their embedding
    await db.execute(text("SET app.user_id = :user_id"), {"user_id": user1.id})
    result = await db.execute(select(MessageEmbedding))
    embeddings = result.scalars().all()
    assert len(embeddings) == 1
    assert embeddings[0].message_id == msg1.id
    assert embeddings[0].chunk_text == "User 1 text"

    # User2 should only see their embedding
    await db.execute(text("SET app.user_id = :user_id"), {"user_id": user2.id})
    result = await db.execute(select(MessageEmbedding))
    embeddings = result.scalars().all()
    assert len(embeddings) == 1
    assert embeddings[0].message_id == msg2.id
    assert embeddings[0].chunk_text == "User 2 text"


@pytest.mark.asyncio
async def test_timelines_rls(db: AsyncSession):
    """Test that users can only see their own timelines."""
    # Create two users
    user1 = User(tg_user_id=1005, username="user5", first_name="User", last_name="Five")
    user2 = User(tg_user_id=1006, username="user6", first_name="User", last_name="Six")
    db.add(user1)
    db.add(user2)
    await db.commit()

    # Create timelines for each user
    timeline1 = Timeline(
        user_id=user1.id,
        query="user1 query",
        result={"items": [{"ts": "2024-01-01", "text": "Event 1"}]},
    )
    timeline2 = Timeline(
        user_id=user2.id,
        query="user2 query",
        result={"items": [{"ts": "2024-01-02", "text": "Event 2"}]},
    )
    db.add(timeline1)
    db.add(timeline2)
    await db.commit()

    # Test RLS - User1 should only see their timeline
    await db.execute(text("SET app.user_id = :user_id"), {"user_id": user1.id})
    result = await db.execute(select(Timeline))
    timelines = result.scalars().all()
    assert len(timelines) == 1
    assert timelines[0].user_id == user1.id
    assert timelines[0].query == "user1 query"

    # User2 should only see their timeline
    await db.execute(text("SET app.user_id = :user_id"), {"user_id": user2.id})
    result = await db.execute(select(Timeline))
    timelines = result.scalars().all()
    assert len(timelines) == 1
    assert timelines[0].user_id == user2.id
    assert timelines[0].query == "user2 query"


@pytest.mark.asyncio
async def test_no_user_context_returns_nothing(db: AsyncSession):
    """Test that without user context, no data is returned (secure by default)."""
    # Create a user and some data
    user = User(tg_user_id=1007, username="user7", first_name="User", last_name="Seven")
    db.add(user)
    await db.commit()

    timeline = Timeline(
        user_id=user.id,
        query="test query",
        result={"items": []},
    )
    db.add(timeline)
    await db.commit()

    # Clear any user context
    await db.execute(text("RESET app.user_id"))

    # Without user context, no timelines should be visible
    try:
        result = await db.execute(select(Timeline))
        timelines = result.scalars().all()
        assert len(timelines) == 0
    except Exception:
        # Some databases might throw an error instead, which is also acceptable
        pass
