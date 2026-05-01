from __future__ import annotations

import re


_BLANK_LINE_RE = re.compile(r"\n\s*\n+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if overlap < 0:
        raise ValueError("overlap must not be negative.")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    normalized = _normalize_text(text)
    if not normalized:
        return []

    units = _build_units(normalized, chunk_size)
    return _pack_units(units, chunk_size, overlap)


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _build_units(text: str, chunk_size: int) -> list[str]:
    units: list[str] = []
    pending_heading = ""

    for raw_block in _BLANK_LINE_RE.split(text):
        block = re.sub(r"\n+", " ", raw_block).strip()
        if not block:
            continue

        if _looks_like_heading(block):
            pending_heading = f"{pending_heading}\n{block}".strip()
            continue

        if pending_heading:
            block = f"{pending_heading}\n{block}"
            pending_heading = ""

        if len(block) <= chunk_size:
            units.append(block)
        else:
            units.extend(_split_large_block(block, chunk_size))

    if pending_heading:
        units.append(pending_heading)

    return units


def _looks_like_heading(block: str) -> bool:
    words = block.split()
    return (
        len(block) <= 120
        and len(words) <= 12
        and not block.endswith((".", "?", "!", ",", ";", ":"))
    )


def _split_large_block(block: str, chunk_size: int) -> list[str]:
    units: list[str] = []
    sentences = [sentence.strip() for sentence in _SENTENCE_RE.split(block) if sentence.strip()]

    for sentence in sentences:
        if len(sentence) <= chunk_size:
            units.append(sentence)
        else:
            units.extend(_split_by_words(sentence, chunk_size))

    return units


def _split_by_words(text: str, chunk_size: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []

    for word in text.split():
        candidate = " ".join([*current, word])
        if current and len(candidate) > chunk_size:
            chunks.append(" ".join(current))
            current = [word]
        else:
            current.append(word)

    if current:
        chunks.append(" ".join(current))

    print(chunks)

    return chunks


def _pack_units(units: list[str], chunk_size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []

    for unit in units:
        if not current:
            current = [unit]
            continue

        if _joined_len([*current, unit]) <= chunk_size:
            current.append(unit)
            continue

        chunks.append(_join_units(current))
        overlap_units = _tail_units(current, overlap)
        current = [*overlap_units, unit]
        if _joined_len(current) > chunk_size:
            current = [unit]

    if current:
        chunk = _join_units(current)
        if not chunks or chunks[-1] != chunk:
            chunks.append(chunk)
    
    print(chunks)
    return chunks


def _tail_units(units: list[str], overlap: int) -> list[str]:
    if overlap <= 0:
        return []

    tail: list[str] = []
    for unit in reversed(units):
        tail.insert(0, unit)
        if _joined_len(tail) >= overlap:
            break
    return tail


def _join_units(units: list[str]) -> str:
    return "\n\n".join(unit.strip() for unit in units if unit.strip())


def _joined_len(units: list[str]) -> int:
    return len(_join_units(units))
