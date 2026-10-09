from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from typing import List
from typing import List, Optional

from .database import engine, Base, get_db
from .models import User, Venue, Event, Registration, AgentRun
from .models import User, Venue, Event, Registration, AgentRun, ToolCall, AuditLog, AgentSession
from .schemas import (
    UserCreate, UserOut, Token,
    PasswordChange, UserRoleUpdate,
    VenueCreate, VenueOut,
    EventCreate, EventOut,
    RegistrationOut,
    VenueCreate, VenueUpdate, VenueOut,
    EventCreate, EventUpdate, EventOut,
    RegistrationOut, AuditLogOut,
    ChatRequest, ChatResponse
)
from .auth import hash_password, verify_password, create_access_token, get_current_user, require_admin
from .agent import execute_agent_workflow
from .tools import get_available_venues

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agentic AI Smart Event Management System",
    description="Backend API with integrated Agentic LangGraph tools and RAG knowledge search.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup default seed data
@app.on_event("startup")
def seed_data():
    db = next(get_db())

    # Create default admin if not already present
    admin = db.query(User).filter(User.email == "admin@events.com").first()

    if not admin:
        admin = User(
            name="Admin User",
            email="admin@events.com",
            password_hash=hash_password("admin123"),
            role="ADMIN"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    # Create default participant if not already present
    user = db.query(User).filter(User.email == "user@events.com").first()

    if not user:
        user = User(
            name="Participant One",
            email="user@events.com",
            password_hash=hash_password("user123"),
            role="USER"
        )
        db.add(user)
        db.commit()

    # Create default venue if not already present
    venue = db.query(Venue).filter(Venue.name == "Auditorium Alpha").first()

    if not venue:
        venue = Venue(
            name="Auditorium Alpha",
            capacity=100,
            location="Building A, Tech Park"
        )
        db.add(venue)
        db.commit()
        db.refresh(venue)

    # Create default event if not already present
    event = db.query(Event).filter(
        Event.title == "AI & Agentic Systems Workshop"
    ).first()

    if not event:
        event = Event(
            title="AI & Agentic Systems Workshop",
            description="Hands-on LLM agent design",
            date="2026-10-15",
            time="10:00 AM",
            venue_id=venue.id,
            capacity=50,
            created_by=admin.id
        )
        db.add(event)
        db.commit()

# Auth Endpoints
# ============================================================================
# 1. Auth Endpoints
# ============================================================================
@app.post("/api/auth/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email is already registered")
    user = User(name=payload.name, email=payload.email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)

    # Audit log
    audit = AuditLog(user_id=user.id, action="USER_REGISTER", resource_type="users", resource_id=user.id, details=f"User {user.email} registered")
    db.add(audit)
    db.commit()

    return user

@app.post("/api/auth/login", response_model=Token)
def login(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.password_hash.startswith(("$2a$", "$2b$", "$2y$")):
        user.password_hash = hash_password(payload.password)
        db.commit()
    token = create_access_token({"sub": user.email, "role": user.role})

    # Audit log
    audit = AuditLog(user_id=user.id, action="USER_LOGIN", resource_type="users", resource_id=user.id, details=f"User {user.email} logged in")
    db.add(audit)
    db.commit()

    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user


@app.put("/api/auth/change-password")
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="New password must be different from the current password.")

    user.password_hash = hash_password(payload.new_password)
    db.add(AuditLog(
        user_id=user.id,
        action="CHANGE_PASSWORD",
        resource_type="users",
        resource_id=user.id,
        details="User changed their password",
    ))
    db.commit()
    return {"message": "Password updated successfully."}

# Venue Endpoints
# ============================================================================
# 2. Venue Endpoints
# ============================================================================
@app.post("/api/venues", response_model=VenueOut)
def create_venue(payload: VenueCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    venue = Venue(**payload.model_dump())
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue

@app.get("/api/venues", response_model=List[VenueOut])
def list_venues(db: Session = Depends(get_db)):
    return db.query(Venue).all()


@app.get("/api/venues/available", response_model=List[VenueOut])
def list_available_venues(
    date: Optional[str] = None,
    time: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if not date or not time:
        return db.query(Venue).all()
    return get_available_venues(db, date, time)

# Event Endpoints
@app.get("/api/venues/{venue_id}", response_model=VenueOut)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue

@app.put("/api/venues/{venue_id}", response_model=VenueOut)
def update_venue(venue_id: int, payload: VenueUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(venue, k, v)
    db.commit()
    db.refresh(venue)
    return venue

# ============================================================================
# 3. Event Endpoints
# ============================================================================
def event_response_payload(event: Event):
    venue_name = event.venue.name if event.venue else f"Venue {event.venue_id}"
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "date": event.date,
        "time": event.time,
        "venue_id": event.venue_id,
        "venue": venue_name,
        "venue_name": venue_name,
        "capacity": event.capacity,
        "status": event.status,
        "created_by": event.created_by,
    }


@app.post("/api/events", response_model=EventOut)
def create_event(payload: EventCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    venue = db.query(Venue).filter(Venue.id == payload.venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    conflict = db.query(Event).filter(
        Event.venue_id == payload.venue_id,
        Event.date == payload.date,
        Event.time == payload.time,
        Event.status == "SCHEDULED",
    ).first()
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"Venue '{venue.name}' is already booked on {payload.date} at {payload.time}. Please choose another time or venue.",
        )

    event = Event(**payload.model_dump(), created_by=admin.id)
    db.add(event)
    db.commit()
    db.refresh(event)

    audit = AuditLog(user_id=admin.id, action="CREATE_EVENT", resource_type="events", resource_id=event.id, details=f"Event {event.title} created")
    db.add(audit)
    db.commit()

    return event_response_payload(event)

@app.get("/api/events", response_model=List[EventOut])
def list_events(
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Event).options(joinedload(Event.venue)).filter(Event.status == "SCHEDULED")

    if keyword:
        query = query.filter(Event.title.ilike(f"%{keyword}%"))

    return [event_response_payload(event) for event in query.all()]

@app.get("/api/events/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).options(joinedload(Event.venue)).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event_response_payload(event)

@app.put("/api/events/{event_id}", response_model=EventOut)
def update_event(event_id: int, payload: EventUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(event, k, v)
    db.commit()
    db.refresh(event)

    audit = AuditLog(user_id=admin.id, action="UPDATE_EVENT", resource_type="events", resource_id=event.id, details=f"Event {event.title} updated")
    db.add(audit)
    db.commit()

    return event

@app.delete("/api/events/{event_id}")
def cancel_event(event_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.status = "CANCELLED"
    db.commit()

    audit = AuditLog(user_id=admin.id, action="CANCEL_EVENT", resource_type="events", resource_id=event.id, details=f"Event {event.title} cancelled")
    db.add(audit)
    db.commit()

    return {"message": "Event successfully cancelled"}

# Registration Endpoints
# ============================================================================
# 4. Registration Endpoints
# ============================================================================
@app.post("/api/events/{event_id}/register")
def register_to_event(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from .tools import register_participant
    result = register_participant(db, user.id, event_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    audit = AuditLog(user_id=user.id, action="REGISTER_EVENT", resource_type="registrations", resource_id=event_id, details=f"User registered for event ID {event_id}")
    db.add(audit)
    db.commit()

    return result

@app.delete("/api/events/{event_id}/register")
def cancel_event_registration(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from .tools import cancel_registration
    result = cancel_registration(db, user.id, event_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    audit = AuditLog(user_id=user.id, action="CANCEL_REGISTRATION", resource_type="registrations", resource_id=event_id, details=f"User cancelled registration for event ID {event_id}")
    db.add(audit)
    db.commit()

    return result

@app.get("/api/events/{event_id}/registrations", response_model=List[RegistrationOut])
def get_event_registrations(event_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(Registration).filter(Registration.event_id == event_id).all()

@app.get("/api/registrations/me", response_model=List[RegistrationOut])
def get_user_registrations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Registration).filter(Registration.user_id == user.id).all()


@app.get("/api/user/registrations")
def get_current_user_registration_records(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    registrations = (
        db.query(Registration)
        .join(Event, Registration.event_id == Event.id)
        .filter(Registration.user_id == user.id)
        .order_by(Registration.registered_at.desc(), Registration.id.desc())
        .all()
    )
    return [
        {
            "id": registration.id,
            "event_id": registration.event_id,
            "event_title": registration.event.title,
            "registration_date": registration.registered_at.isoformat() if registration.registered_at else None,
            "status": registration.status,
        }
        for registration in registrations
    ]

# Agent Chat Endpoint
# ============================================================================
# 5. Agent Chat Endpoint
# ============================================================================
@app.post("/api/chat", response_model=ChatResponse)
def agent_chat(payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute_agent_workflow(db, user.id, payload.message)

# Observability Dashboard Logs
# ============================================================================
# 6. Observability & Audit Logs
# ============================================================================
@app.get("/api/admin/agent-activity")
def get_agent_logs(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(AgentRun).order_by(AgentRun.timestamp.desc()).limit(100).all()

@app.get("/api/admin/audit-logs", response_model=List[AuditLogOut])
def get_audit_logs(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()

# Admin User Management
@app.get("/api/admin/users")
def get_all_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = db.query(User).all()
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role, "created_at": str(u.created_at)} for u in users]


@app.put("/api/admin/users/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")
    if target_user.id == admin.id and payload.role != admin.role:
        raise HTTPException(status_code=400, detail="You cannot change your own administrator role.")
    if target_user.role == payload.role:
        return {"id": target_user.id, "name": target_user.name, "email": target_user.email, "role": target_user.role}

    previous_role = target_user.role
    target_user.role = payload.role
    db.add(AuditLog(
        user_id=admin.id,
        action="UPDATE_USER_ROLE",
        resource_type="users",
        resource_id=target_user.id,
        details=f"Role changed from {previous_role} to {payload.role}",
    ))
    db.commit()
    return {"id": target_user.id, "name": target_user.name, "email": target_user.email, "role": target_user.role}


@app.get("/api/admin/registrations")
def get_all_registrations(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    registrations = (
        db.query(Registration)
        .options(joinedload(Registration.user), joinedload(Registration.event))
        .order_by(Registration.registered_at.desc(), Registration.id.desc())
        .all()
    )
    return [
        {
            "id": registration.id,
            "user_email": registration.user.email,
            "event_title": registration.event.title,
            "registration_date": registration.registered_at.isoformat() if registration.registered_at else None,
            "status": registration.status,
        }
        for registration in registrations
    ]


def update_admin_registration_status(
    registration_id: int,
    target_status: str,
    db: Session,
    admin: User,
):
    registration = (
        db.query(Registration)
        .filter(Registration.id == registration_id)
        .with_for_update()
        .first()
    )
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    if registration.status == target_status:
        confirmed_count = db.query(Registration).filter(
            Registration.event_id == registration.event_id,
            Registration.status == "CONFIRMED",
        ).count()
        return {
            "id": registration.id,
            "user_email": registration.user.email,
            "event_title": registration.event.title,
            "registration_date": registration.registered_at.isoformat() if registration.registered_at else None,
            "status": registration.status,
            "available_seats": max(registration.event.capacity - confirmed_count, 0),
        }

    if target_status == "CONFIRMED":
        confirmed_count = db.query(Registration).filter(
            Registration.event_id == registration.event_id,
            Registration.status == "CONFIRMED",
        ).count()
        if confirmed_count >= registration.event.capacity:
            raise HTTPException(status_code=409, detail="The event has no available seats")
        action = "RESTORE_REGISTRATION"
    else:
        action = "CANCEL_REGISTRATION"

    previous_status = registration.status
    registration.status = target_status
    db.add(AuditLog(
        user_id=admin.id,
        action=action,
        resource_type="registrations",
        resource_id=registration.id,
        details=f"Registration status changed from {previous_status} to {target_status}",
    ))
    db.commit()

    confirmed_count = db.query(Registration).filter(
        Registration.event_id == registration.event_id,
        Registration.status == "CONFIRMED",
    ).count()
    return {
        "id": registration.id,
        "user_email": registration.user.email,
        "event_title": registration.event.title,
        "registration_date": registration.registered_at.isoformat() if registration.registered_at else None,
        "status": registration.status,
        "available_seats": max(registration.event.capacity - confirmed_count, 0),
    }


@app.put("/api/admin/registrations/{registration_id}/cancel")
def cancel_admin_registration(
    registration_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return update_admin_registration_status(registration_id, "CANCELLED", db, admin)


@app.put("/api/admin/registrations/{registration_id}/restore")
def restore_admin_registration(
    registration_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return update_admin_registration_status(registration_id, "CONFIRMED", db, admin)

@app.delete("/api/admin/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account.")
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")
    user_name = target_user.name
    db.delete(target_user)
    db.commit()

    audit = AuditLog(user_id=admin.id, action="DELETE_USER", resource_type="users", resource_id=user_id, details=f"Admin deleted user {user_name}")
    db.add(audit)
    db.commit()

    return {"message": f"User '{user_name}' successfully removed."}

# Dashboard Global Statistics (Matches Reference Design)
@app.get("/api/admin/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_events = db.query(Event).filter(Event.status == "SCHEDULED").count()
    total_attendees = db.query(Registration).filter(Registration.status == "CONFIRMED").count()
    total_venues = db.query(Venue).count()
    agent_queries = db.query(AgentRun).count()
    total_users = db.query(User).count()

    return {
        "total_events": total_events,
        "total_attendees": total_attendees,
        "total_venues": total_venues,
        "agent_queries": agent_queries,
        "total_users": total_users
    }

