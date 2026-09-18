import json
import os
import time
from typing import Optional

from dotenv import load_dotenv
from google import genai
from sqlalchemy.orm import Session

from .tools import (
    search_events,
    register_participant,
    cancel_registration
)

from .rag import answer_with_rag
from .models import AgentRun


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not set. "
        "Add it to backend/.env"
    )


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)

AGENT_MODEL = "gemini-2.5-flash"


# =========================================================
# LLM INTENT DETECTION
# =========================================================

def detect_intent(message: str) -> dict:
    """
    Ask Gemini to understand the user's request and
    choose the appropriate action.

    The LLM does NOT execute tools.
    It only returns a structured decision.
    """

    prompt = f"""
You are the intent router for a Smart Event Management System.

Understand the user's request and classify it into exactly
ONE of these intents:

1. SEARCH_EVENTS
   Use when the user wants to find, browse, list, or see events.

2. REGISTER_PARTICIPANT
   Use when the user wants to register/book/reserve a place
   in an event.

3. CANCEL_REGISTRATION
   Use when the user wants to cancel their existing
   registration.

4. RAG_POLICY_SEARCH
   Use when the user asks a question about:
   - event policies
   - cancellation rules
   - registration rules
   - venue rules
   - attendance
   - capacity
   - FAQs
   - deadlines
   - penalties
   - what is allowed
   - what happens under a rule

5. GENERAL_QUERY
   Use when the request does not fit the above categories.

Important distinction:

"Can I cancel my registration?"
→ RAG_POLICY_SEARCH

"Cancel my registration for event 1."
→ CANCEL_REGISTRATION

"Can I register if the event is full?"
→ RAG_POLICY_SEARCH

"Register me for event 1."
→ REGISTER_PARTICIPANT

"Show me available events."
→ SEARCH_EVENTS


You must return ONLY valid JSON.

JSON format:

{{
    "intent": "SEARCH_EVENTS",
    "event_id": null,
    "keyword": null
}}

Rules:

- intent must be exactly one of the five allowed intents.
- event_id must be an integer if an event ID is explicitly
  mentioned; otherwise null.
- keyword should contain a useful event-search keyword if
  the user is searching for a specific type/title.
- For RAG_POLICY_SEARCH, keyword should normally be null.
- Do not invent an event ID.

User request:
{message}
"""

    try:

        response = client.models.generate_content(
            model=AGENT_MODEL,
            contents=prompt
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty intent response."
            )

        raw_text = response.text.strip()

        # Remove markdown code fences if Gemini adds them
        if raw_text.startswith("```"):
            raw_text = raw_text.replace(
                "```json",
                ""
            ).replace(
                "```",
                ""
            ).strip()

        decision = json.loads(raw_text)

        allowed_intents = {
            "SEARCH_EVENTS",
            "REGISTER_PARTICIPANT",
            "CANCEL_REGISTRATION",
            "RAG_POLICY_SEARCH",
            "GENERAL_QUERY"
        }

        intent = decision.get("intent")

        if intent not in allowed_intents:
            raise ValueError(
                f"Invalid intent returned by Gemini: {intent}"
            )

        event_id = decision.get("event_id")
        keyword = decision.get("keyword")

        # Validate event ID
        if event_id is not None:
            try:
                event_id = int(event_id)
            except (TypeError, ValueError):
                event_id = None

        # Normalize keyword
        if keyword is not None:
            keyword = str(keyword).strip()

            if not keyword:
                keyword = None

        return {
            "intent": intent,
            "event_id": event_id,
            "keyword": keyword
        }

    except Exception as error:

        print(
            f"INTENT DETECTION ERROR: {error}"
        )

        # Safe fallback
        return {
            "intent": "GENERAL_QUERY",
            "event_id": None,
            "keyword": None
        }


# =========================================================
# SEARCH EVENTS
# =========================================================

def handle_search_events(
    db: Session,
    keyword: Optional[str]
):

    events = search_events(
        db,
        keyword or ""
    )

    if not events:

        if keyword:
            return (
                f"No events matching '{keyword}' "
                "were found."
            )

        return "No available events were found."

    response = "Matching events:\n"

    response += "\n".join(
        [
            (
                f"- {event['title']} "
                f"(ID: {event['id']}, "
                f"Date: {event['date']}, "
                f"Capacity: {event['capacity']})"
            )
            for event in events
        ]
    )

    return response


# =========================================================
# REGISTER PARTICIPANT
# =========================================================

