"""
Configuração de fixtures para testes.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Cliente de teste FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_openai_response():
    """Retorna uma função que simula resposta da OpenAI."""

    def _make(content: str):
        class Choice:
            class Message:
                content = content

            message = Message()
            message.content = content

        class Response:
            choices = [Choice()]

        return Response()

    return _make


@pytest.fixture
def mock_classify():
    """Patch do classify no evaluator (onde é usado) para retornar valores controlados."""
    with patch("app.services.evaluator.classify") as m:
        yield m


@pytest.fixture
def mock_openai_complete():
    """Patch do complete no classifier (onde é usado) para retornar valores controlados."""
    with patch("app.services.classifier.complete") as m:
        yield m


@pytest.fixture
def mock_explainer():
    """Patch do generate_explanation na rota predict."""
    with patch("app.routes.predict.generate_explanation") as m:
        yield m


@pytest.fixture
def temp_test_jsonl():
    """Cria arquivo JSONL temporário para testes de eval."""
    data = [
        {"input_text": "Caso aluno 1", "label": "em_fase"},
        {"input_text": "Caso aluno 2", "label": "moderada"},
        {"input_text": "Caso aluno 3", "label": "severa"},
    ]
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        path = f.name

    yield path
    Path(path).unlink(missing_ok=True)
