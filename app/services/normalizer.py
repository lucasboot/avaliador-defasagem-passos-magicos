
import re

from app.utils.errors import InvalidPredictionError

VALID_CLASSES = frozenset({"em_fase", "moderada", "severa"})


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
    if raw is None:
        raise InvalidPredictionError(
            "Resposta do modelo é nula",
            raw_output=str(raw),
        )


    normalized = raw.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)


    if normalized in VALID_CLASSES:
        return normalized


    if normalized in NORMALIZATION_MAP:
        return NORMALIZATION_MAP[normalized]


    if "em" in normalized and "fase" in normalized:
        return "em_fase"

    raise InvalidPredictionError(
        f"Resposta do modelo não pôde ser normalizada para uma classe válida: "
        f"'{raw[:100]}'",
        raw_output=raw,
    )
