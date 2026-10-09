import json
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from app.agent import execute_agent_workflow
from app.main import app
from app.agent import _handle_event_conversation
from app.database import SessionLocal
from app.models import AgentRun, Event, Registration, ToolCall, User, Venue

client = TestClient(app)


def test_event_creation_uses_explicit_capacity_from_final_followup():
    db = SessionLocal()
    venue = Venue(
        name="Capacity Follow-up Regression Venue",
        capacity=50,
        location="Test Location",
    )
    db.add(venue)
    db.commit()
    db.refresh(venue)

    event_title_prefix = "Capacity Follow-up Regression Event"
    try:
        for requested_capacity, event_date in ((40, "2098-05-20"), (50, "2098-05-21")):
            event_title = f"{event_title_prefix} {requested_capacity}"
            result = _handle_event_conversation(
                db,
                user_id=1,
                message=f"with {requested_capacity} seats",
                draft={
                    "event_name": event_title,
                    "date": event_date,
                    "time": "10:00 AM",
                    "venue_id": venue.id,
                    "venue_name": venue.name,
                    "seats": venue.capacity,
                },
            )

            event = db.query(Event).filter(Event.title == event_title).one()
            assert result["intent"] == "CREATE_EVENT_COMPLETED"
            assert result["tools_used"] == ["create_event"]
            assert event.capacity == requested_capacity
            assert f"{requested_capacity} seats" in result["response"]
    finally:
        db.query(Event).filter(Event.title.like(f"{event_title_prefix}%")).delete()
        db.delete(venue)
        db.commit()
        db.close()


def test_event_creation_uses_requested_venue_name_not_stale_or_default_venue():
    db = SessionLocal()
    suffix = datetime.now().strftime("%Y%m%d%H%M%S%f")
    stale_venue = Venue(name=f"Stale Venue {suffix}", capacity=20, location="Test Location")
    requested_venue = Venue(name=f"Requested Venue {suffix}", capacity=50, location="Test Location")
    db.add_all([stale_venue, requested_venue])
    db.commit()
    db.refresh(stale_venue)
    db.refresh(requested_venue)

    event_title = f"Requested Venue Event {suffix}"
    event_date = "2098-06-15"
    conflicting_event = Event(
        title=f"Stale Venue Booking {suffix}",
        date=event_date,
        time="10:00 AM",
        venue_id=stale_venue.id,
        capacity=15,
        created_by=1,
        status="SCHEDULED",
    )
    db.add(conflicting_event)
    db.commit()

    try:
        result = _handle_event_conversation(
            db,
            user_id=1,
            message=(
                f"Create event {event_title} on {event_date} at 10:00 AM "
                f"at {requested_venue.name} with 30 seats"
            ),
            draft={
                "event_name": event_title,
                "date": event_date,
                "time": "10:00 AM",
                "venue_id": stale_venue.id,
                "venue_name": stale_venue.name,
                "seats": 30,
            },
        )

        event = db.query(Event).filter(Event.title == event_title).one()
        assert result["intent"] == "CREATE_EVENT_COMPLETED"
        assert event.venue_id == requested_venue.id
        assert requested_venue.name in result["response"]

        missing_venue_result = _handle_event_conversation(
            db,
            user_id=1,
            message="Continue without naming a venue",
            draft={
                "event_name": f"Missing Venue Event {suffix}",
                "date": event_date,
                "time": "11:00 AM",
                "seats": 30,
            },
        )
        assert missing_venue_result["intent"] == "CREATING_EVENT"
        assert "venue" in missing_venue_result["response"].lower()
    finally:
        db.query(Event).filter(Event.title.like(f"%{suffix}%")).delete(synchronize_session=False)
        db.delete(stale_venue)
        db.delete(requested_venue)
        db.commit()
        db.close()


