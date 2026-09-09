import re
import time
from sqlalchemy.orm import Session
from .tools import search_events, register_participant, cancel_registration
from .rag import rag_engine
from .models import AgentRun

def execute_agent_workflow(db: Session, user_id: int, message: str) -> dict:
    start_time = time.time()
    lowered = message.lower()
    tools_used = []
    response_text = ""
    intent = "UNKNOWN"
    tool_input = ""
    tool_output = ""

    # 1. Registration Execution
    if any(k in lowered for k in ["register", "sign up", "book"]):
        intent = "REGISTER_PARTICIPANT"
        match = re.search(r'\b\d+\b', message)
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

    # 2. Cancellation Execution
    elif any(k in lowered for k in ["cancel my registration", "deregister", "drop"]):
        intent = "CANCEL_REGISTRATION"
        match = re.search(r'\b\d+\b', message)
        if match:
            event_id = int(match.group())
            tools_used.append("cancel_registration")
            res = cancel_registration(db, user_id, event_id)
            tool_output = str(res)
            response_text = res["message"]
        else:
            response_text = "Please specify the ID of the event you wish to cancel."

    # 3. Event Search Execution
    elif any(k in lowered for k in ["find", "search", "list", "show events", "workshop"]):
        intent = "SEARCH_EVENTS"
        tools_used.append("search_events")
        words = [w for w in lowered.split() if w not in ["find", "search", "events", "for", "a", "an", "the", "me"]]
        keyword = words[0] if words else ""
        tool_input = f"keyword={keyword}"
        events = search_events(db, keyword)
        tool_output = str(events)
        if events:
            response_text = "Matching events: " + ", ".join([f"{e['title']} (ID: {e['id']})" for e in events])
        else:
            response_text = "No matching events found."

    # 4. Policy/RAG Routing
    elif any(k in lowered for k in ["policy", "rule", "faq", "terms", "deadline", "how to"]):
        intent = "RAG_POLICY_SEARCH"
        tools_used.append("search_event_policy")
        tool_input = message
        docs = rag_engine.retrieve(message)
        if docs:
            tool_output = docs[0][0]
            response_text = f"Policy Reference: {docs[0][0]}"
        else:
            response_text = "No specific policy document directly matches your query."

    # 5. Default Fallback
    else:
        intent = "GENERAL_QUERY"
        response_text = "I can help you discover events, register or cancel reservations, and retrieve venue policies."

    latency = round((time.time() - start_time) * 1000, 2)

    # Persist agent trace
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

    return {
        "response": response_text,
        "intent": intent,
        "tools_used": tools_used,
        "latency_ms": latency
    }
