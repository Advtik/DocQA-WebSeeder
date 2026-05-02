from __future__ import annotations

import json

import httpx
from fastapi import HTTPException

from app.config import settings


REFUSAL_TEXT = "I could not find information about this in the provided document."

PROMPT_TEMPLATE = """<|system|>
You are a focused document analyst. Your only knowledge source is the CONTEXT below.
Never use outside knowledge. Never fabricate facts.

THINKING PROCESS (internal only, never shown):
1. Read the question type: factual / inferential / yes-no / explanatory / indirect
2. Scan all context chunks for direct mentions AND related clues
3. If indirect: reason from what IS stated to what CAN be concluded
4. If partially present: state what is found, note what is missing
5. Form a clean answer — no step labels, no reasoning trace

ANSWER RULES:
- Yes/No questions → start with "Yes" or "No", then support it briefly
- Factual questions → state the fact directly, add brief context if useful
- Explanatory questions → explain using only context details, naturally
- Indirect questions → infer carefully, signal inference with "Based on the document..."
- Multi-part questions → answer each part in one flowing paragraph
- Not in context at all → respond EXACTLY: "I could not find information about this in the provided document."
- If something is not present in the given document or the context then tell it directly
- If there is something not present respond EXACTLY: "I could not find information about this in the provided document."

OUTPUT FORMAT:
- Prose only, no bullet points, no numbered lists, no headers
- No phrases like "According to the context" or "The document states"
- No meta-commentary, no reasoning traces, no self-reference
- Concise but complete — do not truncate important details
<|end|>
<|user|>
CONTEXT:
{context}

QUESTION:
{question}
<|end|>
<|assistant|>
"""


def build_prompt(question: str, chunks: list[str]) -> str:
    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        context_blocks.append(f"---\n[CHUNK {i}]\n{chunk.strip()}")
    context = "\n".join(context_blocks) + "\n---"
    return PROMPT_TEMPLATE.format(context=context, question=question.strip())


async def generate_answer(question: str, context_chunks: list[str]) -> str:
    prompt = build_prompt(question, context_chunks)
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": 180,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
            response = await client.post(
                f"{settings.ollama_url.rstrip('/')}/api/generate",
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Ollama returned {exc.response.status_code}. "
                f"Ensure the '{settings.ollama_model}' model is available."
            ),
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail="Ollama is unreachable. Please run: ollama serve",
        ) from exc

    data = response.json()
    answer = str(data.get("response", "")).strip()
    return answer or REFUSAL_TEXT


async def is_ollama_available() -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{settings.ollama_url.rstrip('/')}/api/tags")
            return response.status_code == 200
    except httpx.RequestError:
        return False


async def stream_answer(
    question: str,
    context_chunks: list[str],
    fallback_text: str = REFUSAL_TEXT,
):
    prompt = build_prompt(question, context_chunks)
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": 180,
        },
    }
    print(context_chunks)

    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
            async with client.stream(
                "POST",
                f"{settings.ollama_url.rstrip('/')}/api/generate",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if chunk.get("error"):
                        yield sse_token(fallback_text)
                        yield "data: [DONE]\n\n"
                        return

                    token = chunk.get("response", "")
                    if token:
                        yield sse_token(token)
                    if chunk.get("done"):
                        yield "data: [DONE]\n\n"
                        return
    except httpx.HTTPStatusError as exc:
        yield sse_token(fallback_text)
        yield "data: [DONE]\n\n"
    except httpx.RequestError:
        yield sse_token(fallback_text)
        yield "data: [DONE]\n\n"


def sse_token(token: str) -> str:
    return sse_payload({"token": token})


def sse_payload(payload: dict[str, object]) -> str:
    return f"data: {json.dumps(payload)}\n\n"
