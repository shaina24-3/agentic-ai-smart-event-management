import json
from typing import List, Optional, Any, Dict
from sqlalchemy.orm import Session
from app.models.agent_log import AgentRun
from app.schemas.agent_log import AgentRunResponse

class ObservabilityService:
    @staticmethod
    def log_run(
        db: Session,
        run_id: str,
        user_id: Optional[int],
        user_prompt: str,
        detected_intent: Optional[str],
        tools_called: Optional[List[Dict[str, Any]]],
        tool_results: Optional[List[Dict[str, Any]]],
        latency_ms: float,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
        final_response: Optional[str] = None
    ) -> AgentRun:
        run = AgentRun(
            run_id=run_id,
            user_id=user_id,
            user_prompt=user_prompt,
            detected_intent=detected_intent,
            tools_called=json.dumps(tools_called) if tools_called else None,
            tool_results=json.dumps(tool_results) if tool_results else None,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
            final_response=final_response
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def list_runs(db: Session, limit: int = 50, offset: int = 0) -> List[AgentRunResponse]:
        runs = db.query(AgentRun).order_by(AgentRun.created_at.desc()).offset(offset).limit(limit).all()
        return [AgentRunResponse.model_validate(r) for r in runs]
