#!/usr/bin/env python3
"""Build the local RAG index from documents/."""
import argparse
import os
from pathlib import Path

from app.rag.embeddings import TfidfEmbedder, create_embedder
from app.rag.loaders import load_directory
from app.rag.splitter import split_documents
from app.rag.vector_store import VectorStore


def main() -> None:
    parser = argparse.ArgumentParser(description="为本地文档建立向量索引")
    parser.add_argument("--directory", type=Path, default=Path("documents"))
    parser.add_argument("--output", type=Path, default=Path("data"))
    parser.add_argument("--size", type=int, default=700)
    parser.add_argument("--overlap", type=int, default=100)
    args = parser.parse_args()

    documents = load_directory(args.directory)
    chunks = split_documents(documents, size=args.size, overlap=args.overlap)
    if not chunks:
        raise SystemExit("没有找到可建库的文档，请把 TXT、MD、PDF 或 DOCX 放入 documents")
    embedder = create_embedder()
    vectors = embedder.encode([chunk.text for chunk in chunks], fit=isinstance(embedder, TfidfEmbedder))
    VectorStore(args.output).save(vectors, chunks)
    if isinstance(embedder, TfidfEmbedder):
        embedder.save(args.output / "tfidf_vectorizer.pkl")
    print(f"文档数: {len(documents)}")
    print(f"切片数: {len(chunks)}")
    print(f"向量维度: {vectors.shape[1]}")
    print(f"向量后端: {os.getenv('EMBEDDING_BACKEND', 'tfidf')}")
    print(f"索引目录: {args.output.resolve()}")


if __name__ == "__main__":
    main()
