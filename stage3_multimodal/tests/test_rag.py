import tempfile
from pathlib import Path
from unittest import TestCase

import numpy as np

from app.rag.loaders import Document, load_directory
from app.rag.splitter import Chunk, split_document
from app.rag.vector_store import VectorStore


class RagTests(TestCase):
    def test_load_and_split_utf8_document(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_text("第一行。\n\n第二行。", encoding="utf-8")
            documents = load_directory(Path(directory))
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].text, "第一行。\n第二行。")
        self.assertGreaterEqual(len(split_document(documents[0], size=6, overlap=1)), 2)

    def test_vector_store_returns_best_match(self) -> None:
        chunks = [Chunk("a:0", "a.txt", "甲"), Chunk("b:0", "b.txt", "乙")]
        with tempfile.TemporaryDirectory() as directory:
            store = VectorStore(Path(directory))
            store.save(np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype="float32"), chunks)
            results = store.search(np.asarray([0.9, 0.1], dtype="float32"), top_k=1)
        self.assertEqual(results[0][1]["chunk_id"], "a:0")

    def test_invalid_split_configuration_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            split_document(Document("sample.txt", "text"), size=10, overlap=10)
