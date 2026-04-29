#!/usr/bin/env python3
"""Batch-run insurance QA cases against API and export predictions JSON.

This script reads cases, uploads each document once, asks questions, and writes
prediction records compatible with evaluate_insurance_qa.py.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import httpx

REFUSAL_PATTERNS = [
    "证据不足",
    "无法确定",
    "无法判断",
    "需人工",
    "无法根据",
    "未检索到",
    "建议人工核对",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch run insurance QA and export predictions")
    parser.add_argument("--cases", required=True, help="Cases JSON path")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="API base URL")
    parser.add_argument("--workspace-root", default=".", help="Workspace root for resolving document_path")
    parser.add_argument("--output", required=True, help="Output predictions JSON path")
    parser.add_argument("--timeout", type=float, default=180.0, help="Single request timeout seconds")
    return parser.parse_args()


def load_cases(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Cases JSON must be an array")
    return [x for x in data if isinstance(x, dict)]


def contains_any(text: str, keywords: List[str]) -> bool:
    return any(k in text for k in keywords if k)


def detect_abstention(answer: str) -> bool:
    return contains_any(answer, REFUSAL_PATTERNS)


def upload_document(client: httpx.Client, base_url: str, doc_path: Path) -> str:
    url = f"{base_url}/api/v1/documents/analyze"
    if not doc_path.exists():
        raise FileNotFoundError(f"Document not found: {doc_path}")

    suffix = doc_path.suffix.lower()
    content_type = "application/pdf" if suffix == ".pdf" else "text/plain"
    with doc_path.open("rb") as f:
        files = {"file": (doc_path.name, f, content_type)}
        resp = client.post(url, files=files)
    resp.raise_for_status()

    payload = resp.json()
    return str(payload.get("data", {}).get("document_id", "")).strip()


def ask_question(client: httpx.Client, base_url: str, doc_id: str, question: str) -> Tuple[Dict[str, Any], float]:
    url = f"{base_url}/api/v1/chat/completions"
    req = {"document_id": doc_id, "question": question}

    t0 = time.perf_counter()
    resp = client.post(url, json=req)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    resp.raise_for_status()
    return resp.json(), elapsed_ms


def main() -> None:
    args = parse_args()

    cases = load_cases(Path(args.cases))
    workspace_root = Path(args.workspace_root).resolve()

    timeout = httpx.Timeout(timeout=args.timeout)
    doc_id_cache: Dict[str, str] = {}
    preds: List[Dict[str, Any]] = []

    with httpx.Client(timeout=timeout) as client:
        for i, case in enumerate(cases, start=1):
            case_id = str(case.get("id", "")).strip() or f"case-{i:04d}"
            question = str(case.get("question", "")).strip()
            doc_rel = str(case.get("document_path", "")).strip()

            row: Dict[str, Any] = {
                "id": case_id,
                "answer": "",
                "citations": [],
                "predicted_slots": {},
                "latency_ms": 0.0,
                "abstained": False,
                "status": "error",
            }

            try:
                if not question:
                    raise ValueError("empty question")
                if not doc_rel:
                    raise ValueError("empty document_path")

                doc_path = workspace_root / doc_rel
                cache_key = str(doc_path.resolve())
                if cache_key not in doc_id_cache:
                    doc_id_cache[cache_key] = upload_document(client, args.base_url, doc_path)

                payload, latency_ms = ask_question(client, args.base_url, doc_id_cache[cache_key], question)
                data = payload.get("data", {}) if isinstance(payload, dict) else {}

                answer = str(data.get("answer", ""))
                citations_raw = data.get("citations", [])
                citations: List[str] = []
                if isinstance(citations_raw, list):
                    for c in citations_raw:
                        if isinstance(c, dict):
                            t = str(c.get("text", "")).strip()
                        else:
                            t = str(c).strip()
                        if t:
                            citations.append(t)

                row.update({
                    "answer": answer,
                    "citations": citations,
                    "latency_ms": round(float(latency_ms), 2),
                    "abstained": detect_abstention(answer),
                    "status": str(data.get("status", "")) or "ok",
                })

            except Exception as exc:  # noqa: BLE001
                row["error"] = str(exc)

            preds.append(row)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(preds, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Batch finished: {len(preds)}")
    print(f"Output: {out}")


if __name__ == "__main__":
    main()
