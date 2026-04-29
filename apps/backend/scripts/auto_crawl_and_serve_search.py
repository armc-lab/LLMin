#!/usr/bin/env python3
"""One-click pipeline: crawl website(s) and serve local search.

Given one or multiple site URLs, this script will:
1) run crawl_contracts_from_web.py to collect contract-like text chunks
2) optionally start contract_text_web_search.py for browser retrieval

Usage:
conda run -n baichuan-chat python scripts/auto_crawl_and_serve_search.py \
    --site-url https://css2.pingan.com/personal/insurance/health_ins.jsp \
    --site-url https://www.pingan.com/ \
    --output-jsonl data/pingan_auto_contract_chunks.jsonl \
    --serve

Batch mode via file:
conda run -n baichuan-chat python scripts/auto_crawl_and_serve_search.py \
    --sites-file seeds.txt \
    --output-jsonl data/pingan_auto_contract_chunks.jsonl
"""

from __future__ import annotations

import argparse
import socket
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto crawl website and serve local retrieval")
    parser.add_argument("--site-url", action="append", default=[], help="Entry URL of target site (repeatable)")
    parser.add_argument("--sites-file", default="", help="Text file with one site URL per line")
    parser.add_argument("--allow-domain", action="append", default=[], help="Allowed domain (repeatable); default inferred from URLs")
    parser.add_argument("--output-jsonl", default="data/auto_contract_chunks.jsonl", help="Output corpus JSONL path")

    parser.add_argument("--max-pages", type=int, default=150, help="Crawler max pages")
    parser.add_argument("--max-depth", type=int, default=2, help="Crawler max depth")
    parser.add_argument("--delay", type=float, default=0.4, help="Crawler delay seconds")
    parser.add_argument("--min-keyword-hits", type=int, default=2, help="Min keyword hits to keep page")
    parser.add_argument("--ultra-clean", action="store_true", help="Enable ultra strict text cleaning")

    parser.add_argument("--serve", action="store_true", help="Start web search UI after crawl")
    parser.add_argument("--serve-host", default="127.0.0.1", help="Search UI host")
    parser.add_argument("--serve-port", type=int, default=8098, help="Search UI port")
    parser.add_argument("--serve-max-results", type=int, default=30, help="Search UI max results")
    return parser.parse_args()


def run_cmd(cmd: list[str], cwd: Path) -> None:
    print("[run]", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=True)


def is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def pick_available_port(host: str, preferred_port: int, max_tries: int = 20) -> int:
    for i in range(max_tries + 1):
        p = preferred_port + i
        if is_port_free(host, p):
            return p
    raise RuntimeError(f"No free port found from {preferred_port} to {preferred_port + max_tries}")


def load_site_urls(site_urls: list[str], sites_file: str) -> list[str]:
    urls = [u.strip() for u in site_urls if u and u.strip()]
    if sites_file:
        p = Path(sites_file).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"sites file not found: {p}")
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                urls.append(s)

    out: list[str] = []
    for u in urls:
        if not u.startswith(("http://", "https://")):
            continue
        if u not in out:
            out.append(u)
    return out


def main() -> None:
    args = parse_args()
    base_dir = Path(__file__).resolve().parents[1]
    scripts_dir = base_dir / "scripts"
    output_path = (base_dir / args.output_jsonl).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    site_urls = load_site_urls(args.site_url, args.sites_file)
    if not site_urls:
        raise SystemExit("请提供至少一个 --site-url 或 --sites-file")

    inferred_hosts = []
    for u in site_urls:
        h = (urlparse(u).hostname or "").strip().lower()
        if h and h not in inferred_hosts:
            inferred_hosts.append(h)

    allow_domains = [d.strip().lower() for d in args.allow_domain if d and d.strip()]
    if not allow_domains:
        allow_domains = inferred_hosts

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".txt") as tf:
        for u in site_urls:
            tf.write(u + "\n")
        seeds_file_path = tf.name

    crawler_cmd = [
        "python",
        str(scripts_dir / "crawl_contracts_from_web.py"),
        "--seeds-file",
        seeds_file_path,
        "--max-pages",
        str(args.max_pages),
        "--max-depth",
        str(args.max_depth),
        "--delay",
        str(args.delay),
        "--strict-keywords-only",
        "--keyword",
        "保险责任",
        "--keyword",
        "责任免除",
        "--keyword",
        "等待期",
        "--keyword",
        "理赔",
        "--keyword",
        "赔付",
        "--keyword",
        "合同条款",
        "--keyword",
        "保险金",
        "--keyword",
        "免责",
        "--min-keyword-hits",
        str(args.min_keyword_hits),
        "--output-jsonl",
        str(output_path),
    ]

    for d in allow_domains:
        crawler_cmd.extend(["--allow-domain", d])

    if args.ultra_clean:
        crawler_cmd.append("--ultra-clean")

    # Keep pages closer to insurance paths by default.
    crawler_cmd.extend(["--url-include", "insurance", "--url-include", "health", "--url-include", "policy", "--url-include", "contract"])

    run_cmd(crawler_cmd, base_dir)
    print(f"[done] corpus={output_path}")

    if not args.serve:
        return

    serve_port = pick_available_port(args.serve_host, args.serve_port)
    if serve_port != args.serve_port:
        print(f"[warn] port {args.serve_port} in use, switched to {serve_port}")

    serve_cmd = [
        "python",
        str(scripts_dir / "contract_text_web_search.py"),
        "--corpus",
        str(output_path),
        "--host",
        args.serve_host,
        "--port",
        str(serve_port),
        "--max-results",
        str(args.serve_max_results),
    ]
    print(f"[open] http://{args.serve_host}:{serve_port}")
    run_cmd(serve_cmd, base_dir)


if __name__ == "__main__":
    main()