def test_complete_event_request_creates_immediately_for_user_and_admin():
    db = SessionLocal()
    suffix = datetime.now().strftime("%Y%m%d%H%M%S%f")
    filler_venues = []
    highest_venue = db.query(Venue).order_by(Venue.id.desc()).first()
    while highest_venue is None or highest_venue.id < 4:
        filler = Venue(
            name=f"One Message Filler Venue {suffix} {len(filler_venues)}",
            capacity=60,
            location="Test Location",
        )
        db.add(filler)
        db.commit()
        db.refresh(filler)
        filler_venues.append(filler)
        highest_venue = filler

    venue = Venue(name=f"One Message Venue {suffix}", capacity=60, location="Test Location")
    stale_venue = Venue(name=f"Stale Draft Venue {suffix}", capacity=10, location="Test Location")
    user = User(
        name=f"One Message User {suffix}",
        email=f"one-message-{suffix}@example.com",
        password_hash="unused-test-password",
        role="USER",
    )
    admin = db.query(User).filter(User.email == "admin@events.com").first()
    db.add_all([venue, stale_venue, user])
    db.commit()
    db.refresh(venue)
    db.refresh(stale_venue)
    db.refresh(user)
    assert venue.id > 3
    assert admin is not None

    venue_suggestions = _handle_event_conversation(
        db,
        user.id,
        "Create event Venue Suggestions Check",
        None,
    )
    assert f"Venue #{venue.id}: {venue.name}" in venue_suggestions["response"]

    request_data = []
    try:
        for actor, event_date, event_time, venue_reference in (
            (user, "2098-07-15", "10:00 AM", venue.name),
            (admin, "2098-07-16", "11:00 AM", f"venue {venue.id}"),
        ):
            event_title = f"One Message Event {actor.role} {suffix}"
            message = (
                f"Create event '{event_title}' on {event_date} at {event_time} "
                f"at {venue_reference} with 50 seats"
            )
            request_data.append((actor.id, message, event_title))
            db.add_all([
                AgentRun(
                    user_id=actor.id,
                    user_request=f"Pending registration {suffix}",
                    detected_intent="REGISTER_AWAITING_EVENT_NAME",
                    tool_output=json.dumps({"awaiting_event_name": True}),
                ),
                AgentRun(
                    user_id=actor.id,
                    user_request=f"Pending event draft {suffix}",
                    detected_intent="CREATE_EVENT_GATHERING",
                    tool_output=json.dumps({
                        "event_name": "Stale Draft Event",
                        "date": "2097-01-01",
                        "time": "09:00 AM",
                        "venue_id": stale_venue.id,
                        "venue_name": stale_venue.name,
                        "seats": 10,
                    }),
                ),
            ])
            db.commit()

            result = execute_agent_workflow(db, actor.id, message)
            created = db.query(Event).filter(Event.title == event_title).one()
            assert result["intent"] == "CREATE_EVENT_COMPLETED"
            assert result["tools_used"] == ["create_event"]
            assert created.date == event_date
            assert created.time == event_time
            assert created.venue_id == venue.id
            assert created.capacity == 50
            assert event_title in result["response"]
            assert venue.name in result["response"]
            assert "please specify" not in result["response"].lower()
    finally:
        run_keys = {(user_id, message) for user_id, message, _ in request_data}
        for user_id, message in run_keys:
            run_ids = [
                run.id for run in db.query(AgentRun).filter(
                    AgentRun.user_id == user_id,
                    AgentRun.user_request.in_([message, f"Pending registration {suffix}", f"Pending event draft {suffix}"]),
                ).all()
            ]
            if run_ids:
                db.query(ToolCall).filter(ToolCall.run_id.in_(run_ids)).delete(synchronize_session=False)
                db.query(AgentRun).filter(AgentRun.id.in_(run_ids)).delete(synchronize_session=False)
        db.query(Event).filter(Event.title.like(f"%{suffix}%")).delete(synchronize_session=False)
        db.delete(user)
        db.delete(venue)
        db.delete(stale_venue)
        for filler in filler_venues:
            db.delete(filler)
        db.commit()
        db.close()


