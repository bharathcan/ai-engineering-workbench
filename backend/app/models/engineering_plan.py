from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.requirement import Requirement


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EngineeringPlan(Base):
    __tablename__ = "engineering_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id"), nullable=False)
    requirement_analysis_id: Mapped[int] = mapped_column(
        ForeignKey("requirement_analyses.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # "GENERATED" or "BLOCKED" — see app.services.task_decomposer for the
    # ambiguity gate that decides which one this is.
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    assumptions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    unresolved_ambiguities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    risks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Plan-level review is not driven by any endpoint yet in this phase —
    # review happens per-task (POST /api/v1/tasks/{id}/decision). This field
    # is descriptive only; see docs/api-design.md.
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")

    tasks: Mapped[list["EngineeringTask"]] = relationship(
        back_populates="plan", order_by="EngineeringTask.sequence"
    )
    requirement: Mapped["Requirement"] = relationship()

    @property
    def public_id(self) -> str:
        return f"PLAN-{self.id:03d}"


class EngineeringTask(Base):
    __tablename__ = "engineering_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("engineering_plans.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    requirement_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Dependencies are stored as the *public* TASK-xxx ids of other tasks in
    # the same plan, already remapped from the AI's plan-local ids — see
    # app.services.task_decomposer._persist_plan.
    dependencies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    acceptance_criteria: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    ai_assistance_type: Mapped[str] = mapped_column(String(32), nullable=False)
    risks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Planning/review lifecycle only for this phase — no execution states
    # (READY, IN_PROGRESS, IMPLEMENTED, VALIDATION_*) are modeled yet; see
    # docs/api-design.md for which states this phase actually uses.
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="REVIEW_REQUIRED")
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")

    plan: Mapped["EngineeringPlan"] = relationship(back_populates="tasks")
    decisions: Mapped[list["EngineerDecision"]] = relationship(
        back_populates="task", order_by="EngineerDecision.id"
    )
    ai_runs: Mapped[list["AIRun"]] = relationship(back_populates="task", order_by="AIRun.id")

    @property
    def public_id(self) -> str:
        return f"TASK-{self.id:03d}"


class AIRun(Base):
    __tablename__ = "ai_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("engineering_tasks.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    assistance_type: Mapped[str] = mapped_column(String(32), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # "COMPLETED" or "FAILED". Unlike Phase 3/4's analyze/decompose endpoints,
    # a failed run is still persisted here — see docs/api-design.md — so the
    # audit trail includes attempts that didn't produce a usable
    # recommendation, not just successful ones.
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Set when this run follows a MODIFY decision on an earlier run for the
    # same task — see app.services.ai_run_service. Preserves the
    # AI-RUN-001 -> MODIFY -> AI-RUN-002 lineage explicitly, rather than
    # leaving it to be inferred from timestamps.
    revised_from_ai_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_runs.id"), nullable=True
    )

    task: Mapped["EngineeringTask"] = relationship(back_populates="ai_runs")
    decisions: Mapped[list["EngineerDecision"]] = relationship(
        back_populates="ai_run", order_by="EngineerDecision.id"
    )

    @property
    def public_id(self) -> str:
        return f"AI-RUN-{self.id:03d}"


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("engineering_tasks.id"), nullable=False)
    ai_run_id: Mapped[int] = mapped_column(ForeignKey("ai_runs.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    artifact_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # Relative to the sandboxed generated/ workspace root — never an
    # absolute path or one containing '..'. Enforced in
    # app.services.artifact_generator before this row is ever created; see
    # docs/api-design.md "Controlled File Writes".
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    # PENDING_REVIEW (initial) -> APPROVED | NEEDS_REVISION | REJECTED, via
    # POST /api/v1/artifacts/{id}/decision. Never any value implying an
    # unreviewed artifact is safe to treat as final.
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING_REVIEW")

    # Versioning: regenerating an artifact for the same (task_id, path) never
    # overwrites the previous row — it inserts a new one with version = N+1
    # and supersedes_artifact_id pointing at the row it replaces. Both rows
    # persist. See app.repositories.artifact_repository.
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    supersedes_artifact_id: Mapped[int | None] = mapped_column(
        ForeignKey("artifacts.id"), nullable=True
    )

    task: Mapped["EngineeringTask"] = relationship()
    ai_run: Mapped["AIRun"] = relationship()
    decisions: Mapped[list["EngineerDecision"]] = relationship(
        back_populates="artifact", order_by="EngineerDecision.id"
    )

    @property
    def public_id(self) -> str:
        return f"ARTIFACT-{self.id:03d}"


class Validation(Base):
    __tablename__ = "validations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("artifacts.id"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("engineering_tasks.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    validation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # The actual allowlisted command that was run — never arbitrary,
    # frontend-supplied text. See app.services.validation_runner.
    command: Mapped[str] = mapped_column(String(200), nullable=False)

    # PASSED | FAILED | NOT_VALIDATED. PENDING/RUNNING are valid states in
    # the domain model but this runner is synchronous — a row is only ever
    # written once a result (or a documented non-result) already exists, so
    # no row is ever persisted mid-flight in either of those two states.
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=False, default="")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    artifact: Mapped["Artifact"] = relationship()
    task: Mapped["EngineeringTask"] = relationship()

    @property
    def public_id(self) -> str:
        return f"VALIDATION-{self.id:03d}"


class EngineerDecision(Base):
    __tablename__ = "engineer_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("engineering_tasks.id"), nullable=False)
    # NULL for a Phase 4 task-plan-review decision; set for a Phase 5
    # decision on a specific AI run's recommendation.
    ai_run_id: Mapped[int | None] = mapped_column(ForeignKey("ai_runs.id"), nullable=True)
    # Set for a Phase 6 decision on a generated artifact.
    artifact_id: Mapped[int | None] = mapped_column(ForeignKey("artifacts.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    decision: Mapped[str] = mapped_column(String(16), nullable=False)  # ACCEPT | MODIFY | REJECT
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    changes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # No authentication exists anywhere in this system yet (see
    # docs/validation/PHASE-4-SECURITY-REVIEW.md and PHASE-5). Always NULL —
    # never accepted from the client, since an unauthenticated,
    # client-supplied reviewer string would be trivially spoofable.
    reviewer: Mapped[str | None] = mapped_column(String(100), nullable=True)

    task: Mapped["EngineeringTask"] = relationship(back_populates="decisions")
    ai_run: Mapped["AIRun | None"] = relationship(back_populates="decisions")
    artifact: Mapped["Artifact | None"] = relationship(back_populates="decisions")

    @property
    def public_id(self) -> str:
        return f"DECISION-{self.id:03d}"
