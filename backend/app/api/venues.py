from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.venue import VenueCreate, VenueResponse
from app.services.venue_service import VenueService
from app.services.auth_service import require_admin
from app.models.user import User

router = APIRouter(prefix="/venues", tags=["Venues"])

@router.post("", response_model=VenueResponse)
def create_venue(venue_in: VenueCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return VenueService.create_venue(db, venue_in)

@router.get("", response_model=List[VenueResponse])
def list_venues(db: Session = Depends(get_db)):
    return VenueService.list_venues(db)

@router.get("/{venue_id}", response_model=VenueResponse)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    return VenueService.get_venue(db, venue_id)
