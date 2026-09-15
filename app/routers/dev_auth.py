"""Dev-only 'login as' picker, used when AUTH_MODE=local. No password, no
external dependency - for prototyping before Microsoft SSO is wired up.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config import AUTH_MODE
from app.database import get_session
from app.models import User
from app.templating import templates

router = APIRouter(prefix="/auth", tags=["dev-auth"])


def _require_local_mode():
    if AUTH_MODE != "local":
        raise HTTPException(status_code=404)


@router.get("/dev-login")
def dev_login_page(request: Request, session: Session = Depends(get_session)):
    _require_local_mode()
    users = session.exec(select(User).where(User.is_active == True).order_by(User.display_name)).all()  # noqa: E712
    return templates.TemplateResponse(
        "dev_login.html", {"request": request, "users": users}
    )


@router.post("/dev-login/{user_id}")
def dev_login(request: Request, user_id: int, session: Session = Depends(get_session)):
    _require_local_mode()
    user = session.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")
