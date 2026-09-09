from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.venue import VenueResponse

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    venue_id: int
    capacity: int

class EventCreate(EventBase):
    status: Optional[str] = "ACTIVE"

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    venue_id: Optional[int] = None
    capacity: Optional[int] = None
    status: Optional[str] = None

class EventResponse(EventBase):
    id: int
    status: str
    created_by: int
    created_at: datetime
    venue: Optional[VenueResponse] = None
    confirmed_registrations_count: Optional[int] = 0
    available_seats: Optional[int] = None

    class Config:
        from_attributes = True
