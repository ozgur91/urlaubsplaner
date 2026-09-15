import calendar as pycalendar
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, select

from app.auth import current_user
from app.database import get_session
from app.holidays import holidays_in_range
from app.i18n import month_label, weekday_label
from app.models import LeaveRequest, LeaveType, Role, RequestStatus, Team, User
from app.routers.approvals import _can_approve
from app.templating import templates

router = APIRouter(tags=["calendar"])

LEAVE_TYPE_PALETTE_SIZE = 4


@router.get("/")
def dashboard(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    team_id: int | None = None,
    day: str | None = None,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    today = date.today()
    year = year or today.year
    month = month or today.month

    first_day = date(year, month, 1)
    last_day = date(year, month, pycalendar.monthrange(year, month)[1])

    weeks = pycalendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
    grid_start, grid_end = weeks[0][0], weeks[-1][-1]

    if user.role in (Role.admin, Role.head_of):
        teams = session.exec(select(Team)).all()
    elif user.role == Role.teamlead:
        teams = session.exec(select(Team).where(Team.team_lead_id == user.id)).all()
        if user.team and user.team_id not in [t.id for t in teams]:
            teams.append(user.team)
    else:
        teams = [user.team] if user.team else []

    visible_ids = [t.id for t in teams]
    if team_id is not None and team_id in visible_ids:
        active_team_id = team_id
    else:
        active_team_id = user.team_id if user.team_id in visible_ids else (visible_ids[0] if visible_ids else None)

    members: list[User] = []
    if active_team_id is not None:
        members = session.exec(
            select(User).where(User.team_id == active_team_id).order_by(User.display_name)
        ).all()

    member_ids = [m.id for m in members]
    visible_requests: list[LeaveRequest] = []
    if member_ids:
        visible_requests = session.exec(
            select(LeaveRequest)
            .where(LeaveRequest.employee_id.in_(member_ids))
            .where(LeaveRequest.status.in_((RequestStatus.approved, RequestStatus.pending)))
            .where(LeaveRequest.start_date <= grid_end)
            .where(LeaveRequest.end_date >= grid_start)
        ).all()

    entries_by_date: dict[date, list[LeaveRequest]] = {}
    for leave_request in visible_requests:
        d = max(leave_request.start_date, grid_start)
        end = min(leave_request.end_date, grid_end)
        while d <= end:
            entries_by_date.setdefault(d, []).append(leave_request)
            d += timedelta(days=1)
    for entries in entries_by_date.values():
        entries.sort(key=lambda r: r.employee.display_name)

    leave_types = session.exec(select(LeaveType).order_by(LeaveType.id)).all()
    color_by_leave_type = {lt.id: i % LEAVE_TYPE_PALETTE_SIZE for i, lt in enumerate(leave_types)}

    holiday_dates = {h.date for h in holidays_in_range(grid_start, grid_end)}

    prev_month_date = (first_day - timedelta(days=1)).replace(day=1)
    next_month_date = last_day + timedelta(days=1)

    if day:
        try:
            selected_date = date.fromisoformat(day)
        except ValueError:
            selected_date = today
        if not (grid_start <= selected_date <= grid_end):
            selected_date = today
    elif grid_start <= today <= grid_end:
        selected_date = today
    else:
        selected_date = first_day

    week_cells = [
        [
            {
                "date": d,
                "in_month": d.month == month,
                "is_today": d == today,
                "is_weekend": d.weekday() >= 5,
                "is_holiday": d in holiday_dates,
                "is_selected": d == selected_date,
                "entries": entries_by_date.get(d, []),
            }
            for d in week
        ]
        for week in weeks
    ]

    selected_entries = entries_by_date.get(selected_date, [])
    decidable_ids = {
        r.id
        for r in selected_entries
        if r.status == RequestStatus.pending and _can_approve(session, user, r.employee)
    }
    cancellable_ids = {
        r.id
        for r in selected_entries
        if r.employee_id == user.id
        and r.status in (RequestStatus.pending, RequestStatus.approved)
        and not (r.status == RequestStatus.approved and r.start_date < today)
    }

    month_start = first_day if first_day > grid_start else grid_start
    month_end = last_day if last_day < grid_end else grid_end
    stats = {
        "members": len(members),
        "approved_this_month": sum(
            1
            for r in visible_requests
            if r.status == RequestStatus.approved and r.start_date <= month_end and r.end_date >= month_start
        ),
        "pending_this_month": sum(
            1
            for r in visible_requests
            if r.status == RequestStatus.pending and r.start_date <= month_end and r.end_date >= month_start
        ),
    }

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "teams": teams,
            "active_team_id": active_team_id,
            "members": members,
            "weeks": week_cells,
            "weekday_labels": [weekday_label(i) for i in range(7)],
            "color_by_leave_type": color_by_leave_type,
            "year": year,
            "month": month,
            "month_name": month_label(year, month),
            "prev_year": prev_month_date.year,
            "prev_month": prev_month_date.month,
            "next_year": next_month_date.year,
            "next_month": next_month_date.month,
            "today": today,
            "selected_date": selected_date,
            "selected_entries": selected_entries,
            "decidable_ids": decidable_ids,
            "cancellable_ids": cancellable_ids,
            "stats": stats,
        },
    )
