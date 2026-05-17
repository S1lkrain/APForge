from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.pool import StaticPool

from .schema import GenerateRequest, GeneratedItem


class Base(DeclarativeBase):
    pass


class RunRecord(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    request_id: Mapped[str] = mapped_column(String(36), index=True)
    subject: Mapped[str] = mapped_column(String(64))
    skill: Mapped[str] = mapped_column(String(120))
    difficulty: Mapped[int] = mapped_column(Integer)
    item_type: Mapped[str] = mapped_column(String(16))
    prompt_version: Mapped[str] = mapped_column(String(32))
    model_id: Mapped[str] = mapped_column(String(64))
    latency_ms: Mapped[int] = mapped_column(Integer)
    repaired: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_status: Mapped[str] = mapped_column(String(32), default="valid")
    token_usage: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    harness_version: Mapped[str] = mapped_column(String(32), default="v1")
    policy_version: Mapped[str] = mapped_column(String(32), default="v1")
    prompt_pack_version: Mapped[str] = mapped_column(String(32), default="v1")
    gate_mode: Mapped[str] = mapped_column(String(16), default="warn")
    final_status: Mapped[str] = mapped_column(String(32), default="accepted")
    failure_reason_code: Mapped[str] = mapped_column(String(64), default="NONE")
    attempt_count_by_skill: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ItemRecord(Base):
    __tablename__ = "items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    question: Mapped[str] = mapped_column(Text)
    choices: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    item_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON)
    reviewer_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reviewer_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class EvalRecord(Base):
    __tablename__ = "eval_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    schema_valid: Mapped[bool] = mapped_column(Boolean)
    answer_consistent: Mapped[bool] = mapped_column(Boolean)
    explanation_score: Mapped[int] = mapped_column(Integer)
    difficulty_score: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(Text, default="")
    judge_scores: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


@dataclass
class Storage:
    database_url: str

    def __post_init__(self) -> None:
        if self.database_url == "sqlite:///:memory:":
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        self._migrate_sqlite_schema()

    def _migrate_sqlite_schema(self) -> None:
        if not self.database_url.startswith("sqlite"):
            return

        runs_columns = {
            "harness_version": "TEXT DEFAULT 'v1'",
            "policy_version": "TEXT DEFAULT 'v1'",
            "prompt_pack_version": "TEXT DEFAULT 'v1'",
            "gate_mode": "TEXT DEFAULT 'warn'",
            "final_status": "TEXT DEFAULT 'accepted'",
            "failure_reason_code": "TEXT DEFAULT 'NONE'",
            "attempt_count_by_skill": "JSON DEFAULT '{}'",
        }
        eval_columns = {
            "judge_scores": "JSON DEFAULT '{}'",
        }

        with self.engine.begin() as conn:
            existing_runs = {
                row[1]
                for row in conn.exec_driver_sql("PRAGMA table_info(runs)").fetchall()
            }
            for col, ddl in runs_columns.items():
                if col not in existing_runs:
                    conn.exec_driver_sql(f"ALTER TABLE runs ADD COLUMN {col} {ddl}")

            existing_eval = {
                row[1]
                for row in conn.exec_driver_sql("PRAGMA table_info(eval_results)").fetchall()
            }
            for col, ddl in eval_columns.items():
                if col not in existing_eval:
                    conn.exec_driver_sql(f"ALTER TABLE eval_results ADD COLUMN {col} {ddl}")

    def save_generation(
        self,
        *,
        request_id: str,
        req: GenerateRequest,
        item: GeneratedItem,
        model_id: str,
        latency_ms: int,
        repaired: bool,
        harness_version: str,
        policy_version: str,
        prompt_pack_version: str,
        gate_mode: str,
        final_status: str,
        failure_reason_code: str,
        attempt_count_by_skill: dict[str, int],
        token_usage: dict[str, Any] | None = None,
    ) -> str:
        run_id = str(uuid.uuid4())
        item_id = str(uuid.uuid4())
        with Session(self.engine) as session:
            session.add(
                RunRecord(
                    id=run_id,
                    request_id=request_id,
                    subject=req.subject.value,
                    skill=req.skill,
                    difficulty=req.difficulty,
                    item_type=req.type.value,
                    prompt_version=item.metadata.prompt_version,
                    model_id=model_id,
                    latency_ms=latency_ms,
                    repaired=repaired,
                    validation_status="valid",
                    token_usage=token_usage or {},
                    harness_version=harness_version,
                    policy_version=policy_version,
                    prompt_pack_version=prompt_pack_version,
                    gate_mode=gate_mode,
                    final_status=final_status,
                    failure_reason_code=failure_reason_code,
                    attempt_count_by_skill=attempt_count_by_skill,
                )
            )
            session.add(
                ItemRecord(
                    id=item_id,
                    run_id=run_id,
                    question=item.question,
                    choices=json.dumps(item.choices),
                    answer=item.answer,
                    explanation=item.explanation,
                    item_metadata=item.metadata.model_dump(),
                )
            )
            session.commit()
        return run_id

    def list_items(self, *, subject: str | None = None, skill: str | None = None, difficulty: int | None = None) -> list[dict]:
        with Session(self.engine) as session:
            query = session.query(ItemRecord, RunRecord).join(RunRecord, ItemRecord.run_id == RunRecord.id)
            if subject:
                query = query.filter(RunRecord.subject == subject)
            if skill:
                query = query.filter(RunRecord.skill == skill)
            if difficulty is not None:
                query = query.filter(RunRecord.difficulty == difficulty)
            rows = query.order_by(RunRecord.created_at.desc()).limit(100).all()

        output = []
        for item, run in rows:
            output.append(
                {
                    "run_id": run.id,
                    "created_at": run.created_at.isoformat(),
                    "subject": run.subject,
                    "skill": run.skill,
                    "difficulty": run.difficulty,
                    "type": run.item_type,
                    "final_status": run.final_status,
                    "failure_reason_code": run.failure_reason_code,
                    "question": item.question,
                    "choices": json.loads(item.choices),
                    "answer": item.answer,
                    "explanation": item.explanation,
                    "metadata": item.item_metadata,
                }
            )
        return output

    def save_eval(self, *, run_id: str, eval_data: dict) -> None:
        with Session(self.engine) as session:
            session.add(
                EvalRecord(
                    id=str(uuid.uuid4()),
                    run_id=run_id,
                    schema_valid=eval_data["schema_valid"],
                    answer_consistent=eval_data["answer_consistent"],
                    explanation_score=eval_data["explanation_score"],
                    difficulty_score=eval_data["difficulty_score"],
                    notes=eval_data.get("notes", ""),
                    judge_scores=eval_data.get("judge_scores", {}),
                )
            )
            session.commit()
