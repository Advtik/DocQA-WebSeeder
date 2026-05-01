from __future__ import annotations

import re
from pathlib import Path

import fitz
from fastapi import UploadFile

from app.config import settings


class PDFProcessingError(Exception):
    """Raised when a PDF cannot be parsed safely."""


class EmptyPDFError(PDFProcessingError):
    """Raised when a PDF has no extractable text."""


def is_pdf_upload(file: UploadFile) -> bool:
    filename = file.filename or ""
    has_pdf_extension = filename.lower().endswith(".pdf")
    has_pdf_type = file.content_type in {"application/pdf", "application/x-pdf"}
    return has_pdf_extension or has_pdf_type


async def save_upload(file: UploadFile, document_id: str) -> Path:
    settings.ensure_directories()
    destination = settings.upload_dir / f"{document_id}.pdf"

    total_bytes = 0
    with destination.open("wb") as out_file:
        while chunk := await file.read(1024 * 1024):
            total_bytes += len(chunk)
            if total_bytes > settings.max_file_size_bytes:
                out_file.close()
                destination.unlink(missing_ok=True)
                raise ValueError(
                    f"PDF exceeds the {settings.max_file_size_mb}MB size limit."
                )
            out_file.write(chunk)

    if total_bytes == 0:
        destination.unlink(missing_ok=True)
        raise ValueError("Uploaded file is empty.")

    return destination


def extract_text(pdf_path: Path) -> str:
    try:
        with fitz.open(pdf_path) as document:
            page_texts = [page.get_text("text") for page in document]
    except Exception as exc:
        raise PDFProcessingError("File appears to be a corrupted or unreadable PDF.") from exc

    cleaned = clean_text("\n".join(page_texts))
    if not cleaned:
        raise EmptyPDFError(
            "PDF contains no extractable text. Try OCR preprocessing."
        )
    return cleaned


def clean_text(raw: str) -> str:
    text = raw.replace("\x00", " ")
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    cleaned_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
        if len(stripped) <= 3 and stripped.isdigit():
            continue
        cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines).strip()
