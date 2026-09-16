#!/usr/bin/env python3
"""Run a real readiness, RAG, image-QA and optional OCR smoke test."""
import argparse
import mimetypes
from pathlib import Path

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the FastAPI, RAG and image-QA paths")
    parser.add_argument("--api-url", default="http://127.0.0.1:9000")
    parser.add_argument("--image", type=Path, default=Path("../demo/test_image.jpg"))
    parser.add_argument("--ocr", action="store_true")
    args = parser.parse_args()

    base = args.api_url.rstrip("/")
    ready = requests.get(f"{base}/ready", timeout=15)
    ready.raise_for_status()
    print("READY", ready.json())

    rag = requests.post(
        f"{base}/v1/rag/query",
        data={"question": "项目中使用了哪些技术？", "top_k": "3"},
        timeout=180,
    )
    rag.raise_for_status()
    rag_body = rag.json()
    print("RAG sources:", len(rag_body.get("sources", [])))
    print("RAG answer:", rag_body.get("answer", "")[:240])

    if not args.image.is_file():
        raise SystemExit(f"图片不存在: {args.image}")
    media_type = mimetypes.guess_type(args.image.name)[0] or "application/octet-stream"
    with args.image.open("rb") as handle:
        image = requests.post(
            f"{base}/v1/image/qa",
            files={"image": (args.image.name, handle, media_type)},
            data={"question": "请描述图片中的主要内容，并读取清晰可见的文字。"},
            timeout=300,
        )
    image.raise_for_status()
    print("IMAGE answer:", image.json().get("answer", "")[:240])

    if args.ocr:
        with args.image.open("rb") as handle:
            ocr = requests.post(
                f"{base}/v1/ocr",
                files={"image": (args.image.name, handle, media_type)},
                timeout=60,
            )
        ocr.raise_for_status()
        print("OCR text:", ocr.json().get("text", "")[:240])

    print("SMOKE PASS")


if __name__ == "__main__":
    main()
