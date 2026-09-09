from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.event import EventResponse
from app.schemas.user import UserResponse

class RegistrationCreate(BaseModel):
    event_id: int

class RegistrationResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    registered_at: datetime
    status: str
    event: Optional[EventResponse] = None
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True
