"""
Classificador de risco de defasagem escolar.
"""

import logging

from app.config import settings
from app.services.normalizer import normalize_prediction
from app.services.openai_client import complete

logger = logging.getLogger(__name__)


def classify(student_text: str) -> dict:
    """
    Classifica o risco de defasagem escolar a partir do texto descritivo do aluno.

    Chama o modelo fine-tuned da OpenAI e normaliza a resposta para uma das
    3 classes válidas: em_fase, moderada, severa.

    Args:
        student_text: Texto descrevendo o aluno em linguagem natural.

    Returns:
        Dict com prediction, raw_output, normalized e model.
    """
    raw_output = complete(student_text)
    prediction = normalize_prediction(raw_output)

    result = {
        "prediction": prediction,
        "model": settings.openai_model,
        "raw_output": raw_output,
        "normalized": True,
    }

    logger.info(
        "Classification completed",
        extra={"prediction": prediction, "raw_preview": raw_output[:50]},
    )
    return result
