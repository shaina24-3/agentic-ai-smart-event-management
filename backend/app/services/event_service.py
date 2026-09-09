from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import HTTPException, status
from app.models.event import Event
from app.models.registration import Registration
from app.schemas.event import EventCreate, EventUpdate, EventResponse
from app.schemas.venue import VenueResponse
from app.services.venue_service import VenueService

class EventService:
    @staticmethod
    def _enrich_event_response(db: Session, event: Event) -> EventResponse:
        confirmed_count = db.query(func.count(Registration.id)).filter(
            Registration.event_id == event.id,
            Registration.status == "CONFIRMED"
        ).scalar() or 0

        venue_resp = VenueResponse.model_validate(event.venue) if event.venue else None

        return EventResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            date=event.date,
            time=event.time,
            venue_id=event.venue_id,
            capacity=event.capacity,
            status=event.status,
            created_by=event.created_by,
            created_at=event.created_at,
            venue=venue_resp,
            confirmed_registrations_count=confirmed_count,
            available_seats=max(0, event.capacity - confirmed_count)
        )

    @staticmethod
    def create_event(db: Session, event_in: EventCreate, created_by_user_id: int) -> EventResponse:
        venue = VenueService.get_venue(db, event_in.venue_id)
        if event_in.capacity > venue.capacity:
            raise HTTPException(status_code=400, detail=f"Event capacity cannot exceed venue capacity ({venue.capacity}).")
        
        is_available = VenueService.check_venue_availability(db, event_in.venue_id, event_in.date, event_in.time)
        if not is_available:
            raise HTTPException(status_code=400, detail=f"Venue '{venue.name}' is already booked on {event_in.date} at {event_in.time}.")

        event = Event(
            title=event_in.title,
            description=event_in.description,
            date=event_in.date,
            time=event_in.time,
            venue_id=event_in.venue_id,
            capacity=event_in.capacity,
            status=event_in.status or "ACTIVE",
            created_by=created_by_user_id
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return EventService._enrich_event_response(db, event)

    @staticmethod
    def get_event(db: Session, event_id: int) -> EventResponse:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail=f"Event with id {event_id} not found.")
        return EventService._enrich_event_response(db, event)

    @staticmethod
    def update_event(db: Session, event_id: int, event_in: EventUpdate) -> EventResponse:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail=f"Event with id {event_id} not found.")

        new_venue_id = event_in.venue_id or event.venue_id
        new_date = event_in.date or event.date
        new_time = event_in.time or event.time

        if event_in.venue_id or event_in.date or event_in.time:
            is_avail = VenueService.check_venue_availability(db, new_venue_id, new_date, new_time, exclude_event_id=event_id)
            if not is_avail:
                raise HTTPException(status_code=400, detail=f"Venue is already booked on {new_date} at {new_time}.")

        update_data = event_in.model_dump(exclude_unset=True)
        for field, val in update_data.items():
            setattr(event, field, val)

        db.commit()
        db.refresh(event)
        return EventService._enrich_event_response(db, event)

    @staticmethod
    def cancel_event(db: Session, event_id: int) -> EventResponse:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail=f"Event with id {event_id} not found.")
        event.status = "CANCELLED"
        db.commit()
        db.refresh(event)
        return EventService._enrich_event_response(db, event)

    @staticmethod
    def search_events(
        db: Session,
        query: Optional[str] = None,
        date: Optional[str] = None,
        venue_id: Optional[int] = None,
        available_only: bool = False
    ) -> List[EventResponse]:
        q = db.query(Event).filter(Event.status == "ACTIVE")
        if query:
            q = q.filter(or_(Event.title.ilike(f"%{query}%"), Event.description.ilike(f"%{query}%")))
        if date:
            q = q.filter(Event.date == date)
        if venue_id:
            q = q.filter(Event.venue_id == venue_id)

        events = q.all()
        results = [EventService._enrich_event_response(db, ev) for ev in events]
        if available_only:
            results = [r for r in results if (r.available_seats or 0) > 0]
        return results
