from typing import Optional
from pydantic import BaseModel

class VenueBase(BaseModel):
    name: str
    capacity: int
    location: str
    contact_info: Optional[str] = None

class VenueCreate(VenueBase):
    pass

class VenueUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    location: Optional[str] = None
    contact_info: Optional[str] = None

class VenueResponse(VenueBase):
    id: int

    class Config:
        from_attributes = True
