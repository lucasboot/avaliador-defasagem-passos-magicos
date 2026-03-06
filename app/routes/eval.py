"""
Rota de avaliação do classificador.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas import EvalResponse
from app.services.evaluator import run_evaluation

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/eval", response_model=EvalResponse)
def eval_route() -> EvalResponse:
    """
    Executa avaliação do classificador sobre o arquivo test.jsonl.
    """
    dataset_path = settings.eval_dataset_path_resolved

    if not dataset_path.exists():
        logger.error("Dataset não encontrado: %s", dataset_path)
        raise HTTPException(
            status_code=404,
            detail=f"Arquivo de dataset não encontrado: {dataset_path}",
        )

    logger.info("Iniciando avaliação em %s", dataset_path)
    result = run_evaluation(dataset_path)
    logger.info(
        "Avaliação concluída",
        extra={"total": result["total"], "accuracy": result["accuracy"]},
    )
    return EvalResponse(**result)