def test_event_name_answer_stays_in_creation_flow_for_user_and_admin():
    db = SessionLocal()
    suffix = datetime.now().strftime("%Y%m%d%H%M%S%f")
    user = User(
        name=f"Creation Flow User {suffix}",
        email=f"creation-flow-{suffix}@example.com",
        password_hash="unused-test-password",
        role="USER",
    )
    admin = db.query(User).filter(User.email == "admin@events.com").first()
    db.add(user)
    db.commit()
    db.refresh(user)
    assert admin is not None

    matched_event = Event(
        title="College Briefing",
        date="2098-08-20",
        time="10:00 AM",
        venue_id=db.query(Venue).first().id,
        capacity=30,
        created_by=admin.id,
        status="SCHEDULED",
    )
    db.add(matched_event)
    db.commit()

    requests = []
    try:
        for actor in (user, admin):
            db.add(AgentRun(
                user_id=actor.id,
                user_request=f"Pending registration {suffix}",
                detected_intent="REGISTER_AWAITING_EVENT_NAME",
                tool_output=json.dumps({"awaiting_event_name": True}),
            ))
            db.commit()

            start_message = "I want to create an event"
            requests.append((actor.id, start_message))
            start_result = execute_agent_workflow(db, actor.id, start_message)
            assert start_result["intent"] == "CREATING_EVENT"
            assert "What is the name of the event" in start_result["response"]

            name_message = "college briefing"
            requests.append((actor.id, name_message))
            name_result = execute_agent_workflow(db, actor.id, name_message)
            assert name_result["intent"] == "CREATING_EVENT"
            assert name_result["tools_used"] == []
            assert name_result["response"] == (
                "Got it! 'college briefing' is the name. Now, please share the date, time, and venue details for this event."
            )
            assert db.query(Registration).filter(
                Registration.user_id == actor.id,
                Registration.event_id == matched_event.id,
            ).first() is None
    finally:
        runs = db.query(AgentRun).filter(
            AgentRun.user_id.in_([user.id, admin.id]),
            AgentRun.user_request.in_([message for _, message in requests] + [f"Pending registration {suffix}"]),
        ).all()
        run_ids = [run.id for run in runs]
        if run_ids:
            db.query(ToolCall).filter(ToolCall.run_id.in_(run_ids)).delete(synchronize_session=False)
            db.query(AgentRun).filter(AgentRun.id.in_(run_ids)).delete(synchronize_session=False)
        db.delete(matched_event)
        db.delete(user)
        db.commit()
        db.close()


def test_event_search_filters_completed_dates_and_specific_venues():
    db = SessionLocal()
    suffix = datetime.now().strftime("%Y%m%d%H%M%S%f")
    venue_name = f"Search Regression Venue {suffix}"
    other_venue_name = f"Other Search Regression Venue {suffix}"
    venue = Venue(name=venue_name, capacity=50, location="Test Location")
    other_venue = Venue(name=other_venue_name, capacity=50, location="Other Location")
    db.add_all([venue, other_venue])
    db.commit()
    db.refresh(venue)
    db.refresh(other_venue)

    today = datetime.now().date()
    past_title = f"Past Scheduled Event {suffix}"
    today_title = f"Today Scheduled Event {suffix}"
    cancelled_title = f"Past Cancelled Event {suffix}"
    other_title = f"Other Venue Event {suffix}"
    events = [
        Event(title=past_title, date=(today - timedelta(days=1)).isoformat(), time="09:00 AM", venue_id=venue.id, capacity=20, created_by=1, status="SCHEDULED"),
        Event(title=today_title, date=today.isoformat(), time="10:00 AM", venue_id=venue.id, capacity=20, created_by=1, status="SCHEDULED"),
        Event(title=cancelled_title, date=(today - timedelta(days=2)).isoformat(), time="11:00 AM", venue_id=venue.id, capacity=20, created_by=1, status="CANCELLED"),
        Event(title=other_title, date=(today + timedelta(days=1)).isoformat(), time="12:00 PM", venue_id=other_venue.id, capacity=20, created_by=1, status="SCHEDULED"),
    ]
    db.add_all(events)
    db.commit()

    requests = [
        "What events are already completed?",
        f"What are the upcoming events at venue {venue.id}?",
        f"Upcoming events at {venue_name}",
    ]
    try:
        completed = execute_agent_workflow(db, 1, requests[0])
        completed_output = json.loads(
            db.query(AgentRun).filter(AgentRun.user_request == requests[0]).order_by(AgentRun.id.desc()).first().tool_output
        )
        assert completed["intent"] == "SEARCH_EVENTS"
        assert any(event["title"] == past_title for event in completed_output)
        assert all(event["title"] != today_title for event in completed_output)
        assert all(event["title"] != cancelled_title for event in completed_output)

        for request in requests[1:]:
            result = execute_agent_workflow(db, 1, request)
            run = db.query(AgentRun).filter(AgentRun.user_request == request).order_by(AgentRun.id.desc()).first()
            venue_events = json.loads(run.tool_output)
            assert result["intent"] == "SEARCH_EVENTS"
            assert venue_events
            assert all(event["venue"] == venue_name for event in venue_events)
            assert all(event["title"] != other_title for event in venue_events)
    finally:
        run_ids = [
            run.id for run in db.query(AgentRun).filter(AgentRun.user_request.in_(requests)).all()
        ]
        if run_ids:
            db.query(ToolCall).filter(ToolCall.run_id.in_(run_ids)).delete(synchronize_session=False)
            db.query(AgentRun).filter(AgentRun.id.in_(run_ids)).delete(synchronize_session=False)
        db.query(Event).filter(Event.title.in_([past_title, today_title, cancelled_title, other_title])).delete(synchronize_session=False)
        db.delete(venue)
        db.delete(other_venue)
        db.commit()
        db.close()


