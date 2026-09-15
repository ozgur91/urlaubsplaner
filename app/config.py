import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./urlaubsplaner.db")

# "local" = dev "login as" picker, no external dependency (default, for prototyping).
# "microsoft" = real Microsoft Entra ID SSO, requires the MICROSOFT_* settings below.
AUTH_MODE = os.environ.get("AUTH_MODE", "local")

MICROSOFT_CLIENT_ID = os.environ.get("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.environ.get("MICROSOFT_CLIENT_SECRET", "")
MICROSOFT_TENANT_ID = os.environ.get("MICROSOFT_TENANT_ID", "common")
MICROSOFT_REDIRECT_URI = os.environ.get(
    "MICROSOFT_REDIRECT_URI", "http://localhost:8000/auth/callback"
)

BOOTSTRAP_ADMIN_EMAIL = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "")
