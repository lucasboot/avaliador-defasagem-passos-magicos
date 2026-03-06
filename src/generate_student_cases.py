#!/usr/bin/env python3
"""
Script para gerar casos de alunos em formato textual a partir do dataset PEDE Passos Mágicos.
Converte cada linha em descrição textual para treino/avaliação de modelo LLM de classificação
de risco de defasagem escolar.
"""

import argparse
import json
import logging
import re
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Valores considerados ausentes/inválidos
VALORES_INVALIDOS = {"", "nan", "Não avaliado", "ERRO", "nan"}

# Mapeamento de NIVEL_IDEAL para número (ALFA=0, Nível/Fase 1=1, etc.)
NIVEL_ALFA_PATTERN = re.compile(r"ALFA\s*\(.*\)", re.IGNORECASE)
NIVEL_NUMERO_PATTERN = re.compile(r"(?:Nível|Fase)\s*(\d+)", re.IGNORECASE)

# Colunas prioritárias por categoria (base sem ano)
COLUNAS_PRIORITARIAS = {
    "aluno": ["IDADE_ALUNO", "ANOS_PM", "ANO_INGRESSO"],
    "educacionais": ["IDA", "IEG", "IAA", "IPS", "IPP", "IPV", "IAN"],
    "academicas": ["NOTA_PORT", "NOTA_MAT", "NOTA_ING"],
    "institucionais": ["INDE", "PEDRA", "BOLSISTA", "PONTO_VIRADA"],
    "observacao": [
        "DESTAQUE_IEG",
        "DESTAQUE_IDA",
        "DESTAQUE_IPV",
        "REC_EQUIPE_1",
        "REC_EQUIPE_2",
        "REC_EQUIPE_3",
        "REC_EQUIPE_4",
        "REC_AVA_1",
        "REC_AVA_2",
        "REC_AVA_3",
        "REC_AVA_4",
    ],
}
COLUNAS_ESPECIAIS = ["FASE", "FASE_TURMA", "NIVEL_IDEAL"]

SYSTEM_PROMPT = (
    "Você é um especialista em educação que classifica risco de defasagem escolar."
)


def _valor_valido(val) -> bool:
    """Verifica se o valor não é ausente ou inválido."""
    if pd.isna(val):
        return False
    s = str(val).strip()
    return s not in VALORES_INVALIDOS and s.lower() != "nan"


def _formatar_numero(val) -> str:
    """Formata número para exibição (remove decimais desnecessários)."""
    if pd.isna(val) or not _valor_valido(val):
        return ""
    try:
        f = float(val)
        return str(int(f)) if f == int(f) else f"{f:.2f}".rstrip("0").rstrip(".")
    except (ValueError, TypeError):
        return str(val).strip()


def extrair_nivel_ideal_numero(val) -> int | None:
    """
    Extrai o número do nível ideal a partir do texto.
    ALFA -> 0, Nível/Fase 1 -> 1, etc.
    """
    if not _valor_valido(val):
        return None
    s = str(val).strip()
    if NIVEL_ALFA_PATTERN.search(s):
        return 0
    match = NIVEL_NUMERO_PATTERN.search(s)
    if match:
        return int(match.group(1))
    return None


def extrair_fase_numero(val, ano: int) -> int | None:
    """
    Extrai o número da fase. FASE_2021/2022 são numéricos.
    FASE_TURMA_2020 tem formato "2H", "3B" - primeiro char é o número.
    """
    if not _valor_valido(val):
        return None
    s = str(val).strip()
    try:
        f = float(s)
        return int(f)
    except (ValueError, TypeError):
        pass
    # Formato FASE_TURMA: "2H", "3B"
    if len(s) >= 1 and s[0].isdigit():
        return int(s[0])
    return None


def obter_label(
    row: pd.Series,
    label_year: int,
    df_columns: list[str],
) -> str | None:
    """
    Obtém o label de defasagem (em_fase, moderada, severa).
    Usa DEFASAGEM_{year} se existir, senão calcula a partir de FASE e NIVEL_IDEAL.
    """
    col_defasagem = f"DEFASAGEM_{label_year}"
    if col_defasagem in df_columns:
        val = row.get(col_defasagem)
        if _valor_valido(val):
            try:
                d = float(val)
                return _defasagem_para_classe(d)
            except (ValueError, TypeError):
                pass

    col_fase = f"FASE_{label_year}"
    col_nivel = f"NIVEL_IDEAL_{label_year}"
    if col_fase not in df_columns or col_nivel not in df_columns:
        return None

    fase = extrair_fase_numero(row.get(col_fase), label_year)
    nivel = extrair_nivel_ideal_numero(row.get(col_nivel))
    if fase is None or nivel is None:
        return None

    defasagem = fase - nivel
    return _defasagem_para_classe(defasagem)


def _defasagem_para_classe(defasagem: float) -> str:
    """Converte valor numérico de defasagem em classe."""
    if defasagem >= 0:
        return "em_fase"
    if defasagem == -1:
        return "moderada"
    return "severa"


