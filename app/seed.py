from sqlmodel import Session, select

from app.models import LeaveType, Role, Team, User


def seed_demo_data(session: Session) -> None:
    """Create a small set of demo users/teams/leave types for local prototyping.

    Only runs once (skipped if any user already exists), so it's safe to call
    on every startup.
    """
    if session.exec(select(User)).first():
        return

    head_of = User(
        email="head@example.com",
        display_name="Hannah Head",
        job_title="Abteilungsleitung",
        role=Role.head_of,
    )
    admin = User(
        email="admin@example.com",
        display_name="Alex Admin",
        job_title="Systemadministration",
        role=Role.admin,
    )
    session.add(head_of)
    session.add(admin)
    session.commit()

    product = Team(name="Produkt")
    support = Team(name="Support")
    session.add(product)
    session.add(support)
    session.commit()
    session.refresh(product)
    session.refresh(support)

    product_lead = User(
        email="teamlead.produkt@example.com",
        display_name="Tom Teamleiter",
        job_title="Teamleitung Produkt",
        role=Role.teamlead,
        team_id=product.id,
    )
    support_lead = User(
        email="teamlead.support@example.com",
        display_name="Sara Teamleiterin",
        job_title="Teamleitung Support",
        role=Role.teamlead,
        team_id=support.id,
    )
    session.add(product_lead)
    session.add(support_lead)
    session.commit()
    session.refresh(product_lead)
    session.refresh(support_lead)

    product.team_lead_id = product_lead.id
    support.team_lead_id = support_lead.id
    session.add(product)
    session.add(support)

    session.add(
        User(
            email="erik@example.com",
            display_name="Erik Mitarbeiter",
            job_title="Software Engineer",
            role=Role.employee,
            team_id=product.id,
        )
    )
    session.add(
        User(
            email="emma@example.com",
            display_name="Emma Mitarbeiterin",
            job_title="Product Designer",
            role=Role.employee,
            team_id=product.id,
        )
    )
    session.add(
        User(
            email="finn@example.com",
            display_name="Finn Mitarbeiter",
            job_title="Support Specialist",
            role=Role.employee,
            team_id=support.id,
        )
    )

    for name in ("Urlaub", "Krankheit", "Unbezahlt"):
        session.add(LeaveType(name=name))

    session.commit()
