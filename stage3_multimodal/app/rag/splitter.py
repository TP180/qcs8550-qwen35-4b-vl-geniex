from dataclasses import dataclass

from .loaders import Document


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source: str
    text: str


def split_document(document: Document, size: int = 700, overlap: int = 100) -> list[Chunk]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("需要满足 size > 0 且 0 <= overlap < size")
    text = document.text
    chunks: list[Chunk] = []
    start = 0
    number = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = max(text.rfind("\n", start, end), text.rfind("。", start, end), text.rfind(".", start, end))
            if boundary > start + size // 2:
                end = boundary + 1
        piece = text[start:end].strip()
        if piece:
            chunks.append(Chunk(f"{document.source}:{number}", document.source, piece))
            number += 1
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def split_documents(documents: list[Document], size: int = 700, overlap: int = 100) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        chunks.extend(split_document(document, size=size, overlap=overlap))
    return chunks
