"""
Testes para o normalizador de predições.
"""

import pytest

from app.services.normalizer import normalize_prediction
from app.utils.errors import InvalidPredictionError


class TestNormalizePrediction:
    """Testes de normalização de predições válidas."""

    def test_moderada_simples(self):
        assert normalize_prediction("moderada") == "moderada"

    def test_moderada_com_espacos(self):
        assert normalize_prediction("  MODERADA  ") == "moderada"

    def test_em_fase_com_underscore(self):
        assert normalize_prediction("em_fase") == "em_fase"

    def test_em_fase_com_espaco(self):
        assert normalize_prediction("Em Fase") == "em_fase"

    def test_em_fase_minusculas(self):
        assert normalize_prediction("em fase") == "em_fase"

    def test_severa_simples(self):
        assert normalize_prediction("severa") == "severa"

    def test_severa_maiusculas(self):
        assert normalize_prediction("SEVERA") == "severa"

    def test_moderado_mapeia_para_moderada(self):
        assert normalize_prediction("moderado") == "moderada"

    def test_severo_mapeia_para_severa(self):
        assert normalize_prediction("severo") == "severa"

    def test_emfase_sem_espaco(self):
        assert normalize_prediction("emfase") == "em_fase"

    def test_com_quebras_de_linha(self):
        assert normalize_prediction("\n  moderada  \n") == "moderada"

    def test_multiplos_espacos_internos(self):
        assert normalize_prediction("  em   fase  ") == "em_fase"


class TestNormalizePredictionInvalid:
    """Testes de predições inválidas."""

    def test_outra_coisa_levanta_erro(self):
        with pytest.raises(InvalidPredictionError) as exc_info:
            normalize_prediction("outra_coisa")
        assert "outra_coisa" in str(exc_info.value.message)

    def test_string_vazia_levanta_erro(self):
        with pytest.raises(InvalidPredictionError):
            normalize_prediction("")

    def test_apenas_espacos_levanta_erro(self):
        with pytest.raises(InvalidPredictionError):
            normalize_prediction("   ")

    def test_none_levanta_erro(self):
        with pytest.raises(InvalidPredictionError):
            normalize_prediction(None)

    def test_classe_inexistente_levanta_erro(self):
        with pytest.raises(InvalidPredictionError):
            normalize_prediction("alta")
