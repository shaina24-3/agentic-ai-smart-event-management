import re
from app.agent.state import AgentState
from app.tools.event_tools import tool_search_events
from app.tools.venue_tools import tool_check_venue_availability
from app.tools.registration_tools import (
    tool_register_participant,
    tool_cancel_registration,
    tool_get_user_registrations
)
from app.tools.rag_tools import tool_search_event_policy

def router_node(state: AgentState) -> AgentState:
    text = state.user_prompt.lower()
    
    if ("find" in text or "search" in text or "workshop" in text or "event" in text) and \
       ("register" in text or "sign me up" in text or "book" in text):
        state.intent = "MULTI_STEP_SEARCH_AND_REGISTER"
    elif "cancel" in text and ("registration" in text or "ticket" in text or "event" in text or "seat" in text):
        state.intent = "CANCEL_REGISTRATION"
    elif "my registration" in text or "registered events" in text:
        state.intent = "VIEW_MY_REGISTRATIONS"
    elif "register" in text or "sign up" in text or "book" in text:
        state.intent = "REGISTER_EVENT"
    elif "venue" in text or "available" in text or "auditorium" in text or "conference room" in text:
        state.intent = "CHECK_VENUE"
    elif "policy" in text or "refund" in text or "rule" in text or "faq" in text or "guideline" in text or "how do i" in text:
        state.intent = "POLICY_RAG"
    elif "event" in text or "find" in text or "search" in text or "what" in text or "list" in text:
        state.intent = "SEARCH_EVENT"
    else:
        state.intent = "GENERAL_CHAT"
        
    return state

def tool_execution_node(state: AgentState) -> AgentState:
    db = state.db_session
    text = state.user_prompt
    user_id = state.user_id or 1

    if state.intent == "MULTI_STEP_SEARCH_AND_REGISTER":
        query = "AI" if "ai" in text.lower() else None
        state.tool_calls.append({"tool": "search_events", "input": {"query": query}})
        search_res = tool_search_events(db, query=query, available_only=True)
        state.tool_results.append({"tool": "search_events", "result": search_res})
        
        events = search_res.get("events", [])
        if events:
            selected_event = events[0]
            state.tool_calls.append({"tool": "register_participant", "input": {"event_id": selected_event["id"], "user_id": user_id}})
            reg_res = tool_register_participant(db, user_id=user_id, event_id=selected_event["id"])
            state.tool_results.append({"tool": "register_participant", "result": reg_res})
        else:
            state.tool_results.append({"tool": "register_participant", "result": {"success": False, "error": "No matching available events found to register."}})

    elif state.intent == "SEARCH_EVENT":
        q = None
        for kw in ["ai", "cloud", "workshop", "summit", "devops", "security"]:
            if kw in text.lower():
                q = kw
                break
        state.tool_calls.append({"tool": "search_events", "input": {"query": q}})
        res = tool_search_events(db, query=q)
        state.tool_results.append({"tool": "search_events", "result": res})

    elif state.intent == "REGISTER_EVENT":
        id_match = re.search(r'\b(?:id\s*|event\s*|#)?(\d+)\b', text, re.IGNORECASE)
        event_id = int(id_match.group(1)) if id_match else None
        if not event_id:
            search_res = tool_search_events(db, query=None)
            for ev in search_res.get("events", []):
                if ev["title"].lower() in text.lower():
                    event_id = ev["id"]
                    break
        
        if event_id:
            state.tool_calls.append({"tool": "register_participant", "input": {"event_id": event_id, "user_id": user_id}})
            res = tool_register_participant(db, user_id=user_id, event_id=event_id)
            state.tool_results.append({"tool": "register_participant", "result": res})
        else:
            state.tool_results.append({"tool": "register_participant", "result": {"success": False, "error": "Please specify the event ID or title."}})

    elif state.intent == "CANCEL_REGISTRATION":
        id_match = re.search(r'\b(?:id\s*|event\s*|#)?(\d+)\b', text, re.IGNORECASE)
        event_id = int(id_match.group(1)) if id_match else None
        if not event_id:
            regs_res = tool_get_user_registrations(db, user_id)
            for r in regs_res.get("registrations", []):
                if r["status"] == "CONFIRMED":
                    event_id = r["event_id"]
                    break
        if event_id:
            state.tool_calls.append({"tool": "cancel_registration", "input": {"event_id": event_id, "user_id": user_id}})
            res = tool_cancel_registration(db, user_id=user_id, event_id=event_id)
            state.tool_results.append({"tool": "cancel_registration", "result": res})
        else:
            state.tool_results.append({"tool": "cancel_registration", "result": {"success": False, "error": "Please specify the event ID."}})

    elif state.intent == "VIEW_MY_REGISTRATIONS":
        state.tool_calls.append({"tool": "get_user_registrations", "input": {"user_id": user_id}})
        res = tool_get_user_registrations(db, user_id=user_id)
        state.tool_results.append({"tool": "get_user_registrations", "result": res})

    elif state.intent == "CHECK_VENUE":
        venue_id = 1
        if "conference" in text.lower():
            venue_id = 2
        elif "innovation" in text.lower():
            venue_id = 3
        date_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
        date = date_match.group(1) if date_match else "2026-09-15"
        time_match = re.search(r'\b(\d{1,2}:\d{2})\b', text)
        time = time_match.group(1) if time_match else "10:00"

        state.tool_calls.append({"tool": "check_venue_availability", "input": {"venue_id": venue_id, "date": date, "time": time}})
        res = tool_check_venue_availability(db, venue_id=venue_id, date=date, time=time)
        state.tool_results.append({"tool": "check_venue_availability", "result": res})

    elif state.intent == "POLICY_RAG":
        state.tool_calls.append({"tool": "search_event_policy", "input": {"query": text}})
        rag_res = tool_search_event_policy(query=text, top_k=2)
        state.retrieved_documents = rag_res.get("relevant_chunks", [])
        state.tool_results.append({"tool": "search_event_policy", "result": rag_res})

    return state

