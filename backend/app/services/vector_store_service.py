from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

import faiss
import numpy as np


@dataclass(frozen=True)
class DocumentMetadata:
    filename: str
    chunk_count: int


faiss_indices: dict[str, faiss.Index] = {}
chunk_stores: dict[str, list[str]] = {}
document_metadata: dict[str, DocumentMetadata] = {}
_store_lock = RLock()


def create_index(
    document_id: str,
    vectors: np.ndarray,
    chunks: list[str],
    filename: str,
) -> None:
    if vectors.ndim != 2:
        raise ValueError("vectors must have shape (n, dimensions).")
    if vectors.shape[0] != len(chunks):
        raise ValueError("vectors and chunks must have matching lengths.")
    if vectors.shape[0] == 0:
        raise ValueError("Cannot index an empty document.")

    prepared_vectors = np.asarray(vectors, dtype="float32")
    dimension = prepared_vectors.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(prepared_vectors)

    with _store_lock:
        faiss_indices[document_id] = index
        chunk_stores[document_id] = chunks
        document_metadata[document_id] = DocumentMetadata(
            filename=filename,
            chunk_count=len(chunks),
        )


def search(
    document_id: str,
    query_vector: np.ndarray,
    k: int,
) -> list[dict[str, int | float | str]]:
    with _store_lock:
        index = faiss_indices.get(document_id)
        chunks = chunk_stores.get(document_id)

    if index is None or chunks is None:
        raise KeyError(f"Document {document_id} is not indexed.")

    top_k = max(1, min(k, index.ntotal))
    prepared_query = np.asarray(query_vector, dtype="float32").reshape(1, -1)
    scores, indices = index.search(prepared_query, top_k)

    results: list[dict[str, int | float | str]] = []
    for score, idx in zip(scores[0], indices[0], strict=False):
        if idx == -1:
            continue
        results.append(
            {
                "chunk_index": int(idx),
                "score": float(score),
                "text": chunks[int(idx)],
            }
        )
    return results


def document_exists(document_id: str) -> bool:
    with _store_lock:
        return document_id in faiss_indices


def document_count() -> int:
    with _store_lock:
        return len(faiss_indices)


def get_document_metadata(document_id: str) -> DocumentMetadata | None:
    with _store_lock:
        return document_metadata.get(document_id)


def delete_document(document_id: str) -> None:
    with _store_lock:
        faiss_indices.pop(document_id, None)
        chunk_stores.pop(document_id, None)
        document_metadata.pop(document_id, None)
