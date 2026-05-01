from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.models.responses import UploadResponse
from app.services import (
    chunking_service,
    embedding_service,
    pdf_service,
    vector_store_service,
)

router = APIRouter(tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
    if not pdf_service.is_pdf_upload(file):
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF.")

    document_id = str(uuid4())

    try:
        pdf_path = await pdf_service.save_upload(file, document_id)
        raw_text = await run_in_threadpool(pdf_service.extract_text, pdf_path)
        chunks = chunking_service.chunk_text(
            raw_text,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="PDF contains no extractable text. Try OCR preprocessing.",
            )

        vectors = await run_in_threadpool(embedding_service.encode_batch, chunks)
        vector_store_service.create_index(
            document_id=document_id,
            vectors=vectors,
            chunks=chunks,
            filename=file.filename or f"{document_id}.pdf",
        )
    except HTTPException:
        raise
    except pdf_service.EmptyPDFError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except pdf_service.PDFProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {exc}",
        ) from exc

    return UploadResponse(
        document_id=document_id,
        filename=file.filename or f"{document_id}.pdf",
        chunk_count=len(chunks),
        status="ready",
    )
