from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="USER", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    registrations = relationship("Registration", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="creator")
    sessions = relationship("AgentSession", back_populates="user")
    agent_runs = relationship("AgentRun", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

class Venue(Base):
    __tablename__ = "venues"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    location = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship("Event", back_populates="venue", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    date = Column(String(50), nullable=False, index=True)
    time = Column(String(50), nullable=False)
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="CASCADE"), nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="SCHEDULED", index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    venue = relationship("Venue", back_populates="events")
    creator = relationship("User", back_populates="events")
    registrations = relationship("Registration", back_populates="event", cascade="all, delete-orphan")

class Registration(Base):
    __tablename__ = "registrations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), nullable=False, default="CONFIRMED", index=True)

    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_user_event"),)

    user = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")

class AgentSession(Base):
    __tablename__ = "agent_sessions"
    id = Column(String(100), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    runs = relationship("AgentRun", back_populates="session")

class AgentRun(Base):
    __tablename__ = "agent_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), ForeignKey("agent_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_request = Column(Text, nullable=False)
    detected_intent = Column(String(50), nullable=True, index=True)
    tool_selected = Column(String(100), nullable=True)
    tool_input = Column(Text, nullable=True)
    tool_output = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=True)
    final_response = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="agent_runs")
    session = relationship("AgentSession", back_populates="runs")
    tool_calls = relationship("ToolCall", back_populates="run", cascade="all, delete-orphan")

class ToolCall(Base):
    __tablename__ = "tool_calls"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    tool_input = Column(Text, nullable=True)
    tool_output = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("AgentRun", back_populates="tool_calls")

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    file_path = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(JSON, nullable=True)

    document = relationship("KnowledgeDocument", back_populates="chunks")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")
