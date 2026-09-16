import argparse
from pathlib import Path

from app.rag.loaders import load_directory
from app.rag.splitter import split_documents


def main() -> None:
    parser = argparse.ArgumentParser(description="查看文档解析和切块结果")
    parser.add_argument("--directory", type=Path, default=Path("documents"))
    parser.add_argument("--size", type=int, default=700)
    parser.add_argument("--overlap", type=int, default=100)
    args = parser.parse_args()

    documents = load_directory(args.directory)
    chunks = split_documents(documents, size=args.size, overlap=args.overlap)
    print(f"读取文档: {len(documents)} 个")
    print(f"生成切片: {len(chunks)} 个")
    for chunk in chunks:
        preview = chunk.text.replace("\n", " ")[:120]
        print(f"[{chunk.chunk_id}] {preview}")


if __name__ == "__main__":
    main()
