from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from typing import Any
import urllib.parse

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
import msal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import (
    AUTHORITY,
    CLIENT_ID,
    CLIENT_SECRET,
    DEV_AUTH_BYPASS,
    REDIRECT_URI,
    SCOPES,
    TENANT_ID,
)
from app.database import get_db
from app.errors import api_error
from app.models.sessao import Sessao
from app.models.usuario import Usuario

router = APIRouter()

FRONTEND_URL = "http://localhost:5000"
SESSION_COOKIE = "patrimonio_session"
SESSION_MAX_AGE = 60 * 60 * 8


def _build_msal_app():
    return msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY,
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def _serialize_user(usuario: Usuario) -> dict[str, Any]:
    return {
        "id": usuario.id,
        "azure_oid": usuario.azure_oid,
        "nome": usuario.nome,
        "email": usuario.email,
        "cargo": usuario.cargo,
        "filial": usuario.filial,
        "perfil": usuario.perfil,
    }


def _upsert_user(db: Session, claims: dict[str, Any]) -> Usuario:
    azure_oid = claims.get("oid", "")
    email = claims.get("preferred_username", "")
    nome = claims.get("name", email)

    usuario = db.scalar(select(Usuario).where(Usuario.azure_oid == azure_oid))

    if usuario is None:
        usuario = Usuario(
            azure_oid=azure_oid,
            nome=nome,
            email=email,
            cargo="Administrador",
            filial="Matriz",
            perfil="administrador",
            ativo=True,
        )
        db.add(usuario)
    else:
        usuario.nome = nome
        usuario.email = email
        usuario.ativo = True
        usuario.atualizado_em = _now()

    db.commit()
    db.refresh(usuario)
    return usuario


def _create_session(db: Session, usuario: Usuario) -> str:
    token = token_urlsafe(32)
    agora = _now()

    sessao = Sessao(
        token_hash=_hash_token(token),
        usuario_id=usuario.id,
        criado_em=agora,
        expira_em=agora + timedelta(seconds=SESSION_MAX_AGE),
        ultimo_acesso_em=agora,
    )

    db.add(sessao)
    db.commit()
    return token


def _remove_session(request: Request, db: Session) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return

    sessao = db.scalar(select(Sessao).where(Sessao.token_hash == _hash_token(token)))
    if sessao and sessao.revogado_em is None:
        sessao.revogado_em = _now()
        db.commit()


def _delete_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=False,
        samesite="lax",
    )


@router.post("/auth/dev-login")
def dev_login(db: Session = Depends(get_db)):
    if not DEV_AUTH_BYPASS:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            "MODO_DESENVOLVIMENTO_INATIVO",
            "O acesso de desenvolvimento não está habilitado.",
        )

    usuario = _upsert_user(
        db,
        {
            "oid": "desenvolvimento-local",
            "preferred_username": "dev@sistema.local",
            "name": "Desenvolvimento",
        },
    )
    token = _create_session(db, usuario)
    response = JSONResponse(_serialize_user(usuario))
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return response


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise api_error(
            status.HTTP_401_UNAUTHORIZED,
            "SESSAO_AUSENTE",
            "Sessão ausente.",
        )

    sessao = db.scalar(select(Sessao).where(Sessao.token_hash == _hash_token(token)))
    agora = _now()

    if not sessao or sessao.revogado_em is not None or sessao.expira_em <= agora:
        raise api_error(
            status.HTTP_401_UNAUTHORIZED,
            "SESSAO_INVALIDA",
            "Sessão inválida ou expirada.",
        )

    usuario = sessao.usuario
    if not usuario or not usuario.ativo:
        raise api_error(
            status.HTTP_401_UNAUTHORIZED,
            "USUARIO_INATIVO",
            "Usuário inativo ou não encontrado.",
        )

    sessao.ultimo_acesso_em = agora
    db.commit()

    return _serialize_user(usuario)


@router.get("/auth/login")
def login():
    app = _build_msal_app()
    auth_url = app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    return RedirectResponse(auth_url)


@router.get("/auth/callback")
def callback(
    request: Request,
    code: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
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
        mensagem = result.get("error_description", "Falha na autenticacao")
        return RedirectResponse(f"{FRONTEND_URL}/?erro={urllib.parse.quote(mensagem)}")

    claims = result.get("id_token_claims", {})
    usuario = _upsert_user(db, claims)
    token = _create_session(db, usuario)

    response = RedirectResponse(FRONTEND_URL)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
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
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    _remove_session(request, db)
    _delete_session_cookie(response)
    return {"status": "ok"}


@router.get("/auth/logout")
def logout_browser(request: Request, db: Session = Depends(get_db)):
    _remove_session(request, db)

    post_logout_redirect = urllib.parse.quote(FRONTEND_URL, safe="")
    microsoft_logout_url = (
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={post_logout_redirect}"
    )

    response = RedirectResponse(microsoft_logout_url)
    _delete_session_cookie(response)
    return response
