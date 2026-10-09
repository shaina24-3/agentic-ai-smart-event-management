import re
from sqlalchemy.orm import Session
from .models import Event, Venue, Registration, User


def search_events(db: Session, keyword: str = ""):
    query = db.query(Event).filter(Event.status == "SCHEDULED")
    if keyword:
        cleaned_kw = re.sub(r"(?i)\b(events?|workshops?|sessions?|the|a|an)\b", "", keyword).strip(" .,!?'\"")
        search_kw = cleaned_kw if cleaned_kw else keyword.strip()
        query = query.filter(Event.title.ilike(f"%{search_kw}%"))
    events = query.order_by(Event.date.asc(), Event.time.asc(), Event.id.asc()).all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "date": e.date,
            "time": e.time,
            "capacity": e.capacity,
            "venue_id": e.venue_id,
            "venue": e.venue.name if e.venue else None,
            "venue_name": e.venue.name if e.venue else None,
        }
        for e in events
    ]


def _find_event_matches(db: Session, reference: str, include_inactive: bool):
    if not reference:
        return []

    query = db.query(Event)
    if not include_inactive:
        query = query.filter(Event.status == "SCHEDULED")
    raw = reference.strip().strip(" .,!?'\"")

    # 1. Exact Event ID check
    digits = re.findall(r"\b\d+\b", raw)
    if digits and len(digits) == 1 and (raw.isdigit() or raw.lower().startswith("event")):
        event = query.filter(Event.id == int(digits[0])).first()
        if event:
            return [event]

    # 2. Normalize text: remove trailing/leading filler words like "event", "workshop", "the"
    cleaned = re.sub(r"(?i)\b(events?|workshops?|sessions?|the|a|an)\b", "", raw).strip(" .,!?'\"")
    search_term = cleaned if cleaned else raw

    # SQL ILIKE search with cleaned term
    sql_matches = query.filter(Event.title.ilike(f"%{search_term}%")).order_by(Event.date, Event.time).all()
    if sql_matches:
        return sql_matches

    # 3. Flexible Python lowercase substring matching
    all_events = query.order_by(Event.date, Event.time).all()
    term_lower = search_term.lower()
    raw_lower = raw.lower()

    matched = []
    for e in all_events:
        t_lower = e.title.lower()
        if term_lower in t_lower or t_lower in raw_lower or t_lower in term_lower:
            matched.append(e)
            continue
        tokens = [w for w in term_lower.split() if len(w) > 2]
        if tokens and any(tok in t_lower for tok in tokens):
            matched.append(e)

    return matched


def find_event_matches(db: Session, reference: str):
    return _find_event_matches(db, reference, include_inactive=False)


def find_event_matches_any_status(db: Session, reference: str):
    return _find_event_matches(db, reference, include_inactive=True)


def is_venue_available(db: Session, venue_id: int, date: str, time: str) -> bool:
    conflict = db.query(Event).filter(
        Event.venue_id == venue_id,
        Event.date == date,
        Event.time == time,
        Event.status == "SCHEDULED",
    ).first()
    return conflict is None


def get_available_venues(db: Session, date: str, time: str):
    booked_ids = [
        row.venue_id
        for row in db.query(Event).filter(
            Event.date == date,
            Event.time == time,
            Event.status == "SCHEDULED",
        ).all()
    ]
    if not booked_ids:
        return db.query(Venue).all()
    return db.query(Venue).filter(Venue.id.not_in(booked_ids)).all()


def search_venues(db: Session, date: str = "", time: str = ""):
    if date and time:
        return get_available_venues(db, date, time)
    return db.query(Venue).order_by(Venue.name).all()


def create_venue_record(db: Session, name: str, capacity: int, location: str):
    if capacity < 1:
        return {"status": "error", "message": "Venue capacity must be a positive number."}
    existing = db.query(Venue).filter(Venue.name.ilike(name.strip())).first()
    if existing:
        return {"status": "error", "message": f"A venue named '{existing.name}' already exists."}

    venue = Venue(name=name.strip(), capacity=capacity, location=location.strip())
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return {"status": "success", "venue": venue}


def create_event_record(
    db: Session,
    user_id: int,
    title: str,
    description: str,
    date: str,
    time: str,
    venue_id: int,
    capacity: int,
):
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        return {"status": "error", "message": "Venue not found. Please choose an existing venue."}
    if capacity < 1:
        return {"status": "error", "message": "Event capacity must be a positive number."}
    if capacity > venue.capacity:
        return {"status": "error", "message": f"{venue.name} can hold at most {venue.capacity} participants."}
    if not is_venue_available(db, venue_id, date, time):
        return {"status": "error", "message": f"{venue.name} is already booked on {date} at {time}. Please choose another time or venue."}

    event = Event(
        title=title,
        description=description,
        date=date,
        time=time,
        venue_id=venue_id,
        capacity=capacity,
        created_by=user_id,
        status="SCHEDULED",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"status": "success", "event": event, "venue": venue}


def delete_event_record(db: Session, reference: str):
    if not reference or not reference.strip():
        return {"status": "error", "message": "Event name is required."}

    ref = reference.strip().strip(" .,!?'\"")
    event = None
    if ref.isdigit():
        event = db.query(Event).filter(Event.id == int(ref)).first()
    else:
        event = db.query(Event).filter(Event.title.ilike(ref)).first()

    if not event:
        return {"status": "error", "message": f"Event '{ref}' was not found."}

    event.status = "CANCELLED"
    db.commit()
    return {"status": "success", "message": f"Event '{event.title}' has been deleted.", "event": event}


def delete_venue_record(db: Session, reference: str):
    if not reference or not reference.strip():
        return {"status": "error", "message": "Venue name is required."}

    ref = reference.strip().strip(" .,!?'\"")
    venue = None
    if ref.isdigit():
        venue = db.query(Venue).filter(Venue.id == int(ref)).first()
    else:
        venue = db.query(Venue).filter(Venue.name.ilike(ref)).first()

    if not venue:
        return {"status": "error", "message": f"Venue '{ref}' was not found."}

    linked_events = db.query(Event).filter(Event.venue_id == venue.id, Event.status == "SCHEDULED").count()
    if linked_events > 0:
        return {
            "status": "error",
            "message": f"Venue '{venue.name}' cannot be deleted because it has scheduled events.",
        }

    db.delete(venue)
    db.commit()
    return {"status": "success", "message": f"Venue '{venue.name}' has been deleted.", "venue": venue}


def get_event_attendees(db: Session, event_id: int):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return {"status": "error", "message": "Event not found."}
    attendees = (
        db.query(User.name, User.email)
        .join(Registration, Registration.user_id == User.id)
        .filter(
            Registration.event_id == event_id,
            Registration.status == "CONFIRMED",
        )
        .order_by(User.name)
        .all()
    )
    return {
        "status": "success",
        "event": event,
        "count": len(attendees),
        "attendees": [{"name": name, "email": email} for name, email in attendees],
    }


def check_venue_availability(db: Session, venue_id: int, date: str, time: str = ""):
    if not time:
        time = "09:00 AM"
    available = is_venue_available(db, venue_id, date, time)
    return {"available": available, "venue_id": venue_id, "date": date, "time": time}

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
