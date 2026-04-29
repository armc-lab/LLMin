#!/usr/bin/env python3
"""Crawl local insurance materials and export text chunks.

This script is designed for the common offline workflow:
- recursively scan a directory for PDF/TXT/MD/HTML files
- extract plain text
- chunk long text into model-friendly segments
- export JSONL for downstream fine-tuning, retrieval indexing, or manual review

Examples:
python scripts/crawl_insurance_materials.py \
  --input /data2/wangliangmin/snap/Baichuan/contracts \
  --output data/insurance_materials.jsonl

python scripts/crawl_insurance_materials.py \
  --input /data2/wangliangmin/snap/Baichuan/contracts/a.pdf \
  --output data/a.jsonl \
  --chunk-size 900
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence

try:
    import fitz  # PyMuPDF
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "缺少 PyMuPDF(fitz)。请在 baichuan-chat 环境中运行，或先安装依赖：conda run -n baichuan-chat python -m pip install PyMuPDF"
    ) from exc


SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md", ".html", ".htm"}


@dataclass
class ChunkRecord:
    source_path: str
    file_name: str
    file_type: str
    sha256: str
    chunk_index: int
    chunk_count: int
    char_count: int
    text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl local insurance materials")
    parser.add_argument("--input", required=True, help="Input file or directory")
    parser.add_argument("--output", required=True, help="Output JSONL path")
    parser.add_argument("--chunk-size", type=int, default=900, help="Chunk size in characters")
    parser.add_argument("--chunk-overlap", type=int, default=120, help="Overlap size in characters")
    parser.add_argument("--min-chunk-chars", type=int, default=120, help="Skip chunks shorter than this")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files when scanning directories")
    parser.add_argument("--dedup", action="store_true", help="Deduplicate chunks by SHA256")
    return parser.parse_args()


def iter_input_files(path: Path, include_hidden: bool = False) -> Iterator[Path]:
    if path.is_file():
        if path.suffix.lower() in SUPPORTED_SUFFIXES:
            yield path
        return

    if not path.exists():
        raise FileNotFoundError(f"Input path not found: {path}")

    for item in sorted(path.rglob("*")):
        if not item.is_file():
            continue
        if item.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if not include_hidden and any(part.startswith(".") for part in item.parts):
            continue
        yield item


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\u3000", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_html_tags(text: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</p\s*>", "\n", text)
    text = re.sub(r"(?is)<.*?>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    return normalize_text(text)


def extract_pdf_text(path: Path) -> str:
    with fitz.open(path) as doc:
        pages = [page.get_text("text") for page in doc]
    return normalize_text("\n".join(pages))


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_text(path)
    if suffix in {".txt", ".md"}:
        return normalize_text(path.read_text(encoding="utf-8", errors="ignore"))
    if suffix in {".html", ".htm"}:
        return strip_html_tags(path.read_text(encoding="utf-8", errors="ignore"))
    raise ValueError(f"Unsupported file type: {path}")


def split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []

    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
    chunks: List[str] = []
    buffer: List[str] = []

    def flush_buffer() -> None:
        nonlocal buffer
        if buffer:
            chunks.append("\n".join(buffer).strip())
            buffer = []

    for para in paragraphs:
        if len(para) > chunk_size:
            flush_buffer()
            start = 0
            step = max(1, chunk_size - overlap)
            while start < len(para):
                piece = para[start:start + chunk_size].strip()
                if piece:
                    chunks.append(piece)
                start += step
            continue

        cur_len = sum(len(x) for x in buffer) + max(0, len(buffer) - 1)
        if buffer and cur_len + len(para) > chunk_size:
            flush_buffer()
        buffer.append(para)

    flush_buffer()

    if overlap > 0 and len(chunks) > 1:
        merged: List[str] = []
        prev_tail = ""
        for chunk in chunks:
            if prev_tail and chunk.startswith(prev_tail):
                merged.append(chunk)
            else:
                merged.append(chunk)
            prev_tail = chunk[-overlap:]
        chunks = merged

    return [normalize_text(c) for c in chunks if normalize_text(c)]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    seen_hashes = set()
    records: List[ChunkRecord] = []
    source_files = list(iter_input_files(input_path, include_hidden=args.include_hidden))

    for file_path in source_files:
        try:
            raw_text = extract_text(file_path)
        except Exception as exc:  # noqa: BLE001
            print(f"[skip] {file_path}: {exc}")
            continue

        chunks = split_text(raw_text, chunk_size=args.chunk_size, overlap=args.chunk_overlap)
        chunk_count = len(chunks)
        if not chunks:
            print(f"[skip] {file_path}: empty after extraction")
            continue

        file_hash = sha256_text(raw_text)
        for idx, chunk in enumerate(chunks, start=1):
            if len(chunk) < args.min_chunk_chars:
                continue
            chunk_hash = sha256_text(chunk)
            if args.dedup and chunk_hash in seen_hashes:
                continue
            seen_hashes.add(chunk_hash)
            records.append(
                ChunkRecord(
                    source_path=str(file_path),
                    file_name=file_path.name,
                    file_type=file_path.suffix.lower().lstrip("."),
                    sha256=file_hash,
                    chunk_index=idx,
                    chunk_count=chunk_count,
                    char_count=len(chunk),
                    text=chunk,
                )
            )

    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    print(f"[done] files={len(source_files)} chunks={len(records)} output={output_path}")


if __name__ == "__main__":
    main()