def colunas_para_ano(ano: int, df_columns: list[str]) -> list[str]:
    """Retorna colunas disponíveis com sufixo do ano dado."""
    sufixo = f"_{ano}"
    return [c for c in df_columns if c.endswith(sufixo)]


def gerar_descricao_aluno(row: pd.Series, ano: int, df_columns: list[str]) -> str:
    """
    Converte uma linha do dataset em descrição textual do aluno.
    Usa apenas colunas do ano especificado (e colunas sem ano quando aplicável).
    """
    partes = []

    # 1. Idade e anos na associação
    idade_col = f"IDADE_ALUNO_{ano}"
    if idade_col not in df_columns:
        idade_col = "IDADE_ALUNO_2020"  # fallback
    anos_col = f"ANOS_PM_{ano}"
    if anos_col not in df_columns:
        anos_col = "ANOS_PM_2020"
    ano_ingresso_col = f"ANO_INGRESSO_{ano}"
    if ano_ingresso_col not in df_columns:
        ano_ingresso_col = "ANO_INGRESSO_2022"

    idade = row.get(idade_col)
    anos_pm = row.get(anos_col)
    ano_ingresso = row.get(ano_ingresso_col)

    if _valor_valido(idade):
        idade_str = _formatar_numero(idade)
        if _valor_valido(anos_pm):
            anos_str = _formatar_numero(anos_pm)
            partes.append(f"Aluno de {idade_str} anos que está há {anos_str} anos na associação.")
        elif _valor_valido(ano_ingresso):
            ai = _formatar_numero(ano_ingresso)
            partes.append(f"Aluno de {idade_str} anos, ingressou em {ai}.")
        else:
            partes.append(f"Aluno de {idade_str} anos.")
    elif _valor_valido(anos_pm):
        anos_str = _formatar_numero(anos_pm)
        partes.append(f"Aluno que está há {anos_str} anos na associação.")

    # 2. Fase atual e nível ideal
    fase_col = f"FASE_{ano}"
    fase_turma_col = f"FASE_TURMA_{ano}"
    nivel_col = f"NIVEL_IDEAL_{ano}"

    fase_val = row.get(fase_col) if fase_col in df_columns else None
    if not _valor_valido(fase_val) and fase_turma_col in df_columns:
        fase_val = row.get(fase_turma_col)
    nivel_val = row.get(nivel_col) if nivel_col in df_columns else None

    if _valor_valido(fase_val):
        fase_num = extrair_fase_numero(fase_val, ano)
        if fase_num is not None:
            partes.append(f"Está na fase {fase_num} da associação.")
    if _valor_valido(nivel_val):
        nivel_str = str(nivel_val).strip()
        partes.append(f"O nível ideal para sua idade seria {nivel_str}.")

    # 3. Indicadores educacionais
    indicadores = []
    for base in COLUNAS_PRIORITARIAS["educacionais"]:
        col = f"{base}_{ano}"
        if col not in df_columns:
            continue
        val = row.get(col)
        if _valor_valido(val):
            num = _formatar_numero(val)
            if num:
                nome = {"IDA": "desempenho acadêmico IDA", "IEG": "engajamento IEG", "IPS": "indicador psicossocial IPS",
                        "IPP": "indicador psicopedagógico IPP", "IAA": "IAA", "IPV": "IPV", "IAN": "IAN"}.get(base, base)
                indicadores.append(f"{nome} de {num}")
    if indicadores:
        partes.append("Possui " + ", ".join(indicadores) + ".")

    # 4. Notas
    notas = []
    for base, nome in [("NOTA_PORT", "português"), ("NOTA_MAT", "matemática"), ("NOTA_ING", "inglês")]:
        col = f"{base}_{ano}"
        if col in df_columns:
            val = row.get(col)
            if _valor_valido(val):
                num = _formatar_numero(val)
                if num:
                    notas.append(f"{nome} {num}")
    if notas:
        partes.append("Suas notas são: " + ", ".join(notas) + ".")

    # 5. INDE, PEDRA, BOLSISTA, PONTO_VIRADA
    info_inst = []
    for base in ["INDE", "PEDRA", "BOLSISTA", "PONTO_VIRADA"]:
        col = f"{base}_{ano}"
        if col in df_columns:
            val = row.get(col)
            if _valor_valido(val):
                s = str(val).strip()
                if base == "PONTO_VIRADA":
                    if s.lower() in ("sim", "yes", "1"):
                        info_inst.append("atingiu ponto de virada no ano avaliado")
                    else:
                        info_inst.append("não atingiu ponto de virada no ano avaliado")
                elif base == "BOLSISTA":
                    if s.lower() in ("sim", "yes", "1"):
                        info_inst.append("é bolsista")
                    else:
                        info_inst.append("não é bolsista")
                elif base == "INDE" and _formatar_numero(val):
                    info_inst.append(f"INDE de {_formatar_numero(val)}")
                elif base == "PEDRA":
                    info_inst.append(f"pedra {s}")
    if info_inst:
        partes.append("O aluno " + ", ".join(info_inst) + ".")

    # 6. Destaques (resumidos - apenas indicar se há destaque ou ponto a melhorar)
    destaque_parts = []
    for base in ["DESTAQUE_IEG", "DESTAQUE_IDA", "DESTAQUE_IPV"]:
        col = f"{base}_{ano}"
        if col in df_columns:
            val = row.get(col)
            if _valor_valido(val):
                s = str(val).strip()
                if "Destaque:" in s or "destaque" in s.lower() or "Seu destaque" in s:
                    destaque_parts.append("possui destaque")
                    break
                if "Melhorar:" in s or "melhorar" in s.lower() or "Ponto a melhorar" in s:
                    destaque_parts.append("possui pontos a melhorar")
                    break
    if destaque_parts:
        partes.append("O aluno " + destaque_parts[0] + ".")

    if not partes:
        return ""

    return " ".join(partes).strip()


