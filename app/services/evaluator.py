"""
Serviço de avaliação do classificador sobre dataset JSONL.
"""

import json
import logging
from pathlib import Path
from typing import TypedDict

from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from app.services.classifier import classify

logger = logging.getLogger(__name__)


class EvalResult(TypedDict):
    """Resultado da avaliação."""

    total: int
    accuracy: float
    macro_f1: float
    f1_per_class: dict[str, float]
    confusion_matrix: list[list[int]]
    errors: list[dict]


def run_evaluation(dataset_path: Path, max_errors: int = 10) -> EvalResult:
    """
    Executa avaliação do classificador sobre o arquivo JSONL.

    Cada linha deve ter formato: {"input_text": "...", "label": "em_fase|moderada|severa"}

    Args:
        dataset_path: Caminho para o arquivo test.jsonl.
        max_errors: Número máximo de erros a incluir na lista resumida.

    Returns:
        EvalResult com métricas e lista de erros.
    """
    y_true: list[str] = []
    y_pred: list[str] = []
    errors: list[dict] = []

    with open(dataset_path, encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue

            data = json.loads(line)
            input_text = data.get("input_text", "")
            expected = data.get("label", "")

            if not input_text or not expected:
                logger.warning("Linha %d sem input_text ou label, pulando", idx + 1)
                continue

            try:
                result = classify(input_text)
                pred = result["prediction"]
            except Exception as e:
                logger.exception("Erro ao classificar linha %d: %s", idx + 1, e)
                pred = "__error__"

            y_true.append(expected)
            y_pred.append(pred)

            if pred != expected:
                errors.append(
                    {
                        "index": idx + 1,
                        "expected": expected,
                        "predicted": pred,
                    }
                )

    total = len(y_true)
    if total == 0:
        return EvalResult(
            total=0,
            accuracy=0.0,
            macro_f1=0.0,
            f1_per_class={},
            confusion_matrix=[],
            errors=[],
        )

    accuracy = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    labels = sorted(set(y_true) | set(y_pred))
    labels = [l for l in labels if l != "__error__"]
    if not labels:
        labels = ["em_fase", "moderada", "severa"]

    f1_values = f1_score(
        y_true, y_pred, labels=labels, average=None, zero_division=0
    )
    f1_per_class = {k: float(v) for k, v in zip(labels, f1_values)}

    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_list = cm.tolist()

    return EvalResult(
        total=total,
        accuracy=accuracy,
        macro_f1=macro_f1,
        f1_per_class={k: float(v) for k, v in f1_per_class.items()},
        confusion_matrix=cm_list,
        errors=errors[:max_errors],
    )
