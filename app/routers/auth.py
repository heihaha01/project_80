from __future__ import annotations

from fastapi import APIRouter, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.security import SESSION_COOKIE_NAME, verify_credentials

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": "Login"})

@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    if verify_credentials(username, password):
        # Successful login
        # Allow redirect to dashboard
        resp = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
        resp.set_cookie(
            key=SESSION_COOKIE_NAME,
            value="authenticated",
            httponly=True,
            max_age=60 * 60 * 24 * 7, # 7 days
            samesite="lax"
        )
        return resp
    else:
        return templates.TemplateResponse(
            "login.html", 
            {
                "request": request, 
                "title": "Login",
                "error": "Invalid username or password"
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )

@router.get("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie(SESSION_COOKIE_NAME)
    return resp
