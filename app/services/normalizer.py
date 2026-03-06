"""
Normalização da saída do modelo para classes válidas.
"""

import re

from app.utils.errors import InvalidPredictionError

VALID_CLASSES = frozenset({"em_fase", "moderada", "severa"})

# Mapeamento de variações previsíveis para a classe canônica
NORMALIZATION_MAP = {
    "em_fase": "em_fase",
    "em fase": "em_fase",
    "emfase": "em_fase",
    "moderada": "moderada",
    "moderado": "moderada",
    "severa": "severa",
    "severo": "severa",
}


def normalize_prediction(raw: str) -> str:
    """
    Normaliza a resposta do modelo para exatamente uma das 3 classes válidas.

    - Remove espaços extras e quebras de linha
    - Converte para minúsculas
    - Mapeia variações previsíveis (em fase, Em Fase, etc.) para em_fase

    Args:
        raw: Resposta bruta do modelo.

    Returns:
        Uma das strings: "em_fase", "moderada", "severa".

    Raises:
        InvalidPredictionError: Se não for possível mapear para uma classe válida.
    """
    if raw is None:
        raise InvalidPredictionError(
            "Resposta do modelo é nula",
            raw_output=str(raw),
        )

    # Remove espaços extras, quebras de linha e colapsa múltiplos espaços
    normalized = raw.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)

    # Se já for uma classe válida, retorna
    if normalized in VALID_CLASSES:
        return normalized

    # Tenta mapear variações conhecidas
    if normalized in NORMALIZATION_MAP:
        return NORMALIZATION_MAP[normalized]

    # Tenta extrair a primeira palavra/token relevante para "em fase"
    if "em" in normalized and "fase" in normalized:
        return "em_fase"

    raise InvalidPredictionError(
        f"Resposta do modelo não pôde ser normalizada para uma classe válida: "
        f"'{raw[:100]}'",
        raw_output=raw,
    )