def test_agent_chat():
    # Login
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Admin User",
            "email": "admin@events.com",
            "password": "admin123",
            "role": "ADMIN"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Call Agent API with authentication
    response = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": "What events are available?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "response" in data
    assert "intent" in data
    assert "tools_used" in data


def test_agent_event_delete_prompt_requires_name():
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Admin User",
            "email": "admin@events.com",
            "password": "admin123",
            "role": "ADMIN"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "I want to delete an event"}
    )

    assert response.status_code == 200
    assert response.json()["response"] == "Please provide the name of the event you want to delete. Example: 'Delete event [Event Name]'"


def test_agent_venue_delete_prompt_requires_name():
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Admin User",
            "email": "admin@events.com",
            "password": "admin123",
            "role": "ADMIN"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "I want to delete a venue"}
    )

    assert response.status_code == 200
    assert response.json()["response"] == "Please provide the name of the venue you want to delete. Example: 'Delete venue [Venue Name]'"


def test_agent_event_search():
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Admin User",
            "email": "admin@events.com",
            "password": "admin123",
            "role": "ADMIN"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": "Find AI events"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "response" in data
    assert "intent" in data
    assert "tools_used" in data 
def test_agent_policy_question():
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Admin User",
            "email": "admin@events.com",
            "password": "admin123",
            "role": "ADMIN"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": "What is the cancellation policy?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "response" in data
    assert "intent" in data
    assert "tools_used" in data   
def test_agent_rag_policy_integration():
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Admin User",
            "email": "admin@events.com",
            "password": "admin123",
            "role": "ADMIN"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": "What is the cancellation policy?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "RAG_POLICY_SEARCH"
    assert "search_event_policy" in data["tools_used"]
    assert "Cancellation Policy" in data["response"]
def test_agent_register_participant():
    import uuid

    # Create user
    email = f"agent_register_{uuid.uuid4().hex[:8]}@example.com"

    register_response = client.post(
        "/api/auth/register",
        json={
            "name": "Agent Register User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert register_response.status_code == 200

    # Login
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Agent Register User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Get an available event
    events_response = client.get("/api/events")

    assert events_response.status_code == 200
    events = events_response.json()
    assert len(events) > 0

    event_id = events[0]["id"]

    # Ask Agent to register
    response = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": f"Register me for event {event_id}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "REGISTER_PARTICIPANT"
    assert "register_participant" in data["tools_used"]
    assert "successfully registered" in data["response"].lower()


def test_agent_cancel_registration():
    import uuid

    # Create user
    email = f"agent_cancel_{uuid.uuid4().hex[:8]}@example.com"

    register_response = client.post(
        "/api/auth/register",
        json={
            "name": "Agent Cancel User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert register_response.status_code == 200

    # Login
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Agent Cancel User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Get an available event
    events_response = client.get("/api/events")

    assert events_response.status_code == 200
    events = events_response.json()
    assert len(events) > 0

    event_id = events[0]["id"]

    # Register first
    register_chat = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": f"Register me for event {event_id}"
        }
    )

    assert register_chat.status_code == 200

    # Ask Agent to cancel
    cancel_response = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": f"Cancel my registration for event {event_id}"
        }
    )

    assert cancel_response.status_code == 200

    data = cancel_response.json()

    assert data["intent"] == "CANCEL_REGISTRATION"
    assert "cancel_registration" in data["tools_used"]
    assert "successfully canceled" in data["response"]


