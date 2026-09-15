from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.auth import require_approver
from app.database import get_session
from app.models import LeaveRequest, Role, RequestStatus, Team, User
from app.services import overlapping_team_requests
from app.templating import templates

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _safe_redirect(next_url: str, default: str) -> RedirectResponse:
    if next_url.startswith("/") and not next_url.startswith("//"):
        return RedirectResponse(url=next_url, status_code=303)
    return RedirectResponse(url=default, status_code=303)


def _led_team_ids(session: Session, user: User) -> list[int]:
    return list(session.exec(select(Team.id).where(Team.team_lead_id == user.id)))


def _can_approve(session: Session, approver: User, employee: User) -> bool:
    """Whether `approver` is allowed to decide a leave request from `employee`.

    Employees are approved by their team's team lead. Team leads and Admins
    are approved by any Head of. A Head of's own leave is auto-approved on
    submission (see requests.create_request), so it never reaches here.
    """
    if employee.id == approver.id:
        return False
    if approver.role == Role.teamlead:
        return employee.role == Role.employee and employee.team_id in _led_team_ids(session, approver)
    if approver.role == Role.head_of:
        return employee.role in (Role.teamlead, Role.admin)
    return False


def _visible_requests(session: Session, user: User, status: RequestStatus | None):
    all_requests = session.exec(
        select(LeaveRequest).order_by(LeaveRequest.start_date)
    ).all()
    visible = [r for r in all_requests if _can_approve(session, user, r.employee)]
    if status is not None:
        visible = [r for r in visible if r.status == status]
    return visible


@router.get("")
def list_pending(
    request: Request,
    user: User = Depends(require_approver),
    session: Session = Depends(get_session),
):
    pending = _visible_requests(session, user, RequestStatus.pending)
    approved = _visible_requests(session, user, RequestStatus.approved)

    overlaps: dict[int, list[LeaveRequest]] = {}
    for leave_request in pending:
        employee = leave_request.employee
        if employee.team_id is None:
            continue
        conflicts = overlapping_team_requests(
            session,
            team_id=employee.team_id,
            start_date=leave_request.start_date,
            end_date=leave_request.end_date,
            exclude_request_id=leave_request.id,
        )
        if conflicts:
            overlaps[leave_request.id] = conflicts

    return templates.TemplateResponse(
        "approvals.html",
        {
            "request": request,
            "user": user,
            "pending": pending,
            "approved": approved,
            "overlaps": overlaps,
        },
    )


def _get_request_in_scope(session: Session, user: User, request_id: int) -> LeaveRequest:
    leave_request = session.get(LeaveRequest, request_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Antrag nicht gefunden")
    if not _can_approve(session, user, leave_request.employee):
        raise HTTPException(status_code=403, detail="Nicht erlaubt")
    return leave_request


@router.post("/{request_id}/approve")
def approve(
    request_id: int,
    next: str = Form("/approvals"),
    user: User = Depends(require_approver),
    session: Session = Depends(get_session),
):
    leave_request = _get_request_in_scope(session, user, request_id)
    if leave_request.status != RequestStatus.pending:
        raise HTTPException(status_code=400, detail="Nur ausstehende Anträge können genehmigt werden")

    leave_request.status = RequestStatus.approved
    leave_request.decided_by_id = user.id
    leave_request.updated_at = datetime.utcnow()
    session.add(leave_request)
    session.commit()
    return _safe_redirect(next, "/approvals")


@router.post("/{request_id}/reject")
def reject(
    request_id: int,
    next: str = Form("/approvals"),
    user: User = Depends(require_approver),
    session: Session = Depends(get_session),
):
    leave_request = _get_request_in_scope(session, user, request_id)
    if leave_request.status != RequestStatus.pending:
        raise HTTPException(status_code=400, detail="Nur ausstehende Anträge können abgelehnt werden")

    leave_request.status = RequestStatus.rejected
    leave_request.decided_by_id = user.id
    leave_request.updated_at = datetime.utcnow()
    session.add(leave_request)
    session.commit()
    return _safe_redirect(next, "/approvals")


@router.post("/{request_id}/revoke")
def revoke(
    request_id: int,
    next: str = Form("/approvals"),
    user: User = Depends(require_approver),
    session: Session = Depends(get_session),
):
    leave_request = _get_request_in_scope(session, user, request_id)
    if leave_request.status != RequestStatus.approved:
        raise HTTPException(status_code=400, detail="Nur genehmigte Anträge können widerrufen werden")

    leave_request.status = RequestStatus.revoked
    leave_request.decided_by_id = user.id
    leave_request.updated_at = datetime.utcnow()
    session.add(leave_request)
    session.commit()
    return _safe_redirect(next, "/approvals")
