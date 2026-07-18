import io

from docx import Document
from fastapi import HTTPException
from pypdf import PdfReader

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
# Caps how much text we ever send to Gemini per generation call — keeps token
# cost and latency predictable, at the cost of only using the first several
# pages of a very long document. A known, deliberate limitation for MVP.
MAX_EXTRACTED_CHARS = 12000


def extract_text_from_upload(filename: str, content: bytes) -> str:
    lower_name = filename.lower()

    if lower_name.endswith(".txt"):
        text = content.decode("utf-8", errors="ignore")

    elif lower_name.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Couldn't read this PDF: {exc}")
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No extractable text found in this PDF — it may be a scanned image "
                "rather than text-based, which isn't supported yet.",
            )

    elif lower_name.endswith(".docx"):
        try:
            document = Document(io.BytesIO(content))
            text = "\n".join(p.text for p in document.paragraphs)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Couldn't read this document: {exc}")

    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a .txt, .pdf, or .docx file.",
        )

    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="This file appears to be empty.")

    return text[:MAX_EXTRACTED_CHARS]