def test_registration_uses_new_events_from_active_database_for_user_and_admin():
    db = SessionLocal()
    suffix = datetime.now().strftime("%Y%m%d%H%M%S%f")
    venue = Venue(name=f"Registration Sync Venue {suffix}", capacity=50, location="Test Location")
    user = User(
        name=f"Registration Sync User {suffix}",
        email=f"registration-sync-{suffix}@example.com",
        password_hash="unused-test-password",
        role="USER",
    )
    admin = User(
        name=f"Registration Sync Admin {suffix}",
        email=f"registration-sync-admin-{suffix}@example.com",
        password_hash="unused-test-password",
        role="ADMIN",
    )
    db.add_all([venue, user, admin])
    db.commit()
    db.refresh(venue)
    db.refresh(user)
    db.refresh(admin)

    events = []
    actors = (user, admin)
    try:
        for actor in actors:
            event = Event(
                title=f"Hackathon 2026 Registration Sync {actor.role} {suffix}",
                date="2098-10-15",
                time="10:00 AM",
                venue_id=venue.id,
                capacity=50,
                created_by=admin.id,
                status="SCHEDULED",
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            similar_event = Event(
                title=f"Special {event.title}",
                date="2098-09-16",
                time="11:00 AM",
                venue_id=venue.id,
                capacity=50,
                created_by=admin.id,
                status="SCHEDULED",
            )
            db.add(similar_event)
            db.commit()
            db.refresh(similar_event)
            events.append(event)
            events.append(similar_event)

            result = execute_agent_workflow(
                db,
                actor.id,
                f"Register me for event {event.title}",
            )
            registration = db.query(Registration).filter(
                Registration.user_id == actor.id,
                Registration.event_id == event.id,
                Registration.status == "CONFIRMED",
            ).first()
            assert result["intent"] == "REGISTER_PARTICIPANT"
            assert "register_participant" in result["tools_used"]
            assert registration is not None

            followup_title = f"Follow-up Exact Registration {actor.role} {suffix}"
            followup_event = Event(
                title=followup_title,
                date="2098-10-17",
                time="10:00 AM",
                venue_id=venue.id,
                capacity=50,
                created_by=admin.id,
                status="SCHEDULED",
            )
            longer_match = Event(
                title=f"Special {followup_title}",
                date="2098-10-18",
                time="11:00 AM",
                venue_id=venue.id,
                capacity=50,
                created_by=admin.id,
                status="SCHEDULED",
            )
            db.add_all([followup_event, longer_match])
            db.commit()
            db.refresh(followup_event)
            events.extend([followup_event, longer_match])

            prompt_result = execute_agent_workflow(db, actor.id, "I want to register")
            assert prompt_result["intent"] == "REGISTER_AWAITING_EVENT_NAME"
            followup_result = execute_agent_workflow(db, actor.id, followup_title.lower())
            followup_registration = db.query(Registration).filter(
                Registration.user_id == actor.id,
                Registration.event_id == followup_event.id,
                Registration.status == "CONFIRMED",
            ).first()
            assert followup_result["intent"] == "REGISTER_PARTICIPANT"
            assert "register_participant" in followup_result["tools_used"]
            assert followup_registration is not None

        deleted_event = Event(
            title=f"Deleted Registration Sync Event {suffix}",
            date="2098-10-16",
            time="11:00 AM",
            venue_id=venue.id,
            capacity=50,
            created_by=admin.id,
            status="SCHEDULED",
        )
        db.add(deleted_event)
        db.commit()
        deleted_title = deleted_event.title
        db.delete(deleted_event)
        db.commit()

        deleted_result = execute_agent_workflow(
            db,
            user.id,
            f"Register me for event {deleted_title}",
        )
        assert "register_participant" not in deleted_result["tools_used"]
        assert db.query(Registration).filter(
            Registration.user_id == user.id,
            Registration.event_id == deleted_event.id,
        ).first() is None
    finally:
        actor_ids = [actor.id for actor in actors]
        run_ids = [
            run.id for run in db.query(AgentRun).filter(AgentRun.user_id.in_(actor_ids)).all()
        ]
        if run_ids:
            db.query(ToolCall).filter(ToolCall.run_id.in_(run_ids)).delete(synchronize_session=False)
            db.query(AgentRun).filter(AgentRun.id.in_(run_ids)).delete(synchronize_session=False)
        db.query(Registration).filter(Registration.user_id.in_(actor_ids)).delete(synchronize_session=False)
        for event in events:
            db.delete(event)
        db.delete(user)
        db.delete(admin)
        db.delete(venue)
        db.commit()
        db.close()


def test_cancellation_prompt_name_followup_and_direct_command_for_user_and_admin():
    db = SessionLocal()
    suffix = datetime.now().strftime("%Y%m%d%H%M%S%f")
    venue = Venue(name=f"Cancellation Flow Venue {suffix}", capacity=50, location="Test Location")
    actors = (
        User(
            name=f"Cancellation User {suffix}",
            email=f"cancellation-user-{suffix}@example.com",
            password_hash="unused-test-password",
            role="USER",
        ),
        User(
            name=f"Cancellation Admin {suffix}",
            email=f"cancellation-admin-{suffix}@example.com",
            password_hash="unused-test-password",
            role="ADMIN",
        ),
    )
    db.add_all([venue, *actors])
    db.commit()
    db.refresh(venue)
    for actor in actors:
        db.refresh(actor)
    admin_id = actors[1].id

    events = []
    try:
        for actor in actors:
            event = Event(
                title=f"Cancellation Hackathon 2026 {actor.role} {suffix}",
                date="2098-10-17",
                time="10:00 AM",
                venue_id=venue.id,
                capacity=50,
                created_by=admin_id,
                status="SCHEDULED",
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            events.append(event)
            db.add(Registration(user_id=actor.id, event_id=event.id, status="CONFIRMED"))
            db.commit()

            db.add(AgentRun(
                user_id=actor.id,
                user_request=f"Pending event creation draft {suffix}",
                detected_intent="CREATE_EVENT_GATHERING",
                tool_output=json.dumps({
                    "event_name": None,
                    "date": None,
                    "time": None,
                    "venue_id": None,
                    "seats": None,
                }),
            ))
            db.commit()

            prompt_result = execute_agent_workflow(
                db,
                actor.id,
                "I want to cancel my registration",
            )
            assert prompt_result["response"] == (
                "Please provide the name of the event whose registration you want to cancel."
            )
            assert prompt_result["intent"] == "REGISTRATION_CANCELLATION"
            assert prompt_result["tools_used"] == []

            name_result = execute_agent_workflow(db, actor.id, event.title)
            assert name_result["response"] == (
                f"Success! Your registration for '{event.title}' has been successfully canceled."
            )
            assert "cancel_registration" in name_result["tools_used"]
            assert db.query(Registration).filter(
                Registration.user_id == actor.id,
                Registration.event_id == event.id,
                Registration.status == "CONFIRMED",
            ).first() is None

            direct_event = Event(
                title=f"Cancellation Direct Hackathon 2026 {actor.role} {suffix}",
                date="2098-10-18",
                time="11:00 AM",
                venue_id=venue.id,
                capacity=50,
                created_by=admin_id,
                status="SCHEDULED",
            )
            db.add(direct_event)
            db.commit()
            db.refresh(direct_event)
            events.append(direct_event)
            db.add(Registration(user_id=actor.id, event_id=direct_event.id, status="CONFIRMED"))
            db.commit()
            direct_result = execute_agent_workflow(
                db,
                actor.id,
                f"Cancel my registration for event {direct_event.title}",
            )
            assert direct_result["response"] == (
                f"Success! Your registration for '{direct_event.title}' has been successfully canceled."
            )
            assert "cancel_registration" in direct_result["tools_used"]

            duplicate_title = f"Cancellation Duplicate Fest2026 {actor.role} {suffix}"
            older_duplicate = Event(
                title=duplicate_title,
                date="2098-10-19",
                time="10:00 AM",
                venue_id=venue.id,
                capacity=50,
                created_by=admin_id,
                status="SCHEDULED",
            )
            newer_duplicate = Event(
                title=duplicate_title.lower(),
                date="2098-10-20",
                time="11:00 AM",
                venue_id=venue.id,
                capacity=50,
                created_by=admin_id,
                status="SCHEDULED",
            )
            db.add_all([older_duplicate, newer_duplicate])
            db.commit()
            db.refresh(older_duplicate)
            db.refresh(newer_duplicate)
            events.extend([older_duplicate, newer_duplicate])
            db.add_all([
                Registration(
                    user_id=actor.id,
                    event_id=older_duplicate.id,
                    status="CONFIRMED",
                    registered_at=datetime.utcnow() - timedelta(days=1),
                ),
                Registration(
                    user_id=actor.id,
                    event_id=newer_duplicate.id,
                    status="CONFIRMED",
                    registered_at=datetime.utcnow(),
                ),
            ])
            db.commit()

            duplicate_result = execute_agent_workflow(
                db,
                actor.id,
                f"Cancel my registration for event {duplicate_title}",
            )
            if actor.role == "USER":
                assert duplicate_result["response"] == (
                    f"Success! Your registration for '{newer_duplicate.title}' has been successfully canceled."
                )
                assert "cancel_registration" in duplicate_result["tools_used"]
                assert db.query(Registration).filter(
                    Registration.user_id == actor.id,
                    Registration.event_id == newer_duplicate.id,
                    Registration.status == "CONFIRMED",
                ).first() is None
                assert db.query(Registration).filter(
                    Registration.user_id == actor.id,
                    Registration.event_id == older_duplicate.id,
                    Registration.status == "CONFIRMED",
                ).first() is not None
            else:
                assert "Which registration should I cancel?" in duplicate_result["response"]
                assert duplicate_result["tools_used"] == []
    finally:
        db.rollback()
        actor_ids = [actor.id for actor in actors]
        run_ids = [
            run.id for run in db.query(AgentRun).filter(AgentRun.user_id.in_(actor_ids)).all()
        ]
        if run_ids:
            db.query(ToolCall).filter(ToolCall.run_id.in_(run_ids)).delete(synchronize_session=False)
            db.query(AgentRun).filter(AgentRun.id.in_(run_ids)).delete(synchronize_session=False)
        db.query(Registration).filter(Registration.user_id.in_(actor_ids)).delete(synchronize_session=False)
        for event in events:
            db.delete(event)
        for actor in actors:
            db.delete(actor)
        db.delete(venue)
        db.commit()
        db.close()


def test_explicit_registration_overrides_pending_event_drafts_for_user_and_admin():
    db = SessionLocal()
    suffix = datetime.now().strftime("%Y%m%d%H%M%S%f")
    venue = Venue(name=f"Registration Draft Venue {suffix}", capacity=50, location="Test Location")
    user = User(
        name=f"Registration Draft User {suffix}",
        email=f"registration-draft-{suffix}@example.com",
        password_hash="unused-test-password",
        role="USER",
    )
    admin = db.query(User).filter(User.email == "admin@events.com").first()
    db.add_all([venue, user])
    db.commit()
    db.refresh(venue)
    db.refresh(user)
    assert admin is not None

    event = Event(
        title=f"Registration Draft Event {suffix}",
        date="2098-09-15",
        time="10:00 AM",
        venue_id=venue.id,
        capacity=50,
        created_by=admin.id,
        status="SCHEDULED",
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    actors = (user, admin)
    marker = f"Registration Draft {suffix}"
    try:
        for actor in actors:
            db.add_all([
                AgentRun(
                    user_id=actor.id,
                    user_request=f"Pending event draft {marker}",
                    detected_intent="CREATING_EVENT",
                    tool_output=json.dumps({"event_name": None, "date": None, "time": None, "venue_id": None, "seats": None}),
                ),
                AgentRun(
                    user_id=actor.id,
                    user_request=f"Pending registration draft {marker}",
                    detected_intent="REGISTER_AWAITING_EVENT_NAME",
                    tool_output=json.dumps({"awaiting_event_name": True}),
                ),
            ])
            db.commit()

            result = execute_agent_workflow(db, actor.id, f"Register me for the event {event.title}")

            registration = db.query(Registration).filter(
                Registration.user_id == actor.id,
                Registration.event_id == event.id,
                Registration.status == "CONFIRMED",
            ).first()
            assert result["intent"] == "REGISTER_PARTICIPANT"
            assert "register_participant" in result["tools_used"]
            assert registration is not None
            assert "successfully registered" in result["response"].lower()
            assert "date, time" not in result["response"].lower()
    finally:
        actor_ids = [actor.id for actor in actors]
        run_ids = [
            run.id for run in db.query(AgentRun).filter(
                AgentRun.user_id.in_(actor_ids),
                AgentRun.user_request.contains(suffix),
            ).all()
        ]
        if run_ids:
            db.query(ToolCall).filter(ToolCall.run_id.in_(run_ids)).delete(synchronize_session=False)
            db.query(AgentRun).filter(AgentRun.id.in_(run_ids)).delete(synchronize_session=False)
        db.query(Registration).filter(Registration.event_id == event.id).delete(synchronize_session=False)
        db.delete(event)
        db.delete(user)
        db.delete(venue)
        db.commit()
        db.close()