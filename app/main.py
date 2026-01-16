from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.db import engine
from app.models import Base, User, UserSettings
from app.routers import auth, calendar_view, dashboard, food, medical, metrics, reports

app = FastAPI(title=settings.app_name)

def _ensure_dirs() -> None:
    Path("storage").mkdir(exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)


def _ensure_single_user() -> None:
    with Session(engine) as db:
        user = db.execute(select(User).where(User.username == "self")).scalar_one_or_none()
        if user is None:
            user = User(username="self")
            db.add(user)
            db.flush()
            db.add(
                UserSettings(user_id=user.id, height_cm=settings.user_height_cm, goal_weight_kg=settings.goal_weight_kg)
            )
            db.commit()


@app.on_event("startup")
def on_startup() -> None:
    _ensure_dirs()
    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as e:
        raise RuntimeError(
            "Database connection failed. Check DATABASE_URL (host/user/password) and MySQL grants. "
            "If you are running this app on your local PC but MySQL is on a remote server, you must "
            "grant access for this client IP or run the app on the same server as MySQL."
        ) from e
    _ensure_single_user()

_ensure_dirs()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(metrics.router)
app.include_router(food.router)
app.include_router(medical.router)
app.include_router(reports.router)
app.include_router(calendar_view.router)
