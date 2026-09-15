from fastapi.templating import Jinja2Templates

from app.models import ROLE_LABELS_DE, STATUS_LABELS_DE

templates = Jinja2Templates(directory="app/templates")
templates.env.filters["role_label"] = lambda r: ROLE_LABELS_DE.get(r, getattr(r, "value", r))
templates.env.filters["status_label"] = lambda s: STATUS_LABELS_DE.get(s, getattr(s, "value", s))
