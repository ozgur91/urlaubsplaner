from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.auth import require_admin
from app.database import get_session
from app.models import ROLE_LABELS_DE, LeaveType, Role, Team, User
from app.templating import templates

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("")
def admin_home(
    request: Request,
    user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    users = session.exec(select(User).order_by(User.display_name)).all()
    teams = session.exec(select(Team).order_by(Team.name)).all()
    leave_types = session.exec(select(LeaveType).order_by(LeaveType.name)).all()
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "teams": teams,
            "leave_types": leave_types,
            "roles": list(Role),
            "role_labels": ROLE_LABELS_DE,
        },
    )


@router.post("/teams")
def create_team(
    name: str = Form(...),
    team_lead_id: str = Form(""),
    user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    team = Team(name=name, team_lead_id=int(team_lead_id) if team_lead_id else None)
    session.add(team)
    session.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/teams/{team_id}/team-lead")
def set_team_lead(
    team_id: int,
    team_lead_id: str = Form(""),
    user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team nicht gefunden")
    team.team_lead_id = int(team_lead_id) if team_lead_id else None
    session.add(team)
    session.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/users/{user_id}/role")
def set_user_role(
    user_id: int,
    role: Role = Form(...),
    user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    target.role = role
    session.add(target)
    session.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/users/{user_id}/team")
def set_user_team(
    user_id: int,
    team_id: str = Form(""),
    user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    target.team_id = int(team_id) if team_id else None
    session.add(target)
    session.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/users/{user_id}/active")
def set_user_active(
    user_id: int,
    is_active: bool = Form(...),
    user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    if target.id == user.id and not is_active:
        raise HTTPException(status_code=400, detail="Du kannst dich nicht selbst deaktivieren")
    target.is_active = is_active
    session.add(target)
    session.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/leave-types")
def create_leave_type(
    name: str = Form(...),
    user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    existing = session.exec(select(LeaveType).where(LeaveType.name == name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Abwesenheitsart existiert bereits")
    session.add(LeaveType(name=name))
    session.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/leave-types/{leave_type_id}/active")
def set_leave_type_active(
    leave_type_id: int,
    is_active: bool = Form(...),
    user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    leave_type = session.get(LeaveType, leave_type_id)
    if not leave_type:
        raise HTTPException(status_code=404, detail="Abwesenheitsart nicht gefunden")
    leave_type.is_active = is_active
    session.add(leave_type)
    session.commit()
    return RedirectResponse(url="/admin", status_code=303)
