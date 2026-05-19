from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text, create_engine, func, or_
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


def compute_quality_score(judge_scores: dict[str, Any] | None) -> float | None:
    if not judge_scores:
        return None
    keys = ("schema_score", "consistency_score", "pedagogy_score", "compliance_score")
    values = [judge_scores.get(key) for key in keys]
    if not all(isinstance(value, (int, float)) for value in values):
        return None
    return round(sum(values) / len(values), 1)  # type: ignore[arg-type]


def map_ui_status(final_status: str) -> str:
    if final_status == "accepted":
        return "Success"
    if final_status == "accepted_with_warning":
        return "Warn"
    return "Rejected"


VALID_ITEM_SORTS = frozenset({"newest", "oldest", "quality_desc", "quality_asc"})


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _like_pattern(q: str) -> str:
    return f"%{_escape_like(q.strip().lower())}%"


def _dedupe_rows(rows: list[tuple]) -> list[tuple]:
    seen: set[str] = set()
    deduped: list[tuple] = []
    for row in rows:
        run_id = row[1].id
        if run_id in seen:
            continue
        seen.add(run_id)
        deduped.append(row)
    return deduped


def ui_status_to_final_statuses(status: str) -> list[str] | None:
    normalized = status.strip().lower()
    if normalized in ("success", "accepted"):
        return ["accepted"]
    if normalized in ("warn", "warning", "accepted_with_warning"):
        return ["accepted_with_warning"]
    if normalized in ("rejected", "fallback"):
        return ["rejected", "fallback"]
    return None


def row_to_item_dict(item: ItemRecord, run: RunRecord, eval_row: EvalRecord | None) -> dict:
    judge_scores = eval_row.judge_scores if eval_row else {}
    return {
        "run_id": run.id,
        "created_at": run.created_at.isoformat(),
        "subject": run.subject,
        "skill": run.skill,
        "difficulty": run.difficulty,
        "type": run.item_type,
        "final_status": run.final_status,
        "status": map_ui_status(run.final_status),
        "failure_reason_code": run.failure_reason_code,
        "quality_score": compute_quality_score(judge_scores),
        "question": item.question,
        "choices": json.loads(item.choices),
        "answer": item.answer,
        "explanation": item.explanation,
        "metadata": item.item_metadata,
    }


def _matches_quality_filters(
    quality_score: float | None,
    *,
    quality_min: float | None,
    quality_max: float | None,
    has_quality: bool | None,
) -> bool:
    if has_quality is True and quality_score is None:
        return False
    if has_quality is False and quality_score is not None:
        return False
    if quality_min is not None and (quality_score is None or quality_score < quality_min):
        return False
    if quality_max is not None and (quality_score is None or quality_score > quality_max):
        return False
    return True


