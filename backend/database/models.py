from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from datetime import datetime, timezone
from database.database import Base

class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String(100))
    lastname = Column(String(100))
    email = Column(String(50), unique=True)
    password = Column(String(255))

class Document(Base):

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(50), ForeignKey("users.email"), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Message(Base):

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(50), ForeignKey("users.email"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    sender = Column(String(10), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))