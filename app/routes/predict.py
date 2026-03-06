
import logging

from fastapi import APIRouter, Request

from app.schemas import PredictRequest, PredictResponse
from app.services.classifier import classify
from app.services.explainer import generate_explanation
from app.utils.errors import InvalidPredictionError
from app.utils.logging import set_request_id

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/predict", response_model=PredictResponse)
def predict(request: Request, body: PredictRequest) -> PredictResponse:
    set_request_id()
    logger.info("Predict request received", extra={"student_text_len": len(body.student_text)})

    try:
        result = classify(body.student_text)
        explanation = None
        if body.include_explanation:
            explanation = generate_explanation(body.student_text, result["prediction"])
        result["explanation"] = explanation
        return PredictResponse(**result)
    except InvalidPredictionError as e:
        logger.warning(
            "Invalid prediction from model",
            extra={"raw_output": e.raw_output, "error_detail": e.message},
        )
        raise
