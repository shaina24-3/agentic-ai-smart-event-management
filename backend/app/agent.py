import json
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .models import AgentRun, Event, ToolCall, User, Venue
from .rag import rag_engine
from .tools import cancel_registration, register_participant, search_events, get_available_venues, is_venue_available

SYSTEM_PROMPT = """You are a helpful event-management assistant. Respond warmly to greetings and ordinary chitchat.
When a user wants to create an event, gather the event name, date, time, venue ID or venue name, and number of seats conversationally.
Ask for only the missing details. Never invent defaults or call the event-creation tool until every required detail is present and the venue is verified.
If a requested venue is unavailable, ask the user to choose another venue or time."""


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
            )[0].strip(" .,!\t")
            if title:
                return title
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
            AgentRun.detected_intent.in_(("CREATE_EVENT_GATHERING", "CREATE_EVENT_COMPLETED", "CREATE_EVENT_CANCELLED")),
        )
        .order_by(AgentRun.timestamp.desc(), AgentRun.id.desc())
        .first()
    )
    if not run or run.detected_intent != "CREATE_EVENT_GATHERING" or not run.tool_output:
        return None
    if run.timestamp and run.timestamp < datetime.utcnow() - timedelta(hours=2):
        return None
    try:
        return json.loads(run.tool_output)
    except (TypeError, json.JSONDecodeError):
        return None


