from io import BytesIO
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import AsyncMock, patch

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.rag.embeddings import TfidfEmbedder
from app.rag.splitter import Chunk
from app.rag.vector_store import VectorStore


def png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), color="white").save(buffer, format="PNG")
    return buffer.getvalue()


class ApiTests(TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    @patch("app.main.healthcheck", new_callable=AsyncMock)
    def test_health_and_readiness(self, healthcheck: AsyncMock) -> None:
        healthcheck.return_value = True
        self.assertEqual(self.client.get("/health").json(), {"service": "ok", "llama_server": True})
        self.assertEqual(self.client.get("/ready").status_code, 200)
        healthcheck.return_value = False
        self.assertEqual(self.client.get("/ready").status_code, 503)

    def test_image_type_is_validated(self) -> None:
        response = self.client.post(
            "/v1/image/qa",
            data={"question": "describe image"},
            files={"image": ("sample.txt", b"not an image", "text/plain")},
        )
        self.assertEqual(response.status_code, 415)

    @patch("app.main.answer_image", new_callable=AsyncMock)
    def test_image_question(self, answer_image: AsyncMock) -> None:
        answer_image.return_value = "a white image"
        response = self.client.post(
            "/v1/image/qa",
            data={"question": "describe image"},
            files={"image": ("sample.png", png_bytes(), "image/png")},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "a white image")

    @patch("app.main.answer_text", new_callable=AsyncMock)
    def test_rag_query_uses_existing_index(self, answer_text: AsyncMock) -> None:
        answer_text.return_value = "The project uses FastAPI and a local model."
        with tempfile.TemporaryDirectory() as directory:
            index_dir = Path(directory)
            chunks = [Chunk("README.md:0", "README.md", "The project uses FastAPI and a local model.")]
            embedder = TfidfEmbedder()
            vectors = embedder.encode([chunk.text for chunk in chunks], fit=True)
            embedder.save(index_dir / "tfidf_vectorizer.pkl")
            VectorStore(index_dir).save(np.asarray(vectors, dtype="float32"), chunks)
            with patch("app.main.INDEX_DIR", index_dir):
                response = self.client.post(
                    "/v1/rag/query",
                    data={"question": "Which technology does the project use?", "top_k": "2"},
                )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["sources"])
