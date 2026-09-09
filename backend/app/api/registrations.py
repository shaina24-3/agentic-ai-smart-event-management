from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.registration import RegistrationResponse
from app.services.registration_service import RegistrationService
from app.services.auth_service import get_current_user, require_admin
from app.models.user import User

router = APIRouter(tags=["Registrations"])

@router.post("/events/{event_id}/register", response_model=RegistrationResponse)
def register_for_event(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return RegistrationService.register_participant(db, user_id=current_user.id, event_id=event_id)

@router.delete("/events/{event_id}/register", response_model=RegistrationResponse)
def cancel_registration_for_event(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return RegistrationService.cancel_registration(db, user_id=current_user.id, event_id=event_id)

@router.get("/registrations/me", response_model=List[RegistrationResponse])
def get_my_registrations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return RegistrationService.get_user_registrations(db, user_id=current_user.id)

@router.get("/events/{event_id}/registrations", response_model=List[RegistrationResponse])
def get_event_registrations(event_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return RegistrationService.get_event_registrations(db, event_id=event_id)
