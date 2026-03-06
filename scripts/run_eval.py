"""
Executa a avaliação offline (sem subir servidor) e imprime JSON no stdout.
"""

import json
import sys

from app.config import settings
from app.services.evaluator import run_evaluation


def main() -> int:
    dataset_path = settings.eval_dataset_path_resolved

    if not dataset_path.exists():
        print(
            json.dumps(
                {"error": f"Arquivo de dataset não encontrado: {dataset_path}"},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1

    result = run_evaluation(dataset_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
