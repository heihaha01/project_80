from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import DailyMetrics
from app.security import require_auth_dependency as basic_auth_dependency

router = APIRouter(dependencies=[Depends(basic_auth_dependency())])
templates = Jinja2Templates(directory="app/templates")


def _to_float(v: str | float | None) -> float | None:
    if v is None or v == "":
        return None
    return float(v)


def _to_int(v: str | int | None) -> int | None:
    if v is None or v == "":
        return None
    return int(float(v))


@router.get("/metrics", response_class=HTMLResponse)
def metrics_list(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    metrics = db.execute(select(DailyMetrics).order_by(DailyMetrics.day.desc()).limit(120)).scalars().all()
    return templates.TemplateResponse("metrics_list.html", {"request": request, "metrics": metrics})


@router.get("/metrics/new", response_class=HTMLResponse)
def new_metrics(
    request: Request,
    day: str | None = Query(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    day_value = day or date.today().isoformat()
    d = date.fromisoformat(day_value)
    metric = db.execute(select(DailyMetrics).where(DailyMetrics.day == d)).scalar_one_or_none()
    return templates.TemplateResponse(
        "metrics_new.html",
        {"request": request, "day": day_value, "metric": metric},
    )


@router.post("/metrics/new")
def create_or_update_metrics(
    day: str = Form(...),
    weight_kg: str | float | None = Form(None),
    fasting_glucose_mmol_l: str | float | None = Form(None),
    post2h_glucose_mmol_l: str | float | None = Form(None),
    waist_cm: str | float | None = Form(None),
    sleep_hours: str | float | None = Form(None),
    bp_systolic: str | int | None = Form(None),
    bp_diastolic: str | int | None = Form(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    d = date.fromisoformat(day)
    metric = db.execute(select(DailyMetrics).where(DailyMetrics.day == d)).scalar_one_or_none()
    if metric is None:
        metric = DailyMetrics(day=d)
        db.add(metric)

    metric.weight_kg = _to_float(weight_kg)
    metric.fasting_glucose_mmol_l = _to_float(fasting_glucose_mmol_l)
    metric.post2h_glucose_mmol_l = _to_float(post2h_glucose_mmol_l)
    metric.waist_cm = _to_float(waist_cm)
    metric.sleep_hours = _to_float(sleep_hours)
    metric.bp_systolic = _to_int(bp_systolic)
    metric.bp_diastolic = _to_int(bp_diastolic)

    db.commit()
    return RedirectResponse(url=f"/metrics/new?day={day}", status_code=303)


@router.post("/metrics/delete")
def delete_metrics(day: str = Form(...), db: Session = Depends(get_db)) -> RedirectResponse:
    d = date.fromisoformat(day)
    metric = db.execute(select(DailyMetrics).where(DailyMetrics.day == d)).scalar_one_or_none()
    if metric is not None:
        db.delete(metric)
        db.commit()
    return RedirectResponse(url="/metrics", status_code=303)

