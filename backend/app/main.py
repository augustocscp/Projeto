from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth import get_current_user, router as auth_router
from app.config import AUTO_CREATE_DATABASE_OBJECTS
from app.database import create_database_objects
from app.routers.cadastros_patrimoniais import router as cadastros_router
from app.routers.integracoes import router as integracoes_router
from app.routers.patrimonio import router as patrimonio_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    if AUTO_CREATE_DATABASE_OBJECTS:
        create_database_objects()
    yield


app = FastAPI(title="Sistema Patrimonial API", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    campos = [str(erro["loc"][-1]) for erro in exc.errors() if erro.get("loc")]
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "codigo": "DADOS_INVALIDOS",
                "mensagem": "Os dados informados são inválidos.",
                "campos": campos,
            }
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(patrimonio_router)
app.include_router(cadastros_router)
app.include_router(integracoes_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/cadastro-geral")
def list_cadastro_geral(user=Depends(get_current_user)):
    return {"usuario": user["email"], "itens": []}


@app.get("/api/cadastro-veicular")
def list_cadastro_veicular(user=Depends(get_current_user)):
    return {"usuario": user["email"], "veiculos": []}


@app.get("/api/auditoria")
def list_auditorias(user=Depends(get_current_user)):
    return {"usuario": user["email"], "auditorias": []}


@app.get("/api/logs")
def list_logs(user=Depends(get_current_user)):
    return {"usuario": user["email"], "logs": []}
