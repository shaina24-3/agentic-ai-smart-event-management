from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True, nullable=False)
    description = Column(Text, nullable=True)
    date = Column(String(20), nullable=False)  # YYYY-MM-DD
    time = Column(String(20), nullable=False)  # HH:MM
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)  # "ACTIVE", "CANCELLED"
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    venue = relationship("Venue", back_populates="events")
    creator = relationship("User", back_populates="created_events")
    registrations = relationship("Registration", back_populates="event", cascade="all, delete-orphan")
