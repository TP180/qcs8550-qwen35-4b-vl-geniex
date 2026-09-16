import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="核对模型制品并生成完整性报告")
    parser.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parents[2] / "MODEL_MANIFEST.json")
    parser.add_argument("--output", type=Path, default=Path(".run/artifact-report.json"))
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    root = args.manifest.resolve().parent
    files = []
    failed = False
    for name in ("model", "mmproj"):
        entry = manifest["local_cpu"][name]
        path = root / entry["path"]
        exists = path.is_file()
        actual_hash = sha256(path) if exists else None
        actual_size = path.stat().st_size if exists else None
        ok = exists and actual_size == entry["bytes"] and actual_hash.lower() == entry["sha256"].lower()
        failed = failed or not ok
        files.append({
            "name": name,
            "path": str(path),
            "exists": exists,
            "expected_bytes": entry["bytes"],
            "actual_bytes": actual_size,
            "expected_sha256": entry["sha256"],
            "actual_sha256": actual_hash,
            "ok": ok,
        })

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(args.manifest.resolve()),
        "files": files,
        "all_ok": not failed,
        "board_files": "collect separately with board-ssh.ps1; never include private key",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
