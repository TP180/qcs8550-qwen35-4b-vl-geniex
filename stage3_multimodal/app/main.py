from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from .config import settings
from .llm import LlamaServerError, answer_image, answer_text, healthcheck
from .ocr import OCRUnavailable, extract_text
from .rag.pipeline import RagPipeline

app = FastAPI(title="Qwen3.5-VL Stage 3", version="0.1.0")
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
INDEX_DIR = Path(__file__).resolve().parents[1] / "data"


async def read_image(file: UploadFile) -> tuple[bytes, str]:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "仅支持 JPEG、PNG、WEBP 图片")
    data = await file.read(settings.max_image_bytes + 1)
    if len(data) > settings.max_image_bytes:
        raise HTTPException(413, f"图片不能超过 {settings.max_image_mb} MB")
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(400, "文件不是有效图片") from exc
    return data, file.content_type


@app.get("/health")
async def health() -> dict:
    return {"service": "ok", "llama_server": await healthcheck()}


@app.get("/ready")
async def ready() -> dict:
    if not await healthcheck():
        raise HTTPException(503, "模型服务尚未就绪")
    return {"service": "ready", "llama_server": True}


@app.post("/v1/image/qa")
async def image_qa(question: str = Form(..., min_length=1, max_length=4000), image: UploadFile = File(...)) -> dict:
    data, media_type = await read_image(image)
    try:
        answer = await answer_image(question.strip(), data, media_type)
    except LlamaServerError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"question": question.strip(), "answer": answer, "model": settings.llama_model}


@app.post("/v1/ocr")
async def ocr(image: UploadFile = File(...)) -> dict:
    data, _ = await read_image(image)
    try:
        text = extract_text(data)
    except OCRUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"text": text, "language": settings.ocr_lang}


@app.post("/v1/rag/query")
async def rag_query(question: str = Form(..., min_length=1, max_length=4000), top_k: int = Form(3)) -> dict:
    if not (1 <= top_k <= 8):
        raise HTTPException(422, "top_k 必须在 1 到 8 之间")
    if not (INDEX_DIR / "vectors.npy").exists() or not (INDEX_DIR / "metadata.jsonl").exists():
        raise HTTPException(503, "知识库尚未建立，请先运行 build_index")
    try:
        pipeline = RagPipeline(INDEX_DIR)
        results = pipeline.retrieve(question.strip(), top_k=top_k)
        if not results:
            return {
                "question": question.strip(),
                "answer": "资料中没有找到与问题相关的内容。",
                "sources": [],
            }
        prompt = pipeline.build_prompt(question.strip(), results)
        answer = await answer_text(prompt)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(503, f"知识库不可用: {exc}") from exc
    except LlamaServerError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {
        "question": question.strip(),
        "answer": answer,
        "sources": [
            {"source": item["source"], "chunk_id": item["chunk_id"], "score": round(score, 4)}
            for score, item in results
        ],
    }
