"""
Testes para o endpoint /predict.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestPredictSuccess:
    """Testes de sucesso do /predict."""

    def test_predict_retorna_json_correto(self, mock_openai_complete):
        mock_openai_complete.return_value = "moderada"

        response = client.post(
            "/predict",
            json={
                "student_text": "Aluno de 10 anos, fase 2, IDA 5.3.",
                "include_explanation": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] == "moderada"
        assert data["model"]
        assert data["raw_output"] == "moderada"
        assert data["normalized"] is True
        assert "explanation" in data

    def test_predict_normaliza_resposta(self, mock_openai_complete):
        mock_openai_complete.return_value = "  MODERADA  "

        response = client.post(
            "/predict",
            json={"student_text": "Aluno teste", "include_explanation": False},
        )

        assert response.status_code == 200
        assert response.json()["prediction"] == "moderada"

    def test_predict_inclui_explicacao_quando_solicitado(
        self, mock_openai_complete, mock_explainer
    ):
        mock_openai_complete.return_value = "moderada"
        mock_explainer.return_value = "Explicação humanizada para o usuário."

        response = client.post(
            "/predict",
            json={"student_text": "Aluno de 10 anos.", "include_explanation": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["explanation"] == "Explicação humanizada para o usuário."

    def test_predict_sem_explicacao_quando_include_explanation_false(
        self, mock_openai_complete
    ):
        mock_openai_complete.return_value = "em_fase"

        response = client.post(
            "/predict",
            json={"student_text": "Aluno de 10 anos.", "include_explanation": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["explanation"] is None


class TestPredictErrors:
    """Testes de erro do /predict."""

    def test_entrada_vazia_retorna_422(self):
        response = client.post(
            "/predict",
            json={"student_text": ""},
        )
        assert response.status_code == 422

    def test_entrada_faltando_retorna_422(self):
        response = client.post("/predict", json={})
        assert response.status_code == 422

    def test_resposta_invalida_retorna_422(self, mock_openai_complete):
        mock_openai_complete.return_value = "classe_inexistente"

        response = client.post(
            "/predict",
            json={"student_text": "Aluno teste", "include_explanation": False},
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "raw_output" in data

    def test_erro_openai_retorna_500(self, mock_openai_complete):
        mock_openai_complete.side_effect = Exception("API Error")

        client_no_raise = TestClient(app, raise_server_exceptions=False)
        response = client_no_raise.post(
            "/predict",
            json={"student_text": "Aluno teste", "include_explanation": False},
        )

        assert response.status_code == 500
