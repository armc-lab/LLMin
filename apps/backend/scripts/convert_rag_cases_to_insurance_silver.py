#!/usr/bin/env python3
"""Convert existing RAG cases to a silver insurance QA set.

Input example (existing):
[
  {
    "name": "告知义务拒赔-001",
    "document_path": "test_contract.pdf",
    "question": "...",
    "expected": {
      "status": "hit",
      "citation_keywords": ["..."],
      "answer_keywords": ["..."]
    }
  }
]

Output example:
[
  {
    "id": "silver-0001",
    "question": "...",
    "document_path": "...",
    "expected": {
      "must_include": ["..."],
      "citation_keywords": ["..."],
      "should_abstain": false
    }
  }
]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert rag_eval_cases to insurance silver set")
    parser.add_argument("--input", required=True, help="Input rag cases json")
    parser.add_argument("--output", required=True, help="Output silver cases json")
    return parser.parse_args()


def load_array(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Input JSON must be an array")
    return [x for x in data if isinstance(x, dict)]


def to_list(v: Any) -> List[str]:
    if not isinstance(v, list):
        return []
    out: List[str] = []
    for x in v:
        s = str(x).strip()
        if s:
            out.append(s)
    return out


def main() -> None:
    args = parse_args()
    src = load_array(Path(args.input))

    out: List[Dict[str, Any]] = []
    for i, row in enumerate(src, start=1):
        expected = row.get("expected", {}) if isinstance(row.get("expected", {}), dict) else {}
        status = str(expected.get("status", "")).strip().lower()

        silver = {
            "id": f"silver-{i:04d}",
            "name": str(row.get("name", "")).strip() or f"silver-case-{i:04d}",
            "category": str(row.get("category", "unknown")).strip() or "unknown",
            "question": str(row.get("question", "")).strip(),
            "document_path": str(row.get("document_path", "")).strip(),
            "expected": {
                "must_include": to_list(expected.get("answer_keywords", [])),
                "citation_keywords": to_list(expected.get("citation_keywords", [])),
                "should_abstain": status == "miss",
            },
        }
        out.append(silver)

    dst = Path(args.output)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Converted: {len(out)} cases")
    print(f"Output: {dst}")


if __name__ == "__main__":
    main()
