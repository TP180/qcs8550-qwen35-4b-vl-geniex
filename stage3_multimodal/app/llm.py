import base64
from typing import Any

import httpx

from .config import settings


class LlamaServerError(RuntimeError):
    """Raised when llama-server rejects or cannot answer a request."""


def _data_url(content: bytes, media_type: str) -> str:
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def _extract_content(response: httpx.Response) -> str:
    try:
        body = response.json()
        content = body["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LlamaServerError("llama-server 返回格式无效") from exc
    if not isinstance(content, str):
        raise LlamaServerError("llama-server 返回的回答不是文本")
    return content


async def answer_image(question: str, image: bytes, media_type: str) -> str:
    payload: dict[str, Any] = {
        "model": settings.llama_model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": _data_url(image, media_type)}},
        ]}],
        "temperature": 0.2,
        "stream": False,
    }
    url = settings.llama_base_url.rstrip("/") + "/v1/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except (httpx.HTTPError, ValueError) as exc:
        raise LlamaServerError(f"llama-server 请求失败: {exc}") from exc
    return _extract_content(response)


async def answer_text(prompt: str) -> str:
    payload: dict[str, Any] = {
        "model": settings.llama_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "stream": False,
    }
    url = settings.llama_base_url.rstrip("/") + "/v1/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except (httpx.HTTPError, ValueError) as exc:
        raise LlamaServerError(f"llama-server 请求失败: {exc}") from exc
    return _extract_content(response)


async def healthcheck() -> bool:
    url = settings.llama_base_url.rstrip("/") + "/health"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            return (await client.get(url)).is_success
    except httpx.HTTPError:
        return False
