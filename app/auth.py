from typing import Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session, select

from app.config import (
    MICROSOFT_CLIENT_ID,
    MICROSOFT_CLIENT_SECRET,
    MICROSOFT_REDIRECT_URI,
    MICROSOFT_TENANT_ID,
)
from app.database import get_session
from app.models import Role, User

oauth = OAuth()
oauth.register(
    name="microsoft",
    client_id=MICROSOFT_CLIENT_ID,
    client_secret=MICROSOFT_CLIENT_SECRET,
    server_metadata_url=(
        f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}"
        "/v2.0/.well-known/openid-configuration"
    ),
    client_kwargs={"scope": "openid email profile User.Read"},
)


def current_user(
    request: Request, session: Session = Depends(get_session)
) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nicht angemeldet")
    user = session.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nicht angemeldet")
    return user


def current_user_optional(
    request: Request, session: Session = Depends(get_session)
) -> Optional[User]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = session.get(User, user_id)
    if user and user.is_active:
        return user
    return None


def require_role(*roles: Role):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nicht erlaubt")
        return user

    return dependency


require_teamlead = require_role(Role.teamlead)
require_head_of = require_role(Role.head_of)
require_approver = require_role(Role.teamlead, Role.head_of)
require_admin = require_role(Role.admin)


def find_or_create_user(session: Session, *, oid: str, email: str, display_name: str) -> User:
    from app.config import BOOTSTRAP_ADMIN_EMAIL

    user = session.exec(select(User).where(User.microsoft_oid == oid)).first()
    if user:
        return user

    user = session.exec(select(User).where(User.email == email)).first()
    if user:
        user.microsoft_oid = oid
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    role = Role.employee
    if BOOTSTRAP_ADMIN_EMAIL and email.lower() == BOOTSTRAP_ADMIN_EMAIL.lower():
        role = Role.admin

    user = User(
        email=email,
        display_name=display_name,
        microsoft_oid=oid,
        role=role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
