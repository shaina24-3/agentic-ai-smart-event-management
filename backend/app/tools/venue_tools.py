from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.venue_service import VenueService

def tool_check_venue_availability(db: Session, venue_id: int, date: str, time: str) -> Dict[str, Any]:
    try:
        venue = VenueService.get_venue(db, venue_id)
        is_avail = VenueService.check_venue_availability(db, venue_id, date, time)
        return {
            "venue_id": venue_id,
            "venue_name": venue.name,
            "date": date,
            "time": time,
            "is_available": is_avail,
            "message": f"Venue '{venue.name}' is {'AVAILABLE' if is_avail else 'BOOKED'} on {date} at {time}."
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def tool_list_venues(db: Session) -> Dict[str, Any]:
    venues = VenueService.list_venues(db)
    return {
        "count": len(venues),
        "venues": [{"id": v.id, "name": v.name, "capacity": v.capacity, "location": v.location} for v in venues]
    }
