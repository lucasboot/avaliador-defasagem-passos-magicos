"""
Rota de health check.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """Retorna status simples da API."""
    return {"status": "ok"}
