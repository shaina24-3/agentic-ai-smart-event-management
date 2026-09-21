from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from .database import engine, Base, SessionLocal, get_db
from .models import User, Venue, Event, Registration, AgentRun, AuditLog
from .schemas import (
    UserRegister, UserLogin, UserOut, Token,
    VenueCreate, VenueOut,
    EventCreate, EventOut,
    RegistrationOut,
    ChatRequest, ChatResponse, AuditLogOut
)
from .auth import hash_password, verify_password, create_access_token, get_current_user, require_admin, record_audit
from .agent import run_agent_turn
from .tools import register_participant_tool, cancel_registration_tool

# 1. Initialize FastAPI app first
app = FastAPI(
    title="Agentic AI Smart Event Management System",
    description="Backend API implemented over the 10-table MySQL Event Schema",
    version="2.0.0"
)

# 2. Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Startup Hook to create tables & seed safely
@app.on_event("startup")
def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        admin_exists = db.query(User).filter(User.email == "admin@eventsystem.com").first()
        if not admin_exists:
            admin = User(
                name="Admin User",
                email="admin@eventsystem.com",
                password_hash=hash_password("password123"),
                role="ADMIN"
            )
            db.add(admin)
            db.commit()
        db.close()
    except Exception as e:
        print(f"Database initialization notice: {e}")

# --- Authentication Routes ---
@app.post("/api/auth/register", response_model=UserOut)
def register_user(payload: UserRegister, request: Request, db: Session = Depends(get_db)):
    # Check existing
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    try:
        user = User(
            name=payload.name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=payload.role or "USER"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database user creation error: {str(e)}")

    try:
        record_audit(db, user.id, "USER_REGISTER", "users", user.id, f"Registered user {user.email}", request)
    except Exception as audit_err:
        print(f"Audit log warning (non-fatal): {audit_err}")

    return user
@app.post("/api/auth/login", response_model=Token)
def login_user(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": user.email, "role": user.role})
    record_audit(db, user.id, "USER_LOGIN", "users", user.id, f"Login successful for {user.email}", request)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserOut)
def get_current_user_profile(user: User = Depends(get_current_user)):
    return user

# --- Venue Routes ---
@app.post("/api/venues", response_model=VenueOut)
def create_venue(payload: VenueCreate, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    venue = Venue(**payload.model_dump())
    db.add(venue)
    db.commit()
    db.refresh(venue)
    record_audit(db, admin.id, "CREATE_VENUE", "venues", venue.id, f"Admin created venue: {venue.name}", request)
    return venue

@app.get("/api/venues", response_model=List[VenueOut])
def list_venues(db: Session = Depends(get_db)):
    return db.query(Venue).all()

# --- Event Routes ---
@app.post("/api/events", response_model=EventOut)
def create_event(payload: EventCreate, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    event = Event(**payload.model_dump(), created_by=admin.id)
    db.add(event)
    db.commit()
    db.refresh(event)
    record_audit(db, admin.id, "CREATE_EVENT", "events", event.id, f"Admin created event: {event.title}", request)
    return event

@app.get("/api/events", response_model=List[EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).filter(Event.status == "SCHEDULED").all()

@app.delete("/api/events/{event_id}")
def cancel_event(event_id: int, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.status = "CANCELLED"
    db.commit()
    record_audit(db, admin.id, "CANCEL_EVENT", "events", event.id, f"Admin cancelled event: {event.title}", request)
    return {"message": f"Event {event_id} successfully cancelled"}

# --- Registration Routes ---
@app.post("/api/events/{event_id}/register")
def register_for_event(event_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    res = register_participant_tool(db, user.id, event_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res["output"])
    record_audit(db, user.id, "REGISTER_PARTICIPANT", "registrations", event_id, f"User registered for event ID {event_id}", request)
    return res

@app.delete("/api/events/{event_id}/register")
def cancel_event_registration(event_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    res = cancel_registration_tool(db, user.id, event_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res["output"])
    record_audit(db, user.id, "CANCEL_REGISTRATION", "registrations", event_id, f"User cancelled registration for event ID {event_id}", request)
    return res

@app.get("/api/registrations/me", response_model=List[RegistrationOut])
def get_my_registrations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Registration).filter(Registration.user_id == user.id).all()

# --- Agent Chat Interface ---
@app.post("/api/chat", response_model=ChatResponse)
def chat_with_agent(payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return run_agent_turn(db, user.id, payload.message, payload.session_id)

# --- Observability Logs ---
@app.get("/api/admin/audit-logs", response_model=List[AuditLogOut])
def get_audit_trail(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()

@app.get("/api/admin/agent-activity")
def get_agent_observability(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    runs = db.query(AgentRun).order_by(AgentRun.timestamp.desc()).limit(50).all()
    return [{
        "run_id": r.id,
        "session_id": r.session_id,
        "user_id": r.user_id,
        "request": r.user_request,
        "intent": r.detected_intent,
        "tools": r.tool_selected,
        "latency_ms": r.latency_ms,
        "timestamp": r.timestamp,
        "tool_calls": [
            {
                "tool_name": tc.tool_name,
                "input": tc.tool_input,
                "output": tc.tool_output,
                "latency_ms": tc.latency_ms
            } for tc in r.tool_calls
        ]
    } for r in runs]
