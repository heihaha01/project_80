from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import DailyMetrics
from app.security import require_auth_dependency as basic_auth_dependency
from app.services.calendar import month_grid


router = APIRouter(dependencies=[Depends(basic_auth_dependency())])
templates = Jinja2Templates(directory="app/templates")


@router.get("/calendar", response_class=HTMLResponse)
def calendar(
    request: Request,
    year: int | None = Query(None),
    month: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    today = date.today()
    y = year or today.year
    m = month or today.month

    if m == 1:
        prev_year, prev_month = y - 1, 12
    else:
        prev_year, prev_month = y, m - 1

    if m == 12:
        next_year, next_month = y + 1, 1
    else:
        next_year, next_month = y, m + 1

    weeks = month_grid(y, m)
    
    # Calculate date range for batch fetching
    all_days = [d.day for week in weeks for d in week]
    if not all_days:
        return templates.TemplateResponse("calendar.html", {
            "request": request, "year": y, "month": m, 
            "prev_year": prev_year, "prev_month": prev_month,
            "next_year": next_year, "next_month": next_month,
            "weeks": weeks, "day_to_summary": {}
        })

    min_date = min(all_days)
    max_date = max(all_days)
    
    # Batch Fetch DailyMetrics
    metrics_list = db.execute(select(DailyMetrics).where(DailyMetrics.day >= min_date, DailyMetrics.day <= max_date)).scalars().all()
    metrics_map = {m.day: m for m in metrics_list}

    # Batch Fetch FoodLog
    # Note: FoodLog uses datetime, so we need full range
    from datetime import datetime, time
    start_dt = datetime.combine(min_date, time.min)
    end_dt = datetime.combine(max_date, time.max)
    
    from app.models import FoodLog
    logs_list = db.execute(select(FoodLog).where(FoodLog.eaten_at >= start_dt, FoodLog.eaten_at <= end_dt)).scalars().all()
    
    # Group logs by date
    logs_map = {}
    for log in logs_list:
        d = log.eaten_at.date()
        if d not in logs_map:
            logs_map[d] = []
        logs_map[d].append(log)

    from app.services.rules import evaluate_day_from_data

    day_to_summary = {}
    for d_obj in all_days:
        if d_obj > today:
            day_to_summary[d_obj] = None
        else:
            # In-memory calculation using batch data (FAST)
            m_obj = metrics_map.get(d_obj)
            l_objs = logs_map.get(d_obj, [])
            result = evaluate_day_from_data(m_obj, l_objs)
            day_to_summary[d_obj] = result.color.value

    return templates.TemplateResponse(
        "calendar.html",
        {
            "request": request,
            "year": y,
            "month": m,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "weeks": weeks,
            "day_to_summary": day_to_summary,
        },
    )
