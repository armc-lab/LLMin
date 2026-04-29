#!/usr/bin/env python3
"""Crawl contract materials from web pages and export text chunks.

Features:
- Start from seed URLs and crawl links with BFS.
- Respect robots.txt by default.
- Fetch HTML/PDF and extract plain text.
- Filter likely contract pages by keywords.
- Export chunked JSONL for retrieval or fine-tuning.

Example:
conda run -n baichuan-chat python scripts/crawl_contracts_from_web.py \
  --seed https://example.com/contracts/ \
  --allow-domain example.com \
  --output-jsonl data/web_contract_chunks.jsonl

If you have multiple seeds:
conda run -n baichuan-chat python scripts/crawl_contracts_from_web.py \
  --seeds-file seeds.txt \
  --allow-domain example.com \
  --allow-domain insurance.example.org \
  --output-jsonl data/web_contract_chunks.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Optional, Set, Tuple
from urllib import robotparser
from urllib.parse import urljoin, urldefrag, urlparse

import httpx

try:
    import fitz  # PyMuPDF
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "缺少 PyMuPDF(fitz)。请在 baichuan-chat 环境中运行，或先安装依赖：conda run -n baichuan-chat python -m pip install PyMuPDF"
    ) from exc


DEFAULT_CONTRACT_KEYWORDS = [
    "合同",
    "条款",
    "保险",
    "保单",
    "协议",
    "免责",
    "理赔",
    "责任",
    "contract",
    "policy",
    "terms",
    "agreement",
]

NAV_TERMS = {
    "首页", "网上直销", "企业客户", "个人客户", "银行", "信用卡", "证券", "期货", "信托", "理财规划",
    "平安vip俱乐部", "平安一账通", "汽车保险", "旅游保险", "家庭财产保险", "养老保险", "健康保险",
    "更多>>", "咨询预约", "了解详情", "保险客户服务", "保险服务常见问答", "下载表格及文件",
}

MARKETING_TERMS = {
    "咨询预约", "了解详情", "服务热线", "统一服务邮箱", "专业顾问", "产品特色", "适用对象",
    "推荐治疗方案", "贵宾", "高端", "尊享", "更多>>", "打印", "返回页首", "投保示例",
}

LEGAL_KEEP_TERMS = {
    "保险责任", "责任免除", "免责", "等待期", "犹豫期", "保险金", "给付", "赔付", "理赔",
    "被保险人", "投保人", "受益人", "条款", "合同", "保障范围", "续保", "除外责任",
    "生效", "终止", "年龄", "保费", "住院", "医疗费用", "赔偿", "事故通知",
}

LEGAL_KEEP_PATTERNS = [
    re.compile(r"第\s*\d+(?:\.\d+)?\s*条"),
    re.compile(r"第\s*\d+\s*章"),
    re.compile(r"\d+\s*日"),
    re.compile(r"\d+\s*岁"),
    re.compile(r"\d+\s*元"),
    re.compile(r"\d+\s*%"),
]


@dataclass
class WebChunkRecord:
    source_url: str
    file_type: str
    title: str
    sha256: str
    fetched_at: str
    chunk_index: int
    chunk_count: int
    char_count: int
    text: str


@dataclass
class CrawlTask:
    url: str
    depth: int


class LinkAndTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []
        self._texts: List[str] = []
        self._title_parts: List[str] = []
        self._in_title = False

    @property
    def text(self) -> str:
        return " ".join(self._texts)

    @property
    def title(self) -> str:
        return " ".join(self._title_parts).strip()

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag.lower() == "a":
            for k, v in attrs:
                if k.lower() == "href" and v:
                    self.links.append(v.strip())
                    break
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        s = data.strip()
        if not s:
            return
        self._texts.append(s)
        if self._in_title:
            self._title_parts.append(s)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl contract texts from web")
    parser.add_argument("--seed", action="append", default=[], help="Seed URL (repeatable)")
    parser.add_argument("--seeds-file", default="", help="Text file with one seed URL per line")
    parser.add_argument("--allow-domain", action="append", default=[], help="Allowed domain (repeatable), e.g. example.com")
    parser.add_argument("--cross-domain", action="store_true", help="Allow crawling across allowed domains")
    parser.add_argument("--respect-robots", action="store_true", default=True, help="Respect robots.txt (default true)")
    parser.add_argument("--ignore-robots", action="store_true", help="Ignore robots.txt")

    parser.add_argument("--output-jsonl", required=True, help="Output JSONL path")
    parser.add_argument("--download-dir", default="", help="Optional folder to save downloaded PDF/HTML")

    parser.add_argument("--max-pages", type=int, default=200, help="Max fetched pages")
    parser.add_argument("--max-depth", type=int, default=2, help="Max BFS depth")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout seconds")
    parser.add_argument("--delay", type=float, default=0.4, help="Delay seconds between requests")
    parser.add_argument("--max-results-per-page", type=int, default=80, help="Max links to enqueue from one page")

    parser.add_argument("--chunk-size", type=int, default=900, help="Chunk size in characters")
    parser.add_argument("--chunk-overlap", type=int, default=120, help="Chunk overlap in characters")
    parser.add_argument("--min-chunk-chars", type=int, default=120, help="Skip chunks shorter than this")
    parser.add_argument("--dedup", action="store_true", help="Deduplicate chunks by hash")

    parser.add_argument("--keyword", action="append", default=[], help="Additional contract keyword (repeatable)")
    parser.add_argument("--strict-keywords-only", action="store_true", help="Use only custom --keyword list and disable default keyword list")
    parser.add_argument("--min-keyword-hits", type=int, default=1, help="Minimum keyword hits to keep a page")
    parser.add_argument("--url-include", action="append", default=[], help="Keep page only when URL contains any of these substrings")
    parser.add_argument("--disable-clean-boilerplate", action="store_true", help="Disable nav/header/footer cleanup")
    parser.add_argument("--ultra-clean", action="store_true", help="Apply ultra strict cleaning and keep only legal-like clauses")
    parser.add_argument("--user-agent", default="Mozilla/5.0 (compatible; ContractCrawler/1.0; +local)", help="HTTP User-Agent")
    return parser.parse_args()


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\u3000", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []

    paras = [p.strip() for p in text.splitlines() if p.strip()]
    chunks: List[str] = []
    buf: List[str] = []

    def flush() -> None:
        nonlocal buf
        if buf:
            chunks.append("\n".join(buf).strip())
            buf = []

    for para in paras:
        if len(para) > chunk_size:
            flush()
            step = max(1, chunk_size - overlap)
            for i in range(0, len(para), step):
                piece = para[i:i + chunk_size].strip()
                if piece:
                    chunks.append(piece)
            continue

        cur = sum(len(x) for x in buf) + max(0, len(buf) - 1)
        if buf and cur + len(para) > chunk_size:
            flush()
        buf.append(para)

    flush()
    return [normalize_text(x) for x in chunks if normalize_text(x)]


def split_clauses(text: str) -> List[str]:
    t = normalize_text(text)
    if not t:
        return []
    parts = re.split(r"[\n。！？；;]+", t)
    return [p.strip() for p in parts if p and p.strip()]


def is_navigation_clause(clause: str) -> bool:
    c = clause.strip()
    if not c:
        return True
    c_l = c.lower()

    nav_hits = sum(1 for term in NAV_TERMS if term in c_l)
    if nav_hits >= 8:
        return True

    if nav_hits >= 4 and len(c) <= 320:
        return True

    if ("首页" in c and "信用卡" in c and "证券" in c) or ("网上直销" in c and "企业客户" in c and "个人客户" in c):
        return True

    # menu-like dense short tokens, typically nav bars
    tokens = [x for x in re.split(r"\s+", c) if x]
    short_token_ratio = (sum(1 for t in tokens if len(t) <= 6) / len(tokens)) if tokens else 0.0
    if len(tokens) >= 8 and short_token_ratio >= 0.8 and nav_hits >= 2:
        return True

    noise_markers = ["万里通积分奖励计划", "投资者关系", "关于平安", "网上门店", "更多>>"]
    if any(x in c for x in noise_markers) and len(c) <= 260:
        return True

    code_markers = ["document.cookie", "typeof(", "function(", "window.location", "gConvert", "script", "var "]
    if any(x in c for x in code_markers):
        return True

    symbol_ratio = sum(1 for ch in c if ch in "{}[]();=<>" ) / max(1, len(c))
    if symbol_ratio > 0.08 and len(c) > 40:
        return True

    return False


def clean_extracted_web_text(
    text: str,
    repeated_short_clause_counter: Dict[str, int],
    contract_keywords: List[str],
    enabled: bool,
    ultra_clean: bool = False,
) -> str:
    if not enabled:
        return normalize_text(text)

    clauses = split_clauses(text)
    if not clauses:
        return ""

    out: List[str] = []
    kws = [k.strip().lower() for k in contract_keywords if k and k.strip()]

    for clause in clauses:
        c = clause.strip()
        if not c:
            continue
        if is_navigation_clause(c):
            continue

        c_l = c.lower()
        key = re.sub(r"\s+", "", c_l)

        # Remove repeated short boilerplate blocks that appear across pages,
        # unless they look contract-related.
        has_contract_signal = any(k in c_l for k in kws)
        if len(key) <= 90 and repeated_short_clause_counter.get(key, 0) >= 2 and (not has_contract_signal):
            continue

        if ultra_clean:
            if any(term in c_l for term in MARKETING_TERMS):
                continue

            keep_by_term = any(term in c_l for term in LEGAL_KEEP_TERMS)
            keep_by_pattern = any(p.search(c) for p in LEGAL_KEEP_PATTERNS)
            # Ultra mode keeps only legal-style clauses.
            if not (keep_by_term or keep_by_pattern or has_contract_signal):
                continue

            if len(c) < 18:
                continue

        out.append(c)
        if len(key) <= 120:
            repeated_short_clause_counter[key] = repeated_short_clause_counter.get(key, 0) + 1

    cleaned = normalize_text("\n".join(out))
    return cleaned


def load_seeds(args: argparse.Namespace) -> List[str]:
    seeds = [x.strip() for x in args.seed if x and x.strip()]
    if args.seeds_file:
        p = Path(args.seeds_file).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"seeds file not found: {p}")
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                seeds.append(s)

    out: List[str] = []
    for s in seeds:
        if not s.startswith(("http://", "https://")):
            continue
        u = normalize_url(s)
        if u and u not in out:
            out.append(u)
    return out


def normalize_url(url: str) -> str:
    u, _frag = urldefrag(url.strip())
    parsed = urlparse(u)
    if parsed.scheme not in {"http", "https"}:
        return ""
    # avoid duplicated slash-only tails differences
    path = parsed.path or "/"
    normalized = parsed._replace(path=path, params="", fragment="")
    return normalized.geturl()


def domain_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def allowed_by_domain(url: str, allow_domains: Set[str], seed_domains: Set[str], cross_domain: bool) -> bool:
    host = domain_of(url)
    if not host:
        return False

    if allow_domains:
        return any(host == d or host.endswith("." + d) for d in allow_domains)

    if cross_domain:
        return True

    return host in seed_domains


def looks_like_contract(
    url: str,
    title: str,
    text: str,
    keywords: List[str],
    min_hits: int = 1,
    url_includes: Optional[List[str]] = None,
) -> bool:
    if url_includes:
        u = url.lower()
        if not any(x.lower() in u for x in url_includes if x.strip()):
            return False

    hay = (url + "\n" + title + "\n" + text[:2400]).lower()
    hits = 0
    for k in keywords:
        kw = k.lower().strip()
        if kw and kw in hay:
            hits += 1
    return hits >= max(1, min_hits)


def is_probably_binary_contract(url: str, content_type: str) -> bool:
    u = url.lower()
    ct = content_type.lower()
    if ".pdf" in u:
        return True
    if "application/pdf" in ct:
        return True
    # common downloadable docs
    if any(x in u for x in [".doc", ".docx", ".rtf"]):
        return True
    return False


def extract_pdf_text_from_bytes(raw: bytes) -> str:
    with fitz.open(stream=raw, filetype="pdf") as doc:
        pages = [page.get_text("text") for page in doc]
    return normalize_text("\n".join(pages))


def robots_allowed(url: str, user_agent: str, cache: Dict[str, robotparser.RobotFileParser], client: httpx.Client) -> bool:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    rp = cache.get(base)
    if rp is None:
        rp = robotparser.RobotFileParser()
        rp.set_url(urljoin(base, "/robots.txt"))
        try:
            resp = client.get(rp.url, follow_redirects=True)
            if resp.status_code < 400 and resp.text:
                rp.parse(resp.text.splitlines())
            else:
                # default allow when robots missing/unavailable
                rp = robotparser.RobotFileParser()
                rp.parse(["User-agent: *", "Allow: /"])
        except Exception:
            rp = robotparser.RobotFileParser()
            rp.parse(["User-agent: *", "Allow: /"])
        cache[base] = rp
    return rp.can_fetch(user_agent, url)


def save_optional_download(download_dir: Optional[Path], url: str, raw: bytes, hint_ext: str) -> None:
    if download_dir is None:
        return
    download_dir.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    safe_ext = hint_ext if hint_ext.startswith(".") else f".{hint_ext}"
    path = download_dir / f"{h}{safe_ext}"
    path.write_bytes(raw)


def main() -> None:
    args = parse_args()
    seeds = load_seeds(args)
    if not seeds:
        raise SystemExit("没有有效种子URL。请提供 --seed 或 --seeds-file")

    allow_domains = {d.strip().lower() for d in args.allow_domain if d.strip()}
    seed_domains = {domain_of(s) for s in seeds if domain_of(s)}
    custom_keywords = [k.strip() for k in args.keyword if k and k.strip()]
    if args.strict_keywords_only:
        keywords = custom_keywords
    else:
        keywords = DEFAULT_CONTRACT_KEYWORDS + custom_keywords
    if not keywords:
        keywords = DEFAULT_CONTRACT_KEYWORDS
    url_includes = [x.strip() for x in args.url_include if x and x.strip()]

    out_path = Path(args.output_jsonl).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    download_dir = Path(args.download_dir).expanduser().resolve() if args.download_dir else None

    queue: Deque[CrawlTask] = deque(CrawlTask(url=s, depth=0) for s in seeds)
    visited: Set[str] = set()
    seen_chunk_hashes: Set[str] = set()
    robots_cache: Dict[str, robotparser.RobotFileParser] = {}
    repeated_short_clause_counter: Dict[str, int] = {}

    fetched_pages = 0
    kept_docs = 0
    kept_chunks = 0

    headers = {"User-Agent": args.user_agent}
    timeout = httpx.Timeout(args.timeout)

    with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client, out_path.open("w", encoding="utf-8") as f:
        while queue and fetched_pages < args.max_pages:
            task = queue.popleft()
            url = normalize_url(task.url)
            if not url or url in visited:
                continue
            visited.add(url)

            if not allowed_by_domain(url, allow_domains, seed_domains, args.cross_domain):
                continue

            if (not args.ignore_robots) and args.respect_robots:
                if not robots_allowed(url, args.user_agent, robots_cache, client):
                    continue

            try:
                resp = client.get(url)
            except Exception:
                continue

            fetched_pages += 1
            content_type = (resp.headers.get("content-type") or "").lower()
            raw = resp.content
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")

            if args.delay > 0:
                time.sleep(args.delay)

            # PDF-like response
            if is_probably_binary_contract(url, content_type):
                if "pdf" not in content_type and ".pdf" not in url.lower():
                    # Skip non-PDF binaries for now
                    continue
                try:
                    text = extract_pdf_text_from_bytes(raw)
                except Exception:
                    continue

                if not looks_like_contract(
                    url,
                    "",
                    text,
                    keywords,
                    min_hits=args.min_keyword_hits,
                    url_includes=url_includes,
                ):
                    continue

                chunks = split_text(text, chunk_size=args.chunk_size, overlap=args.chunk_overlap)
                if not chunks:
                    continue

                save_optional_download(download_dir, url, raw, ".pdf")
                kept_docs += 1
                sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
                for idx, chunk in enumerate(chunks, start=1):
                    if len(chunk) < args.min_chunk_chars:
                        continue
                    ch = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
                    if args.dedup and ch in seen_chunk_hashes:
                        continue
                    seen_chunk_hashes.add(ch)
                    rec = WebChunkRecord(
                        source_url=url,
                        file_type="pdf",
                        title="",
                        sha256=sha,
                        fetched_at=now,
                        chunk_index=idx,
                        chunk_count=len(chunks),
                        char_count=len(chunk),
                        text=chunk,
                    )
                    f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
                    kept_chunks += 1
                continue

            # HTML page
            if "text/html" in content_type or url.lower().endswith((".html", ".htm", "/")):
                html_text = ""
                try:
                    html_text = resp.text
                except Exception:
                    continue

                parser = LinkAndTextParser()
                try:
                    parser.feed(html_text)
                except Exception:
                    pass

                title = normalize_text(parser.title)
                body_text = clean_extracted_web_text(
                    parser.text,
                    repeated_short_clause_counter=repeated_short_clause_counter,
                    contract_keywords=keywords,
                    enabled=(not args.disable_clean_boilerplate),
                    ultra_clean=args.ultra_clean,
                )

                if looks_like_contract(
                    url,
                    title,
                    body_text,
                    keywords,
                    min_hits=args.min_keyword_hits,
                    url_includes=url_includes,
                ):
                    chunks = split_text(body_text, chunk_size=args.chunk_size, overlap=args.chunk_overlap)
                    if chunks:
                        kept_docs += 1
                        sha = hashlib.sha256(body_text.encode("utf-8")).hexdigest()
                        save_optional_download(download_dir, url, html_text.encode("utf-8", errors="ignore"), ".html")
                        for idx, chunk in enumerate(chunks, start=1):
                            if len(chunk) < args.min_chunk_chars:
                                continue
                            ch = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
                            if args.dedup and ch in seen_chunk_hashes:
                                continue
                            seen_chunk_hashes.add(ch)
                            rec = WebChunkRecord(
                                source_url=url,
                                file_type="html",
                                title=title,
                                sha256=sha,
                                fetched_at=now,
                                chunk_index=idx,
                                chunk_count=len(chunks),
                                char_count=len(chunk),
                                text=chunk,
                            )
                            f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
                            kept_chunks += 1

                if task.depth >= args.max_depth:
                    continue

                enqueued = 0
                for href in parser.links:
                    nxt = normalize_url(urljoin(url, href))
                    if not nxt or nxt in visited:
                        continue
                    if not allowed_by_domain(nxt, allow_domains, seed_domains, args.cross_domain):
                        continue
                    queue.append(CrawlTask(url=nxt, depth=task.depth + 1))
                    enqueued += 1
                    if enqueued >= args.max_results_per_page:
                        break

    print(
        f"[done] fetched_pages={fetched_pages} kept_docs={kept_docs} kept_chunks={kept_chunks} output={out_path}"
    )


if __name__ == "__main__":
    main()
