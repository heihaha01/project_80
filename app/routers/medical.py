from __future__ import annotations

import uuid
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import LabMetric, LabReport, MedicationInventory, MedicationLog
from app.security import require_auth_dependency as basic_auth_dependency


router = APIRouter(dependencies=[Depends(basic_auth_dependency())])
templates = Jinja2Templates(directory="app/templates")


def _safe_ext(filename: str) -> str:
    lower = filename.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".pdf"):
        if lower.endswith(ext):
            return ext
    return ""


@router.get("/medical", response_class=HTMLResponse)
def medical_home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    meds = db.execute(select(MedicationLog).order_by(MedicationLog.taken_at.desc()).limit(50)).scalars().all()
    inventory = db.execute(select(MedicationInventory).order_by(MedicationInventory.name.asc())).scalars().all()
    lab_metrics = db.execute(select(LabMetric).order_by(LabMetric.metric_date.desc()).limit(50)).scalars().all()
    reports = db.execute(select(LabReport).order_by(LabReport.created_at.desc()).limit(20)).scalars().all()
    return templates.TemplateResponse(
        "medical.html",
        {
            "request": request,
            "today": date.today().isoformat(),
            "now_iso": datetime.now().strftime("%Y-%m-%dT%H:%M"),
            "meds": meds,
            "inventory": inventory,
            "lab_metrics": lab_metrics,
            "reports": reports,
        },
    )


@router.post("/medical/medication")
def add_medication(
    name: str = Form(...),
    dose: str | None = Form(None),
    taken_at: str = Form(...),
    next_reminder_at: str | None = Form(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    taken_dt = datetime.fromisoformat(taken_at)
    reminder_dt = datetime.fromisoformat(next_reminder_at) if next_reminder_at else None
    db.add(MedicationLog(name=name, dose=dose, taken_at=taken_dt, next_reminder_at=reminder_dt))
    db.commit()
    return RedirectResponse(url="/medical", status_code=303)


@router.post("/medical/inventory")
def set_inventory(name: str = Form(...), remaining: int = Form(...), db: Session = Depends(get_db)) -> RedirectResponse:
    item = db.execute(select(MedicationInventory).where(MedicationInventory.name == name)).scalar_one_or_none()
    if item is None:
        item = MedicationInventory(name=name, remaining=remaining)
        db.add(item)
    else:
        item.remaining = remaining
    db.commit()
    return RedirectResponse(url="/medical", status_code=303)


@router.post("/medical/lab-metric")
def add_lab_metric(
    metric_date: str = Form(...),
    name: str = Form(...),
    value: float = Form(...),
    unit: str | None = Form(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    d = date.fromisoformat(metric_date)
    db.add(LabMetric(metric_date=d, name=name, value=value, unit=unit))
    db.commit()
    return RedirectResponse(url="/medical", status_code=303)


@router.post("/medical/report")
async def add_lab_report(
    report_date: str | None = Form(None),
    notes: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    image_rel = None
    if file and file.filename:
        ext = _safe_ext(file.filename)
        if ext:
            content = await file.read()
            if len(content) <= settings.max_upload_mb * 1024 * 1024:
                folder = settings.upload_dir / "reports"
                folder.mkdir(parents=True, exist_ok=True)
                filename = f"{uuid.uuid4().hex}{ext}"
                path = folder / filename
                path.write_bytes(content)
                image_rel = str(Path(folder.name) / filename).replace("\\", "/")

    d = date.fromisoformat(report_date) if report_date else None
    db.add(LabReport(report_date=d, image_path=image_rel, notes=notes))
    db.commit()
    return RedirectResponse(url="/medical", status_code=303)

