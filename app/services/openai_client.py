"""
Cliente para chamadas ao modelo fine-tuned da OpenAI.
"""

import logging

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Você é um especialista em educação que classifica risco de defasagem escolar."
)


def complete(student_text: str) -> str:
    """
    Chama o modelo fine-tuned da OpenAI para classificar o caso do aluno.

    Args:
        student_text: Texto descrevendo o aluno em linguagem natural.

    Returns:
        O texto da resposta do assistant (classe esperada: em_fase, moderada ou severa).

    Raises:
        Exception: Em caso de erro na API da OpenAI.
    """
    # Mock temporário para testes - remover quando o modelo fine-tuned estiver pronto
    return "moderada"

    client = OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": student_text},
        ],
        temperature=0,
        max_tokens=10,
    )

    content = response.choices[0].message.content or ""
    logger.info(
        "OpenAI response received",
        extra={"model": settings.openai_model, "content_preview": content[:50]},
    )
    return content.strip()
