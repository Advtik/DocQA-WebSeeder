from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.routers import ask, upload
from app.services import embedding_service, qa_service, vector_store_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_directories()
    await run_in_threadpool(embedding_service.load_model)
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(ask.router)


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "indexed_documents": vector_store_service.document_count(),
        "ollama_available": await qa_service.is_ollama_available(),
    }
