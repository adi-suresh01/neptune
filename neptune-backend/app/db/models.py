from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Create a single Base instance
Base = declarative_base()

class FileSystem(Base):
    __tablename__ = "filesystem"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    path = Column(String(500), nullable=True)  # Changed to nullable=True
    type = Column(String(50), nullable=False)  # 'file' or 'folder'
    parent_id = Column(Integer, ForeignKey('filesystem.id'), nullable=True)
    content = Column(Text, nullable=True)  # For file content
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Self-referential relationship for folder structure
    parent = relationship("FileSystem", remote_side=[id], backref="children")

class Note(Base):
    __tablename__ = "notes"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    file_id = Column(Integer, ForeignKey('filesystem.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to filesystem
    file = relationship("FileSystem", backref="notes")

class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class NoteTopic(Base):
    __tablename__ = "note_topics"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey('notes.id'), nullable=False)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False)
    confidence = Column(String(50), default="medium")  # low, medium, high
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    note = relationship("Note", backref="note_topics")
    topic = relationship("Topic", backref="note_topics")