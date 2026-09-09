from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.user import User
from app.models.venue import Venue
from app.models.event import Event
from app.core.security import get_password_hash
import app.models

from app.api.auth import router as auth_router
from app.api.venues import router as venues_router
from app.api.events import router as events_router
from app.api.registrations import router as registrations_router
from app.api.chat import router as chat_router
from app.api.observability import router as observability_router

def seed_initial_data(db_session=None):
    close_after = False
    if db_session is None:
        db = SessionLocal()
        close_after = True
    else:
        db = db_session
    try:
        admin = db.query(User).filter(User.email == "admin@eventagent.io").first()
        if not admin:
            logger.info("Seeding initial database...")
            admin_user = User(name="System Administrator", email="admin@eventagent.io", password_hash=get_password_hash("admin123"), role="ADMIN")
            standard_user = User(name="Attendee User", email="user@eventagent.io", password_hash=get_password_hash("user123"), role="USER")
            db.add_all([admin_user, standard_user])
            db.commit()

            auditorium = Venue(name="Auditorium A", capacity=250, location="Building 1, Main Campus")
            conf_room = Venue(name="Conference Room B", capacity=50, location="Building 2, 3rd Floor")
            lab = Venue(name="Innovation Lab 1", capacity=35, location="Tech Center, Ground Floor")
            db.add_all([auditorium, conf_room, lab])
            db.commit()

            ev1 = Event(title="Generative AI & Agentic Workflows Hands-on Workshop", description="Building autonomous LangGraph agents and RAG pipelines.", date="2026-09-12", time="10:00", venue_id=auditorium.id, capacity=100, status="ACTIVE", created_by=admin_user.id)
            ev2 = Event(title="Cloud Native Microservices Architecture Summit", description="Event-driven architectures and Kubernetes deployments.", date="2026-09-15", time="14:00", venue_id=conf_room.id, capacity=40, status="ACTIVE", created_by=admin_user.id)
            ev3 = Event(title="Enterprise DevOps Bootcamp", description="Continuous deployment and container orchestration.", date="2026-09-20", time="09:30", venue_id=lab.id, capacity=25, status="ACTIVE", created_by=admin_user.id)
            db.add_all([ev1, ev2, ev3])
            db.commit()
    finally:
        if close_after:
            db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_initial_data()
    yield

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(events_router, prefix=settings.API_V1_STR)
app.include_router(venues_router, prefix=settings.API_V1_STR)
app.include_router(registrations_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(observability_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}
