<!--
Sync Impact Report
- Version change: (template, unratified) → 1.0.0
- Modified principles: n/a (initial ratification, no prior named principles)
- Added sections:
  - Core Principles: I. Server-Rendered Simplicity, II. German-Only User Interface,
    III. Minimal, Justified Scope (YAGNI), IV. Role-Based Approval Chain Integrity,
    V. Explicit, Verified Changes
  - Technology & Data Constraints
  - Development Workflow
  - Governance
- Removed sections: none (first fill-in of the scaffold)
- Deferred / TODO items:
  - No automated CI enforcement of these principles exists yet; compliance is
    presently self-reviewed per change (see Governance).
-->

# Urlaubsplaner Constitution

## Core Principles

### I. Server-Rendered Simplicity
The application MUST be built as a single FastAPI process rendering Jinja2
templates enhanced with HTMX. A separate single-page-app frontend, JS build
pipeline, or client-side framework MUST NOT be introduced unless a future
amendment explicitly justifies and scopes it.
Rationale: this is a small internal tool for one company; a single deployable
Python process with no JS toolchain keeps it cheap to run, deploy, and hand
off, and HTMX already covers the interactivity the app needs.

### II. German-Only User Interface
All user-facing text — templates, form labels, validation and error
messages, status labels — MUST be in German. Internal identifiers (Python
names, route paths, database columns) remain in English for maintainability.
Rationale: the app is built for the staff of a German company; a mixed-
language UI creates confusion for its actual users.

### III. Minimal, Justified Scope (YAGNI)
Features MUST NOT be added beyond what is explicitly requested or defined in
an approved spec. Speculative abstractions, unused configuration flags,
backward-compatibility shims for code that has no external consumers yet,
and "just in case" fields MUST NOT be added. When a requirement is unclear,
ask rather than guess-and-build.
Rationale: this is an MVP for a single department; every unrequested feature
is scope that has to be maintained, explained, and kept in sync with the
approval/role model for no confirmed benefit.

### IV. Role-Based Approval Chain Integrity
The leave-approval hierarchy is a core business rule and MUST be enforced in
code, not only reflected in the UI:
- An Employee's request is approved by their team's Teamlead.
- A Teamlead's or Admin's request is approved by any Head of.
- A Head of's request is auto-approved on submission (no role sits above
  Head of in the chain).
- Admin manages users, teams, and leave types but does not approve leave.
Any change to who may decide whose request MUST be made in
`app/routers/approvals.py` (`_can_approve` and related helpers) and MUST be
re-verified end-to-end (see Principle V) before being considered done.
Rationale: this hierarchy is the reason the app exists; silent drift here
(e.g. a role seeing or deciding requests it should not) breaks trust in the
whole system.

### V. Explicit, Verified Changes
A change MUST be verified by actually running the application — starting the
server and exercising the affected flow (e.g. via the local "login as"
picker and curl/browser) — before it is reported complete. Reading the code
or relying on it "looking correct" is not sufficient.
Rationale: the project has no automated test suite yet, so manual,
end-to-end verification is the only safety net against regressions.

## Technology & Data Constraints

- Backend: Python (3.13 in development) with FastAPI and SQLModel
  (SQLAlchemy) as the ORM.
- Frontend: Jinja2 server-rendered templates plus HTMX; no React/Vue/Svelte
  and no frontend build step.
- Database: SQLite by default (`DATABASE_URL` is environment-configurable).
  Moving to PostgreSQL or another engine is a deliberate, separately-scoped
  decision, not a default assumption.
- Authentication: controlled by the `AUTH_MODE` environment variable —
  `local` (a password-less "log in as" picker over seeded demo users, the
  default for prototyping) or `microsoft` (Microsoft Entra ID OAuth via
  Authlib). Real deployments MUST use `AUTH_MODE=microsoft`.
- German public holidays (national + Nordrhein-Westfalen) MUST be computed
  algorithmically (including Easter-based movable feasts), never hardcoded
  per calendar year.
- The application models a single organization; multi-tenant data isolation
  is explicitly out of scope.

## Development Workflow

- Windows with PowerShell is the primary developer environment; setup and
  operational instructions (README, scripts) MUST work from PowerShell, not
  assume a POSIX shell only.
- Git commits are created only when the user explicitly asks for one; work
  is not committed proactively.
- No automated test suite exists yet. Until one is introduced, every
  behavioral change MUST be manually verified end-to-end (Principle V)
  before being reported as done.

## Governance

This constitution supersedes ad hoc conventions and prior informal practice
for this project; where they conflict, this document governs. Amendments are
made via the `/speckit-constitution` command, MUST include a Sync Impact
Report as an HTML comment at the top of the amended file, and MUST follow
semantic versioning for the constitution itself (MAJOR: incompatible
principle removal/redefinition; MINOR: new principle or materially expanded
guidance; PATCH: clarification or wording fix). Compliance is currently
self-reviewed at each significant change, since no CI pipeline enforces it
yet; adding such enforcement is a valid future amendment. Use `README.md`
for concrete setup and runtime guidance that supports these principles.

**Version**: 1.0.0 | **Ratified**: 2026-09-16 | **Last Amended**: 2026-09-16
