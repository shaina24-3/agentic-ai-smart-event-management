from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.venue import Venue
from app.models.event import Event
from app.schemas.venue import VenueCreate

class VenueService:
    @staticmethod
    def create_venue(db: Session, venue_in: VenueCreate) -> Venue:
        existing = db.query(Venue).filter(Venue.name == venue_in.name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Venue '{venue_in.name}' already exists.")
        venue = Venue(
            name=venue_in.name,
            capacity=venue_in.capacity,
            location=venue_in.location,
            contact_info=venue_in.contact_info
        )
        db.add(venue)
        db.commit()
        db.refresh(venue)
        return venue

    @staticmethod
    def get_venue(db: Session, venue_id: int) -> Venue:
        venue = db.query(Venue).filter(Venue.id == venue_id).first()
        if not venue:
            raise HTTPException(status_code=404, detail=f"Venue with id {venue_id} not found.")
        return venue

    @staticmethod
    def list_venues(db: Session) -> List[Venue]:
        return db.query(Venue).all()

    @staticmethod
    def check_venue_availability(db: Session, venue_id: int, date: str, time: str, exclude_event_id: Optional[int] = None) -> bool:
        query = db.query(Event).filter(
            Event.venue_id == venue_id,
            Event.date == date,
            Event.time == time,
            Event.status == "ACTIVE"
        )
        if exclude_event_id:
            query = query.filter(Event.id != exclude_event_id)
        return query.first() is None
