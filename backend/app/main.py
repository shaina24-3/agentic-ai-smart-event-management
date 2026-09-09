from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from .database import engine, Base, get_db
from .models import User, Venue, Event, Registration, AgentRun
from .schemas import (
    UserCreate, UserOut, Token,
    VenueCreate, VenueOut,
    EventCreate, EventOut,
    RegistrationOut,
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
@app.post("/api/auth/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email is already registered")
    user = User(name=payload.name, email=payload.email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/api/auth/login", response_model=Token)
def login(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user

# Venue Endpoints
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
@app.post("/api/events", response_model=EventOut)
def create_event(payload: EventCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    event = Event(**payload.model_dump(), created_by=admin.id)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@app.get("/api/events", response_model=List[EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).filter(Event.status == "SCHEDULED").all()

@app.get("/api/events/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@app.delete("/api/events/{event_id}")
def cancel_event(event_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.status = "CANCELLED"
    db.commit()
    return {"message": "Event successfully cancelled"}

# Registration Endpoints
@app.post("/api/events/{event_id}/register")
def register_to_event(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from .tools import register_participant
    result = register_participant(db, user.id, event_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.delete("/api/events/{event_id}/register")
def cancel_event_registration(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from .tools import cancel_registration
    result = cancel_registration(db, user.id, event_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.get("/api/registrations/me", response_model=List[RegistrationOut])
def get_user_registrations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Registration).filter(Registration.user_id == user.id).all()

# Agent Chat Endpoint
@app.post("/api/chat", response_model=ChatResponse)
def agent_chat(payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return execute_agent_workflow(db, user.id, payload.message)

# Observability Dashboard Logs
@app.get("/api/admin/agent-activity")
def get_agent_logs(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(AgentRun).order_by(AgentRun.timestamp.desc()).limit(100).all()
