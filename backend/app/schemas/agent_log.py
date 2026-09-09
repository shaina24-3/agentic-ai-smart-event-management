from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class AgentRunResponse(BaseModel):
    id: int
    run_id: str
    user_id: Optional[int]
    user_prompt: str
    detected_intent: Optional[str]
    tools_called: Optional[str]
    tool_results: Optional[str]
    latency_ms: float
    status: str
    error_message: Optional[str]
    final_response: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
