
import logging

from app.config import settings
from app.services.normalizer import normalize_prediction
from app.services.openai_client import complete

logger = logging.getLogger(__name__)


def classify(student_text: str) -> dict:
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
