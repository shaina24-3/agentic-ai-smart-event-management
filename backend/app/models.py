import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from .database import Base

# 1. Users Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="USER")  # ADMIN or USER
    role = Column(String(20), default="USER")  # Options: 'ADMIN', 'USER'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    registrations = relationship("Registration", back_populates="user")
    registrations = relationship("Registration", back_populates="user", cascade="all, delete-orphan")
    agent_sessions = relationship("AgentSession", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

# 2. Venues Model
class Venue(Base):
    __tablename__ = "venues"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    location = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    events = relationship("Event", back_populates="venue")
    events = relationship("Event", back_populates="venue", cascade="all, delete-orphan")

# 3. Events Model
class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), index=True, nullable=False)
    description = Column(Text, nullable=True)
    date = Column(String(50), nullable=False)  # Format: YYYY-MM-DD
    date = Column(String(50), nullable=False, index=True)  # Format: YYYY-MM-DD
    time = Column(String(50), nullable=False)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="CASCADE"), nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(String(20), default="SCHEDULED")  # SCHEDULED, CANCELLED
    created_by = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="SCHEDULED", index=True)  # 'SCHEDULED', 'CANCELLED'
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    venue = relationship("Venue", back_populates="events")
    registrations = relationship("Registration", back_populates="event")
    registrations = relationship("Registration", back_populates="event", cascade="all, delete-orphan")

# 4. Registrations Model
class Registration(Base):
    __tablename__ = "registrations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    registered_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(20), default="CONFIRMED")  # CONFIRMED, CANCELLED
    status = Column(String(20), default="CONFIRMED", index=True)  # 'CONFIRMED', 'CANCELLED'

    user = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")

# 5. Agent Sessions Model
class AgentSession(Base):
    __tablename__ = "agent_sessions"
    id = Column(String(100), primary_key=True, index=True)  # Session UUID/Identifier
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="agent_sessions")
    runs = relationship("AgentRun", back_populates="session")

# 6. Agent Runs Model
class AgentRun(Base):
    __tablename__ = "agent_runs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(100), ForeignKey("agent_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_request = Column(Text, nullable=False)
    detected_intent = Column(String(50))
    tool_selected = Column(String(100))
    tool_input = Column(Text)
    tool_output = Column(Text)
    latency_ms = Column(Float)
    final_response = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    detected_intent = Column(String(50), nullable=True, index=True)
    tool_selected = Column(String(100), nullable=True)
    tool_input = Column(Text, nullable=True)
    tool_output = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=True)
    final_response = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    session = relationship("AgentSession", back_populates="runs")
    tool_calls = relationship("ToolCall", back_populates="agent_run", cascade="all, delete-orphan")

# 7. Tool Calls Model
class ToolCall(Base):
    __tablename__ = "tool_calls"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    tool_input = Column(Text, nullable=True)
    tool_output = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    agent_run = relationship("AgentRun", back_populates="tool_calls")

# 8. Knowledge Documents Model
class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    file_path = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")

# 9. Knowledge Chunks Model
class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(JSON, nullable=True)  # Vector embedding stored as JSON list of floats
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("KnowledgeDocument", back_populates="chunks")

# 10. Audit Logs Model
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., 'CREATE_EVENT', 'CANCEL_REGISTRATION'
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")
