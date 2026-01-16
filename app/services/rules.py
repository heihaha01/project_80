from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyMetrics, DailySummary, FoodLog, SelfRating, SummaryColor


@dataclass(frozen=True)
class SummaryResult:
    color: SummaryColor
    score: int
    reasons: list[str]
    commentary: str



def _day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min)
    end = datetime.combine(day, time.max)
    return start, end


def evaluate_day_from_data(metrics: DailyMetrics | None, food_logs: list[FoodLog]) -> SummaryResult:
    reasons: list[str] = []
    score = 0

    glucose_flag = SummaryColor.green
    if metrics and metrics.fasting_glucose_mmol_l is not None:
        g = metrics.fasting_glucose_mmol_l
        if g > 7.0:
            glucose_flag = SummaryColor.red
            reasons.append(f"空腹血糖 {g:.1f} > 7.0")
            score -= 4
        elif g >= 6.0:
            glucose_flag = SummaryColor.yellow
            reasons.append(f"空腹血糖 {g:.1f} 介于 6.0-7.0")
            score -= 2
        else:
            score += 2
    else:
        reasons.append("未录入空腹血糖")
        score -= 1
        glucose_flag = SummaryColor.yellow

    diet_flag = SummaryColor.green
    if not food_logs:
        reasons.append("未记录饮食（可能漏记）")
        score -= 1
        diet_flag = SummaryColor.yellow
    else:
        any_danger = any(log.self_rating == SelfRating.danger for log in food_logs)
        any_risk = any(log.self_rating == SelfRating.risk for log in food_logs)
        any_sugar = any(log.sugar for log in food_logs)
        any_refined = any(log.refined_carbs for log in food_logs)

        if any_danger or (any_sugar and any_refined):
            diet_flag = SummaryColor.red
            reasons.append("饮食：危险/高糖精制碳水")
            score -= 4
        elif any_risk or any_sugar or any_refined:
            diet_flag = SummaryColor.yellow
            reasons.append("饮食：存在风险项")
            score -= 2
        else:
            score += 2

    color = SummaryColor.green
    if glucose_flag == SummaryColor.red or diet_flag == SummaryColor.red:
        color = SummaryColor.red
    elif glucose_flag == SummaryColor.yellow or diet_flag == SummaryColor.yellow:
        color = SummaryColor.yellow

    if color == SummaryColor.red:
        commentary = "昨日行为已触发红灯：立即收紧饮食与作息，避免连续红灯。"
    elif color == SummaryColor.yellow:
        commentary = "昨日行为为黄灯：存在风险项，今天把风险项清零。"
    else:
        commentary = "昨日为绿灯：保持节奏，继续累计绿灯。"

    return SummaryResult(color=color, score=score, reasons=reasons, commentary=commentary)


def evaluate_day(db: Session, day: date) -> SummaryResult:
    metrics = db.execute(select(DailyMetrics).where(DailyMetrics.day == day)).scalar_one_or_none()
    start, end = _day_bounds(day)
    food_logs = (
        db.execute(select(FoodLog).where(FoodLog.eaten_at >= start, FoodLog.eaten_at <= end).order_by(FoodLog.eaten_at))
        .scalars()
        .all()
    )
    return evaluate_day_from_data(metrics, list(food_logs))


def upsert_daily_summary(db: Session, day: date) -> DailySummary:
    result = evaluate_day(db, day)
    existing = db.execute(select(DailySummary).where(DailySummary.day == day)).scalar_one_or_none()
    reasons_text = "\n".join(f"- {r}" for r in result.reasons)

    if existing is None:
        existing = DailySummary(
            day=day,
            color=result.color,
            score=result.score,
            reasons=reasons_text,
            commentary=result.commentary,
        )
        db.add(existing)
    else:
        existing.color = result.color
        existing.score = result.score
        existing.reasons = reasons_text
        existing.commentary = result.commentary

    db.commit()
    db.refresh(existing)
    return existing


def fasting_hours_since(last_meal_end_at: datetime | None, now: datetime) -> float | None:
    if last_meal_end_at is None:
        return None
    delta: timedelta = now - last_meal_end_at
    return delta.total_seconds() / 3600.0
