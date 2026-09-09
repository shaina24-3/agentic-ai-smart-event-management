from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.registration import Registration
from app.models.event import Event
from app.schemas.registration import RegistrationResponse
from app.services.event_service import EventService
from app.schemas.user import UserResponse

class RegistrationService:
    @staticmethod
    def _enrich_registration(db: Session, reg: Registration) -> RegistrationResponse:
        event_resp = EventService._enrich_event_response(db, reg.event) if reg.event else None
        user_resp = UserResponse.model_validate(reg.user) if reg.user else None
        return RegistrationResponse(
            id=reg.id,
            user_id=reg.user_id,
            event_id=reg.event_id,
            registered_at=reg.registered_at,
            status=reg.status,
            event=event_resp,
            user=user_resp
        )

    @staticmethod
    def register_participant(db: Session, user_id: int, event_id: int) -> RegistrationResponse:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event or event.status != "ACTIVE":
            raise HTTPException(status_code=400, detail="Event is not active or does not exist.")

        existing_reg = db.query(Registration).filter(
            Registration.user_id == user_id,
            Registration.event_id == event_id
        ).first()

        confirmed_count = db.query(func.count(Registration.id)).filter(
            Registration.event_id == event_id,
            Registration.status == "CONFIRMED"
        ).scalar() or 0

        if existing_reg:
            if existing_reg.status == "CONFIRMED":
                raise HTTPException(status_code=400, detail="You are already registered for this event.")
            if confirmed_count >= event.capacity:
                raise HTTPException(status_code=400, detail="Event has reached full capacity.")
            existing_reg.status = "CONFIRMED"
            db.commit()
            db.refresh(existing_reg)
            return RegistrationService._enrich_registration(db, existing_reg)

        if confirmed_count >= event.capacity:
            raise HTTPException(status_code=400, detail=f"Event has reached maximum capacity of {event.capacity} seats.")

        new_reg = Registration(user_id=user_id, event_id=event_id, status="CONFIRMED")
        db.add(new_reg)
        db.commit()
        db.refresh(new_reg)
        return RegistrationService._enrich_registration(db, new_reg)

    @staticmethod
    def cancel_registration(db: Session, user_id: int, event_id: int) -> RegistrationResponse:
        reg = db.query(Registration).filter(
            Registration.user_id == user_id,
            Registration.event_id == event_id
        ).first()

        if not reg or reg.status == "CANCELLED":
            raise HTTPException(status_code=404, detail="No active registration found for this event.")

        reg.status = "CANCELLED"
        db.commit()
        db.refresh(reg)
        return RegistrationService._enrich_registration(db, reg)

    @staticmethod
    def get_user_registrations(db: Session, user_id: int) -> List[RegistrationResponse]:
        regs = db.query(Registration).filter(Registration.user_id == user_id).all()
        return [RegistrationService._enrich_registration(db, r) for r in regs]

    @staticmethod
    def get_event_registrations(db: Session, event_id: int) -> List[RegistrationResponse]:
        regs = db.query(Registration).filter(Registration.event_id == event_id).all()
        return [RegistrationService._enrich_registration(db, r) for r in regs]
