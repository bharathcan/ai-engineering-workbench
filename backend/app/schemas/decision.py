from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class EngineerDecisionResponse(BaseModel):
    """Shared by task-plan review decisions (Phase 4, ai_run_id=None) and
    AI-run recommendation decisions (Phase 5, ai_run_id set). Lives in its
    own module so both app.schemas.engineering_plan and app.schemas.ai_run
    can depend on it without importing each other."""

    id: str
    ai_run_id: str | None = None
    decision: Literal["ACCEPT", "MODIFY", "REJECT"]
    rationale: str | None
    changes: str | None
    reviewer: str | None = None
    created_at: datetime