def _handle_event_conversation(db: Session, user_id: int, message: str, draft: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    state = dict(draft or {})
    state.setdefault("event_name", None)
    state.setdefault("date", None)
    state.setdefault("time", None)
    state.setdefault("venue_id", None)
    state.setdefault("venue_name", None)
    state.setdefault("seats", None)

    if not state["event_name"]:
        state["event_name"] = _extract_event_title(message)
    if not state["date"]:
        state["date"] = _extract_event_date(message)
    if not state["time"]:
        state["time"] = _extract_event_time(message)
    if not state["seats"]:
        state["seats"] = _extract_event_capacity(message, allow_bare_number=bool(draft))
    if not state["venue_id"]:
        venue_id, venue_name = _extract_venue(db, message)
        if venue_id:
            state["venue_id"] = venue_id
            state["venue_name"] = venue_name
            state.pop("unresolved_venue", None)
        elif venue_name:
            state["unresolved_venue"] = venue_name

    if draft and not state["event_name"]:
        answer = message.strip()
        if answer and not re.search(r"(?i)\b(?:hi|hello|hey|thanks|thank you|how are you)\b", answer):
            if not any((state["date"], state["time"], state["seats"], state["venue_id"])):
                state["event_name"] = answer

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
        labels = {
            "event name": "the event name",
            "date": "the date",
            "time": "the time",
            "venue ID or exact venue name": "a venue ID or exact venue name",
            "number of seats": "the number of seats",
        }
        response = "Sure, I can help you create that event. Could you share " + ", ".join(labels[field] for field in missing) + "?"
        if state.get("unresolved_venue"):
            response = f"I couldn't find a venue named '{state['unresolved_venue']}'. Please provide a venue ID or an exact venue name. " + response
        return {
            "response": response,
            "intent": "CREATE_EVENT_GATHERING",
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
            "intent": "CREATE_EVENT_GATHERING",
            "tools_used": [],
            "tool_input": "",
            "tool_output": json.dumps(state),
        }

    if not is_venue_available(db, venue.id, state["date"], state["time"]):
        conflict_time = state["time"]
        state["time"] = None
        return {
            "response": f"{venue.name} is already booked on {state['date']} at {conflict_time}. What other time would work?",
            "intent": "CREATE_EVENT_GATHERING",
            "tools_used": [],
            "tool_input": "",
            "tool_output": json.dumps(state),
        }

    event = Event(
        title=state["event_name"],
        description=f"Created from chat request: {message}",
        date=state["date"],
        time=state["time"],
        venue_id=venue.id,
        capacity=state["seats"],
        created_by=user_id,
        status="SCHEDULED",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    state["event_id"] = event.id
    return {
        "response": f"Your event '{event.title}' is booked for {event.date} at {event.time} in {venue.name} for {event.capacity} seats.",
        "intent": "CREATE_EVENT_COMPLETED",
        "tools_used": ["create_event"],
        "tool_input": json.dumps(state),
        "tool_output": json.dumps({"event_id": event.id, "venue": venue.name}),
    }


def execute_agent_workflow(db: Session, user_id: int, message: str) -> dict:
    start_time = time.time()
    lowered = message.lower().strip()
    tools_used: list[str] = []
    response_text = ""
    intent = "UNKNOWN"
    tool_input = ""
    tool_output = ""

    pending_draft = _pending_event_draft(db, user_id)
    is_greeting = bool(re.fullmatch(r"(?:hi|hello|hey)(?: there)?[!. ]*|good morning[!. ]*|good afternoon[!. ]*|good evening[!. ]*", lowered))
    is_smalltalk = any(phrase in lowered for phrase in (
        "how are you", "how's it going", "who are you", "what can you do", "what's up", "thank you", "thanks",
    ))
    is_event_request = bool(re.search(
        r"\b(create|add|schedule|organize|host)\b.*\b(event|workshop|session)\b|"
        r"\b(?:want|would like|help me)\b.*\b(?:create|organize|host|book)\b.*\b(?:event|slot|venue)?\b|"
        r"\bhelp me book a slot\b",
        lowered,
    ))
    is_cancel_draft = bool(re.search(r"\b(cancel|never mind|nevermind|stop)\b", lowered))

    if is_cancel_draft and pending_draft:
        intent = "CREATE_EVENT_CANCELLED"
        response_text = "No problem. I've stopped creating that event. You can start again whenever you're ready."
        tool_output = "{}"
    elif is_greeting:
        intent = "GREETING"
        response_text = "Hi! How can I help with your events today? I can find events, check venues, help create an event, or answer policy questions."
    elif is_smalltalk and not is_event_request:
        intent = "SMALLTALK"
        if "how are you" in lowered or "how's it going" in lowered or "what's up" in lowered:
            response_text = "I'm doing well, thanks for asking! What can I help you with today?"
        elif "who are you" in lowered:
            response_text = "I'm your event assistant. I can help you find events, check venues, create an event, and answer event-policy questions."
        else:
            response_text = "You're welcome! Let me know what you'd like to do with your events."
    elif is_event_request or pending_draft:
        intent = "CREATE_EVENT_GATHERING"
        result = _handle_event_conversation(db, user_id, message, pending_draft if not is_event_request else pending_draft)
        intent = result["intent"]
        tools_used.extend(result["tools_used"])
        tool_input = result["tool_input"]
        tool_output = result["tool_output"]
        response_text = result["response"]

    elif any(k in lowered for k in ["upcoming events", "upcoming event", "next events", "future events", "list events", "show events", "what events are available", "events available"]):
        intent = "SEARCH_EVENTS"
        tools_used.append("search_events")
        tool_input = "upcoming"
        events = search_events(db)
        tool_output = str(events)
        if events:
            response_text = "Upcoming events: " + ", ".join([f"{e['title']} (ID: {e['id']}, {e['date']})" for e in events])
        else:
            response_text = "No upcoming events are currently scheduled."

    elif any(k in lowered for k in ["register", "sign up", "book"]):
        intent = "REGISTER_PARTICIPANT"
        match = re.search(r"\b\d+\b", message)
        if match:
            event_id = int(match.group())
            tools_used.append("register_participant")
            tool_input = f"event_id={event_id}"
            res = register_participant(db, user_id, event_id)
            tool_output = str(res)
            response_text = res["message"]
        else:
            intent = "SEARCH_THEN_REGISTER"
            tools_used.append("search_events")
            events = search_events(db)
            tool_output = str(events)
            if events:
                target = events[0]
                tools_used.append("register_participant")
                reg_res = register_participant(db, user_id, target["id"])
                response_text = f"Found event '{target['title']}' (ID: {target['id']}). Result: {reg_res['message']}"
            else:
                response_text = "No open events found to register for."

    elif any(k in lowered for k in ["cancel my registration", "deregister", "drop", "cancel registration"]):
        intent = "CANCEL_REGISTRATION"
        match = re.search(r"\b\d+\b", message)
        if match:
            event_id = int(match.group())
            tools_used.append("cancel_registration")
            res = cancel_registration(db, user_id, event_id)
            tool_output = str(res)
            response_text = res["message"]
        else:
            response_text = "Please specify the ID of the event you wish to cancel."

    elif any(k in lowered for k in ["venues", "available venue", "capacity", "venue"]):
        intent = "SEARCH_VENUES"
        tools_used.append("search_venues")
        date_match = re.search(r"(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", message)
        time_match = re.search(r"(\d{1,2}:\d{2}\s*(?:am|pm)?)", message, re.IGNORECASE)
        if date_match and time_match:
            requested_date = date_match.group(1).replace("/", "-")
            requested_time = time_match.group(1).strip()
            venues = get_available_venues(db, requested_date, requested_time)
            response_text = f"Available venues for {requested_date} at {requested_time}: " + ", ".join([f"{v.name} (ID: {v.id}, Capacity: {v.capacity})" for v in venues]) if venues else "No venues are available for that slot."
        else:
            venues = db.query(Venue).all()
            if venues:
                response_text = "Available venues: " + ", ".join([f"{v.name} (ID: {v.id}, Capacity: {v.capacity})" for v in venues])
            else:
                response_text = "No venues are currently configured."
        tool_output = str(venues)

    elif any(k in lowered for k in ["find", "search", "list", "show events", "workshop", "what are the events", "what events"]):
        intent = "SEARCH_EVENTS"
        tools_used.append("search_events")
        words = [w for w in lowered.split() if w not in ["find", "search", "events", "event", "for", "a", "an", "the", "me", "what", "are", "show", "list"]]
        keyword = words[0] if words else ""
        tool_input = f"keyword={keyword}"
        events = search_events(db, keyword)
        tool_output = str(events)
        if events:
            response_text = "Matching events: " + ", ".join([f"{e['title']} (ID: {e['id']})" for e in events])
        else:
            response_text = "No matching events found."

    elif any(k in lowered for k in ["policy", "rule", "faq", "terms", "deadline", "refund", "cancellation", "capacity rule", "how to"]):
        intent = "RAG_POLICY_SEARCH"
        tools_used.append("search_event_policy")
        tool_input = message
        docs = rag_engine.retrieve(message)
        if docs:
            tool_output = docs[0][0]
            response_text = f"Policy Reference: {docs[0][0]}"
        else:
            response_text = "No specific policy document directly matches your query."

    else:
        intent = "GENERAL_QUERY"
        response_text = "I can help you discover events, register or cancel reservations, create event schedules, or retrieve venue policies."

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

