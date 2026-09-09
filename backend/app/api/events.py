from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.event import EventCreate, EventUpdate, EventResponse
from app.services.event_service import EventService
from app.services.auth_service import require_admin
from app.models.user import User

router = APIRouter(prefix="/events", tags=["Events"])

@router.post("", response_model=EventResponse)
def create_event(event_in: EventCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return EventService.create_event(db, event_in, created_by_user_id=current_user.id)

@router.get("", response_model=List[EventResponse])
def list_events(
    query: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    venue_id: Optional[int] = Query(None),
    available_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    return EventService.search_events(db, query=query, date=date, venue_id=venue_id, available_only=available_only)

@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    return EventService.get_event(db, event_id)

@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event_in: EventUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return EventService.update_event(db, event_id, event_in)

@router.delete("/{event_id}", response_model=EventResponse)
def cancel_event(event_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return EventService.cancel_event(db, event_id)
