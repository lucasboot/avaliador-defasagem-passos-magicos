"""
Schemas Pydantic para contratos da API.
"""

from typing import Literal

from pydantic import BaseModel, Field

PredictionClass = Literal["em_fase", "moderada", "severa"]


class PredictRequest(BaseModel):
    """Request para o endpoint de predição."""

    student_text: str = Field(..., min_length=1, description="Texto descrevendo o aluno")
    include_explanation: bool = Field(
        default=True,
        description="Se True, gera explicação humanizada da classificação",
    )


class PredictResponse(BaseModel):
    """Response do endpoint de predição."""

    prediction: PredictionClass
    model: str
    raw_output: str
    normalized: bool
    explanation: str | None = None


class EvalResponse(BaseModel):
    """Response do endpoint de avaliação."""

    total: int
    accuracy: float
    macro_f1: float
    f1_per_class: dict[str, float]
    confusion_matrix: list[list[int]]
    errors: list[dict]
