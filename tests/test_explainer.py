"""
Testes para o serviço de explicação.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.explainer import generate_explanation


class TestGenerateExplanation:
    """Testes de geração de explicação."""

    def test_retorna_texto_quando_api_responde(self):
        """Gera explicação quando a API retorna conteúdo."""
        fake_response = "O aluno apresenta indicadores de defasagem moderada."

        mock_message = MagicMock()
        mock_message.content = fake_response
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("app.services.explainer.OpenAI") as mock_openai:
            mock_client = mock_openai.return_value
            mock_client.chat.completions.create.return_value = mock_response

            result = generate_explanation("Aluno de 10 anos.", "moderada")

        assert result == fake_response

    def test_retorna_none_quando_excecao(self):
        """Retorna None quando a API lança exceção."""
        with patch("app.services.explainer.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.side_effect = Exception(
                "API Error"
            )

            result = generate_explanation("Aluno teste", "severa")

        assert result is None
