from __future__ import annotations

import secrets
from typing import Callable

from fastapi import HTTPException, Request, status

from app.config import settings

SESSION_COOKIE_NAME = "project80_session"


def verify_credentials(username: str, password: str) -> bool:
    expected_user = settings.app_basic_auth_user
    expected_pass = settings.app_basic_auth_pass

    if not expected_user or not expected_pass:
        return True

    return secrets.compare_digest(username, expected_user) and secrets.compare_digest(password, expected_pass)


def require_auth_dependency() -> Callable[[Request], None]:
    def _dep(request: Request) -> None:
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if token != "authenticated":
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/login"},
            )

    return _dep

