#!/usr/bin/env python3
"""Validate quantization inputs and run an SDK-provided quantizer command."""
from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a GenieX/llama.cpp quantization command")
    parser.add_argument("--input", type=Path, required=True, help="转换后的语言模型文件")
    parser.add_argument("--output", type=Path, required=True, help="量化后的 GGUF 文件")
    parser.add_argument("--type", default="Q4_0", help="目标量化格式，例如 Q4_0；以 SDK 支持为准")
    parser.add_argument("--command", help="实际量化命令，支持 {input} {output} {type} 占位符")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"输入文件不存在: {args.input}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not args.command or args.dry_run:
        print(f"input={args.input}\noutput={args.output}\ntype={args.type}")
        print("未执行量化。请使用目标 SDK 实际提供的量化工具。")
        return 0
    command = args.command.format(
        input=shlex.quote(str(args.input)), output=shlex.quote(str(args.output)), type=shlex.quote(args.type)
    )
    print(f"执行: {command}")
    return subprocess.run(command, shell=True, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
