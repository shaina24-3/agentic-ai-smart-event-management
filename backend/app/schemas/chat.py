from typing import Optional, List, Any, Dict
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ToolExecutionTrace(BaseModel):
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Any
    latency_ms: Optional[float] = None

class ChatResponse(BaseModel):
    run_id: str
    user_prompt: str
    detected_intent: Optional[str] = None
    final_response: str
    tool_traces: List[ToolExecutionTrace] = []
    latency_ms: float
