import json
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .models import AgentRun, Event, Registration, ToolCall, User, Venue
from .rag import rag_engine, answer_policy_question
from .tools import (
    cancel_registration,
    create_event_record,
    create_venue_record,
    delete_event_record,
    delete_venue_record,
    find_event_matches,
    find_event_matches_any_status,
    get_event_attendees,
    register_participant,
    search_events,
    search_venues,
)

SYSTEM_PROMPT = """You are a helpful event-management assistant. Respond warmly to greetings and ordinary chitchat.
When a user wants to create an event, gather the event name, date, time, venue ID or venue name, and number of seats conversationally.
Ask for only the missing details. Never invent defaults or call the event-creation tool until every required detail is present and the venue is verified.
If the user asks to create an event but has not yet provided a name, ask: 'What is the name of the event you would like to create?' before asking for any other details. Never reuse a previous or default event name.
If a requested venue is unavailable, ask the user to choose another venue or time.
When a user or admin asks to register for an event but has not specified the exact event name (e.g., 'I want to register myself for this event. Can you help me?'), warmly ask: 'Yes, I can definitely help you register! Could you please tell me the name of the event you would like to join?'"""


def _display_event_title(title: Optional[str]) -> str:
    if not title:
        return "this event"
    cleaned = title.strip()
    if not cleaned:
        return "this event"
    return " ".join(part.capitalize() if part.lower() not in {"ai", "llm"} else part.upper() for part in cleaned.split())


