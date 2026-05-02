from sqlalchemy import String, Integer, DateTime, JSON, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from datetime import datetime, timezone
import enum

class EvalStatus(str, enum.Enum):
    running = "running"
    completed = "completed"
    failed = "failed"

class Base(DeclarativeBase):
    pass

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    endpoint_url: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    rubric_rule: Mapped[list["RubricRule"]] = relationship(back_populates="project", cascade="all, delete-orphan" )
    golden_pair: Mapped[list["GoldenPair"]] = relationship(back_populates="project", cascade="all, delete-orphan" )
    eval_run: Mapped[list["EvalRun"]] = relationship(back_populates="project", cascade="all, delete-orphan" )

class RubricRule(Base):
    __tablename__ = "rubric_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_text: Mapped[str] = mapped_column(String)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))

    project: Mapped[Project] = relationship(back_populates="rubric_rule")

class GoldenPair(Base):
    __tablename__ = "golden_pairs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    input_payload: Mapped[dict] = mapped_column(JSON)
    expected_output: Mapped[dict] = mapped_column(JSON)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))

    project: Mapped[Project] = relationship(back_populates="golden_pair")
    eval_result: Mapped[list["EvalResult"]] = relationship(back_populates="golden_pair") 

class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_version_tag: Mapped[str] = mapped_column(String)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    compared_to: Mapped[int | None] = mapped_column(ForeignKey("eval_runs.id"))
    status: Mapped[EvalStatus] = mapped_column(String, default=EvalStatus.running)

    project: Mapped[Project] = relationship(back_populates="eval_run")
    eval_result: Mapped[list["EvalResult"]] = relationship(back_populates="eval_run") 

class EvalResult(Base):
    __tablename__ = "eval_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actual_output: Mapped[dict] = mapped_column(JSON)
    passed: Mapped[bool] = mapped_column(Boolean)
    reason: Mapped[str] = mapped_column(String)
    golden_pair_id: Mapped[int] = mapped_column(ForeignKey("golden_pairs.id"))
    run_id: Mapped[int] = mapped_column(ForeignKey("eval_runs.id"))

    golden_pair: Mapped[GoldenPair] = relationship(back_populates="eval_result")
    eval_run: Mapped[EvalRun] = relationship(back_populates="eval_result")

