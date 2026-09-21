from secrets import token_urlsafe
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
import msal
import urllib.parse

from app.config import (
    CLIENT_ID,
    CLIENT_SECRET,
    AUTHORITY,
    REDIRECT_URI,
    SCOPES,
    TENANT_ID,
)

router = APIRouter()

FRONTEND_URL = "http://localhost:5000"
SESSION_COOKIE = "patrimonio_session"
SESSION_MAX_AGE = 60 * 60 * 8

_sessions: dict[str, dict[str, Any]] = {}


def _build_msal_app():
    return msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY,
    )


def _create_session(user: dict[str, Any]) -> str:
    session_id = token_urlsafe(32)
    _sessions[session_id] = user
    return session_id


def _remove_session(request: Request) -> None:
    session_id = request.cookies.get(SESSION_COOKIE)
    if session_id:
        _sessions.pop(session_id, None)


def _delete_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=False,
        samesite="lax",
    )


def get_current_user(request: Request) -> dict[str, Any]:
    session_id = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão ausente",
        )

    user = _sessions.get(session_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada",
        )

    return user


@router.get("/auth/login")
def login():
    app = _build_msal_app()
    auth_url = app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    return RedirectResponse(auth_url)


@router.get("/auth/callback")
def callback(request: Request, code: str | None = None, error: str | None = None):
    if error:
        return RedirectResponse(f"{FRONTEND_URL}/?erro={urllib.parse.quote(error)}")

    if not code:
        return RedirectResponse(f"{FRONTEND_URL}/?erro=codigo_ausente")

    app = _build_msal_app()
    result = app.acquire_token_by_authorization_code(
        code=code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    if "error" in result:
        mensagem = result.get("error_description", "Falha na autenticação")
        return RedirectResponse(f"{FRONTEND_URL}/?erro={urllib.parse.quote(mensagem)}")

    usuario = result.get("id_token_claims", {})
    session_id = _create_session(
        {
            "id": usuario.get("oid", ""),
            "nome": usuario.get("name", ""),
            "email": usuario.get("preferred_username", ""),
            "cargo": "Administrador",
            "filial": "Matriz",
        }
    )

    response = RedirectResponse(FRONTEND_URL)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return response


@router.get("/auth/me")
def me(user: dict[str, Any] = Depends(get_current_user)):
    return user


@router.post("/auth/logout")
def logout(request: Request, response: Response):
    _remove_session(request)
    _delete_session_cookie(response)
    return {"status": "ok"}


@router.get("/auth/logout")
def logout_browser(request: Request):
    _remove_session(request)

    post_logout_redirect = urllib.parse.quote(FRONTEND_URL, safe="")
    microsoft_logout_url = (
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={post_logout_redirect}"
    )

    response = RedirectResponse(microsoft_logout_url)
    _delete_session_cookie(response)
    return response
