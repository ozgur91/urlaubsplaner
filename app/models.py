from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Role(str, Enum):
    employee = "employee"
    teamlead = "teamlead"
    head_of = "head_of"
    admin = "admin"


ROLE_LABELS_DE = {
    Role.employee: "Mitarbeiter:in",
    Role.teamlead: "Teamleitung",
    Role.head_of: "Abteilungsleitung",
    Role.admin: "Admin",
}


class RequestStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"  # withdrawn by the employee
    revoked = "revoked"  # retracted by an approver after approval


STATUS_LABELS_DE = {
    RequestStatus.pending: "Ausstehend",
    RequestStatus.approved: "Genehmigt",
    RequestStatus.rejected: "Abgelehnt",
    RequestStatus.cancelled: "Storniert",
    RequestStatus.revoked: "Widerrufen",
}


class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    team_lead_id: Optional[int] = Field(default=None, foreign_key="user.id")

    team_lead: Optional["User"] = Relationship(
        back_populates="led_team",
        sa_relationship_kwargs={"foreign_keys": "Team.team_lead_id"},
    )
    members: list["User"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={"foreign_keys": "User.team_id"},
    )


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    display_name: str
    job_title: Optional[str] = None
    role: Role = Field(default=Role.employee)
    microsoft_oid: Optional[str] = Field(default=None, unique=True, index=True)
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
    is_active: bool = Field(default=True)

    team: Optional[Team] = Relationship(
        back_populates="members",
        sa_relationship_kwargs={"foreign_keys": "User.team_id"},
    )
    led_team: Optional[Team] = Relationship(
        back_populates="team_lead",
        sa_relationship_kwargs={"foreign_keys": "Team.team_lead_id"},
    )
    leave_requests: list["LeaveRequest"] = Relationship(
        back_populates="employee",
        sa_relationship_kwargs={"foreign_keys": "LeaveRequest.employee_id"},
    )


class LeaveType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    is_active: bool = Field(default=True)


class LeaveRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="user.id")
    leave_type_id: int = Field(foreign_key="leavetype.id")
    start_date: date
    end_date: date
    status: RequestStatus = Field(default=RequestStatus.pending)
    note: Optional[str] = None
    decided_by_id: Optional[int] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    employee: User = Relationship(
        back_populates="leave_requests",
        sa_relationship_kwargs={"foreign_keys": "LeaveRequest.employee_id"},
    )
    leave_type: LeaveType = Relationship()
    decided_by: Optional[User] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "LeaveRequest.decided_by_id"},
    )
