from pathlib import Path
from unittest import TestCase

from streamlit.testing.v1 import AppTest


class StreamlitSmokeTests(TestCase):
    def test_initial_page_renders(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "streamlit_app.py"
        result = AppTest.from_file(str(app_path), default_timeout=10).run()
        self.assertFalse(result.exception)
        self.assertEqual(result.title[0].value, "本地图片问答与 OCR")