def carregar_dataset(path: str) -> pd.DataFrame:
    """Carrega o dataset e normaliza colunas."""
    logger.info("Carregando dataset de %s", path)
    df = pd.read_csv(path, sep=";", dtype=str, low_memory=False)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def processar_linhas(
    df: pd.DataFrame,
    input_year: int,
    label_year: int,
) -> list[dict]:
    """Processa o dataset e retorna lista de casos {input_text, label}."""
    df_columns = list(df.columns)
    casos = []

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processando linhas"):
        label = obter_label(row, label_year, df_columns)
        if label is None:
            continue

        descricao = gerar_descricao_aluno(row, input_year, df_columns)
        if not descricao or len(descricao) < 20:
            continue

        casos.append({"input_text": descricao, "label": label})

    return casos


def salvar_jsonl(casos: list[dict], path: Path) -> None:
    """Salva lista de dicts em arquivo JSONL."""
    with open(path, "w", encoding="utf-8") as f:
        for item in casos:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def salvar_chat_jsonl(casos: list[dict], path: Path) -> None:
    """Salva em formato chat (messages + label)."""
    with open(path, "w", encoding="utf-8") as f:
        for item in casos:
            chat = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": item["input_text"]},
                ],
                "label": item["label"],
            }
            f.write(json.dumps(chat, ensure_ascii=False) + "\n")


def split_estratificado(
    casos: list[dict],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Split 70/15/15 com estratificação por label."""
    labels = [c["label"] for c in casos]
    rest_ratio = 1 - train_ratio

    train, temp = train_test_split(
        casos,
        test_size=rest_ratio,
        stratify=labels,
        random_state=seed,
    )
    val_labels = [c["label"] for c in temp]
    val_ratio_adj = val_ratio / rest_ratio
    val, test = train_test_split(
        temp,
        test_size=1 - val_ratio_adj,
        stratify=val_labels,
        random_state=seed,
    )
    return train, val, test


def main():
    parser = argparse.ArgumentParser(
        description="Gera casos de alunos em formato textual para treino de LLM."
    )
    parser.add_argument(
        "--input-year",
        type=int,
        default=2021,
        help="Ano dos dados de entrada para a descrição (default: 2021)",
    )
    parser.add_argument(
        "--label-year",
        type=int,
        default=2022,
        help="Ano do label de defasagem (default: 2022)",
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default="data/dataset/dataset.csv",
        help="Caminho do dataset CSV (default: data/dataset/dataset.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Diretório de saída (default: data/processed)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed para reprodutibilidade do split (default: 42)",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    dataset_path = base_dir / args.dataset_path
    output_dir = base_dir / args.output_dir

    if not dataset_path.exists():
        logger.error("Dataset não encontrado: %s", dataset_path)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    df = carregar_dataset(str(dataset_path))
    logger.info("Dataset carregado: %d linhas, %d colunas", len(df), len(df.columns))

    casos = processar_linhas(df, args.input_year, args.label_year)
    logger.info("Casos gerados: %d", len(casos))

    if not casos:
        logger.error("Nenhum caso válido gerado. Verifique input-year e label-year.")
        return 1

    # Salvar student_cases.jsonl e student_cases_chat.jsonl
    cases_path = output_dir / "student_cases.jsonl"
    chat_path = output_dir / "student_cases_chat.jsonl"
    salvar_jsonl(casos, cases_path)
    salvar_chat_jsonl(casos, chat_path)
    logger.info("Salvo: %s e %s", cases_path, chat_path)

    # Split e salvar train/validation/test
    train, val, test = split_estratificado(
        casos,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        seed=args.seed,
    )
    salvar_jsonl(train, output_dir / "train.jsonl")
    salvar_jsonl(val, output_dir / "validation.jsonl")
    salvar_jsonl(test, output_dir / "test.jsonl")
    logger.info(
        "Split: train=%d, validation=%d, test=%d",
        len(train),
        len(val),
        len(test),
    )

    return 0


if __name__ == "__main__":
    exit(main())
