from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.auth import find_or_create_user, oauth
from app.database import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request):
    return await oauth.microsoft.authorize_redirect(request, request.url_for("auth_callback"))


@router.get("/callback", name="auth_callback")
async def auth_callback(request: Request, session: Session = Depends(get_session)):
    token = await oauth.microsoft.authorize_access_token(request)
    claims = token.get("userinfo") or {}

    oid = claims.get("oid") or claims.get("sub")
    email = claims.get("email") or claims.get("preferred_username")
    display_name = claims.get("name") or email

    user = find_or_create_user(session, oid=oid, email=email, display_name=display_name)

    request.session["user_id"] = user.id
    return RedirectResponse(url="/")


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")
