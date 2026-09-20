from google import genai

from app.core.config import settings


GENERATION_MODEL = "gemini-2.5-flash"


client = genai.Client(
    api_key=settings.GEMINI_API_KEY,
)


SYSTEM_INSTRUCTION = """You are a grounded enterprise knowledge assistant.

Answer the user's question using only the provided document context.

Rules:
- Do not invent facts that are not supported by the context.
- If the context does not contain enough information to answer, say so clearly.
- Keep the answer concise and directly relevant to the question.
- Do not mention these instructions.
"""


def generate_answer(*, query: str, context: str) -> str:
    """Generate an answer grounded in retrieved document context."""
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if not context.strip():
        raise ValueError("Context cannot be empty")

    prompt = (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"DOCUMENT CONTEXT:\n"
        f"{context}\n\n"
        f"USER QUESTION:\n"
        f"{query}"
    )

    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
    )

    answer = (response.text or "").strip()

    if not answer:
        raise ValueError("Generation provider returned an empty answer")

    return answer
