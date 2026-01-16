from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class MealType(str, enum.Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"


class SelfRating(str, enum.Enum):
    safe = "safe"
    risk = "risk"
    danger = "danger"


class SummaryColor(str, enum.Enum):
    green = "green"
    yellow = "yellow"
    red = "red"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    settings: Mapped["UserSettings"] = relationship(back_populates="user", uselist=False)


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    height_cm: Mapped[float] = mapped_column(Float, default=170.0, nullable=False)
    goal_weight_kg: Mapped[float] = mapped_column(Float, default=80.0, nullable=False)
    last_meal_end_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="settings")


class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    day: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    fasting_glucose_mmol_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    post2h_glucose_mmol_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)

    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    bp_systolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bp_diastolic: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (Index("ix_daily_metrics_day_unique", "day", unique=True),)


class FoodLog(Base):
    __tablename__ = "food_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    eaten_at: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    meal_type: Mapped[MealType] = mapped_column(Enum(MealType), nullable=False)

    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    refined_carbs: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sugar: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    veggies_first: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    protein_enough: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    self_rating: Mapped[SelfRating] = mapped_column(Enum(SelfRating), nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    meal_end_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MedicationLog(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    dose: Mapped[str | None] = mapped_column(String(128), nullable=True)
    taken_at: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    next_reminder_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MedicationInventory(Base):
    __tablename__ = "medication_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    remaining: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class LabReport(Base):
    __tablename__ = "lab_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class LabMetric(Base):
    __tablename__ = "lab_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class DailySummary(Base):
    __tablename__ = "daily_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    day: Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)
    color: Mapped[SummaryColor] = mapped_column(Enum(SummaryColor), nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reasons: Mapped[str] = mapped_column(Text, default="", nullable=False)
    commentary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

