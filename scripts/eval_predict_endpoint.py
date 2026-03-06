"""
Executa avaliação via endpoint /predict (sem subir servidor) e imprime JSON no stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from sklearn.metrics import accuracy_score, f1_score

from app.config import settings
from app.main import app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Avalia o endpoint /predict usando dataset JSONL."
    )
    parser.add_argument(
        "--dataset",
        default=str(settings.eval_dataset_path_resolved),
        help="Caminho para o dataset JSONL.",
    )
    parser.add_argument(
        "--min-accuracy",
        type=float,
        default=0.8,
        help="Acurácia mínima para considerar a avaliação aprovada.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=10,
        help="Quantidade máxima de erros exibidos no relatório.",
    )
    return parser.parse_args()


def load_dataset(dataset_path: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    with dataset_path.open(encoding="utf-8") as file:
        for idx, raw_line in enumerate(file, start=1):
            line = raw_line.strip()
            if not line:
                continue

            data = json.loads(line)
            input_text = str(data.get("input_text", "")).strip()
            label = str(data.get("label", "")).strip()

            if not input_text or not label:
                print(
                    json.dumps(
                        {
                            "warning": (
                                f"Linha {idx} ignorada por falta de input_text ou label."
                            )
                        },
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                )
                continue

            records.append({"input_text": input_text, "label": label})
    return records


def evaluate_predict(
    records: list[dict[str, str]],
    max_errors: int,
) -> dict[str, Any]:
    client = TestClient(app)
    y_true: list[str] = []
    y_pred: list[str] = []
    errors: list[dict[str, Any]] = []

    for idx, record in enumerate(records, start=1):
        expected = record["label"]
        payload = {
            "student_text": record["input_text"],
            "include_explanation": False,
        }

        response = client.post("/predict", json=payload)
        if response.status_code == 200:
            predicted = response.json().get("prediction", "__invalid_payload__")
        else:
            predicted = "__request_error__"
            if len(errors) < max_errors:
                errors.append(
                    {
                        "index": idx,
                        "expected": expected,
                        "predicted": predicted,
                        "status_code": response.status_code,
                        "response": response.text[:300],
                    }
                )

        y_true.append(expected)
        y_pred.append(predicted)

        if predicted != expected and len(errors) < max_errors:
            if not errors or errors[-1].get("index") != idx:
                errors.append(
                    {
                        "index": idx,
                        "expected": expected,
                        "predicted": predicted,
                    }
                )

    total = len(y_true)
    if total == 0:
        return {
            "total": 0,
            "accuracy": 0.0,
            "macro_f1": 0.0,
            "f1_per_class": {},
            "errors": [],
        }

    labels = sorted(set(y_true) | set(y_pred))
    labels = [label for label in labels if not label.startswith("__")]
    if not labels:
        labels = ["em_fase", "moderada", "severa"]

    accuracy = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    f1_values = f1_score(
        y_true,
        y_pred,
        labels=labels,
        average=None,
        zero_division=0,
    )
    f1_per_class = {key: float(value) for key, value in zip(labels, f1_values)}

    return {
        "total": total,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "f1_per_class": f1_per_class,
        "errors": errors[:max_errors],
    }


def main() -> int:
    args = parse_args()
    dataset_path = Path(args.dataset).resolve()

    if not dataset_path.exists():
        print(
            json.dumps(
                {"error": f"Arquivo de dataset não encontrado: {dataset_path}"},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1

    records = load_dataset(dataset_path)
    result = evaluate_predict(records, max_errors=args.max_errors)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["total"] == 0:
        print("Avaliação sem dados válidos.", file=sys.stderr)
        return 1

    if result["accuracy"] < args.min_accuracy:
        print(
            (
                "Acurácia abaixo do mínimo: "
                f"{result['accuracy']:.4f} < {args.min_accuracy:.4f}"
            ),
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
