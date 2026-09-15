from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.auth import current_user
from app.database import get_session
from app.models import LeaveRequest, LeaveType, RequestStatus, Role, User
from app.templating import templates

router = APIRouter(prefix="/requests", tags=["requests"])


def _safe_redirect(next_url: str, default: str) -> RedirectResponse:
    if next_url.startswith("/") and not next_url.startswith("//"):
        return RedirectResponse(url=next_url, status_code=303)
    return RedirectResponse(url=default, status_code=303)


@router.get("")
def list_my_requests(
    request: Request,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    my_requests = session.exec(
        select(LeaveRequest)
        .where(LeaveRequest.employee_id == user.id)
        .order_by(LeaveRequest.start_date.desc())
    ).all()
    return templates.TemplateResponse(
        "requests.html",
        {"request": request, "user": user, "my_requests": my_requests},
    )


@router.get("/new")
def new_request_form(
    request: Request,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    leave_types = session.exec(select(LeaveType).where(LeaveType.is_active == True)).all()  # noqa: E712
    return templates.TemplateResponse(
        "partials/request_form.html",
        {"request": request, "user": user, "leave_types": leave_types},
    )


@router.post("")
def create_request(
    request: Request,
    leave_type_id: int = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
    note: str = Form(""),
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="Enddatum muss nach dem Startdatum liegen")

    leave_request = LeaveRequest(
        employee_id=user.id,
        leave_type_id=leave_type_id,
        start_date=start_date,
        end_date=end_date,
        note=note or None,
    )
    if user.role == Role.head_of:
        # No one above a Head of in the approval chain - their own leave is
        # confirmed immediately rather than left pending forever.
        leave_request.status = RequestStatus.approved
        leave_request.decided_by_id = user.id
    session.add(leave_request)
    session.commit()
    return RedirectResponse(url="/requests", status_code=303)


@router.post("/{request_id}/cancel")
def cancel_request(
    request_id: int,
    next: str = Form("/requests"),
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    leave_request = session.get(LeaveRequest, request_id)
    if not leave_request or leave_request.employee_id != user.id:
        raise HTTPException(status_code=404, detail="Antrag nicht gefunden")
    if leave_request.status not in (RequestStatus.pending, RequestStatus.approved):
        raise HTTPException(status_code=400, detail="Antrag kann nicht mehr storniert werden")
    if leave_request.status == RequestStatus.approved and leave_request.start_date < date.today():
        raise HTTPException(status_code=400, detail="Bereits begonnener Urlaub kann nicht storniert werden")

    leave_request.status = RequestStatus.cancelled
    leave_request.updated_at = datetime.utcnow()
    session.add(leave_request)
    session.commit()
    return _safe_redirect(next, "/requests")