def synthesis_node(state: AgentState) -> AgentState:
    intent = state.intent
    
    if intent == "MULTI_STEP_SEARCH_AND_REGISTER":
        reg_result = None
        for tr in state.tool_results:
            if tr["tool"] == "register_participant":
                reg_result = tr["result"]
                break
        if reg_result and reg_result.get("success"):
            state.final_response = (
                f"### Registration Confirmed!\n\n"
                f"I found the available session and successfully registered you:\n"
                f"- **Event:** {reg_result.get('event_title')}\n"
                f"- **Date & Time:** {reg_result.get('date')} at {reg_result.get('time')}\n"
                f"- **Registration ID:** `{reg_result.get('registration_id')}`\n"
                f"- **Status:** {reg_result.get('status')}\n\n"
                f"You can view your tickets anytime under **My Registrations**."
            )
        else:
            err = reg_result.get("error", "Could not complete registration.") if reg_result else "No available event."
            state.final_response = f"I looked for an available session, but could not register you: {err}"

    elif intent == "SEARCH_EVENT":
        res = state.tool_results[0]["result"] if state.tool_results else {}
        events = res.get("events", [])
        if not events:
            state.final_response = "No matching events found. Try searching for 'AI' or 'Cloud'."
        else:
            lines = [f"### Found {len(events)} Event(s):\n"]
            for ev in events:
                lines.append(f"- **[{ev['id']}] {ev['title']}**\n  - Date: {ev['date']} @ {ev['time']}\n  - Venue: {ev['venue']}\n  - Seats Available: {ev['available_seats']}/{ev['capacity']}")
            state.final_response = "\n".join(lines)

    elif intent == "REGISTER_EVENT":
        res = state.tool_results[0]["result"] if state.tool_results else {}
        state.final_response = f"### {res.get('message', res.get('error', 'Registration status update'))}"

    elif intent == "CANCEL_REGISTRATION":
        res = state.tool_results[0]["result"] if state.tool_results else {}
        state.final_response = f"### {res.get('message', res.get('error', 'Cancellation status update'))}"

    elif intent == "VIEW_MY_REGISTRATIONS":
        res = state.tool_results[0]["result"] if state.tool_results else {}
        regs = res.get("registrations", [])
        lines = [f"### Your Registered Events ({len(regs)}):\n"]
        for r in regs:
            lines.append(f"- **{r['event_title']}** (ID: {r['event_id']}) - Date: {r['date']} @ {r['time']} - Status: {r['status']}")
        state.final_response = "\n".join(lines) if regs else "You have no active event registrations."

    elif intent == "CHECK_VENUE":
        res = state.tool_results[0]["result"] if state.tool_results else {}
        state.final_response = res.get("message", "Availability checked.")

    elif intent == "POLICY_RAG":
        docs = state.retrieved_documents
        if docs:
            top_chunk = docs[0]
            state.final_response = f"### Event Policy Information\n\n{top_chunk['content']}\n\n*(Source: `{top_chunk['source']}`)*"
        else:
            state.final_response = "No matching policy guidelines found."
    else:
        state.final_response = "Hello! I am your AI Event Assistant. Ask me to find events, register tickets, check venue availability, or explain cancellation policies."

    return state
