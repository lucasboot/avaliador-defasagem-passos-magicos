"""
Serviço de geração de explicação humanizada da classificação.
"""

import logging

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Você é um especialista em educação e avaliação de desenvolvimento escolar,
com experiência em análise de indicadores educacionais utilizados no projeto
Passos Mágicos (PEDE).

Sua tarefa é explicar de forma clara e objetiva por que um estudante foi
classificado em um determinado nível de risco de defasagem escolar.

Contexto dos indicadores utilizados:

- IDA (Indicador de Desempenho Acadêmico): mede o desempenho escolar do aluno
  em avaliações acadêmicas.
- IEG (Indicador de Engajamento): mede o nível de participação, interesse e
  dedicação do estudante nas atividades educacionais.
- IAA (Indicador de Autoavaliação): representa a percepção do próprio aluno
  sobre seu aprendizado e desenvolvimento.
- IPS (Indicador Psicossocial): avalia fatores emocionais, familiares e sociais
  que podem impactar o desenvolvimento educacional.
- IPP (Indicador Psicopedagógico): avalia aspectos cognitivos e de aprendizagem.
- IAN (Indicador de Adequação de Nível): mede a diferença entre a fase escolar
  ideal para a idade do estudante e a fase em que ele se encontra.

Classificação de risco de defasagem:
- "Em fase": o estudante está no nível educacional esperado para sua idade.
- "Moderada": há atraso educacional relevante em relação ao esperado.
- "Severa": há atraso educacional significativo e risco elevado de defasagem.

Instruções:
- Gere uma explicação breve (2 a 4 frases).
- Utilize apenas as informações presentes no caso descrito.
- Explique quais indicadores ou fatores provavelmente influenciaram a
  classificação.
- Use linguagem clara, humana e acessível, adequada para educadores ou
  gestores educacionais.
- Não invente informações que não estejam presentes no texto fornecido.
"""

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
            max_tokens=1000,
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