def handle_registration(
    db: Session,
    user_id: int,
    event_id: Optional[int]
):

    if event_id is None:

        return (
            "Please specify the event ID you want "
            "to register for. For example: "
            "'Register me for event 1.'"
        )

    result = register_participant(
        db,
        user_id,
        event_id
    )

    return result["message"]


# =========================================================
# CANCEL REGISTRATION
# =========================================================

def handle_cancellation(
    db: Session,
    user_id: int,
    event_id: Optional[int]
):

    if event_id is None:

        return (
            "Please specify the event ID whose "
            "registration you want to cancel. "
            "For example: 'Cancel my registration "
            "for event 1.'"
        )

    result = cancel_registration(
        db,
        user_id,
        event_id
    )

    return result["message"]


# =========================================================
# MAIN AGENT WORKFLOW
# =========================================================

def execute_agent_workflow(
    db: Session,
    user_id: int,
    message: str
) -> dict:

    start_time = time.time()

    tools_used = []

    tool_input = ""

    tool_output = ""

    response_text = ""

    intent = "UNKNOWN"


    # =====================================================
    # STEP 1 — ASK GEMINI WHAT THE USER WANTS
    # =====================================================

    decision = detect_intent(
        message
    )

    intent = decision["intent"]

    event_id = decision["event_id"]

    keyword = decision["keyword"]


    # =====================================================
    # STEP 2 — EXECUTE THE SELECTED ACTION
    # =====================================================

    # -----------------------------------------------------
    # RAG
    # -----------------------------------------------------

    if intent == "RAG_POLICY_SEARCH":

        tools_used.append(
            "search_event_policy"
        )

        tool_input = message

        try:

            response_text = answer_with_rag(
                db,
                message,
                top_k=3
            )

            tool_output = response_text

        except Exception as error:

            print(
                f"RAG ERROR: {error}"
            )

            tool_output = str(error)

            response_text = (
                "I couldn't retrieve the relevant "
                "event-management information right now."
            )


    # -----------------------------------------------------
    # SEARCH EVENTS
    # -----------------------------------------------------

    elif intent == "SEARCH_EVENTS":

        tools_used.append(
            "search_events"
        )

        tool_input = (
            f"keyword={keyword}"
        )

        events = search_events(
            db,
            keyword or ""
        )

        tool_output = str(events)

        response_text = handle_search_events(
            db,
            keyword
        )


    # -----------------------------------------------------
    # REGISTER
    # -----------------------------------------------------

    elif intent == "REGISTER_PARTICIPANT":

        tools_used.append(
            "register_participant"
        )

        tool_input = (
            f"event_id={event_id}"
        )

        if event_id is None:

            response_text = (
                "Please specify the event ID you want "
                "to register for. For example: "
                "'Register me for event 1.'"
            )

            tool_output = response_text

        else:

            result = register_participant(
                db,
                user_id,
                event_id
            )

            tool_output = str(result)

            response_text = result["message"]


    # -----------------------------------------------------
    # CANCEL
    # -----------------------------------------------------

    elif intent == "CANCEL_REGISTRATION":

        tools_used.append(
            "cancel_registration"
        )

        tool_input = (
            f"event_id={event_id}"
        )

        if event_id is None:

            response_text = (
                "Please specify the event ID whose "
                "registration you want to cancel."
            )

            tool_output = response_text

        else:

            result = cancel_registration(
                db,
                user_id,
                event_id
            )

            tool_output = str(result)

            response_text = result["message"]


    # -----------------------------------------------------
    # GENERAL QUERY
    # -----------------------------------------------------

    else:

        intent = "GENERAL_QUERY"

        response_text = (
            "I can help you find events, register "
            "for events, cancel registrations, and "
            "answer questions about event policies "
            "and procedures."
        )

        tool_output = response_text


    # =====================================================
    # STEP 3 — CALCULATE LATENCY
    # =====================================================

    latency = round(
        (time.time() - start_time) * 1000,
        2
    )


    # =====================================================
    # STEP 4 — SAVE AGENT RUN
    # =====================================================

    run_log = AgentRun(
        user_id=user_id,
        user_request=message,
        detected_intent=intent,
        tool_selected=",".join(tools_used),
        tool_input=tool_input,
        tool_output=tool_output,
        latency_ms=latency,
        final_response=response_text
    )

    db.add(run_log)

    db.commit()


    # =====================================================
    # STEP 5 — RETURN API RESPONSE
    # =====================================================

    return {
        "response": response_text,
        "intent": intent,
        "tools_used": tools_used,
        "latency_ms": latency
    }