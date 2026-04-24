#!/usr/bin/env python3
"""RAG 评测脚本。

功能：
1) 上传测试文档到现有 API。
2) 执行问答请求并收集输出。
3) 计算基础指标并生成 JSON + Markdown 报告。

用法示例：
python scripts/evaluate_rag.py \
  --cases tests/rag_eval_cases.sample.json \
  --base-url http://127.0.0.1:8001
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import httpx


@dataclass
class EvalMetrics:
    total: int = 0
    success: int = 0
    status_accuracy: float = 0.0
    citation_hit_rate: float = 0.0
    answer_keyword_recall: float = 0.0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0


def load_cases(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("cases 文件必须是 JSON 数组")
    return data


def upload_document(client: httpx.Client, base_url: str, doc_path: Path) -> str:
    url = f"{base_url}/api/v1/documents/analyze"
    if not doc_path.exists():
        raise FileNotFoundError(f"测试文档不存在: {doc_path}")

    suffix = doc_path.suffix.lower()
    content_type = "application/pdf" if suffix == ".pdf" else "text/plain"
    with doc_path.open("rb") as f:
        files = {"file": (doc_path.name, f, content_type)}
        resp = client.post(url, files=files)
    resp.raise_for_status()

    payload = resp.json()
    return payload["data"]["document_id"]


def ask_question(client: httpx.Client, base_url: str, doc_id: str, question: str) -> Tuple[Dict[str, Any], float]:
    url = f"{base_url}/api/v1/chat/completions"
    req = {"document_id": doc_id, "question": question}

    t0 = time.perf_counter()
    resp = client.post(url, json=req)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    resp.raise_for_status()
    return resp.json(), elapsed_ms


def contains_any(text: str, keywords: List[str]) -> bool:
    return any(k in text for k in keywords)


def calc_keyword_recall(text: str, keywords: List[str]) -> float:
    if not keywords:
        return 1.0
    hit = sum(1 for k in keywords if k in text)
    return hit / len(keywords)


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    values_sorted = sorted(values)
    idx = int(round((p / 100.0) * (len(values_sorted) - 1)))
    return values_sorted[idx]


def ensure_service_ready(base_url: str) -> None:
    timeout = httpx.Timeout(timeout=5.0)
    with httpx.Client(timeout=timeout) as client:
        root = client.get(f"{base_url}/")
        root.raise_for_status()


def evaluate(base_url: str, cases: List[Dict[str, Any]], workspace_root: Path) -> Tuple[EvalMetrics, List[Dict[str, Any]]]:
    # 每个文档只上传一次，减少测试时间。
    doc_id_cache: Dict[str, str] = {}

    total = 0
    success = 0
    status_match = 0
    citation_hit = 0
    recall_sum = 0.0
    latencies: List[float] = []
    details: List[Dict[str, Any]] = []

    timeout = httpx.Timeout(timeout=180.0)
    with httpx.Client(timeout=timeout) as client:
        for i, case in enumerate(cases, start=1):
            total += 1
            question = str(case.get("question", "")).strip()
            doc_rel = str(case.get("document_path", "")).strip()
            expected = case.get("expected", {}) or {}

            row: Dict[str, Any] = {
                "case_index": i,
                "question": question,
                "document_path": doc_rel,
                "ok": False,
            }

            try:
                if not question:
                    raise ValueError("question 不能为空")
                if not doc_rel:
                    raise ValueError("document_path 不能为空")

                doc_path = workspace_root / doc_rel
                cache_key = str(doc_path.resolve())
                if cache_key not in doc_id_cache:
                    doc_id_cache[cache_key] = upload_document(client, base_url, doc_path)
                doc_id = doc_id_cache[cache_key]

                payload, latency_ms = ask_question(client, base_url, doc_id, question)
                latencies.append(latency_ms)

                data = payload.get("data", {})
                pred_status = data.get("status", "")
                answer = str(data.get("answer", ""))
                citations = data.get("citations", [])
                citation_text = "\n".join(str(c.get("text", "")) for c in citations if isinstance(c, dict))

                exp_status = str(expected.get("status", "")).strip()
                exp_citation_keywords = [str(x) for x in expected.get("citation_keywords", [])]
                exp_answer_keywords = [str(x) for x in expected.get("answer_keywords", [])]

                status_ok = (pred_status == exp_status) if exp_status else True
                citation_ok = contains_any(citation_text, exp_citation_keywords) if exp_citation_keywords else True
                answer_recall = calc_keyword_recall(answer, exp_answer_keywords)

                success += 1
                if status_ok:
                    status_match += 1
                if citation_ok:
                    citation_hit += 1
                recall_sum += answer_recall

                row.update(
                    {
                        "ok": True,
                        "latency_ms": round(latency_ms, 2),
                        "predicted": {
                            "status": pred_status,
                            "answer_preview": answer[:200],
                            "citation_count": len(citations),
                        },
                        "checks": {
                            "status_ok": status_ok,
                            "citation_ok": citation_ok,
                            "answer_keyword_recall": round(answer_recall, 4),
                        },
                    }
                )
            except Exception as exc:  # noqa: BLE001
                row["error"] = str(exc)

            details.append(row)

    metrics = EvalMetrics(
        total=total,
        success=success,
        status_accuracy=(status_match / success if success else 0.0),
        citation_hit_rate=(citation_hit / success if success else 0.0),
        answer_keyword_recall=(recall_sum / success if success else 0.0),
        avg_latency_ms=(sum(latencies) / len(latencies) if latencies else 0.0),
        p95_latency_ms=percentile(latencies, 95.0),
    )
    return metrics, details


def render_markdown_report(metrics: EvalMetrics, details: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("# RAG 评测报告")
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|---|---:|")
    lines.append(f"| 总样本数 | {metrics.total} |")
    lines.append(f"| 成功请求数 | {metrics.success} |")
    lines.append(f"| 状态准确率(status_accuracy) | {metrics.status_accuracy:.2%} |")
    lines.append(f"| 引用命中率(citation_hit_rate) | {metrics.citation_hit_rate:.2%} |")
    lines.append(f"| 答案关键词召回(answer_keyword_recall) | {metrics.answer_keyword_recall:.2%} |")
    lines.append(f"| 平均时延(avg_latency_ms) | {metrics.avg_latency_ms:.2f} |")
    lines.append(f"| P95 时延(p95_latency_ms) | {metrics.p95_latency_ms:.2f} |")
    lines.append("")
    lines.append("## 明细")
    lines.append("")

    for row in details:
        idx = row.get("case_index")
        lines.append(f"### Case {idx}")
        lines.append("")
        lines.append(f"- 文档: {row.get('document_path', '')}")
        lines.append(f"- 问题: {row.get('question', '')}")
        lines.append(f"- 执行成功: {row.get('ok', False)}")
        if row.get("ok"):
            checks = row.get("checks", {})
            pred = row.get("predicted", {})
            lines.append(f"- 时延(ms): {row.get('latency_ms', 0)}")
            lines.append(f"- 预测状态: {pred.get('status', '')}")
            lines.append(f"- 引用条数: {pred.get('citation_count', 0)}")
            lines.append(f"- status_ok: {checks.get('status_ok', False)}")
            lines.append(f"- citation_ok: {checks.get('citation_ok', False)}")
            lines.append(f"- answer_keyword_recall: {checks.get('answer_keyword_recall', 0)}")
            lines.append(f"- 回答预览: {pred.get('answer_preview', '')}")
        else:
            lines.append(f"- 错误: {row.get('error', '')}")
        lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="评测保险 RAG 问答效果")
    parser.add_argument("--cases", required=True, help="测试用例 JSON 文件路径")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="API 地址")
    parser.add_argument(
        "--output-json",
        default="tests/rag_eval_result.json",
        help="评测明细输出 JSON 路径",
    )
    parser.add_argument(
        "--output-md",
        default="tests/rag_eval_report.md",
        help="评测报告输出 Markdown 路径",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workspace_root = Path(__file__).resolve().parents[1]

    cases_path = (workspace_root / args.cases).resolve() if not Path(args.cases).is_absolute() else Path(args.cases)
    out_json = (workspace_root / args.output_json).resolve() if not Path(args.output_json).is_absolute() else Path(args.output_json)
    out_md = (workspace_root / args.output_md).resolve() if not Path(args.output_md).is_absolute() else Path(args.output_md)

    ensure_service_ready(args.base_url)
    cases = load_cases(cases_path)
    metrics, details = evaluate(args.base_url, cases, workspace_root)

    result = {
        "metrics": {
            "total": metrics.total,
            "success": metrics.success,
            "status_accuracy": metrics.status_accuracy,
            "citation_hit_rate": metrics.citation_hit_rate,
            "answer_keyword_recall": metrics.answer_keyword_recall,
            "avg_latency_ms": metrics.avg_latency_ms,
            "p95_latency_ms": metrics.p95_latency_ms,
        },
        "details": details,
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown_report(metrics, details), encoding="utf-8")

    print(json.dumps(result["metrics"], ensure_ascii=False, indent=2))
    print(f"\n明细已写入: {out_json}")
    print(f"报告已写入: {out_md}")

    # 若全量失败，返回非零退出码，便于 CI/自动化流程识别失败。
    if metrics.success == 0 and metrics.total > 0:
        print("\n评测失败：所有样本均未成功执行，请先检查 vLLM(8000) 与 API(8001) 服务状态。", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
