from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, Float, Integer, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector
from datetime import datetime

from db.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)
    tg_user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    session_file = Column(String(255))  # Path to Telethon session file
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_messages = relationship("UserMessage", back_populates="user")
    timelines = relationship("Timeline", back_populates="user")


class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, unique=True, nullable=False, index=True)
    title = Column(String(255))
    type = Column(String(50))  # private, group, channel
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = relationship("Message", back_populates="chat")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(BigInteger, primary_key=True)
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
    embeddings = relationship("MessageEmbedding", back_populates="message")
    user_messages = relationship("UserMessage", back_populates="message")
    images = relationship("MessageImage", back_populates="message")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('chat_id', 'msg_id', name='unique_chat_msg'),
    )


class UserMessage(Base):
    __tablename__ = "user_messages"
    
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    message_id = Column(BigInteger, ForeignKey("messages.id"), primary_key=True)
    
    # Relationships
    user = relationship("User", back_populates="user_messages")
    message = relationship("Message", back_populates="user_messages")


class MessageEmbedding(Base):
    __tablename__ = "message_embeddings"
    
    id = Column(BigInteger, primary_key=True)
    message_id = Column(BigInteger, ForeignKey("messages.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(3072))  # OpenAI text-embedding-3-large dimension
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="embeddings")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('message_id', 'chunk_index', name='unique_message_chunk'),
    )


class MessageImage(Base):
    __tablename__ = "message_images"
    
    id = Column(BigInteger, primary_key=True)
    message_id = Column(BigInteger, ForeignKey("messages.id"), nullable=False, index=True)
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
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    result = Column(JSON, nullable=False)  # Stored timeline JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="timelines")