from fastapi import FastAPI, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import AUTH_MODE, SECRET_KEY
from app.database import get_session, init_db
from app.routers import admin, approvals, calendar, requests
from app.seed import seed_demo_data
from app.templating import templates

app = FastAPI(title="Urlaubsplaner")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

if AUTH_MODE == "microsoft":
    from app.routers import auth

    app.include_router(auth.router)
else:
    from app.routers import dev_auth

    app.include_router(dev_auth.router)

app.include_router(calendar.router)
app.include_router(requests.router)
app.include_router(approvals.router)
app.include_router(admin.router)


@app.exception_handler(StarletteHTTPException)
async def auth_redirect_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url="/login")
    return await http_exception_handler(request, exc)


@app.get("/login")
def login_page(request: Request):
    if AUTH_MODE != "microsoft":
        return RedirectResponse(url="/auth/dev-login")
    return templates.TemplateResponse("login.html", {"request": request})


@app.on_event("startup")
def on_startup():
    init_db()
    if AUTH_MODE != "microsoft":
        session = next(get_session())
        seed_demo_data(session)
