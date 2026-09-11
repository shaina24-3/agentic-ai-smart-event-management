from sqlalchemy.orm import Session
from .models import Event, Venue, Registration

def search_events(db: Session, keyword: str = ""):
    query = db.query(Event).filter(Event.status == "SCHEDULED")
    if keyword:
        query = query.filter(Event.title.ilike(f"%{keyword}%"))
    events = query.all()
    return [{"id": e.id, "title": e.title, "date": e.date, "capacity": e.capacity} for e in events]

def check_venue_availability(db: Session, venue_id: int, date: str):
    conflict = db.query(Event).filter(
        Event.venue_id == venue_id,
        Event.date == date,
        Event.status == "SCHEDULED"
    ).first()
    return {"available": conflict is None, "venue_id": venue_id, "date": date}

def register_participant(db: Session, user_id: int, event_id: int):
    event = db.query(Event).filter(Event.id == event_id, Event.status == "SCHEDULED").first()
    if not event:
        return {"status": "error", "message": "Event not found or cancelled"}
    
    current_count = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.status == "CONFIRMED"
    ).count()
    
    if current_count >= event.capacity:
        return {"status": "error", "message": "Event capacity reached"}
        
    existing = db.query(Registration).filter(
        Registration.user_id == user_id,
        Registration.event_id == event_id,
        Registration.status == "CONFIRMED"
    ).first()
    if existing:
        return {"status": "error", "message": "Already registered"}

    reg = Registration(user_id=user_id, event_id=event_id, status="CONFIRMED")
    db.add(reg)
    db.commit()
    return {"status": "success", "message": f"Successfully registered for event ID {event_id}"}

def cancel_registration(db: Session, user_id: int, event_id: int):
    reg = db.query(Registration).filter(
        Registration.user_id == user_id,
        Registration.event_id == event_id,
        Registration.status == "CONFIRMED"
    ).first()
    if not reg:
        return {"status": "error", "message": "No active registration found"}
    reg.status = "CANCELLED"
    db.commit()
    return {"status": "success", "message": "Registration cancelled successfully"}
