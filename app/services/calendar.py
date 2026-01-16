from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class CalendarDay:
    day: date
    in_month: bool


def month_grid(year: int, month: int) -> list[list[CalendarDay]]:
    first = date(year, month, 1)
    start = first - timedelta(days=first.weekday())  # Monday start

    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    last = next_month - timedelta(days=1)

    end = last + timedelta(days=(6 - last.weekday()))

    days: list[CalendarDay] = []
    cur = start
    while cur <= end:
        days.append(CalendarDay(day=cur, in_month=(cur.month == month)))
        cur += timedelta(days=1)

    weeks: list[list[CalendarDay]] = []
    for i in range(0, len(days), 7):
        weeks.append(days[i : i + 7])
    return weeks

