from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyMetrics, DailySummary


def get_recent_metrics(db: Session, days: int = 30) -> list[DailyMetrics]:
    start_day = date.today() - timedelta(days=days - 1)
    return (
        db.execute(select(DailyMetrics).where(DailyMetrics.day >= start_day).order_by(DailyMetrics.day.asc()))
        .scalars()
        .all()
    )


def get_weight_baseline(db: Session) -> float | None:
    first = (
        db.execute(select(DailyMetrics).where(DailyMetrics.weight_kg.is_not(None)).order_by(DailyMetrics.day.asc()).limit(1))
        .scalars()
        .first()
    )
    return None if first is None else first.weight_kg


def get_summary_counts(db: Session) -> dict[str, int]:
    rows = db.execute(select(DailySummary.color)).scalars().all()
    counts: dict[str, int] = {"green": 0, "yellow": 0, "red": 0}
    for c in rows:
        counts[c.value] += 1
    return counts

