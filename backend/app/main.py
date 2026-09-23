from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from typing import List, Optional

from .database import engine, Base, get_db
from .models import User, Venue, Event, Registration, AgentRun
from .models import User, Venue, Event, Registration, AgentRun, ToolCall, AuditLog, AgentSession
from .schemas import (
    UserCreate, UserOut, Token,
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
    if not db.query(User).first():
        admin = User(name="Admin User", email="admin@events.com", password_hash=hash_password("admin123"), role="ADMIN")
        user = User(name="Participant One", email="user@events.com", password_hash=hash_password("user123"), role="USER")
        db.add_all([admin, user])
        db.commit()
        
        venue = Venue(name="Auditorium Alpha", capacity=100, location="Building A, Tech Park")
        db.add(venue)
        db.commit()

        event = Event(title="AI & Agentic Systems Workshop", description="Hands-on LLM agent design", date="2026-10-15", time="10:00 AM", venue_id=venue.id, capacity=50, created_by=admin.id)
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
    token = create_access_token({"sub": user.email, "role": user.role})

    # Audit log
    audit = AuditLog(user_id=user.id, action="USER_LOGIN", resource_type="users", resource_id=user.id, details=f"User {user.email} logged in")
    db.add(audit)
    db.commit()

    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user

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
@app.post("/api/events", response_model=EventOut)
def create_event(payload: EventCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    event = Event(**payload.model_dump(), created_by=admin.id)
    db.add(event)
    db.commit()
    db.refresh(event)

    audit = AuditLog(user_id=admin.id, action="CREATE_EVENT", resource_type="events", resource_id=event.id, details=f"Event {event.title} created")
    db.add(audit)
    db.commit()

    return event

@app.get("/api/events", response_model=List[EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).filter(Event.status == "SCHEDULED").all()
def list_events(keyword: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Event).filter(Event.status == "SCHEDULED")
    if keyword:
        query = query.filter(Event.title.ilike(f"%{keyword}%"))
    return query.all()

@app.get("/api/events/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

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
