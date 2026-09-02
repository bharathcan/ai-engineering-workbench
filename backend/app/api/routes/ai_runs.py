import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AIRunNotFoundError, PersistenceError
from app.schemas.ai_run import AIRunDecisionRequest, AIRunResponse
from app.services import ai_run_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai-runs"])


@router.post("/api/v1/ai-runs/{ai_run_id}/decision", response_model=AIRunResponse)
def decide_ai_run(ai_run_id: str, payload: AIRunDecisionRequest, db: Session = Depends(get_db)):
    try:
        return ai_run_service.decide_ai_run(
            db, ai_run_id, payload.decision, payload.rationale, payload.changes
        )
    except AIRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to record decision for %s: %s", ai_run_id, exc)
        raise HTTPException(status_code=500, detail="Failed to record the decision.") from exc
