#!/usr/bin/env python3
"""Validate conversion inputs and optionally invoke a vendor conversion command.

GenieX conversion tools are distributed with the Qualcomm SDK and their CLI
varies by SDK release. This script does not invent a fixed command: pass the
exact command from the installed SDK with --command.
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and run a GenieX model conversion command")
    parser.add_argument("--input", type=Path, required=True, help="原始模型目录或文件")
    parser.add_argument("--output", type=Path, required=True, help="转换产物目录")
    parser.add_argument("--command", help="已安装 GenieX SDK 提供的实际转换命令")
    parser.add_argument("--dry-run", action="store_true", help="只检查路径，不执行命令")
    args = parser.parse_args()

    if not args.input.exists():
        parser.error(f"输入不存在: {args.input}")
    args.output.mkdir(parents=True, exist_ok=True)
    print(f"input={args.input}")
    print(f"output={args.output}")
    if not args.command or args.dry_run:
        print("未执行转换。请按目标 GenieX SDK 文档提供 --command。")
        return 0

    command = args.command.format(input=shlex.quote(str(args.input)), output=shlex.quote(str(args.output)))
    print(f"执行: {command}")
    return subprocess.run(command, shell=True, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
