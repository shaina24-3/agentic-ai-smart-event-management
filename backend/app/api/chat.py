import time
import uuid
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ToolExecutionTrace
from app.agent.state import AgentState
from app.agent.graph import agent_graph
from app.services.observability_service import ObservabilityService
from app.services.auth_service import get_current_user
from app.models.user import User

router = APIRouter(tags=["AI Agent Chat"])

@router.post("/chat", response_model=ChatResponse)
def chat_with_agent(chat_req: ChatRequest, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user)):
    start_time = time.perf_counter()
    run_id = f"run_{uuid.uuid4().hex[:10]}"
    
    state = AgentState(
        user_id=current_user.id if current_user else 1,
        role=current_user.role if current_user else "USER",
        user_prompt=chat_req.message,
        session_id=chat_req.session_id,
        db_session=db
    )
    
    final_state = agent_graph.invoke(state)
    result_state = AgentState(**final_state) if isinstance(final_state, dict) else final_state
    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    
    tool_traces = [
        ToolExecutionTrace(
            tool_name=c.get("tool", "unknown"),
            tool_input=c.get("input", {}),
            tool_output=r.get("result", {})
        )
        for c, r in zip(result_state.tool_calls, result_state.tool_results)
    ]
        
    ObservabilityService.log_run(
        db=db,
        run_id=run_id,
        user_id=result_state.user_id,
        user_prompt=chat_req.message,
        detected_intent=result_state.intent,
        tools_called=result_state.tool_calls,
        tool_results=result_state.tool_results,
        latency_ms=latency_ms,
        status="SUCCESS",
        final_response=result_state.final_response
    )
    
    return ChatResponse(
        run_id=run_id,
        user_prompt=chat_req.message,
        detected_intent=result_state.intent,
        final_response=result_state.final_response or "",
        tool_traces=tool_traces,
        latency_ms=latency_ms
    )
