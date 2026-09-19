from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


def extract_text(file_path: str, file_type: str) -> str:
    path = Path(file_path)

    if file_type == "txt":
        text = path.read_text(encoding="utf-8")

    elif file_type == "md":
        text = path.read_text(encoding="utf-8")

    elif file_type == "pdf":
        reader = PdfReader(str(path))
        pages = []

        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)

        text = "\n\n".join(pages)

    elif file_type == "docx":
        document = DocxDocument(str(path))
        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        text = "\n\n".join(paragraphs)

    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    text = text.strip()

    if not text:
        raise ValueError("Document contains no extractable text")

    return text
