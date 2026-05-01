from __future__ import annotations

from functools import lru_cache
from threading import Lock

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings


_model: SentenceTransformer | None = None
_model_lock = Lock()


def load_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer(settings.embedding_model_name)
    return _model


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype("float32")


def encode_batch(chunks: list[str]) -> np.ndarray:
    if not chunks:
        raise ValueError("Cannot embed an empty chunk list.")

    model = load_model()
    vectors = model.encode(
        chunks,
        batch_size=32,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return _normalize(np.asarray(vectors, dtype="float32"))


def encode_single(text: str) -> np.ndarray:
    stripped = text.strip()
    if not stripped:
        raise ValueError("Question must not be empty.")

    return _encode_single_cached(stripped).copy()


@lru_cache(maxsize=512)
def _encode_single_cached(text: str) -> np.ndarray:
    vector = encode_batch([text])
    return vector.reshape(1, -1)
