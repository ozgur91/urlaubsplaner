from datetime import date

from sqlmodel import Session, select

from app.models import LeaveRequest, RequestStatus, User


def overlapping_team_requests(
    session: Session,
    *,
    team_id: int,
    start_date: date,
    end_date: date,
    exclude_request_id: int | None = None,
) -> list[LeaveRequest]:
    """Approved requests from the same team whose date range overlaps the given range."""
    statement = (
        select(LeaveRequest)
        .join(User, LeaveRequest.employee_id == User.id)
        .where(User.team_id == team_id)
        .where(LeaveRequest.status == RequestStatus.approved)
        .where(LeaveRequest.start_date <= end_date)
        .where(LeaveRequest.end_date >= start_date)
    )
    if exclude_request_id is not None:
        statement = statement.where(LeaveRequest.id != exclude_request_id)
    return list(session.exec(statement))
