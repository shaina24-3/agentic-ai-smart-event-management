from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.agent_log import AgentRunResponse
from app.services.observability_service import ObservabilityService
from app.services.auth_service import get_current_user
from app.models.user import User

router = APIRouter(prefix="/observability", tags=["Observability"])

@router.get("/runs", response_model=List[AgentRunResponse])
def get_agent_runs(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ObservabilityService.list_runs(db, limit=limit, offset=offset)
