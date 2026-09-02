from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CREATED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    analyses: Mapped[list["RequirementAnalysis"]] = relationship(
        back_populates="requirement", order_by="RequirementAnalysis.id"
    )

    @property
    def public_id(self) -> str:
        return f"REQ-{self.id:03d}"


class RequirementAnalysis(Base):
    __tablename__ = "requirement_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    functional_requirements: Mapped[list] = mapped_column(JSON, nullable=False)
    non_functional_requirements: Mapped[list] = mapped_column(JSON, nullable=False)
    ambiguities: Mapped[list] = mapped_column(JSON, nullable=False)
    assumptions: Mapped[list] = mapped_column(JSON, nullable=False)
    constraints: Mapped[list] = mapped_column(JSON, nullable=False)
    success_criteria: Mapped[list] = mapped_column(JSON, nullable=False)
    engineering_concerns: Mapped[list] = mapped_column(JSON, nullable=False)

    requirement: Mapped["Requirement"] = relationship(back_populates="analyses")

    @property
    def public_id(self) -> str:
        return f"ANALYSIS-{self.id:03d}"
