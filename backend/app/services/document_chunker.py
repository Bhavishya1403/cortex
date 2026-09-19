from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    text: str
    chunk_index: int


DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


def normalize_text(text: str) -> str:
    """Normalize whitespace while preserving paragraph boundaries."""
    paragraphs = [
        " ".join(paragraph.split())
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    ]

    return "\n\n".join(paragraphs)


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    """
    Split document text into overlapping chunks.

    chunk_size:
        Maximum number of characters in each chunk.

    chunk_overlap:
        Number of characters repeated between consecutive chunks.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    normalized_text = normalize_text(text)

    if not normalized_text:
        raise ValueError("Document contains no text to chunk")

    chunks: list[DocumentChunk] = []

    start = 0
    text_length = len(normalized_text)
    step = chunk_size - chunk_overlap

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = normalized_text[start:end].strip()

        if chunk:
            chunks.append(
                DocumentChunk(
                    text=chunk,
                    chunk_index=len(chunks),
                )
            )

        if end >= text_length:
            break

        start += step

    return chunks
