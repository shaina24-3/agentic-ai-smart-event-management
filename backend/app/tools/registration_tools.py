from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.registration_service import RegistrationService

def tool_register_participant(db: Session, user_id: int, event_id: int) -> Dict[str, Any]:
    try:
        reg = RegistrationService.register_participant(db, user_id=user_id, event_id=event_id)
        return {
            "success": True,
            "registration_id": reg.id,
            "event_title": reg.event.title if reg.event else "N/A",
            "date": reg.event.date if reg.event else "N/A",
            "time": reg.event.time if reg.event else "N/A",
            "status": reg.status,
            "message": f"Registration confirmed! You are registered for '{reg.event.title if reg.event else event_id}'."
        }
    except Exception as exc:
        return {"success": False, "error": getattr(exc, "detail", str(exc))}

def tool_cancel_registration(db: Session, user_id: int, event_id: int) -> Dict[str, Any]:
    try:
        reg = RegistrationService.cancel_registration(db, user_id=user_id, event_id=event_id)
        return {
            "success": True,
            "registration_id": reg.id,
            "status": "CANCELLED",
            "message": f"Your registration for event ID {event_id} has been cancelled."
        }
    except Exception as exc:
        return {"success": False, "error": getattr(exc, "detail", str(exc))}

def tool_get_user_registrations(db: Session, user_id: int) -> Dict[str, Any]:
    regs = RegistrationService.get_user_registrations(db, user_id)
    return {
        "count": len(regs),
        "registrations": [
            {
                "id": r.id,
                "event_id": r.event_id,
                "event_title": r.event.title if r.event else "N/A",
                "date": r.event.date if r.event else "N/A",
                "time": r.event.time if r.event else "N/A",
                "status": r.status
            }
            for r in regs
        ]
    }