def _extract_event_title(message: str) -> Optional[str]:
    text = message.strip()
    patterns = (
        r"(?i)\b(?:event|workshop|session)\s+(?:called|named|titled)\s+(.+)",
        r"(?i)^(?:create|add|schedule)\s+(?:an?\s+)?(?:event|workshop|session)\s+(.+)",
        r"(?i)\b(?:want to|would like to)\s+(?:create|organize|host)\s+(?:an?\s+)?(?:event|workshop|session)\s+(.+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            title = match.group(1).strip(" .,!\t")
            title = re.split(
                r"(?i)\s+(?:on\s+\d|at\s+\d|at\s+(?:venue|hall)|with\s+\d|for\s+\d)",
                title,
                maxsplit=1,
            )[0].strip(" .,!'\t\"")
            if title:
                return title
    return None


def _extract_delete_event_reference(message: str) -> Optional[str]:
    patterns = (
        r"(?i)\b(?:delete|remove)\s+(?:the\s+)?(?:an?\s+)?(?:event|workshop|session)\s*(?:named|called|titled)?\s*(.+)$",
        r"(?i)\b(?:i\s+want\s+to\s+)?(?:delete|remove)\s+(?:the\s+)?(?:an?\s+)?(?:event|workshop|session)\s*(?:named|called|titled)?\s*(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            reference = match.group(1).strip(" .,!?'\"")
            return reference or None
    return None


def _extract_delete_venue_reference(message: str) -> Optional[str]:
    patterns = (
        r"(?i)\b(?:delete|remove)\s+(?:the\s+)?(?:an?\s+)?(?:venue|hall)\s*(?:named|called|titled)?\s*(.+)$",
        r"(?i)\b(?:i\s+want\s+to\s+)?(?:delete|remove)\s+(?:the\s+)?(?:an?\s+)?(?:venue|hall)\s*(?:named|called|titled)?\s*(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            reference = match.group(1).strip(" .,!?'\"")
            return reference or None
    return None


def _extract_event_date(message: str) -> Optional[str]:
    match = re.search(r"\b(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", message)
    if match:
        value = match.group(1).replace("/", "-")
        formats = ("%Y-%m-%d", "%m-%d-%Y", "%m-%d-%y", "%d-%m-%Y", "%d-%m-%y")
        for date_format in formats:
            try:
                return datetime.strptime(value, date_format).strftime("%Y-%m-%d")
            except ValueError:
                continue
    match = re.search(
        r"(?i)\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:,?\s+\d{4})?",
        message,
    )
    if match:
        value = match.group(0).replace(",", "")
        for date_format in ("%B %d %Y", "%b %d %Y", "%B %d", "%b %d"):
            try:
                parsed = datetime.strptime(value, date_format)
                if "%Y" not in date_format:
                    parsed = parsed.replace(year=datetime.now().year)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


def _extract_event_capacity(message: str, allow_bare_number: bool = False) -> Optional[int]:
    match = re.search(r"\b(\d+)\s+(?:seats?|attendees?|participants?)\b", message, re.IGNORECASE)
    if not match:
        match = re.search(r"\b(?:for|with)\s+(\d+)\b", message, re.IGNORECASE)
    if not match and allow_bare_number:
        match = re.fullmatch(r"\s*(\d+)\s*", message)
    if match:
        capacity = int(match.group(1))
        return capacity if capacity > 0 else None
    return None


def _extract_event_venue_reference(db: Session, message: str) -> Optional[str]:
    venues = db.query(Venue).all()
    for venue in sorted(venues, key=lambda item: len(item.name), reverse=True):
        if re.search(rf"(?i)(?<!\w){re.escape(venue.name)}(?!\w)", message):
            return venue.name

    venue_id_match = re.search(r"(?i)\b(?:venue|hall)\s*#?\s*(\d+)\b", message)
    if venue_id_match:
        return venue_id_match.group(1)

    venue_name_match = re.search(r"(?i)\bat\s+(?:the\s+)?(.+?)\s*[?.!]*$", message)
    if venue_name_match:
        return venue_name_match.group(1).strip(" .,!?'\"") or None
    return None


def _extract_event_time(message: str) -> Optional[str]:
    match = re.search(r"\b(\d{1,2}:\d{2}\s*(?:am|pm)?)\b", message, re.IGNORECASE)
    if not match:
        match = re.search(r"(?i)\bat\s+(\d{1,2})\s*(am|pm)\b", message)
        if match:
            return f"{match.group(1)}:00 {match.group(2).upper()}"
    if match:
        value = re.sub(r"\s+", " ", match.group(1).strip()).upper()
        if value.endswith(("AM", "PM")):
            return value
        hour, minute = value.split(":")
        if int(hour) <= 23 and int(minute) <= 59:
            return f"{int(hour):02d}:{minute}"
    return None


def _extract_venue(db: Session, message: str) -> tuple[Optional[int], Optional[str]]:
    venues = db.query(Venue).all()
    for venue in sorted(venues, key=lambda item: len(item.name), reverse=True):
        if re.search(rf"(?i)(?<!\w){re.escape(venue.name)}(?!\w)", message):
            return venue.id, venue.name

    match = re.search(r"(?i)\b(?:venue|hall)\s*#?\s*(\d+)\b", message)
    if match:
        venue = db.query(Venue).filter(Venue.id == int(match.group(1))).first()
        return (venue.id, venue.name) if venue else (None, f"Venue {match.group(1)}")

    normalized = re.sub(r"(?i)^\s*(?:at|venue|hall)\s+", "", message.strip()).strip(" .,!?")
    if normalized:
        venue = db.query(Venue).filter(Venue.name.ilike(normalized)).first()
        if venue:
            return venue.id, venue.name
    return None, None


def _pending_event_draft(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
    run = (
        db.query(AgentRun)
        .filter(
            AgentRun.user_id == user_id,
            AgentRun.detected_intent.in_(("CREATING_EVENT", "CREATE_EVENT_GATHERING", "CREATE_EVENT_COMPLETED", "CREATE_EVENT_CANCELLED")),
        )
        .order_by(AgentRun.timestamp.desc(), AgentRun.id.desc())
        .first()
    )
    if not run or run.detected_intent not in ("CREATING_EVENT", "CREATE_EVENT_GATHERING") or not run.tool_output:
        return None
    if run.timestamp and run.timestamp < datetime.utcnow() - timedelta(hours=2):
        return None
    try:
        return json.loads(run.tool_output)
    except (TypeError, json.JSONDecodeError):
        return None


def _pending_venue_draft(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
    run = (
        db.query(AgentRun)
        .filter(
            AgentRun.user_id == user_id,
            AgentRun.detected_intent.in_(
                ("CREATE_VENUE_GATHERING", "CREATE_VENUE_COMPLETED", "CREATE_VENUE_CANCELLED")
            ),
        )
        .order_by(AgentRun.timestamp.desc(), AgentRun.id.desc())
        .first()
    )
    if not run or run.detected_intent != "CREATE_VENUE_GATHERING" or not run.tool_output:
        return None
    if run.timestamp and run.timestamp < datetime.utcnow() - timedelta(hours=2):
        return None
    try:
        return json.loads(run.tool_output)
    except (TypeError, json.JSONDecodeError):
        return None


def _pending_registration_draft(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
    run = (
        db.query(AgentRun)
        .filter(
            AgentRun.user_id == user_id,
            AgentRun.detected_intent.in_(
                ("REGISTER_AWAITING_EVENT_NAME", "REGISTER_COMPLETED", "REGISTER_CANCELLED")
            ),
        )
        .order_by(AgentRun.timestamp.desc(), AgentRun.id.desc())
        .first()
    )
    if not run or run.detected_intent != "REGISTER_AWAITING_EVENT_NAME" or not run.tool_output:
        return None
    if run.timestamp and run.timestamp < datetime.utcnow() - timedelta(hours=2):
        return None
    try:
        return json.loads(run.tool_output)
    except (TypeError, json.JSONDecodeError):
        return None


def _pending_cancellation_draft(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
    run = (
        db.query(AgentRun)
        .filter(AgentRun.user_id == user_id)
        .order_by(AgentRun.timestamp.desc(), AgentRun.id.desc())
        .first()
    )
    if (
        not run
        or run.detected_intent not in (
            "REGISTRATION_CANCELLATION",
            "CANCEL_REGISTRATION_AWAITING_EVENT_NAME",
        )
        or not run.tool_output
    ):
        return None
    if run.timestamp and run.timestamp < datetime.utcnow() - timedelta(hours=2):
        return None
    try:
        return json.loads(run.tool_output)
    except (TypeError, json.JSONDecodeError):
        return None


def _most_recent_user_registration_event(
    db: Session,
    user_id: int,
    events: list[Event],
) -> Optional[Event]:
    if not events:
        return None
    return (
        db.query(Event)
        .join(Registration, Registration.event_id == Event.id)
        .filter(
            Registration.user_id == user_id,
            Registration.status == "CONFIRMED",
            Event.id.in_([event.id for event in events]),
        )
        .order_by(Registration.registered_at.desc(), Registration.id.desc())
        .first()
    )


def _extract_registration_reference(message: str, cancelling: bool = False) -> Optional[str]:
    if cancelling:
        patterns = (
            r"(?i)\b(?:cancel|deregister|drop)\s+(?:my\s+)?(?:registration|reservation)(?:\s+(?:for|of))?\s+(?:the\s+)?(?:event\s+)?(.+)$",
            r"(?i)\b(?:cancel|deregister|drop)\s+(?:my\s+)?(?:registration|reservation)\b",
        )
    else:
        patterns = (
            r"(?i)\bregister(?:\s+(?:me|myself))?\s+(?:for|to|in)\s+(?:(?:the|a|an|upcoming|available)\s+)*(?:event\s+)?(.+)$",
            r"(?i)\bsign\s+(?:(?:me|myself)\s+)?up\s+for\s+(?:(?:the|a|an|upcoming|available)\s+)*(?:event\s+)?(.+)$",
            r"(?i)\bbook\s+(?:(?:me|myself)\s+)?(?:for|on|in|seat\s+in|ticket\s+for)\s+(?:the\s+)?(?:event\s+)?(.+)$",
            r"(?i)\b(?:join|attend)\s+(?:the\s+)?(?:event\s+)?(.+)$",
            r"(?i)\bregister\s+(?:for\s+)?(.+)$",
        )
    for pattern in patterns:
        match = re.search(pattern, message)
        if match and match.lastindex:
            reference = match.group(1).strip(" .,!?'\"")
            reference = re.sub(r"(?i)^(?:(?:the|a|an|upcoming|available)\s+)+", "", reference).strip()
            return reference or None
    return None


def _extract_attendee_event_reference(message: str) -> Optional[str]:
    match = re.search(r"(?i)\b(?:for|of|in)\s+(?:the\s+)?(?:event\s+)?(.+)$", message)
    if not match:
        return None
    reference = match.group(1).strip(" .,!?'\"")
    return re.sub(r"(?i)^the\s+", "", reference).strip() or None


def _extract_venue_details(message: str) -> Optional[Dict[str, Any]]:
    match = re.search(r"(?i)\b(?:add|create)\s+(?:(?:a\s+)?(?:new\s+)?)?venue\b\s*(.*)$", message)
    if not match:
        return None

    remainder = match.group(1).strip()
    capacity_match = re.search(
        r"(?i)\b(?:with\s+)?capacity(?:\s+of)?\s*[:=]?\s*(\d+)\b|\b(\d+)\s+(?:seats?|people|persons)\b",
        remainder,
    )
    capacity = int(next(group for group in capacity_match.groups() if group)) if capacity_match else None

    location_match = re.search(r"(?i)\b(?:located\s+at|location|at|in)(?:\s*[:=]\s*|\s+)(.+)$", remainder)
    location = location_match.group(1).strip(" .,!?'\"") if location_match else None
    if location:
        location = re.split(r"(?i)\s+(?:with\s+)?capacity\b", location, maxsplit=1)[0].strip(" .,!'\"")

    cut_positions = [len(remainder)]
    if capacity_match:
        cut_positions.append(capacity_match.start())
    if location_match:
        cut_positions.append(location_match.start())
    name = remainder[:min(cut_positions)].strip(" .,;:'\"")
    name = re.sub(r"(?i)\s+(?:with|capacity|location)$", "", name).strip()
    return {"name": name or None, "capacity": capacity, "location": location or None}


def _handle_venue_conversation(
    db: Session,
    message: str,
    draft: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    state = dict(draft or {})
    state.setdefault("name", None)
    state.setdefault("capacity", None)
    state.setdefault("location", None)

    extracted = _extract_venue_details(message)
    if extracted:
        for field in ("name", "capacity", "location"):
            if extracted[field] is not None:
                state[field] = extracted[field]
    elif draft:
        requested_field = state.get("next_field")
        answer = message.strip().strip(" .,!?'\"")
        if requested_field == "capacity":
            capacity_match = re.search(r"\d+", answer)
            if capacity_match and int(capacity_match.group()) > 0:
                state["capacity"] = int(capacity_match.group())
        elif requested_field in ("name", "location") and answer:
            state[requested_field] = answer

    missing = [field for field in ("name", "capacity", "location") if not state[field]]
    if missing:
        field = missing[0]
        state["next_field"] = field
        prompts = {
            "name": "What should the venue be called?",
            "capacity": "What is its seating capacity?",
            "location": "Where is the venue located?",
        }
        return {
            "response": prompts[field],
            "intent": "CREATE_VENUE_GATHERING",
            "tools_used": [],
            "tool_input": "",
            "tool_output": json.dumps(state),
        }

    result = create_venue_record(db, state["name"], int(state["capacity"]), state["location"])
    if result["status"] == "error":
        return {
            "response": result["message"],
            "intent": "CREATE_VENUE_GATHERING",
            "tools_used": ["create_venue"],
            "tool_input": json.dumps(state),
            "tool_output": str(result),
        }
    venue = result["venue"]
    return {
        "response": f"Venue '{venue.name}' has been added with capacity {venue.capacity} at {venue.location}.",
        "intent": "CREATE_VENUE_COMPLETED",
        "tools_used": ["create_venue"],
        "tool_input": json.dumps(state),
        "tool_output": json.dumps({"venue_id": venue.id}),
    }


def _handle_event_conversation(db: Session, user_id: int, message: str, draft: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    state = dict(draft or {})
    state.setdefault("event_name", None)
    state.setdefault("date", None)
    state.setdefault("time", None)
    state.setdefault("venue_id", None)
    state.setdefault("venue_name", None)
    state.setdefault("seats", None)

    is_fresh_create_request = bool(re.search(
        r"(?i)\b(?:create|add|schedule|organize|host)\b.*\b(?:event|workshop|session)\b|^(?:create|schedule|add)\s+(?:an?\s+)?event\b",
        message,
    ))
    awaiting_event_name = bool(draft is not None and not state["event_name"])
    if is_fresh_create_request:
        for field in ("event_name", "date", "time", "venue_id", "venue_name", "seats"):
            state[field] = None
        state.pop("unresolved_venue", None)

    if awaiting_event_name and not is_fresh_create_request:
        event_name = message.strip().strip(" .,!'\t\"")
        if event_name:
            state["event_name"] = event_name
            return {
                "response": f"Got it! '{event_name}' is the name. Now, please share the date, time, and venue details for this event.",
                "intent": "CREATING_EVENT",
                "tools_used": [],
                "tool_input": "",
                "tool_output": json.dumps(state),
            }

    explicit_title = _extract_event_title(message)
    if explicit_title:
        state["event_name"] = explicit_title
    elif re.search(r"(?i)\b(?:create|add|schedule|organize|host)\b.*\b(?:event|workshop|session)\b|^(?:create|schedule|add)\s+(?:an?\s+)?event\b", message):
        # A fresh event request without an explicit title must not inherit a stale
        # or previous event name from an older draft.
        state["event_name"] = None

    requested_date = _extract_event_date(message)
    if requested_date:
        state["date"] = requested_date
    requested_time = _extract_event_time(message)
    if requested_time:
        state["time"] = requested_time
    requested_capacity = _extract_event_capacity(message, allow_bare_number=bool(draft))
    if requested_capacity is not None:
        state["seats"] = requested_capacity
    venue_id, venue_name = _extract_venue(db, message)
    if venue_id:
        state["venue_id"] = venue_id
        state["venue_name"] = venue_name
        state.pop("unresolved_venue", None)
    elif venue_name:
        state["unresolved_venue"] = venue_name

    if draft and not state["event_name"]:
        answer = message.strip()
        is_generic_create_request = bool(re.search(
            r"(?i)\b(?:create|add|schedule|organize|host)\b.*\b(?:event|workshop|session)\b|^(?:create|schedule|add)\s+(?:an?\s+)?event\b",
            answer,
        ))
        if answer and not is_generic_create_request and not re.search(r"(?i)\b(?:hi|hello|hey|thanks|thank you|how are you)\b", answer):
            if not any((state["date"], state["time"], state["seats"], state["venue_id"])):
                state["event_name"] = answer

    # Never invent a default time when the user did not specify it.
    # If time is missing, force the agent to request it instead of silently falling back.

    # Check remaining missing fields.
    # Time is mandatory; if it is absent, the agent must ask explicitly instead of defaulting.
    missing = [
        label for field, label in (
            ("event_name", "event name"),
            ("date", "date"),
            ("time", "time"),
            ("venue_id", "venue ID or exact venue name"),
            ("seats", "number of seats"),
        ) if not state[field]
    ]

    if missing:
        all_venues = db.query(Venue).all()
        venue_lines = "\n".join(
            f"  - Venue #{venue.id}: {venue.name} ({venue.capacity} seats, {venue.location})"
            for venue in all_venues
        )

        if not state["event_name"]:
            response = (
                "What is the name of the event you would like to create?\n\n"
                "Once you share the name, I can help with the date, time, and venue details."
            )
        else:
            encoded_title = state["event_name"] or "this event"
            title_display = _display_event_title(encoded_title)

            if "time" in missing:
                response = (
                    f"I can help you create {title_display}! Please specify the date, time, venue, and number of seats.\n\n"
                    f"Available Venues:\n{venue_lines}\n\n"
                    f"At what time would you like to schedule this event (e.g., 10:00 AM, 02:00 PM)?\n\n"
                    f"Example: 'Create event {title_display} on 2026-10-25 at 10:00 AM at venue 1 with 50 seats'"
                )
            else:
                response = (
                    f"I can help you create {title_display}! Please specify the date, time, venue, and number of seats.\n\n"
                    f"Available Venues:\n{venue_lines}\n\n"
                    f"Example: 'Create event {title_display} on 2026-10-25 at 10:00 AM at venue 1 with 50 seats'"
                )

        if state.get("unresolved_venue"):
            response = f"Could not find a venue named '{state['unresolved_venue']}'.\n\n" + response

        return {
            "response": response,
            "intent": "CREATING_EVENT",
            "tools_used": [],
            "tool_input": "",
            "tool_output": json.dumps(state),
        }

    venue = db.query(Venue).filter(Venue.id == state["venue_id"]).first()
    if not venue:
        state["venue_id"] = None
        state["venue_name"] = None
        return {
            "response": "I couldn't find that venue. Please provide a valid venue ID or exact venue name.",
            "intent": "CREATING_EVENT",
            "tools_used": [],
            "tool_input": "",
            "tool_output": json.dumps(state),
        }

    if not state.get("time"):
        return {
            "response": "At what time would you like to schedule this event (e.g., 10:00 AM, 02:00 PM)?",
            "intent": "CREATING_EVENT",
            "tools_used": [],
            "tool_input": json.dumps(state),
            "tool_output": json.dumps({"missing": ["time"]}),
        }

    result = create_event_record(
        db=db,
        user_id=user_id,
        title=state["event_name"],
        description=f"Created from chat request: {message}",
        date=state["date"],
        time=state["time"],
        venue_id=venue.id,
        capacity=int(state["seats"]),
    )
    if result["status"] == "error":
        state["time"] = None if "already booked" in result["message"] else state["time"]
        state["seats"] = None if "capacity" in result["message"].lower() else state["seats"]
        return {
            "response": f" {result['message']}",
            "intent": "CREATING_EVENT",
            "tools_used": [],
            "tool_input": "",
            "tool_output": json.dumps(state),
        }

    event = result["event"]
    state["event_id"] = event.id
    return {
        "response": f"Successfully scheduled event '{event.title}' on {event.date} at {event.time} in {venue.name} with capacity for {event.capacity} seats!",
        "intent": "CREATE_EVENT_COMPLETED",
        "tools_used": ["create_event"],
        "tool_input": json.dumps(state),
        "tool_output": json.dumps({"event_id": event.id, "venue": venue.name}),
    }


def execute_agent_workflow(db: Session, user_id: int, message: str) -> dict:
    start_time = time.time()
    lowered = message.lower().strip()
    actor = db.query(User).filter(User.id == user_id).first()
    role = (actor.role if actor else "USER").upper()
    normalized_role = re.sub(r"[^A-Z]", "", role)
    is_admin = normalized_role in {"ADMIN", "ADMISSIONADMIN"}
    is_admission_admin = is_admin
    tools_used: list[str] = []
    response_text = ""
    intent = "GENERAL_QUERY"
    tool_input = ""
    tool_output = ""

    pending_event = _pending_event_draft(db, user_id)
    pending_venue = _pending_venue_draft(db, user_id) if is_admin else None
    pending_reg = _pending_registration_draft(db, user_id)
    pending_cancel = _pending_cancellation_draft(db, user_id)
    is_greeting = bool(re.fullmatch(
        r"(?:hi|hello|hey|hy|hii|heyy|hlo|howdy)(?: there)?[!. ]*|good morning[!. ]*|good afternoon[!. ]*|good evening[!. ]*",
        lowered,
    ))
    is_smalltalk = any(phrase in lowered for phrase in (
        "how are you", "how's it going", "who are you", "what can you do", "what's up", "thank you", "thanks",
    ))
    is_event_request = bool(re.search(
        r"\b(create|add|schedule|organize|host)\b.*\b(event|workshop|session)\b|"
        r"^(?:create|schedule|add)\s+(?:an?\s+)?event\b",
        lowered,
    ))
    is_delete_event_request = bool(re.search(r"\b(?:delete|remove)\b.*\b(?:event|workshop|session)\b", lowered))
    is_delete_venue_request = bool(re.search(r"\b(?:delete|remove)\b.*\b(?:venue|hall)\b", lowered))
    is_venue_creation_request = bool(re.search(r"\b(?:add|create)\s+(?:(?:a\s+)?(?:new\s+)?)?venue\b", lowered))
    is_cancel_draft = bool(re.search(r"\b(cancel|never mind|nevermind|stop)\b", lowered))
    is_cancel_registration = bool(re.search(
        r"\b(?:cancel|deregister|drop)\b.*\b(?:my\s+)?(?:registration|reservation)\b",
        lowered,
    ))
    is_registration_request = not is_cancel_registration and bool(re.search(
        r"\b(register|sign\s+(?:me\s+)?up|book|enroll|reserve|join|attend)\b"
        r"|\bi\s+want\s+to\s+(register|book|join|attend)\b"
        r"|\bhelp\s+me\s+(register|book|sign\s+up)\b",
        lowered,
    ))
    is_attendee_query = bool(re.search(
        r"\b(attendees?|participants?|registrants?|who\s+registered|registered\s+users)\b",
        lowered,
    ))
    is_policy_query = not is_cancel_registration and any(term in lowered for term in (
        "policy", "policies", "rule", "faq", "terms", "deadline", "refund", "cancellation policy",
        "who can create", "who can register", "can admin", "can user", "guideline",
    ))
    mentions_event = bool(re.search(r"\b(events?|workshops?|sessions?)\b", lowered))
    is_event_query = mentions_event and bool(re.search(
        r"\b(available|upcoming|next|show|list|find|search|what|which|all|schedule|completed|past)\b",
        lowered,
    ))
    is_completed_events_query = bool(re.search(r"\b(?:completed|past)\b", lowered))
    is_venue_query = bool(re.search(r"\b(venues?|halls?)\b", lowered)) and bool(re.search(
        r"\b(available|availability|show|list|find|search|what|which|open)\b",
        lowered,
    ))

    if is_cancel_draft and not is_cancel_registration and (
        pending_event or pending_venue or pending_reg or pending_cancel
    ):
        if pending_cancel:
            intent = "CANCEL_REGISTRATION_CANCELLED"
        elif pending_event:
            intent = "CREATE_EVENT_CANCELLED"
        elif pending_venue:
            intent = "CREATE_VENUE_CANCELLED"
        else:
            intent = "REGISTER_CANCELLED"
        response_text = "No problem. I've stopped that request. You can start again whenever you're ready."
        tool_output = "{}"
    elif pending_cancel and not is_cancel_registration and not is_registration_request and not any((
        is_greeting,
        is_policy_query,
        is_smalltalk,
        is_event_query,
        is_venue_query,
        is_event_request,
        is_venue_creation_request,
        is_delete_event_request,
        is_delete_venue_request,
    )):
        event_reference = message.strip().strip(" .,!?'\"")
        matches = find_event_matches_any_status(db, event_reference)
        intent = "REGISTRATION_CANCELLATION"
        tool_output = json.dumps({"awaiting_event_name": True})
        event = (
            matches[0]
            if len(matches) == 1
            else _most_recent_user_registration_event(db, user_id, matches)
            if not is_admin
            else None
        )
        if event:
            tools_used.append("cancel_registration")
            tool_input = f"user_id={user_id}, event_id={event.id}"
            result = cancel_registration(db, user_id, event.id)
            tool_output = str(result)
            if result["status"] == "success":
                intent = "CANCEL_REGISTRATION"
                response_text = (
                    f"Success! Your registration for '{event.title}' has been successfully canceled."
                )
            else:
                intent = "CANCEL_REGISTRATION_FAILED"
                response_text = result["message"]
        elif matches and is_admin:
            tool_output = json.dumps({"awaiting_event_name": True})
            response_text = "I found multiple matching events: " + ", ".join(
                event.title for event in matches
            ) + ". Which event's registration would you like to cancel?"
        elif matches:
            intent = "CANCEL_REGISTRATION_FAILED"
            tool_output = json.dumps({"active_registration_found": False})
            response_text = f"I couldn't find an active registration matching '{event_reference}'."
        else:
            response_text = (
                f"I couldn't find an active event matching '{event_reference}'. "
                "Please provide the event name again."
            )
    elif pending_event and not pending_event.get("event_name") and not is_registration_request and not is_cancel_registration:
        result = _handle_event_conversation(db, user_id, message, pending_event)
        intent = result["intent"]
        tools_used.extend(result["tools_used"])
        tool_input = result["tool_input"]
        tool_output = result["tool_output"]
        response_text = result["response"]
    elif pending_reg and not pending_event and not is_registration_request and not any((
        is_greeting,
        is_policy_query,
        is_smalltalk,
        is_cancel_registration,
        is_event_query,
        is_venue_query,
        is_event_request,
        is_venue_creation_request,
        is_delete_event_request,
        is_delete_venue_request,
    )):
        # Context Capture: The user was asked for the event name in previous turn.
        # Seamlessly pass extracted parameter into flexible search tool.
        event_candidate = message.strip().strip(" .,!?'\"")
        matches = find_event_matches(db, event_candidate)
        exact_matches = [
            event for event in matches
            if event.title.casefold() == event_candidate.casefold()
        ]
        target_event = exact_matches[0] if exact_matches else matches[0] if len(matches) == 1 else None
        if target_event:
            tools_used.append("register_participant")
            tool_input = f"user_id={user_id}, event_id={target_event.id}"
            result = register_participant(db, user_id, target_event.id)
            tool_output = str(result)
            intent = "REGISTER_PARTICIPANT"
            response_text = (
                f"You are successfully registered for '{target_event.title}'! See you on {target_event.date} at {target_event.time}."
                if result["status"] == "success"
                else result["message"]
            )
        elif matches:
            tools_used.append("search_events")
            tool_input = event_candidate
            tool_output = str([{"id": e.id, "title": e.title} for e in matches])
            intent = "REGISTER_AWAITING_EVENT_NAME"
            response_text = "I found multiple matching events:\n" + "\n".join(
                f"- **{e.title}** (ID: {e.id}) on {e.date} at {e.time}" for e in matches
            ) + f"\n\nWhich one would you like to register for? (e.g. 'Register for event {matches[0].id}')"
        else:
            intent = "REGISTER_AWAITING_EVENT_NAME"
            tool_output = json.dumps({"awaiting_event_name": True})
            response_text = f"I couldn't find an event matching '{event_candidate}'. Could you please tell me the name of the event you would like to join?"
    elif is_greeting:
        intent = "GREETING"
        response_text = "Hi! How can I help you? I can look up events and venues, help with registrations, and answer policy questions."
    elif is_smalltalk and not any((is_event_request, is_venue_creation_request, is_registration_request, is_cancel_registration)):
        intent = "SMALLTALK"
        if "how are you" in lowered or "how's it going" in lowered or "what's up" in lowered:
            response_text = "I'm doing well, thanks for asking! What can I help you with today?"
        elif "who are you" in lowered:
            response_text = "I'm your event assistant. I can find events, check venues, manage registrations, and answer policy questions."
        else:
            response_text = "You're welcome! Let me know what you'd like to do with your events."
    elif is_venue_creation_request:
        if not is_admin:
            intent = "PERMISSION_DENIED"
            response_text = "Only administrators can create venues. I can help you find venues or events instead."
        else:
            result = _handle_venue_conversation(db, message, pending_venue)
            intent = result["intent"]
            tools_used.extend(result["tools_used"])
            tool_input = result["tool_input"]
            tool_output = result["tool_output"]
            response_text = result["response"]
    elif is_delete_event_request:
        if not is_admission_admin:
            intent = "PERMISSION_DENIED"
            response_text = "Only Admission Admin can delete events."
        else:
            event_reference = _extract_delete_event_reference(message)
            if not event_reference:
                intent = "DELETE_EVENT_AWAITING_NAME"
                response_text = "Please provide the name of the event you want to delete. Example: 'Delete event [Event Name]'"
            else:
                result = delete_event_record(db, event_reference)
                intent = "DELETE_EVENT" if result["status"] == "success" else "DELETE_EVENT_FAILED"
                response_text = result["message"]
                if result["status"] == "success":
                    tools_used.append("delete_event")
                    tool_input = event_reference
                    tool_output = json.dumps({"event": result["event"].title})
                else:
                    tools_used.append("delete_event")
                    tool_input = event_reference
                    tool_output = json.dumps({"error": result["message"]})
    elif is_delete_venue_request:
        if not is_admission_admin:
            intent = "PERMISSION_DENIED"
            response_text = "Only Admission Admin can delete venues."
        else:
            venue_reference = _extract_delete_venue_reference(message)
            if not venue_reference:
                intent = "DELETE_VENUE_AWAITING_NAME"
                response_text = "Please provide the name of the venue you want to delete. Example: 'Delete venue [Venue Name]'"
            else:
                result = delete_venue_record(db, venue_reference)
                intent = "DELETE_VENUE" if result["status"] == "success" else "DELETE_VENUE_FAILED"
                response_text = result["message"]
                tools_used.append("delete_venue")
                tool_input = venue_reference
                tool_output = json.dumps({"status": result["status"], "message": result["message"]})
    elif is_event_request:
        result = _handle_event_conversation(db, user_id, message, pending_event)
        intent = result["intent"]
        tools_used.extend(result["tools_used"])
        tool_input = result["tool_input"]
        tool_output = result["tool_output"]
        response_text = result["response"]
    elif is_attendee_query:
        if not is_admin:
            intent = "PERMISSION_DENIED"
            response_text = "Attendee details are only available to administrators."
        else:
            event_reference = _extract_attendee_event_reference(message)
            matches = find_event_matches(db, event_reference or "")
            tools_used.append("get_event_attendees")
            tool_input = event_reference or ""
            if len(matches) == 1:
                attendee_result = get_event_attendees(db, matches[0].id)
                tool_output = json.dumps({
                    "event_id": matches[0].id,
                    "count": attendee_result.get("count", 0),
                    "attendees": attendee_result.get("attendees", []),
                })
                intent = "GET_EVENT_ATTENDEES"
                if attendee_result["status"] == "success":
                    attendees = attendee_result["attendees"]
                    names = ", ".join(f"{person['name']} ({person['email']})" for person in attendees)
                    response_text = f"{attendee_result['count']} confirmed attendees for '{matches[0].title}'."
                    if names:
                        response_text += f" Attendees: {names}."
                else:
                    response_text = attendee_result["message"]
            elif matches:
                intent = "GET_EVENT_ATTENDEES"
                tool_output = str([event.id for event in matches])
                response_text = "I found multiple matching events: " + ", ".join(
                    f"{event.title} (ID {event.id})" for event in matches
                ) + ". Which event do you mean?"
            else:
                intent = "GET_EVENT_ATTENDEES"
                tools_used.clear()
                response_text = "Which event's attendees would you like to see? Please provide its title or ID."
    elif is_cancel_registration:
        event_reference = _extract_registration_reference(message, cancelling=True)
        if not event_reference:
            intent = "REGISTRATION_CANCELLATION"
            tool_output = json.dumps({"awaiting_event_name": True})
            response_text = "Please provide the name of the event whose registration you want to cancel."
        else:
            matches = find_event_matches_any_status(db, event_reference)
            intent = "CANCEL_REGISTRATION"
            event = (
                matches[0]
                if len(matches) == 1
                else _most_recent_user_registration_event(db, user_id, matches)
                if not is_admin
                else None
            )
            if event:
                tools_used.append("cancel_registration")
                tool_input = f"user_id={user_id}, event_id={event.id}"
                result = cancel_registration(db, user_id, event.id)
                tool_output = str(result)
                if result["status"] == "success":
                    intent = "CANCEL_REGISTRATION"
                    response_text = (
                        f"Success! Your registration for '{event.title}' has been successfully canceled."
                    )
                else:
                    intent = "CANCEL_REGISTRATION_FAILED"
                    response_text = result["message"]
            elif matches and is_admin:
                intent = "REGISTRATION_CANCELLATION"
                tool_output = json.dumps({"awaiting_event_name": True})
                response_text = "I found multiple matching events: " + ", ".join(
                    f"{event.title} (ID {event.id})" for event in matches
                ) + ". Which registration should I cancel?"
            elif matches:
                intent = "CANCEL_REGISTRATION_FAILED"
                tool_output = json.dumps({"active_registration_found": False})
                response_text = f"I couldn't find an active registration matching '{event_reference}'."
            else:
                intent = "CANCEL_REGISTRATION_FAILED"
                response_text = f"I couldn't find an active event matching '{event_reference}'. Please check the event name and try again."
    elif is_registration_request:
        event_reference = _extract_registration_reference(message)

        # Check if user triggered registration intent without specifying the exact event name
        # Examples: "I want to register myself for this event. Can you help me?", "I want to register", "Help me register", "Book me a seat"
        is_partial = False
        if not event_reference:
            is_partial = True
        else:
            cleaned_ref = re.sub(
                r"(?i)\b(this|that|the|an?|my|upcoming|available|can|you|help|me|myself|for|to|in|join|please)\b",
                "",
                event_reference,
            ).strip(" .,!?'\"")
            if not cleaned_ref or cleaned_ref.lower() in {"event", "events", "slot", "slots"}:
                is_partial = True

        if is_partial:
            intent = "REGISTER_AWAITING_EVENT_NAME"
            tool_output = json.dumps({"awaiting_event_name": True})
            response_text = "Yes, I can definitely help you register! Could you please tell me the name of the event you would like to join?"
        else:
            intent = "REGISTER_PARTICIPANT"
            matches = find_event_matches(db, event_reference or "")
            exact_matches = [
                event for event in matches
                if event.title.casefold() == (event_reference or "").casefold()
            ]
            event = exact_matches[0] if exact_matches else matches[0] if len(matches) == 1 else None
            if event:
                tools_used.append("register_participant")
                tool_input = f"user_id={user_id}, event_id={event.id}"
                result = register_participant(db, user_id, event.id)
                tool_output = str(result)
                response_text = (
                    f"You are successfully registered for '{event.title}'! See you on {event.date} at {event.time}."
                    if result["status"] == "success"
                    else result["message"]
                )
            elif matches:
                tools_used.append("search_events")
                tool_input = event_reference
                tool_output = str([{"id": event.id, "title": event.title} for event in matches])
                response_text = "I found multiple matching events:\n" + "\n".join(
                    f"**{event.title}** (ID {event.id}) on {event.date} at {event.time}" for event in matches
                ) + f"\n\nWhich one would you like to register for? (e.g. 'Register for event {matches[0].id}')"
            else:
                all_scheduled = db.query(Event).filter(Event.status == "SCHEDULED").order_by(Event.date.asc(), Event.time.asc(), Event.id.asc()).all()
                if all_scheduled:
                    evt_list = "\n".join([f"- **{e.title}** (ID: {e.id}) on {e.date} ({e.time})" for e in all_scheduled[:4]])
                    response_text = (
                        f"I couldn't find an event matching '{event_reference}' to register for.\n\n"
                        f"Upcoming Scheduled Events:\n{evt_list}\n\n"
                        f"Tip: Say 'Register for event {all_scheduled[0].id}'."
                    )
                else:
                    response_text = "There are currently no open events to register for."
    elif is_policy_query:
        intent = "RAG_POLICY_SEARCH"
        tools_used.append("search_event_policy")
        tool_input = message
        # Short concise policy answers for common policy queries
        if any(term in lowered for term in ("cancellation policy", "cancel", "refund", "cancellation")):
            response_text = (
                "‹ **Cancellation Policy:** Cancel at least 24 hours before the event start time for a full refund. "
                "Cancellations made within 24 hours of the event are non-refundable."
            )
            tool_output = json.dumps({"answer": response_text, "source": "cancellation_policy"})
        else:
            rag_result = answer_policy_question(message)
            tool_output = json.dumps(rag_result)
            response_text = rag_result["answer"]
    elif is_event_query:
        intent = "SEARCH_EVENTS"
        tools_used.append("search_events")
        if is_completed_events_query:
            current_date = datetime.now().date().isoformat()
            events = (
                db.query(Event)
                .filter(Event.status == "SCHEDULED", Event.date < current_date)
                .order_by(Event.date.asc(), Event.time.asc(), Event.id.asc())
                .all()
            )
            tool_input = f"status=SCHEDULED,date_before={current_date}"
            tool_output = json.dumps([
                {"id": event.id, "title": event.title, "date": event.date, "time": event.time,
                 "venue": event.venue.name if event.venue else None}
                for event in events
            ])
            if events:
                event_lines = "\n".join(
                    f"  **{event.title}**  {event.date} at {event.time} | Venue: {event.venue.name if event.venue else 'N/A'}"
                    for event in events
                )
                response_text = f"Completed Events ({len(events)} total):\n{event_lines}"
            else:
                response_text = "No completed events are currently scheduled."
        else:
            venue_reference = _extract_event_venue_reference(db, message)
            if venue_reference:
                venue = (
                    db.query(Venue).filter(Venue.id == int(venue_reference)).first()
                    if venue_reference.isdigit()
                    else db.query(Venue).filter(Venue.name.ilike(venue_reference)).first()
                )
                tool_input = f"venue={venue_reference}"
                events = (
                    db.query(Event)
                    .filter(Event.status == "SCHEDULED", Event.venue_id == venue.id)
                    .order_by(Event.date.asc(), Event.time.asc(), Event.id.asc())
                    .all()
                    if venue else []
                )
                tool_output = json.dumps([
                    {"id": event.id, "title": event.title, "date": event.date, "time": event.time,
                     "venue": venue.name}
                    for event in events
                ])
                if not venue:
                    response_text = f"I couldn't find a venue matching '{venue_reference}'."
                elif events:
                    event_lines = "\n".join(
                        f"  **{event.title}**  {event.date} at {event.time} | Venue: {venue.name}"
                        for event in events
                    )
                    response_text = f"Upcoming Events at {venue.name} ({len(events)} total):\n{event_lines}"
                else:
                    response_text = f"No scheduled events are currently listed at {venue.name}."
            else:
                stop_words = {
                    "what", "which", "are", "is", "the", "a", "an", "me", "show", "list", "find", "search",
                    "available", "upcoming", "next", "all", "events", "event", "workshops", "workshop", "sessions", "session",
                    "please", "there", "for", "of", "in",
                }
                keyword = " ".join(word for word in re.findall(r"[a-z0-9'-]+", lowered) if word not in stop_words)
                tool_input = f"keyword={keyword}"
                events = search_events(db, keyword if keyword.strip() else "")
                tool_output = json.dumps(events)
                if events:
                    event_lines = "\n".join(
                        f"  **{event['title']}**  {event['date']} at {event['time']} | Venue: {event.get('venue_name') or event.get('venue') or 'N/A'} | Seats: {event['capacity']}"
                        for event in events
                    )
                    response_text = f" Upcoming Events ({len(events)} total):**\n{event_lines}"
                else:
                    response_text = "No upcoming events are currently scheduled."
    elif is_venue_query:
        intent = "SEARCH_VENUES"
        requested_date = _extract_event_date(message)
        requested_time = _extract_event_time(message)
        venues = search_venues(db, requested_date or "", requested_time or "")
        tools_used.append("search_venues")
        tool_input = json.dumps({"date": requested_date, "time": requested_time})
        tool_output = json.dumps([
            {"id": venue.id, "name": venue.name, "capacity": venue.capacity, "location": venue.location}
            for venue in venues
        ])
        if venues:
            if requested_date and requested_time:
                header = f" **Available Venues for {requested_date} at {requested_time} ({len(venues)} found):**"
            else:
                header = f"**All Venues ({len(venues)} total):**"
            venue_lines = "\n".join(
                f"   **{v.name}** Capacity: {v.capacity} seats | Location: {v.location}"
                for v in venues
            )
            response_text = f"{header}\n{venue_lines}"
        else:
            response_text = (
                "No venues are available for that date and time." if requested_date and requested_time
                else "No venues are currently configured. An admin can add venues using 'add a new venue'."
            )
    elif pending_event:
        result = _handle_event_conversation(db, user_id, message, pending_event)
        intent = result["intent"]
        tools_used.extend(result["tools_used"])
        tool_input = result["tool_input"]
        tool_output = result["tool_output"]
        response_text = result["response"]
    elif pending_venue and is_admin:
        result = _handle_venue_conversation(db, message, pending_venue)
        intent = result["intent"]
        tools_used.extend(result["tools_used"])
        tool_input = result["tool_input"]
        tool_output = result["tool_output"]
        response_text = result["response"]
    else:
        intent = "GENERAL_QUERY"
        response_text = "I can search scheduled events and venues, help you register or cancel your own registration, answer policy questions, and assist admins with event, venue, and attendee management."

    latency = round((time.time() - start_time) * 1000, 2)

    run_log = AgentRun(
        user_id=user_id,
        user_request=message,
        detected_intent=intent,
        tool_selected=",".join(tools_used),
        tool_input=tool_input,
        tool_output=tool_output,
        latency_ms=latency,
        final_response=response_text,
    )
    db.add(run_log)
    db.commit()
    db.refresh(run_log)

    for tool_name in tools_used:
        t_call = ToolCall(
            run_id=run_log.id,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            latency_ms=latency,
        )
        db.add(t_call)
    if tools_used:
        db.commit()

    return {
        "response": response_text,
        "intent": intent,
        "tools_used": tools_used,
        "latency_ms": latency,
    }
