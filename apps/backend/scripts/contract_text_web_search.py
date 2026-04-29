#!/usr/bin/env python3
"""Local web search for insurance contract text.

This script loads either:
- a crawled JSONL corpus produced by crawl_insurance_materials.py
- a source directory/file and builds an in-memory chunk index on startup

It exposes a small FastAPI app with:
- a browser page for keyword search
- /api/search for JSON search results
- /api/documents for corpus stats

Examples:
python scripts/contract_text_web_search.py \
  --corpus tests/insurance_materials.jsonl \
  --host 127.0.0.1 --port 8098

python scripts/contract_text_web_search.py \
  --input /data2/wangliangmin/snap/Baichuan/contracts \
  --host 0.0.0.0 --port 8098
"""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

try:
    import uvicorn
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "缺少 uvicorn。请在 baichuan-chat 环境中运行，或先安装依赖：conda run -n baichuan-chat python -m pip install uvicorn"
    ) from exc

try:
    from scripts.crawl_insurance_materials import (
        SUPPORTED_SUFFIXES,
        extract_text,
        iter_input_files,
        normalize_text,
        split_text,
        sha256_text,
    )
except Exception:  # pragma: no cover
    from crawl_insurance_materials import (  # type: ignore
        SUPPORTED_SUFFIXES,
        extract_text,
        iter_input_files,
        normalize_text,
        split_text,
        sha256_text,
    )


@dataclass
class SearchChunk:
    source_path: str
    file_name: str
    file_type: str
    sha256: str
    chunk_index: int
    chunk_count: int
    char_count: int
    text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local browser search for contract text")
    parser.add_argument("--input", default="", help="Input file or directory to build corpus on startup")
    parser.add_argument("--corpus", default="", help="Existing JSONL corpus exported by crawl_insurance_materials.py")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8098, help="Bind port")
    parser.add_argument("--chunk-size", type=int, default=900, help="Chunk size when building from source files")
    parser.add_argument("--chunk-overlap", type=int, default=120, help="Chunk overlap when building from source files")
    parser.add_argument("--min-chunk-chars", type=int, default=80, help="Skip chunks shorter than this")
    parser.add_argument("--max-results", type=int, default=30, help="Maximum results per query")
    parser.add_argument("--dedup", action="store_true", help="Deduplicate chunks by SHA256")
    return parser.parse_args()


def load_corpus_jsonl(path: Path) -> List[SearchChunk]:
    chunks: List[SearchChunk] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                continue
            text = str(row.get("text", "")).strip()
            if not text:
                continue
            chunks.append(
                SearchChunk(
                    source_path=str(row.get("source_path", "")),
                    file_name=str(row.get("file_name", "")),
                    file_type=str(row.get("file_type", "")),
                    sha256=str(row.get("sha256", "")),
                    chunk_index=int(row.get("chunk_index", 0) or 0),
                    chunk_count=int(row.get("chunk_count", 0) or 0),
                    char_count=int(row.get("char_count", len(text)) or len(text)),
                    text=normalize_text(text),
                )
            )
    return chunks


def build_corpus_from_source(input_path: Path, chunk_size: int, chunk_overlap: int, min_chunk_chars: int, dedup: bool) -> List[SearchChunk]:
    seen_hashes = set()
    chunks: List[SearchChunk] = []
    source_files = list(iter_input_files(input_path, include_hidden=False))

    for file_path in source_files:
        try:
            raw_text = extract_text(file_path)
        except Exception:
            continue

        pieces = split_text(raw_text, chunk_size=chunk_size, overlap=chunk_overlap)
        file_hash = sha256_text(raw_text)
        chunk_count = len(pieces)

        for idx, piece in enumerate(pieces, start=1):
            if len(piece) < min_chunk_chars:
                continue
            piece_hash = sha256_text(piece)
            if dedup and piece_hash in seen_hashes:
                continue
            seen_hashes.add(piece_hash)
            chunks.append(
                SearchChunk(
                    source_path=str(file_path),
                    file_name=file_path.name,
                    file_type=file_path.suffix.lower().lstrip("."),
                    sha256=file_hash,
                    chunk_index=idx,
                    chunk_count=chunk_count,
                    char_count=len(piece),
                    text=piece,
                )
            )
    return chunks


def tokenize_query(query: str) -> List[str]:
    query = normalize_text(query)
    if not query:
        return []
    raw_terms = re.findall(r"\d+(?:\.\d+)*|[\u4e00-\u9fff]{2,8}|[a-zA-Z0-9%]+", query)
    stop_words = {"合同", "条款", "内容", "什么", "怎么", "是否", "可以", "请问", "一下", "这个", "那个"}
    terms: List[str] = []
    for term in raw_terms:
        t = term.strip()
        if not t or t in stop_words:
            continue
        if t not in terms:
            terms.append(t)
    return terms


