from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "USER"

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class VenueCreate(BaseModel):
    name: str
    capacity: int
    location: str

class VenueUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    location: Optional[str] = None

class VenueOut(VenueCreate):
    id: int
    class Config:
        from_attributes = True

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: str
    time: str
    venue_id: int
    capacity: int

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    venue_id: Optional[int] = None
    capacity: Optional[int] = None
    status: Optional[str] = None

class EventOut(EventCreate):
    id: int
    status: str
    created_by: int
    created_by: Optional[int] = None
    class Config:
        from_attributes = True

class RegistrationOut(BaseModel):
    id: int
    user_id: int
    event_id: int
    status: str
    registered_at: datetime
    class Config:
        from_attributes = True

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    ip_address: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    intent: str
    tools_used: List[str]
    latency_ms: float
