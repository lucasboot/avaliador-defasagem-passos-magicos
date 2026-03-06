"""
Exceções de domínio e helpers para tratamento de erros.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse


class InvalidPredictionError(Exception):
    """Exceção lançada quando a resposta do modelo não pode ser normalizada."""

    def __init__(self, message: str, raw_output: str | None = None):
        self.message = message
        self.raw_output = raw_output
        super().__init__(message)


async def invalid_prediction_handler(
    request: Request, exc: InvalidPredictionError
) -> JSONResponse:
    """Converte InvalidPredictionError em resposta HTTP 422."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.message,
            "raw_output": exc.raw_output,
        },
    )
