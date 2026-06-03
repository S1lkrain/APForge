from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.pool import StaticPool

from ..config import Settings


class _QuotaBase(DeclarativeBase):
    pass


class FreeSampleClaimRecord(_QuotaBase):
    __tablename__ = "free_sample_claims"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sample_id: Mapped[str] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ip_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


@dataclass(frozen=True)
class SampleClaim:
    sample_id: str
    status: str


class FreeSampleQuota:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        url = settings.database_url
        if url == "sqlite:///:memory:":
            self._engine = create_engine(
                url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            self._engine = create_engine(url)
        _QuotaBase.metadata.create_all(self._engine)

    def can_start_sample(self, session_id: str) -> bool:
        row = self._get(session_id)
        if row is None:
            return True
        if row.status == "consumed":
            return False
        if row.status == "failed":
            return True
        if row.status == "pending":
            return self._is_stale(row.created_at)
        return True

    def begin_sample(self, session_id: str, *, ip_hash: str | None) -> SampleClaim:
        with Session(self._engine) as session:
            row = session.get(FreeSampleClaimRecord, session_id)
            now = datetime.now(timezone.utc)
            if row is not None:
                if row.status == "consumed":
                    raise HTTPException(status_code=403, detail="Free sample already used for this session.")
                if row.status == "pending" and not self._is_stale(row.created_at):
                    raise HTTPException(status_code=409, detail="A free sample is already in progress.")
                sample_id = str(uuid.uuid4())
                row.sample_id = sample_id
                row.status = "pending"
                row.created_at = now
                row.consumed_at = None
                row.ip_hash = ip_hash
            else:
                sample_id = str(uuid.uuid4())
                session.add(
                    FreeSampleClaimRecord(
                        session_id=session_id,
                        sample_id=sample_id,
                        status="pending",
                        created_at=now,
                        ip_hash=ip_hash,
                    )
                )
            session.commit()
        return SampleClaim(sample_id=sample_id, status="pending")

    def mark_consumed(self, sample_id: str) -> None:
        self._set_status(sample_id, status="consumed", set_consumed_at=True)

    def mark_failed(self, sample_id: str) -> None:
        self._set_status(sample_id, status="failed", set_consumed_at=False)

    def get_status(self, session_id: str) -> str | None:
        row = self._get(session_id)
        return row.status if row else None

    def _set_status(self, sample_id: str, *, status: str, set_consumed_at: bool) -> None:
        with Session(self._engine) as session:
            row = (
                session.query(FreeSampleClaimRecord)
                .filter(FreeSampleClaimRecord.sample_id == sample_id)
                .one_or_none()
            )
            if row is None:
                return
            row.status = status
            if set_consumed_at:
                row.consumed_at = datetime.now(timezone.utc)
            session.commit()

    def _get(self, session_id: str) -> FreeSampleClaimRecord | None:
        with Session(self._engine) as session:
            return session.get(FreeSampleClaimRecord, session_id)

    def _is_stale(self, created_at: datetime) -> bool:
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=self.settings.free_sample_pending_stale_minutes
        )
        return created_at < cutoff
