
import logging

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Você é um especialista em educação que classifica risco de defasagem escolar."
)


def complete(student_text: str) -> str:

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
