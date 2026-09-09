from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from app.db.base import Base

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), index=True, nullable=False)
    user_id = Column(Integer, nullable=True)
    user_prompt = Column(Text, nullable=False)
    detected_intent = Column(String(50), nullable=True)
    tools_called = Column(Text, nullable=True)
    tool_results = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=False)
    status = Column(String(20), default="SUCCESS")
    error_message = Column(Text, nullable=True)
    final_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
