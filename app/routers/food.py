from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import FoodLog, MealType, SelfRating, User, UserSettings
from app.security import require_auth_dependency as basic_auth_dependency
from app.services.rules import fasting_hours_since

router = APIRouter(dependencies=[Depends(basic_auth_dependency())])
templates = Jinja2Templates(directory="app/templates")


def _safe_ext(filename: str) -> str:
    lower = filename.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if lower.endswith(ext):
            return ext
    return ""


def _default_meal_type(dt: datetime) -> MealType:
    hhmm = dt.hour * 60 + dt.minute
    if 5 * 60 <= hhmm < 11 * 60:
        return MealType.breakfast
    if 11 * 60 <= hhmm < 16 * 60:
        return MealType.lunch
    return MealType.dinner


@router.get("/food/new", response_class=HTMLResponse)
def new_food(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    user = db.execute(select(User).where(User.username == "self")).scalar_one()
    user_settings = db.execute(select(UserSettings).where(UserSettings.user_id == user.id)).scalar_one()
    now = datetime.now()
    fasting_hours = fasting_hours_since(user_settings.last_meal_end_at, now)
    return templates.TemplateResponse(
        "food_new.html",
        {
            "request": request,
            "now_iso": now.strftime("%Y-%m-%dT%H:%M"),
            "fasting_hours": fasting_hours,
            "fasting_warning": (fasting_hours is not None and fasting_hours < 16.0),
            "selected_meal_type": _default_meal_type(now).value,
            "error": None,
        },
    )


@router.post("/food/new", response_model=None)
async def create_food(
    request: Request,
    eaten_at: str = Form(...),
    meal_type: MealType = Form(...),
    refined_carbs: bool = Form(False),
    sugar: bool = Form(False),
    veggies_first: bool = Form(False),
    protein_enough: bool = Form(False),
    self_rating: SelfRating = Form(...),
    notes: str | None = Form(None),
    meal_end_at: str | None = Form(None),
    override_fasting_warning: bool = Form(False),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    user = db.execute(select(User).where(User.username == "self")).scalar_one()
    user_settings = db.execute(select(UserSettings).where(UserSettings.user_id == user.id)).scalar_one()

    now = datetime.now()
    fasting_hours = fasting_hours_since(user_settings.last_meal_end_at, now)
    fasting_warning = fasting_hours is not None and fasting_hours < 16.0
    if fasting_warning and not override_fasting_warning:
        return templates.TemplateResponse(
            "food_new.html",
            {
                "request": request,
                "now_iso": eaten_at,
                "fasting_hours": fasting_hours,
                "fasting_warning": True,
                "selected_meal_type": meal_type.value,
                "error": "未达到 16 小时禁食窗口：勾选“仍要记录本次进食”才能提交。",
            },
            status_code=400,
        )

    image_rel = None
    if photo and photo.filename:
        ext = _safe_ext(photo.filename)
        if not ext:
            return templates.TemplateResponse(
                "food_new.html",
                {
                    "request": request,
                    "now_iso": eaten_at,
                    "fasting_hours": fasting_hours,
                    "fasting_warning": fasting_warning,
                    "selected_meal_type": meal_type.value,
                    "error": "仅支持 jpg/jpeg/png/webp 图片。",
                },
                status_code=400,
            )

        content = await photo.read()
        if len(content) > settings.max_upload_mb * 1024 * 1024:
            return templates.TemplateResponse(
                "food_new.html",
                {
                    "request": request,
                    "now_iso": eaten_at,
                    "fasting_hours": fasting_hours,
                    "fasting_warning": fasting_warning,
                    "selected_meal_type": meal_type.value,
                    "error": f"图片过大（>{settings.max_upload_mb}MB）。",
                },
                status_code=400,
            )

        day_folder = settings.upload_dir / now.strftime("%Y%m%d")
        day_folder.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}{ext}"
        path = day_folder / filename
        path.write_bytes(content)
        image_rel = str(Path(day_folder.name) / filename).replace("\\", "/")

    eaten_dt = datetime.fromisoformat(eaten_at)
    meal_end_dt = datetime.fromisoformat(meal_end_at) if meal_end_at else None

    log = FoodLog(
        eaten_at=eaten_dt,
        meal_type=meal_type,
        image_path=image_rel,
        refined_carbs=refined_carbs,
        sugar=sugar,
        veggies_first=veggies_first,
        protein_enough=protein_enough,
        self_rating=self_rating,
        notes=notes,
        meal_end_at=meal_end_dt,
    )
    db.add(log)

    if meal_end_dt is not None:
        user_settings.last_meal_end_at = meal_end_dt

    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

