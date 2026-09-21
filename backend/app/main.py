from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import get_current_user, router as auth_router

app = FastAPI(title="Sistema Patrimonial API")

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


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/patrimonio/resumo")
def get_patrimonio_resumo(user=Depends(get_current_user)):
    return {
        "usuario": user["email"],
        "indicadores": {
            "bensCadastrados": 0,
            "veiculosCadastrados": 0,
            "auditoriasPendentes": 0,
            "eventosRegistrados": 0,
        },
    }


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
