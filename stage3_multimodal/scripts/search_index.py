import argparse
import os
from pathlib import Path

from app.rag.embeddings import TfidfEmbedder, create_embedder
from app.rag.vector_store import VectorStore


def main() -> None:
    parser = argparse.ArgumentParser(description="搜索本地知识库中的相关片段")
    parser.add_argument("query")
    parser.add_argument("--index", type=Path, default=Path("data"))
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    if os.getenv("EMBEDDING_BACKEND", "tfidf").lower() == "tfidf":
        embedder = TfidfEmbedder.load(args.index / "tfidf_vectorizer.pkl")
    else:
        embedder = create_embedder()
    query_vector = embedder.encode([args.query])[0]
    results = VectorStore(args.index).search(query_vector, top_k=args.top_k)
    for rank, (score, metadata) in enumerate(results, start=1):
        print(f"\n[{rank}] 相似度: {score:.4f} | 来源: {metadata['source']} | 片段: {metadata['chunk_id']}")
        print(metadata["text"])


if __name__ == "__main__":
    main()
