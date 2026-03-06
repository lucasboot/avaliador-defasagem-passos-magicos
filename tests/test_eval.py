"""
Testes para o endpoint /eval.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def temp_jsonl_file():
    """Arquivo JSONL temporário com 3 exemplos."""
    data = [
        {"input_text": "Caso 1", "label": "em_fase"},
        {"input_text": "Caso 2", "label": "moderada"},
        {"input_text": "Caso 3", "label": "severa"},
    ]
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        path = Path(f.name)

    yield path
    path.unlink(missing_ok=True)


def test_eval_retorna_estrutura_correta(mock_classify, temp_jsonl_file):
    """Verifica que /eval retorna accuracy, f1, confusion_matrix e errors."""
    def classify_side_effect(text):
        if "Caso 1" in text:
            return {"prediction": "em_fase", "raw_output": "em_fase", "normalized": True}
        if "Caso 2" in text:
            return {"prediction": "moderada", "raw_output": "moderada", "normalized": True}
        return {"prediction": "em_fase", "raw_output": "em_fase", "normalized": True}

    mock_classify.side_effect = classify_side_effect

    mock_settings = Mock()
    mock_settings.eval_dataset_path_resolved = temp_jsonl_file

    with patch("app.routes.eval.settings", mock_settings):
        response = client.post("/eval")

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "accuracy" in data
    assert "macro_f1" in data
    assert "f1_per_class" in data
    assert "confusion_matrix" in data
    assert "errors" in data
    assert data["total"] == 3
    assert isinstance(data["accuracy"], (int, float))
    assert isinstance(data["errors"], list)


def test_eval_dataset_nao_encontrado_retorna_404():
    """Verifica que 404 é retornado quando o dataset não existe."""
    mock_settings = Mock()
    mock_settings.eval_dataset_path_resolved = Path("/caminho/inexistente/arquivo.jsonl")

    with patch("app.routes.eval.settings", mock_settings):
        response = client.post("/eval")

    assert response.status_code == 404
