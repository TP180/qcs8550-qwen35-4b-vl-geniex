from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    llama_base_url: str = os.getenv("LLAMA_BASE_URL", "http://127.0.0.1:8080")
    llama_model: str = os.getenv("LLAMA_MODEL", "Qwen3.5-0.8B-Q4_K_M.gguf")
    request_timeout: float = float(os.getenv("LLAMA_TIMEOUT", "120"))
    max_image_mb: int = int(os.getenv("MAX_IMAGE_MB", "10"))
    ocr_lang: str = os.getenv("OCR_LANG", "chi_sim+eng")

    @property
    def max_image_bytes(self) -> int:
        return self.max_image_mb * 1024 * 1024


settings = Settings()
