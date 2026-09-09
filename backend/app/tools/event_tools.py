from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.services.event_service import EventService
from app.schemas.event import EventCreate

def tool_search_events(db: Session, query: Optional[str] = None, date: Optional[str] = None, venue_id: Optional[int] = None, available_only: bool = False) -> Dict[str, Any]:
    events = EventService.search_events(db, query=query, date=date, venue_id=venue_id, available_only=available_only)
    return {
        "count": len(events),
        "events": [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "date": e.date,
                "time": e.time,
                "capacity": e.capacity,
                "available_seats": e.available_seats,
                "venue": e.venue.name if e.venue else "N/A",
                "status": e.status
            }
            for e in events
        ]
    }

def tool_get_event_details(db: Session, event_id: int) -> Dict[str, Any]:
    try:
        e = EventService.get_event(db, event_id)
        return {
            "success": True,
            "event": {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "date": e.date,
                "time": e.time,
                "capacity": e.capacity,
                "available_seats": e.available_seats,
                "venue": e.venue.name if e.venue else "N/A"
            }
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def tool_create_event(db: Session, title: str, date: str, time: str, venue_id: int, capacity: int, created_by_user_id: int, description: Optional[str] = None) -> Dict[str, Any]:
    try:
        e_in = EventCreate(title=title, description=description, date=date, time=time, venue_id=venue_id, capacity=capacity)
        created = EventService.create_event(db, e_in, created_by_user_id=created_by_user_id)
        return {"success": True, "message": f"Event '{created.title}' created with ID {created.id}.", "event_id": created.id}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def tool_cancel_event(db: Session, event_id: int) -> Dict[str, Any]:
    try:
        cancelled = EventService.cancel_event(db, event_id)
        return {"success": True, "message": f"Event '{cancelled.title}' (ID {cancelled.id}) cancelled."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
