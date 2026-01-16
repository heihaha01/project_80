from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import DailyMetrics
from app.security import require_auth_dependency as basic_auth_dependency
from app.services.rules import upsert_daily_summary


router = APIRouter(dependencies=[Depends(basic_auth_dependency())])
templates = Jinja2Templates(directory="app/templates")


@router.get("/report/weekly", response_class=HTMLResponse)
def weekly_report(request: Request, end: str | None = None, db: Session = Depends(get_db)) -> HTMLResponse:
    end_day = date.fromisoformat(end) if end else date.today()
    start_day = end_day - timedelta(days=6)

    days = [start_day + timedelta(days=i) for i in range(7)]
    summaries = [upsert_daily_summary(db, d) for d in days]

    metrics_list = (
        db.execute(select(DailyMetrics).where(DailyMetrics.day >= start_day, DailyMetrics.day <= end_day))
        .scalars()
        .all()
    )
    metrics = {m.day: m for m in metrics_list}

    colors = [s.color.value for s in summaries]
    green = colors.count("green")
    yellow = colors.count("yellow")
    red = colors.count("red")

    weights = [metrics[d].weight_kg for d in days if d in metrics and metrics[d].weight_kg is not None]
    fasting = [metrics[d].fasting_glucose_mmol_l for d in days if d in metrics and metrics[d].fasting_glucose_mmol_l]

    weight_change = None
    if len(weights) >= 2:
        weight_change = weights[-1] - weights[0]

    fasting_avg = None
    if fasting:
        fasting_avg = sum(fasting) / len(fasting)

    return templates.TemplateResponse(
        "report_weekly.html",
        {
            "request": request,
            "start_day": start_day,
            "end_day": end_day,
            "summaries": summaries,
            "metrics": metrics,
            "green": green,
            "yellow": yellow,
            "red": red,
            "weight_change": weight_change,
            "fasting_avg": fasting_avg,
        },
    )
