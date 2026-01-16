from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import DailyMetrics, User, UserSettings
from app.security import require_auth_dependency as basic_auth_dependency
from app.services.rules import fasting_hours_since, upsert_daily_summary
from app.services.stats import get_recent_metrics, get_summary_counts, get_weight_baseline

router = APIRouter(dependencies=[Depends(basic_auth_dependency())])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    today = date.today()
    yesterday = today - timedelta(days=1)

    summary_yesterday = upsert_daily_summary(db, yesterday)
    warning_image = "warnings/red_warning.svg" if summary_yesterday.color.value == "red" else None

    metrics_today = db.execute(select(DailyMetrics).where(DailyMetrics.day == today)).scalar_one_or_none()
    user = db.execute(select(User).where(User.username == "self")).scalar_one()
    user_settings = db.execute(select(UserSettings).where(UserSettings.user_id == user.id)).scalar_one()

    height_m = max(user_settings.height_cm, 1.0) / 100.0
    bmi = None
    if metrics_today and metrics_today.weight_kg:
        bmi = metrics_today.weight_kg / (height_m * height_m)

    recent = get_recent_metrics(db, days=30)
    chart_days = [m.day.isoformat() for m in recent]
    chart_weight = [m.weight_kg for m in recent]
    chart_glucose = [m.fasting_glucose_mmol_l for m in recent]

    baseline = get_weight_baseline(db)
    weight_change = None
    if baseline is not None and metrics_today and metrics_today.weight_kg is not None:
        weight_change = metrics_today.weight_kg - baseline

    goal_delta = None
    if metrics_today and metrics_today.weight_kg is not None:
        goal_delta = metrics_today.weight_kg - user_settings.goal_weight_kg

    now = datetime.now()
    fasting_hours = fasting_hours_since(user_settings.last_meal_end_at, now)
    fasting_remaining = None
    if fasting_hours is not None:
        fasting_remaining = max(0.0, 16.0 - fasting_hours)

    counts = get_summary_counts(db)
    green_total = counts["green"]
    green_milestone = (green_total // 7) * 7 if green_total >= 7 else None

    weight_milestone = None
    if baseline is not None and metrics_today and metrics_today.weight_kg is not None:
        lost = baseline - metrics_today.weight_kg
        if lost >= 5:
            weight_milestone = int(lost // 5) * 5

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "settings": user_settings,
            "metrics_today": metrics_today,
            "bmi": bmi,
            "goal_delta": goal_delta,
            "weight_change": weight_change,
            "summary_yesterday": summary_yesterday,
            "warning_image": warning_image,
            "chart_days_json": json.dumps(chart_days, ensure_ascii=False),
            "chart_weight_json": json.dumps(chart_weight, ensure_ascii=False),
            "chart_glucose_json": json.dumps(chart_glucose, ensure_ascii=False),
            "fasting_hours": fasting_hours,
            "fasting_remaining": fasting_remaining,
            "green_total": green_total,
            "green_milestone": green_milestone,
            "weight_milestone": weight_milestone,
        },
    )
