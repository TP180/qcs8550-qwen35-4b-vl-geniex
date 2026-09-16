#!/usr/bin/env python3
"""Run a bounded concurrent image request test and save evidence."""
import argparse
import asyncio
import json
import math
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
import time

import httpx


def percentile(values: list[float], rank: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(rank * len(ordered)) - 1)]


async def one_request(client, url, image_name, image, media_type, question, number, gate):
    async with gate:
        started = datetime.now(timezone.utc).isoformat()
        tick = time.perf_counter()
        status = None
        error = None
        try:
            response = await client.post(
                url,
                files={"image": (image_name, image, media_type)},
                data={"question": question},
                timeout=300,
            )
            status = response.status_code
            if not response.is_success:
                error = response.text[:500]
        except httpx.HTTPError as exc:
            error = repr(exc)
        elapsed = time.perf_counter() - tick
        return {
            "request": number,
            "started_at": started,
            "status": status,
            "elapsed_seconds": round(elapsed, 4),
            "ok": error is None and status is not None and 200 <= status < 300,
            "error": error,
        }


async def run(args: argparse.Namespace) -> int:
    if not args.image.is_file():
        raise SystemExit(f"图片不存在: {args.image}")
    base = args.api_url.rstrip("/")
    async with httpx.AsyncClient() as client:
        (await client.get(f"{base}/ready", timeout=15)).raise_for_status()
        image = args.image.read_bytes()
        media_type = mimetypes.guess_type(args.image.name)[0] or "application/octet-stream"
        gate = asyncio.Semaphore(args.concurrency)
        tasks = [
            one_request(
                client, f"{base}/v1/image/qa", args.image.name, image, media_type,
                args.question, index, gate
            )
            for index in range(1, args.requests + 1)
        ]
        records = await asyncio.gather(*tasks)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in records) + "\n",
        encoding="utf-8",
    )
    latencies = [item["elapsed_seconds"] for item in records if item["ok"]]
    summary = {
        "api_url": base,
        "requests": len(records),
        "concurrency": args.concurrency,
        "success": sum(item["ok"] for item in records),
        "failure": sum(not item["ok"] for item in records),
        "success_rate": round(sum(item["ok"] for item in records) / len(records), 6) if records else 0,
        "p50_seconds": percentile(latencies, 0.50),
        "p95_seconds": percentile(latencies, 0.95),
        "p99_seconds": percentile(latencies, 0.99),
        "source_log": str(args.output),
    }
    args.output.with_suffix(".summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["failure"] == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="并发阶梯图片 API 测试")
    parser.add_argument("--api-url", default="http://127.0.0.1:9000")
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--requests", type=int, default=8)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path(".run/concurrency-results.jsonl"))
    parser.add_argument("--question", default="请描述图片中的主要内容，并读取清晰可见的文字。")
    args = parser.parse_args()
    if args.requests <= 0 or args.concurrency <= 0:
        parser.error("--requests 和 --concurrency 必须大于 0")
    raise SystemExit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
