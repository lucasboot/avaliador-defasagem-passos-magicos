
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes import eval as eval_router
from app.routes import health, pages, predict
from app.utils.errors import InvalidPredictionError, invalid_prediction_handler
from app.utils.logging import set_request_id, setup_logging

setup_logging(settings.log_level)

app = FastAPI(
    title="Classificador de Risco de Defasagem Escolar",
    description="API para classificação de risco de defasagem (em_fase, moderada, severa)",
    version="1.0.0",
)


static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


app.include_router(pages.router, tags=["pages"])
app.include_router(predict.router, tags=["predict"])
app.include_router(eval_router.router, tags=["eval"])
app.include_router(health.router, tags=["health"])


app.add_exception_handler(InvalidPredictionError, invalid_prediction_handler)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    set_request_id()
    response = await call_next(request)
    return response


