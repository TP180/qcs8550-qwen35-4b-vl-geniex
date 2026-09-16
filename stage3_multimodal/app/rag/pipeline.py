import os
from pathlib import Path

from .embeddings import TfidfEmbedder, create_embedder
from .vector_store import VectorStore


class RagPipeline:
    def __init__(self, index_dir: Path) -> None:
        self.index_dir = index_dir
        backend = os.getenv("EMBEDDING_BACKEND", "tfidf").lower()
        if backend == "tfidf":
            self.embedder = TfidfEmbedder.load(index_dir / "tfidf_vectorizer.pkl")
        else:
            self.embedder = create_embedder()
        self.store = VectorStore(index_dir)

    def retrieve(self, question: str, top_k: int = 3) -> list[tuple[float, dict]]:
        query_vector = self.embedder.encode([question])[0]
        min_score = 0.0001 if isinstance(self.embedder, TfidfEmbedder) else 0.0
        return self.store.search(query_vector, top_k=max(1, min(top_k, 8)), min_score=min_score)

    def build_prompt(self, question: str, results: list[tuple[float, dict]]) -> str:
        context = "\n\n".join(
            f"[来源: {item['source']} | 片段: {item['chunk_id']}]\n{item['text']}"
            for _, item in results
        )
        return (
            "你是一个严谨的本地知识库助手。请只根据下面提供的资料回答问题。"
            "资料中没有答案时，请明确说‘资料中没有找到答案’，不要编造。"
            "回答末尾列出使用的来源。\n\n"
            f"资料:\n{context}\n\n问题: {question}"
        )