def score_chunk(text: str, terms: List[str]) -> float:
    if not text or not terms:
        return 0.0

    lowered = text.lower()
    score = 0.0
    for term in terms:
        term_l = term.lower()
        cnt = lowered.count(term_l)
        if cnt:
            score += 1.0 + min(cnt, 5) * 0.35

    head = lowered[:400]
    if any(term.lower() in head for term in terms):
        score += 0.5

    return score


def highlight(text: str, terms: List[str]) -> str:
    escaped = html.escape(text)
    if not terms:
        return escaped

    # Longer terms first to reduce partial overlaps.
    for term in sorted(set(terms), key=len, reverse=True):
        if not term:
            continue
        escaped = re.sub(
            re.escape(html.escape(term)),
            lambda m: f"<mark>{m.group(0)}</mark>",
            escaped,
            flags=re.IGNORECASE,
        )
    return escaped.replace("\n", "<br>")


def build_excerpt(text: str, terms: List[str], window: int = 220) -> str:
    if not text:
        return ""
    if not terms:
        return text[:window]

    lowered = text.lower()
    best_pos = -1
    for term in terms:
        pos = lowered.find(term.lower())
        if pos >= 0 and (best_pos < 0 or pos < best_pos):
            best_pos = pos

    if best_pos < 0:
        return text[:window]

    start = max(0, best_pos - window // 3)
    end = min(len(text), start + window)
    return text[start:end]


def render_page(total_files: int, total_chunks: int) -> str:
    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>合同文本搜索</title>
  <style>
    :root {{
      --bg: #0b1220;
      --panel: #111a2e;
      --panel-2: #16223c;
      --text: #e8eefc;
      --muted: #9fb0d0;
      --accent: #7dd3fc;
      --accent-2: #60a5fa;
      --border: rgba(148, 163, 184, 0.18);
      --mark: #fef08a;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif; background: radial-gradient(circle at top, #172554 0, #0b1220 42%, #050816 100%); color: var(--text); }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 28px 20px 48px; }}
    .hero {{ background: linear-gradient(135deg, rgba(96,165,250,.16), rgba(125,211,252,.08)); border: 1px solid var(--border); border-radius: 24px; padding: 24px; box-shadow: 0 20px 60px rgba(0,0,0,.24); }}
    h1 {{ margin: 0 0 8px; font-size: 30px; letter-spacing: .5px; }}
    .sub {{ color: var(--muted); line-height: 1.6; }}
    .stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 16px; }}
    .chip {{ background: rgba(255,255,255,.06); border: 1px solid var(--border); border-radius: 999px; padding: 8px 12px; color: var(--text); font-size: 13px; }}
    .searchbar {{ display: grid; grid-template-columns: 1fr auto auto; gap: 10px; margin: 18px 0 14px; }}
    input, select, button {{ border-radius: 14px; border: 1px solid var(--border); background: rgba(255,255,255,.06); color: var(--text); padding: 14px 16px; font-size: 15px; outline: none; }}
    input::placeholder {{ color: #94a3b8; }}
    button {{ cursor: pointer; background: linear-gradient(135deg, var(--accent-2), var(--accent)); color: #082032; font-weight: 700; min-width: 120px; }}
    button.secondary {{ background: rgba(255,255,255,.06); color: var(--text); }}
    .results {{ display: grid; gap: 14px; margin-top: 16px; }}
    .card {{ background: rgba(10, 16, 32, 0.7); border: 1px solid var(--border); border-radius: 18px; padding: 16px; backdrop-filter: blur(10px); }}
    .card h3 {{ margin: 0 0 6px; font-size: 16px; }}
    .meta {{ color: var(--muted); font-size: 13px; margin-bottom: 10px; display: flex; gap: 12px; flex-wrap: wrap; }}
    .score {{ color: var(--accent); font-weight: 700; }}
    .text {{ line-height: 1.75; color: #ecf2ff; white-space: pre-wrap; word-break: break-word; }}
    mark {{ background: var(--mark); color: #111827; padding: 0 2px; border-radius: 4px; }}
    .empty {{ color: var(--muted); padding: 24px 4px; }}
    .hint {{ color: var(--muted); font-size: 13px; margin-top: 10px; }}
    .footer {{ margin-top: 22px; color: var(--muted); font-size: 12px; }}
    @media (max-width: 900px) {{
      .searchbar {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"hero\">
      <h1>合同文本搜索</h1>
      <div class=\"sub\">本地离线检索合同片段。可以直接搜条款号、关键词、责任免除、等待期、免赔额等内容。</div>
      <div class=\"stats\">
        <div class=\"chip\">合同文件数: <span id=\"fileCount\">{total_files}</span></div>
        <div class=\"chip\">文本块数: <span id=\"chunkCount\">{total_chunks}</span></div>
        <div class=\"chip\">支持 PDF / TXT / MD / HTML</div>
      </div>
      <div class=\"searchbar\">
        <input id=\"q\" placeholder=\"输入关键词，比如：等待期、如实告知、免赔额、责任免除、80%\" />
        <select id=\"limit\">
          <option value=\"10\">10条</option>
          <option value=\"20\" selected>20条</option>
          <option value=\"50\">50条</option>
        </select>
        <button id=\"searchBtn\">搜索</button>
      </div>
      <div class=\"hint\">提示：你也可以搜条款号，例如 11.6、1.2、6.2，或者多个关键词一起搜。</div>
    </div>

    <div id=\"results\" class=\"results\"></div>
    <div class=\"footer\">接口：/api/search?query=关键词；/api/documents 查看统计。</div>
  </div>

  <script>
    const qEl = document.getElementById('q');
    const limitEl = document.getElementById('limit');
    const btn = document.getElementById('searchBtn');
    const resultsEl = document.getElementById('results');

    function escapeHtml(text) {{
      return (text || '').replace(/[&<>"]/g, (m) => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[m]));
    }}

    function render(items) {{
      if (!items.length) {{
        resultsEl.innerHTML = '<div class="empty">没有找到匹配结果。</div>';
        return;
      }}
      resultsEl.innerHTML = items.map((item, idx) => `
        <div class="card">
          <h3>${{idx + 1}}. ${{escapeHtml(item.file_name || item.source_path || '')}}</h3>
          <div class="meta">
            <span>来源：${{escapeHtml(item.source_path || '')}}</span>
            <span>块：${{item.chunk_index || 0}} / ${{item.chunk_count || 0}}</span>
            <span>长度：${{item.char_count || 0}}</span>
            <span class="score">得分：${{(item.score ?? 0).toFixed(2)}}</span>
          </div>
          <div class="text">${{item.highlighted || escapeHtml(item.text || '')}}</div>
        </div>
      `).join('');
    }}

    async function search() {{
      const query = qEl.value.trim();
      const limit = limitEl.value;
      if (!query) {{
        resultsEl.innerHTML = '<div class="empty">请输入一个关键词后再搜索。</div>';
        return;
      }}
      resultsEl.innerHTML = '<div class="empty">搜索中...</div>';
      const resp = await fetch(`/api/search?query=${{encodeURIComponent(query)}}&limit=${{encodeURIComponent(limit)}}`);
      const data = await resp.json();
      render(data.items || []);
    }}

    btn.addEventListener('click', search);
    qEl.addEventListener('keydown', (e) => {{ if (e.key === 'Enter') search(); }});
  </script>
</body>
</html>"""


def create_app(chunks: List[SearchChunk], max_results: int) -> FastAPI:
    app = FastAPI(title="合同文本搜索", version="1.0.0")

    total_files = len({c.source_path for c in chunks})
    total_chunks = len(chunks)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return render_page(total_files, total_chunks)

    @app.get("/api/documents")
    def documents() -> JSONResponse:
        files: Dict[str, Dict[str, Any]] = {}
        for chunk in chunks:
            info = files.setdefault(chunk.source_path, {
                "source_path": chunk.source_path,
                "file_name": chunk.file_name,
                "file_type": chunk.file_type,
                "sha256": chunk.sha256,
                "chunks": 0,
                "char_count": 0,
            })
            info["chunks"] += 1
            info["char_count"] += chunk.char_count
        return JSONResponse({"success": True, "total_files": len(files), "total_chunks": len(chunks), "documents": list(files.values())})

    @app.get("/api/search")
    def search(query: str = Query(..., min_length=1), limit: int = Query(max_results, ge=1, le=200)) -> JSONResponse:
        terms = tokenize_query(query)
        scored = []
        for chunk in chunks:
            score = score_chunk(chunk.text, terms)
            if score <= 0:
                continue
            excerpt = build_excerpt(chunk.text, terms)
            scored.append({
                **asdict(chunk),
                "score": round(score, 4),
                "excerpt": excerpt,
                "highlighted": highlight(excerpt, terms),
            })

        scored.sort(key=lambda x: (x["score"], x["char_count"]), reverse=True)
        return JSONResponse({"success": True, "query": query, "terms": terms, "count": len(scored), "items": scored[:limit]})

    return app


def main() -> None:
    args = parse_args()

    if not args.input and not args.corpus:
        raise SystemExit("必须提供 --input 或 --corpus 其中之一")

    if args.corpus:
        corpus_path = Path(args.corpus).expanduser().resolve()
        if not corpus_path.exists():
            raise FileNotFoundError(f"Corpus not found: {corpus_path}")
        chunks = load_corpus_jsonl(corpus_path)
    else:
        input_path = Path(args.input).expanduser().resolve()
        chunks = build_corpus_from_source(
            input_path=input_path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            min_chunk_chars=args.min_chunk_chars,
            dedup=args.dedup,
        )

    app = create_app(chunks, max_results=args.max_results)
    print(f"[ready] files={len({c.source_path for c in chunks})} chunks={len(chunks)}")
    print(f"[open] http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()