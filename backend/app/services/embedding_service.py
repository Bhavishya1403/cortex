from google import genai
from google.genai import types

from app.core.config import settings


EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 768


client = genai.Client(
    api_key=settings.GEMINI_API_KEY,
)


def embed_text(text: str) -> list[float]:
    """Generate a semantic embedding for a single text string."""
    if not text.strip():
        raise ValueError("Cannot embed empty text")

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )

    if not result.embeddings or not result.embeddings[0].values:
        raise ValueError("Embedding provider returned no vector")

    vector = result.embeddings[0].values

    if len(vector) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSIONS}-dimensional embedding, "
            f"got {len(vector)}"
        )

    return vector
