from io import BytesIO

from PIL import Image, UnidentifiedImageError

from .config import settings


class OCRUnavailable(RuntimeError):
    pass


def extract_text(image_bytes: bytes) -> str:
    """Run local Tesseract OCR. Import is lazy so image QA works without OCR installed."""
    try:
        import pytesseract
    except ImportError as exc:
        raise OCRUnavailable("未安装 pytesseract，请安装 OCR 可选依赖") from exc
    try:
        image = Image.open(BytesIO(image_bytes))
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("无法读取图片") from exc
    try:
        return pytesseract.image_to_string(image, lang=settings.ocr_lang).strip()
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRUnavailable("未找到 Tesseract 可执行文件，请先安装 Tesseract") from exc
