"""
Serviço de geração de explicação humanizada da classificação.
"""

import logging

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Você é um especialista em educação. Sua tarefa é gerar uma explicação breve "
    "(2 a 4 frases) em português, em tom humanizado e acessível, explicando por que "
    "a classificação de risco de defasagem escolar faz sentido com base nos indicadores "
    "do caso descrito. Use apenas as informações fornecidas no texto."
)


def generate_explanation(student_text: str, prediction: str) -> str | None:
    """
    Gera uma explicação breve e humanizada da classificação.

    Args:
        student_text: Texto descrevendo o caso do aluno.
        prediction: Classificação retornada (em_fase, moderada ou severa).

    Returns:
        Texto da explicação ou None em caso de erro.
    """
    try:
        client = OpenAI(api_key=settings.openai_api_key)

        user_content = (
            f"Caso do aluno:\n{student_text}\n\n"
            f"Classificação de risco: {prediction}\n\n"
            "Gere uma explicação breve e humanizada para o usuário."
        )

        response = client.chat.completions.create(
            model=settings.openai_explanation_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=150,
        )

        content = response.choices[0].message.content or ""
        explanation = content.strip()

        logger.info(
            "Explanation generated",
            extra={"prediction": prediction, "length": len(explanation)},
        )
        return explanation if explanation else None

    except Exception as e:
        logger.exception("Failed to generate explanation: %s", e)
        return None
