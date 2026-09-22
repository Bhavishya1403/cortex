from pydantic import BaseModel, Field
from google import genai
from google.genai import errors, types

from app.core.config import settings


CRITIC_MODEL = "gemini-3.6-flash"

CRITIC_MAX_ATTEMPTS = 2


client = genai.Client(
    api_key=settings.GEMINI_API_KEY,
)


class CriticResult(BaseModel):
    grounded: bool = Field(
        description="Whether the answer is fully supported by the provided context."
    )
    feedback: str = Field(
        description="Brief explanation of the grounding decision."
    )


CRITIC_INSTRUCTION = """You are a strict answer verifier for an enterprise RAG system.

Evaluate whether the proposed answer is supported by the provided document context.

Rules:
- Mark grounded=true only when the answer is supported by the context.
- Mark grounded=false when the answer contains unsupported facts, speculation, or claims not justified by the context.
- Do not judge whether the answer is generally true outside the context.
- Keep feedback brief and specific.
"""


def verify_answer(
    *,
    query: str,
    context: str,
    answer: str,
) -> CriticResult:
    """Verify that a generated answer is grounded in retrieved context."""
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if not context.strip():
        raise ValueError("Context cannot be empty")

    if not answer.strip():
        raise ValueError("Answer cannot be empty")

    prompt = (
        f"{CRITIC_INSTRUCTION}\n\n"
        f"DOCUMENT CONTEXT:\n{context}\n\n"
        f"USER QUESTION:\n{query}\n\n"
        f"PROPOSED ANSWER:\n{answer}"
    )

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=CriticResult,
    )

    for attempt in range(CRITIC_MAX_ATTEMPTS):
        try:
            response = client.models.generate_content(
                model=CRITIC_MODEL,
                contents=prompt,
                config=config,
            )
            break
        except errors.ServerError:
            if attempt == CRITIC_MAX_ATTEMPTS - 1:
                raise

    result = (response.text or "").strip()

    if not result:
        raise ValueError("Critic provider returned an empty response")

    return CriticResult.model_validate_json(result)
