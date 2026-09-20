from google import genai

from app.core.config import settings


GENERATION_MODEL = "gemini-3.6-flash"


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


def generate_answer(
    *,
    query: str,
    context: str,
    critic_feedback: str | None = None,
) -> str:
    """Generate an answer grounded in retrieved document context."""
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if not context.strip():
        raise ValueError("Context cannot be empty")

    retry_instruction = ""

    if critic_feedback and critic_feedback.strip():
        retry_instruction = (
            "\n\nPREVIOUS ANSWER FEEDBACK:\n"
            f"{critic_feedback}\n\n"
            "Revise the answer to address this feedback. "
            "Continue using only the provided document context."
        )

    prompt = (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"DOCUMENT CONTEXT:\n"
        f"{context}\n\n"
        f"USER QUESTION:\n"
        f"{query}"
        f"{retry_instruction}"
    )

    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
    )

    answer = (response.text or "").strip()

    if not answer:
        raise ValueError("Generation provider returned an empty answer")

    return answer
