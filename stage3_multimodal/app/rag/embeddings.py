import os
import pickle
import re
from pathlib import Path

import numpy as np


DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"


def tokenize_text(text: str) -> list[str]:
    """Split Chinese into characters and keep English words for offline TF-IDF."""
    return re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9_]+", text.lower())


class Embedder:
    def __init__(self, model_name: str | None = None) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)
        self.model = SentenceTransformer(self.model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = self.model.encode(
            texts,
            batch_size=16,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        return np.asarray(vectors, dtype="float32")


class TfidfEmbedder:
    """Offline fallback: no model download, useful for learning the RAG data flow."""

    def __init__(self, vectorizer=None) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = vectorizer or TfidfVectorizer(
            tokenizer=tokenize_text,
            token_pattern=None,
            lowercase=False,
        )

    def encode(self, texts: list[str], fit: bool = False) -> np.ndarray:
        matrix = self.vectorizer.fit_transform(texts) if fit else self.vectorizer.transform(texts)
        return matrix.toarray().astype("float32")

    def save(self, path: Path) -> None:
        with path.open("wb") as handle:
            pickle.dump(self.vectorizer, handle)

    @classmethod
    def load(cls, path: Path) -> "TfidfEmbedder":
        with path.open("rb") as handle:
            return cls(pickle.load(handle))


def create_embedder() -> Embedder | TfidfEmbedder:
    backend = os.getenv("EMBEDDING_BACKEND", "tfidf").lower()
    if backend == "sentence-transformers":
        return Embedder()
    if backend == "tfidf":
        return TfidfEmbedder()
    raise ValueError("EMBEDDING_BACKEND 只能是 tfidf 或 sentence-transformers")
