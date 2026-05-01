from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.models.requests import AskRequest
from app.models.responses import AskResponse, SourceSnippet
from app.services import embedding_service, qa_service, vector_store_service

router = APIRouter(tags=["questions"])


REFUSAL_TEXT = "I could not find information about this in the provided document."
OLLAMA_UNAVAILABLE_TEXT = (
    "Ollama is unavailable right now, so I cannot generate the full answer yet."
)



def _filter_retrieval_results(
    results: list[dict[str, int | float | str]],
) -> list[dict[str, int | float | str]]:
    if not results:
        return []

    best_score = float(results[0]["score"])
    if best_score < settings.min_similarity_score:
        return []

    score_floor = max(settings.min_similarity_score, best_score * 0.55)
    filtered = [item for item in results if float(item["score"]) >= score_floor]
    return filtered or [results[0]]


def _build_ollama_unavailable_answer(results: list[dict[str, int | float | str]]) -> str:
    preview = _context_preview([str(item["text"]) for item in results])
    if not preview:
        return (
            f"{OLLAMA_UNAVAILABLE_TEXT}\n\n"
            "Please start Ollama and try again for a complete answer."
        )

    return (
        f"{OLLAMA_UNAVAILABLE_TEXT}\n\n"
        "Relevant context found in the document:\n"
        f"{preview}\n\n"
        "Please start Ollama and try again for a complete answer."
    )


def _context_preview(chunks: list[str]) -> str:
    text = " ".join(chunks)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""

    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]
    preview = " ".join(sentences[:2]) if sentences else text
    if len(preview) > 420:
        preview = preview[:417].rstrip() + "..."
    return preview





def _source_metadata_event(document_id: str) -> str | None:
    metadata = vector_store_service.get_document_metadata(document_id)
    if metadata is None:
        return None
    return qa_service.sse_payload(
        {
            "source": {
                "filename": metadata.filename,
                "chunk_count": metadata.chunk_count,
            }
        }
    )


@router.post("/ask", response_model=AskResponse)
async def ask_question(payload: AskRequest) -> AskResponse:
    if not vector_store_service.document_exists(payload.document_id):
        raise HTTPException(status_code=404, detail="document_id does not exist.")

    query_vector = await run_in_threadpool(
        embedding_service.encode_single,
        payload.question,
    )
    results = vector_store_service.search(
        document_id=payload.document_id,
        query_vector=query_vector,
        k=min(payload.top_k, settings.max_top_k),
    )
    filtered_results = _filter_retrieval_results(results)
    metadata = vector_store_service.get_document_metadata(payload.document_id)

    sources = [
        SourceSnippet(
            chunk_index=item["chunk_index"],
            score=item["score"],
            filename=metadata.filename if metadata else None,
        )
        for item in filtered_results
    ]

    if not filtered_results:
        return AskResponse(
            answer=REFUSAL_TEXT,
            question=payload.question,
            document_id=payload.document_id,
            sources=sources,
        )

    
    try:
        answer = await qa_service.generate_answer(
            question=payload.question,
            context_chunks=[item["text"] for item in filtered_results],
        )
    except HTTPException as exc:
        if exc.status_code != 503:
            raise
        answer = _build_ollama_unavailable_answer(filtered_results)

    return AskResponse(
        answer=answer,
        question=payload.question,
        document_id=payload.document_id,
        sources=sources,
    )

@router.get("/ask/stream")   # GET so EventSource works
async def ask_stream(
    document_id: str,
    question: str,
    top_k: int = settings.default_top_k,
):
    if not vector_store_service.document_exists(document_id):
        raise HTTPException(status_code=404, detail="document_id does not exist.")

    stripped_question = question.strip()
    if not stripped_question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    bounded_top_k = max(1, min(top_k, settings.max_top_k))

    query_vector = await run_in_threadpool(
        embedding_service.encode_single, stripped_question
    )
    results = vector_store_service.search(
        document_id=document_id,
        query_vector=query_vector,
        k=bounded_top_k,
    )
    filtered_results = _filter_retrieval_results(results)

    if not filtered_results:
        async def no_answer():
            source_event = _source_metadata_event(document_id)
            if source_event:
                yield source_event
            yield qa_service.sse_token(REFUSAL_TEXT)
            yield "data: [DONE]\n\n"

        return StreamingResponse(no_answer(), media_type="text/event-stream")

    


    async def answer_events():
        source_event = _source_metadata_event(document_id)
        if source_event:
            yield source_event
        async for item in qa_service.stream_answer(
            question=stripped_question,
            context_chunks=[item["text"] for item in filtered_results],
            fallback_text=_build_ollama_unavailable_answer(filtered_results),
        ):
            yield item

    return StreamingResponse(
        answer_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
