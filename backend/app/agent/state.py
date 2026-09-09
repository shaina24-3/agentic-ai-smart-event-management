from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentState(BaseModel):
    user_id: Optional[int] = None
    role: str = "USER"
    user_prompt: str
    session_id: Optional[str] = None
    intent: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_documents: List[Dict[str, Any]] = Field(default_factory=list)
    final_response: Optional[str] = None
    db_session: Any = None

    class Config:
        arbitrary_types_allowed = True
