#!/usr/bin/env python3
"""Run the repository serial image benchmark and preserve JSON evidence."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="调用 stage3_multimodal 的图片 API benchmark")
    parser.add_argument("--api-url", default="http://127.0.0.1:9000")
    parser.add_argument("--image", type=Path, default=Path("demo/test_image.jpg"))
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path(".run/benchmark.jsonl"))
    args = parser.parse_args()
    command = [
        sys.executable,
        "stage3_multimodal/scripts/soak_api.py",
        "--api-url",
        args.api_url,
        "--image",
        str(args.image),
        "--requests",
        str(args.requests),
        "--output",
        str(args.output),
    ]
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
