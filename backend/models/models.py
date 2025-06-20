import os
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.db.database import Base

# Only import Vector for PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL.startswith("sqlite"):
    from pgvector.sqlalchemy import Vector
else:
    # For SQLite, use JSON column instead of Vector
    def Vector(dim):
        return JSON


class User(Base):
    __tablename__ = "users"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    tg_user_id = Column(BigInteger, unique=True, nullable=True, index=True)
    username = Column(String(255), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    session_file = Column(String(255))  # Path to Telethon session file
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user_messages = relationship(
        "UserMessage", back_populates="user", cascade="all, delete-orphan"
    )
    timelines = relationship(
        "Timeline", back_populates="user", cascade="all, delete-orphan"
    )


class Chat(Base):
    __tablename__ = "chats"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    chat_id = Column(BigInteger, unique=True, nullable=False, index=True)
    title = Column(String(255))
    type = Column(String(50))  # private, group, channel
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="chat")


class Message(Base):
    __tablename__ = "messages"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    chat_id = Column(BigInteger, ForeignKey("chats.id"), nullable=False, index=True)
    msg_id = Column(BigInteger, nullable=False)  # Telegram message ID
    sender_id = Column(BigInteger)
    sender_name = Column(String(255))
    text = Column(Text)
    date = Column(DateTime, nullable=False, index=True)
    reply_to_msg_id = Column(BigInteger)
    has_media = Column(Boolean, default=False)
    media_type = Column(String(50))  # photo, video, document, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    embeddings = relationship(
        "MessageEmbedding", back_populates="message", cascade="all, delete-orphan"
    )
    user_messages = relationship(
        "UserMessage", back_populates="message", cascade="all, delete-orphan"
    )
    images = relationship(
        "MessageImage", back_populates="message", cascade="all, delete-orphan"
    )

    # Unique constraint
    __table_args__ = (UniqueConstraint("chat_id", "msg_id", name="unique_chat_msg"),)


class UserMessage(Base):
    __tablename__ = "user_messages"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    message_id = Column(BigInteger, ForeignKey("messages.id"), primary_key=True)

    # Relationships
    user = relationship("User", back_populates="user_messages")
    message = relationship("Message", back_populates="user_messages")


class MessageEmbedding(Base):
    __tablename__ = "message_embeddings"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    message_id = Column(
        BigInteger, ForeignKey("messages.id"), nullable=False, index=True
    )
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_metadata = Column(JSON)  # Store timestamp, chat info, reply context, etc.
    embedding = Column(Vector(3072))  # OpenAI text-embedding-3-large dimension
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    message = relationship("Message", back_populates="embeddings")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("message_id", "chunk_index", name="unique_message_chunk"),
    )


class MessageImage(Base):
    __tablename__ = "message_images"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    message_id = Column(
        BigInteger, ForeignKey("messages.id"), nullable=False, index=True
    )
    file_hash = Column(String(64), unique=True, nullable=False)  # SHA-256
    s3_url = Column(String(500))
    ocr_text = Column(Text)
    img_embedding = Column(Vector(512))  # CLIP ViT-B/32 dimension
    width = Column(Integer)
    height = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    message = relationship("Message", back_populates="images")


class Timeline(Base):
    __tablename__ = "timelines"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    result = Column(JSON, nullable=False)  # Stored timeline JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="timelines")
