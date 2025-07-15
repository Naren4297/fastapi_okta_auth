from fastapi import FastAPI, Request
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, JSONResponse
import django
import os
import sys
from asgiref.sync import sync_to_async

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse




# Django ORM Setup
sys.path.append("../db_core")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db_core.settings")
django.setup()

from authusers.models import OktaUser

# Load secrets from .env or hardcode here for POC
config = Config(environ={
    "OKTA_CLIENT_ID": "0oapm5psnizm1DYd65d7",
    "OKTA_CLIENT_SECRET": "SfTBRD2xv-4U_zEXlyPjBNmAFPZGYvJzTUmRek7CbHTeHzpgeN_-ABM2jmrY5tZj",
    "OKTA_ISSUER": "https://dev-29156637.okta.com/oauth2/default"
})

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="!secret")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

oauth = OAuth(config)
oauth.register(
    name='okta',
    client_id=config("OKTA_CLIENT_ID"),
    client_secret=config("OKTA_CLIENT_SECRET"),
    server_metadata_url=f"{config('OKTA_ISSUER')}/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    user = request.session.get("user")
    if user:
        return RedirectResponse("/events")

    return templates.TemplateResponse("home.html", {"request": request})



@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.okta.authorize_redirect(request, redirect_uri)


@sync_to_async
def get_or_create_user(user_info):
    user_obj, created = OktaUser.objects.get_or_create(
        okta_id=user_info["sub"],
        defaults={
            "email": user_info["email"],
            "name": user_info.get("name", user_info["email"])
        }
    )
    if not created:
        user_obj.last_login = django.utils.timezone.now()
        user_obj.save()
    return user_obj

@app.get("/auth/callback")
async def auth(request: Request):
    token = await oauth.okta.authorize_access_token(request)
    user_info = await oauth.okta.userinfo(token=token)

    # Save both user info and id_token in session
    request.session["user"] = dict(user_info)
    request.session["id_token"] = token["id_token"]

    await get_or_create_user(user_info)

    return RedirectResponse("/events")


@app.get("/logout")
async def logout(request: Request):
    id_token = request.session.get("id_token")
    request.session.clear()

    okta_issuer = config("OKTA_ISSUER")
    post_logout_redirect = "http://localhost:8000/"
    logout_url = (
        f"{okta_issuer}/v1/logout?"
        f"id_token_hint={id_token}&"
        f"post_logout_redirect_uri={post_logout_redirect}"
    )

    return RedirectResponse(logout_url)





@app.get("/events", response_class=HTMLResponse)
async def events(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")

    # Sample event data
    event_list = [
        {"title": "Seminar on AI", "date": "2025-07-20"},
        {"title": "Company Townhall", "date": "2025-07-25"},
        {"title": "Music Competition", "date": "2025-07-30"},
        {"title": "Hackathon 2025", "date": "2025-08-10"}
    ]

    return templates.TemplateResponse("events.html", {
        "request": request,
        "user": user,
        "events": event_list
    })