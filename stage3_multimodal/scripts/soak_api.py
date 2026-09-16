#!/usr/bin/env python3
"""Run serial image requests and write JSONL plus a latency summary."""
import argparse
import json
import math
import mimetypes
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


def percentile(values: list[float], rank: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(rank * len(ordered)) - 1)]


def main() -> int:
    parser = argparse.ArgumentParser(description="串行图片 API soak 测试")
    parser.add_argument("--api-url", default="http://127.0.0.1:9000")
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--requests", type=int, default=0)
    parser.add_argument("--duration-seconds", type=int, default=0)
    parser.add_argument("--interval-seconds", type=float, default=0.0)
    parser.add_argument("--output", type=Path, default=Path(".run/soak-results.jsonl"))
    parser.add_argument("--question", default="请描述图片中的主要内容，并读取清晰可见的文字。")
    args = parser.parse_args()

    if (args.requests <= 0) == (args.duration_seconds <= 0):
        parser.error("必须且只能指定 --requests 或 --duration-seconds")
    if not args.image.is_file():
        parser.error(f"图片不存在: {args.image}")

    base = args.api_url.rstrip("/")
    requests.get(f"{base}/ready", timeout=15).raise_for_status()
    image_bytes = args.image.read_bytes()
    media_type = mimetypes.guess_type(args.image.name)[0] or "application/octet-stream"
    deadline = time.monotonic() + args.duration_seconds if args.duration_seconds > 0 else None
    records = []
    latencies = []
    started = time.monotonic()
    index = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as log:
        while (args.requests <= 0 or index < args.requests) and (
            deadline is None or time.monotonic() < deadline
        ):
            index += 1
            wall_start = datetime.now(timezone.utc).isoformat()
            tick = time.perf_counter()
            status = None
            error = None
            body = {}
            try:
                response = requests.post(
                    f"{base}/v1/image/qa",
                    files={"image": (args.image.name, image_bytes, media_type)},
                    data={"question": args.question},
                    timeout=300,
                )
                status = response.status_code
                try:
                    body = response.json()
                except ValueError:
                    body = {"raw": response.text[:500]}
                if not response.ok:
                    error = str(body.get("detail", body))
            except requests.RequestException as exc:
                error = repr(exc)
            elapsed = time.perf_counter() - tick
            ok = error is None and status is not None and 200 <= status < 300
            if ok:
                latencies.append(elapsed)
            record = {
                "request": index,
                "started_at": wall_start,
                "status": status,
                "elapsed_seconds": round(elapsed, 4),
                "ok": ok,
                "error": error,
                "usage": body.get("usage", {}) if isinstance(body, dict) else {},
            }
            log.write(json.dumps(record, ensure_ascii=False) + "\n")
            log.flush()
            records.append(record)
            if args.interval_seconds > 0:
                time.sleep(args.interval_seconds)

    summary = {
        "started_at": records[0]["started_at"] if records else None,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.monotonic() - started, 3),
        "requests": len(records),
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
    return 0 if summary["failure"] == 0 and summary["requests"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
