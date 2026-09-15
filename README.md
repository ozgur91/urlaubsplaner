# Urlaubsplaner

Team vacation/leave scheduling for a single organization with multiple teams.
FastAPI backend, server-rendered Jinja2 + HTMX frontend (UI in German),
SQLite storage. Login is either a local "log in as" dev picker (default, no
setup needed) or real Microsoft Entra ID (Azure AD) SSO.

## Roles

- **Mitarbeiter:in (Employee)** — submit/cancel their own leave requests, view their team's calendar.
- **Teamleitung (Teamlead)** — approve/reject/revoke leave requests from the employees in the team(s) they lead.
- **Abteilungsleitung (Head of)** — approve/reject/revoke leave requests from Teamleads (and from Admins). Several people can hold this role; any of them can decide any Teamlead's request. A Head of's own request is approved by another Head of (peer review).
- **Admin** — manage users, teams, and leave types. Does not approve leave itself (an Admin's own request goes to a Head of, same as a Teamlead's).

Each Team has exactly one Teamlead (`Team.team_lead_id`). Approval routing is
based on the *requester's* role, not the approver's team membership:

| Requester's role | Approved by |
|---|---|
| Employee | The Teamlead of their team |
| Teamlead | Any Head of |
| Admin | Any Head of |
| Head of | Any other Head of |

## Local prototype (default, no Azure setup)

`AUTH_MODE=local` (the default in `.env.example`) skips Microsoft SSO
entirely. On first startup with an empty database, the app seeds demo data:
a Head of, an Admin, two teams ("Produkt", "Support") each with a Teamlead,
and a few employees. `/login` shows a "log in as" picker listing these users
— click one, no password.

```bash
py -3 -m venv .venv
.venv\Scripts\Activate.ps1       # PowerShell; or .venv\Scripts\activate on cmd
pip install -r requirements.txt
cp .env.example .env             # set SECRET_KEY to any random string
uvicorn app.main:app --reload
```

Open http://localhost:8000.

## Switching to real Microsoft SSO

Set `AUTH_MODE=microsoft` in `.env` and fill in the `MICROSOFT_*` settings:

1. Go to [portal.azure.com](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations** → **New registration**.
2. Name it (e.g. "Urlaubsplaner"), choose the supported account type for your org.
3. Under **Redirect URI**, add a **Web** platform redirect: `http://localhost:8000/auth/callback`.
4. After creation, copy the **Application (client) ID** and **Directory (tenant) ID**.
5. Go to **Certificates & secrets** → **New client secret**, copy the secret value (shown once).
6. Go to **API permissions** and ensure `openid`, `email`, `profile`, and `User.Read` (Microsoft Graph, delegated) are present — these are default/standard scopes.
7. Set `BOOTSTRAP_ADMIN_EMAIL` to your own work email so your first real login becomes Admin.

With `AUTH_MODE=microsoft`, the demo seed data is skipped and every user
starts as an Employee (except the bootstrap admin); assign roles and teams
from the **Admin** screen.

## Notes

- Public holidays (German national + Nordrhein-Westfalen) are computed at
  request time, including movable feasts (Easter-based), so no yearly data
  entry is needed.
- No leave-balance/entitlement tracking, half-day requests, notifications,
  multi-tenant support, or audit history in this MVP.