def _sort_items(items: list[dict], sort: str) -> list[dict]:
    if sort == "oldest":
        return sorted(items, key=lambda row: row["created_at"])
    if sort == "quality_desc":
        return sorted(
            items,
            key=lambda row: (row["quality_score"] is None, -(row["quality_score"] or 0)),
        )
    if sort == "quality_asc":
        return sorted(
            items,
            key=lambda row: (row["quality_score"] is None, row["quality_score"] or 0),
        )
    return sorted(items, key=lambda row: row["created_at"], reverse=True)


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

    def _build_items_query(
        self,
        session: Session,
        *,
        run_id: str | None = None,
        subject: str | None = None,
        skill: str | None = None,
        difficulty: int | None = None,
        item_type: str | None = None,
        status: str | None = None,
        q: str | None = None,
    ):
        query = (
            session.query(ItemRecord, RunRecord, EvalRecord)
            .join(RunRecord, ItemRecord.run_id == RunRecord.id)
            .outerjoin(EvalRecord, EvalRecord.run_id == RunRecord.id)
        )
        if run_id:
            query = query.filter(RunRecord.id == run_id)
        if subject:
            query = query.filter(RunRecord.subject == subject)
        if skill:
            query = query.filter(RunRecord.skill == skill)
        if difficulty is not None:
            query = query.filter(RunRecord.difficulty == difficulty)
        if item_type:
            query = query.filter(RunRecord.item_type == item_type)
        if status:
            final_statuses = ui_status_to_final_statuses(status)
            if final_statuses:
                query = query.filter(RunRecord.final_status.in_(final_statuses))
            else:
                query = query.filter(RunRecord.final_status == status)
        if q and q.strip():
            term = _like_pattern(q)
            query = query.filter(
                or_(
                    func.lower(RunRecord.subject).like(term, escape="\\"),
                    func.lower(RunRecord.skill).like(term, escape="\\"),
                    func.lower(RunRecord.item_type).like(term, escape="\\"),
                    func.lower(ItemRecord.question).like(term, escape="\\"),
                )
            )
        return query

    def list_items(
        self,
        *,
        run_id: str | None = None,
        subject: str | None = None,
        skill: str | None = None,
        difficulty: int | None = None,
        item_type: str | None = None,
        status: str | None = None,
        q: str | None = None,
        quality_min: float | None = None,
        quality_max: float | None = None,
        has_quality: bool | None = None,
        sort: str = "newest",
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        if sort not in VALID_ITEM_SORTS:
            raise ValueError(f"Invalid sort: {sort}")

        page = max(1, page)
        page_size = max(1, min(page_size, 50))
        offset = (page - 1) * page_size

        needs_python_quality = (
            quality_min is not None
            or quality_max is not None
            or has_quality is not None
            or sort in ("quality_desc", "quality_asc")
        )

        with Session(self.engine) as session:
            query = self._build_items_query(
                session,
                run_id=run_id,
                subject=subject,
                skill=skill,
                difficulty=difficulty,
                item_type=item_type,
                status=status,
                q=q,
            )

            if needs_python_quality:
                rows = _dedupe_rows(query.all())
                items = [row_to_item_dict(item, run, eval_row) for item, run, eval_row in rows]
                items = [
                    row
                    for row in items
                    if _matches_quality_filters(
                        row["quality_score"],
                        quality_min=quality_min,
                        quality_max=quality_max,
                        has_quality=has_quality,
                    )
                ]
                items = _sort_items(items, sort)
                total = len(items)
                page_items = items[offset : offset + page_size]
            else:
                total = query.with_entities(RunRecord.id).distinct().count()
                if sort == "oldest":
                    query = query.order_by(RunRecord.created_at.asc())
                else:
                    query = query.order_by(RunRecord.created_at.desc())
                rows = _dedupe_rows(query.offset(offset).limit(page_size).all())
                page_items = [row_to_item_dict(item, run, eval_row) for item, run, eval_row in rows]

        return {
            "items": page_items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def delete_run(self, run_id: str) -> bool:
        with Session(self.engine) as session:
            run = session.get(RunRecord, run_id)
            if run is None:
                return False
            session.query(EvalRecord).filter(EvalRecord.run_id == run_id).delete()
            session.query(ItemRecord).filter(ItemRecord.run_id == run_id).delete()
            session.delete(run)
            session.commit()
            return True

    def get_dashboard_stats(self) -> dict:
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        prev_week_start = now - timedelta(days=14)

        with Session(self.engine) as session:
            total_runs = session.query(func.count(RunRecord.id)).scalar() or 0
            success_runs = (
                session.query(func.count(RunRecord.id))
                .filter(RunRecord.final_status.in_(("accepted", "accepted_with_warning")))
                .scalar()
                or 0
            )
            success_rate = (success_runs / total_runs) if total_runs else 0.0

            eval_rows = session.query(EvalRecord.judge_scores).all()
            quality_scores = [
                score
                for row in eval_rows
                if (score := compute_quality_score(row.judge_scores)) is not None
            ]
            avg_quality_score = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0.0

            recent_runs = (
                session.query(func.count(RunRecord.id)).filter(RunRecord.created_at >= week_ago).scalar() or 0
            )
            prev_runs = (
                session.query(func.count(RunRecord.id))
                .filter(RunRecord.created_at >= prev_week_start, RunRecord.created_at < week_ago)
                .scalar()
                or 0
            )

            recent_success = (
                session.query(func.count(RunRecord.id))
                .filter(
                    RunRecord.created_at >= week_ago,
                    RunRecord.final_status.in_(("accepted", "accepted_with_warning")),
                )
                .scalar()
                or 0
            )
            prev_success = (
                session.query(func.count(RunRecord.id))
                .filter(
                    RunRecord.created_at >= prev_week_start,
                    RunRecord.created_at < week_ago,
                    RunRecord.final_status.in_(("accepted", "accepted_with_warning")),
                )
                .scalar()
                or 0
            )
            recent_success_rate = (recent_success / recent_runs) if recent_runs else 0.0
            prev_success_rate = (prev_success / prev_runs) if prev_runs else 0.0

            recent_evals = (
                session.query(EvalRecord.judge_scores).join(RunRecord, EvalRecord.run_id == RunRecord.id).filter(
                    RunRecord.created_at >= week_ago
                ).all()
            )
            prev_evals = (
                session.query(EvalRecord.judge_scores)
                .join(RunRecord, EvalRecord.run_id == RunRecord.id)
                .filter(RunRecord.created_at >= prev_week_start, RunRecord.created_at < week_ago)
                .all()
            )

        def avg_quality(rows: list) -> float:
            scores = [s for row in rows if (s := compute_quality_score(row.judge_scores)) is not None]
            return round(sum(scores) / len(scores), 1) if scores else 0.0

        recent_avg_quality = avg_quality(recent_evals)
        prev_avg_quality = avg_quality(prev_evals)

        return {
            "total_generated": total_runs,
            "success_rate": round(success_rate, 4),
            "avg_quality_score": avg_quality_score,
            "total_runs": total_runs,
            "week_delta": {
                "total_generated": recent_runs - prev_runs,
                "success_rate": round(recent_success_rate - prev_success_rate, 4),
                "avg_quality_score": round(recent_avg_quality - prev_avg_quality, 1),
                "total_runs": recent_runs - prev_runs,
            },
        }

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
