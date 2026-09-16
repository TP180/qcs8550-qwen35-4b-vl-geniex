import json
from pathlib import Path

import numpy as np

from .splitter import Chunk


class VectorStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.vectors_path = directory / "vectors.npy"
        self.metadata_path = directory / "metadata.jsonl"

    def save(self, vectors: np.ndarray, chunks: list[Chunk]) -> None:
        if len(vectors) != len(chunks):
            raise ValueError("向量数量和文本片段数量不一致")
        self.directory.mkdir(parents=True, exist_ok=True)
        np.save(self.vectors_path, vectors)
        with self.metadata_path.open("w", encoding="utf-8") as handle:
            for chunk in chunks:
                handle.write(json.dumps({
                    "chunk_id": chunk.chunk_id,
                    "source": chunk.source,
                    "text": chunk.text,
                }, ensure_ascii=False) + "\n")

    def search(self, query_vector: np.ndarray, top_k: int = 3, min_score: float = 0.0) -> list[tuple[float, dict]]:
        vectors = np.load(self.vectors_path)
        metadata = [json.loads(line) for line in self.metadata_path.read_text(encoding="utf-8").splitlines() if line]
        if len(vectors) != len(metadata):
            raise RuntimeError("向量文件和元数据数量不一致，请重新建库")
        query = np.asarray(query_vector, dtype="float32").reshape(-1)
        scores = vectors @ query
        indices = [index for index in np.argsort(scores)[::-1] if scores[index] > min_score][:top_k]
        return [(float(scores[index]), metadata[index]) for index in indices]
