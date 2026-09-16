from io import BytesIO
from unittest import TestCase
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


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
            data={"question": "描述图片"},
            files={"image": ("sample.txt", b"not an image", "text/plain")},
        )
        self.assertEqual(response.status_code, 415)

    @patch("app.main.answer_image", new_callable=AsyncMock)
    def test_image_question(self, answer_image: AsyncMock) -> None:
        answer_image.return_value = "一张白色图片"
        response = self.client.post(
            "/v1/image/qa",
            data={"question": "描述图片"},
            files={"image": ("sample.png", png_bytes(), "image/png")},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "一张白色图片")

    @patch("app.main.answer_text", new_callable=AsyncMock)
    def test_rag_query_uses_existing_index(self, answer_text: AsyncMock) -> None:
        answer_text.return_value = "项目使用 FastAPI 和本地模型。"
        response = self.client.post(
            "/v1/rag/query",
            data={"question": "项目使用了哪些技术？", "top_k": "2"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["sources"])
