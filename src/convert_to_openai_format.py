#!/usr/bin/env python3
"""
Converte train.jsonl e validation.jsonl para o formato exigido pela OpenAI
para fine-tuning, adicionando a mensagem assistant com o label.
"""

import json
from pathlib import Path

SYSTEM_PROMPT = (
    "Você é um especialista em educação que classifica risco de defasagem escolar."
)


def converter_para_openai(entrada: dict) -> dict:
    """Converte um caso {input_text, label} para formato OpenAI."""
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": entrada["input_text"]},
            {"role": "assistant", "content": entrada["label"]},
        ]
    }


def processar_arquivo(caminho_entrada: Path, caminho_saida: Path) -> int:
    """Processa um arquivo JSONL e salva no formato OpenAI."""
    count = 0
    with open(caminho_entrada, encoding="utf-8") as f_in, open(
        caminho_saida, "w", encoding="utf-8"
    ) as f_out:
        for linha in f_in:
            linha = linha.strip()
            if not linha:
                continue
            data = json.loads(linha)
            openai_format = converter_para_openai(data)
            f_out.write(json.dumps(openai_format, ensure_ascii=False) + "\n")
            count += 1
    return count


def main():
    base_dir = Path(__file__).resolve().parent.parent
    processed_dir = base_dir / "data" / "processed"

    train_in = processed_dir / "train.jsonl"
    train_out = processed_dir / "train_openai.jsonl"
    val_in = processed_dir / "validation.jsonl"
    val_out = processed_dir / "validation_openai.jsonl"

    if not train_in.exists():
        print(f"Erro: {train_in} não encontrado.")
        return 1
    if not val_in.exists():
        print(f"Erro: {val_in} não encontrado.")
        return 1

    n_train = processar_arquivo(train_in, train_out)
    n_val = processar_arquivo(val_in, val_out)

    print(f"Gerados: {train_out} ({n_train} linhas), {val_out} ({n_val} linhas)")
    return 0


if __name__ == "__main__":
    exit(main())
