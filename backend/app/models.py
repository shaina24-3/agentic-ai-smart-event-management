# import datetime
# from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
# from sqlalchemy.orm import relationship
# from .database import Base

# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(100), nullable=False)
#     email = Column(String(120), unique=True, index=True, nullable=False)
#     password_hash = Column(String(255), nullable=False)
#     role = Column(String(20), default="USER")  # ADMIN or USER

#     registrations = relationship("Registration", back_populates="user")

# class Venue(Base):
#     __tablename__ = "venues"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(100), nullable=False)
#     capacity = Column(Integer, nullable=False)
#     location = Column(String(255), nullable=False)

#     events = relationship("Event", back_populates="venue")

# class Event(Base):
#     __tablename__ = "events"
#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String(200), index=True, nullable=False)
#     description = Column(Text, nullable=True)
#     date = Column(String(50), nullable=False)  # Format: YYYY-MM-DD
#     time = Column(String(50), nullable=False)
#     venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
#     capacity = Column(Integer, nullable=False)
#     status = Column(String(20), default="SCHEDULED")  # SCHEDULED, CANCELLED
#     created_by = Column(Integer, ForeignKey("users.id"))

#     venue = relationship("Venue", back_populates="events")
#     registrations = relationship("Registration", back_populates="event")

# class Registration(Base):
#     __tablename__ = "registrations"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
#     registered_at = Column(DateTime, default=datetime.datetime.utcnow)
#     status = Column(String(20), default="CONFIRMED")  # CONFIRMED, CANCELLED

#     user = relationship("User", back_populates="registrations")
#     event = relationship("Event", back_populates="registrations")

# class AgentRun(Base):
#     __tablename__ = "agent_runs"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, nullable=True)
#     user_request = Column(Text, nullable=False)
#     detected_intent = Column(String(50))
#     tool_selected = Column(String(100))
#     tool_input = Column(Text)
#     tool_output = Column(Text)
#     latency_ms = Column(Float)
#     final_response = Column(Text)
#     timestamp = Column(DateTime, default=datetime.datetime.utcnow)


import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float,
    JSON,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="USER")

    registrations = relationship(
        "Registration",
        back_populates="user"
    )


class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)
    location = Column(String(255), nullable=False)

    events = relationship(
        "Event",
        back_populates="venue"
    )


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True, nullable=False)
    description = Column(Text, nullable=True)
    date = Column(String(50), nullable=False)
    time = Column(String(50), nullable=False)
    venue_id = Column(
        Integer,
        ForeignKey("venues.id"),
        nullable=False
    )
    capacity = Column(Integer, nullable=False)
    status = Column(String(20), default="SCHEDULED")
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    venue = relationship(
        "Venue",
        back_populates="events"
    )

    registrations = relationship(
        "Registration",
        back_populates="event"
    )


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=False
    )
    registered_at = Column(
        DateTime,
        default=datetime.datetime.utcnow
    )
    status = Column(
        String(20),
        default="CONFIRMED"
    )

    user = relationship(
        "User",
        back_populates="registrations"
    )

    event = relationship(
        "Event",
        back_populates="registrations"
    )


class KnowledgeDocument(Base):
    """
    Stores metadata about documents used by the RAG system.

    Corresponds to the knowledge_documents table
    in database/schema.sql.
    """

    __tablename__ = "knowledge_documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(255),
        nullable=False
    )

    file_path = Column(
        String(255),
        nullable=True
    )

    file_type = Column(
        String(50),
        nullable=True
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow
    )

    chunks = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )


class KnowledgeChunk(Base):
    """
    Stores individual text chunks extracted from
    knowledge documents.

    The embedding column stores the vector generated
    by the embedding model as JSON.
    """

    __tablename__ = "knowledge_chunks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    document_id = Column(
        Integer,
        ForeignKey("knowledge_documents.id"),
        nullable=False
    )

    chunk_text = Column(
        Text,
        nullable=False
    )

    chunk_index = Column(
        Integer,
        nullable=False
    )

    embedding = Column(
        JSON,
        nullable=True
    )

    document = relationship(
        "KnowledgeDocument",
        back_populates="chunks"
    )


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        nullable=True
    )

    user_request = Column(
        Text,
        nullable=False
    )

    detected_intent = Column(
        String(50)
    )

    tool_selected = Column(
        String(100)
    )

    tool_input = Column(
        Text
    )

    tool_output = Column(
        Text
    )

    latency_ms = Column(
        Float
    )

    final_response = Column(
        Text
    )

    timestamp = Column(
        DateTime,
        default=datetime.datetime.utcnow
    )
