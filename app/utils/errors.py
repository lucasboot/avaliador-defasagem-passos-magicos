
from fastapi import Request, status
from fastapi.responses import JSONResponse


class InvalidPredictionError(Exception):

    def __init__(self, message: str, raw_output: str | None = None):
        self.message = message
        self.raw_output = raw_output
        super().__init__(message)


async def invalid_prediction_handler(
    request: Request, exc: InvalidPredictionError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.message,
            "raw_output": exc.raw_output,
        },
    )
