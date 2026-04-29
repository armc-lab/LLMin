#!/usr/bin/env python3
"""RAG 综合评测脚本。

相比基础脚本，本脚本新增：
1) 检索证据精确率/召回率（基于 citation 关键词）。
2) 语义关键词召回（同义词组，兼容旧 answer_keywords）。
3) 拒答率与拒答误触发率（如“未命中合同原文”）。
4) 维度化评分与加权总分，便于回归追踪。

兼容输入格式：
- 旧格式：expected.answer_keywords = ["如实告知", "拒赔", "条款"]
- 新格式：expected.answer_keyword_groups = [["拒赔", "不承担保险责任"], ...]

用法示例：
python scripts/evaluate_rag_comprehensive.py \
  --cases tests/rag_eval_cases.100.json \
  --base-url http://127.0.0.1:8001
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import httpx


REFUSAL_PATTERNS = [
    "未命中合同原文",
    "未检索到",
    "上下文未提到",
    "无法根据提供的上下文",
    "请提供具体的上下文",
]


DEFAULT_SCORE_WEIGHTS = {
    "quality": 0.6,
    "grounding": 0.25,
    "performance": 0.15,
}


@dataclass
class EvalMetrics:
    total: int = 0
    success: int = 0

    # 基础质量
    status_accuracy: float = 0.0
    answer_keyword_recall_lexical: float = 0.0
    answer_keyword_recall_semantic: float = 0.0

    # 归因/检索
    citation_hit_rate: float = 0.0
    evidence_precision: float = 0.0
    evidence_recall: float = 0.0

    # 拒答行为
    refusal_rate: float = 0.0
    false_refusal_rate: float = 0.0

    # 性能
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0

    # 综合分
    quality_score: float = 0.0
    grounding_score: float = 0.0
    performance_score: float = 0.0
    overall_score: float = 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RAG 综合评测脚本")
    parser.add_argument("--cases", required=True, help="测试集 JSON（数组）")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="服务地址")
    parser.add_argument(
        "--output-json",
        default="tests/rag_eval_result_comprehensive.json",
        help="输出明细 JSON 路径",
    )
    parser.add_argument(
        "--output-md",
        default="tests/rag_eval_report_comprehensive.md",
        help="输出 Markdown 报告路径",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="单请求超时秒数",
    )
    parser.add_argument(
        "--max-citations-eval",
        type=int,
        default=4,
        help="用于评估的 citation 数量上限",
    )
    return parser.parse_args()


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


def percentile(values: Sequence[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    values_sorted = sorted(values)
    idx = int(round((p / 100.0) * (len(values_sorted) - 1)))
    return float(values_sorted[idx])


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(k in text for k in keywords)


def lexical_keyword_recall(text: str, keywords: Sequence[str]) -> float:
    if not keywords:
        return 1.0
    hit = sum(1 for k in keywords if k in text)
    return hit / len(keywords)


def to_keyword_groups(expected: Dict[str, Any]) -> List[List[str]]:
    raw_groups = expected.get("answer_keyword_groups")
    if isinstance(raw_groups, list) and raw_groups:
        groups: List[List[str]] = []
        for g in raw_groups:
            if isinstance(g, list):
                norm = [str(x).strip() for x in g if str(x).strip()]
                if norm:
                    groups.append(norm)
        if groups:
            return groups

    # 兼容旧字段：每个关键词是一个组
    kws = [str(x).strip() for x in expected.get("answer_keywords", []) if str(x).strip()]
    return [[k] for k in kws]


def semantic_keyword_recall(text: str, keyword_groups: Sequence[Sequence[str]]) -> float:
    if not keyword_groups:
        return 1.0
    hit = 0
    for group in keyword_groups:
        if any(alias in text for alias in group):
            hit += 1
    return hit / len(keyword_groups)


def compute_evidence_stats(citation_texts: Sequence[str], citation_keywords: Sequence[str]) -> Tuple[float, float, bool]:
    """返回 (precision, recall, hit_any)。

    precision: 命中关键词的 citation 数 / citation 总数
    recall: 被 citation 覆盖的关键词数 / 关键词总数
    hit_any: 是否至少有一个关键词在 citation 中出现
    """
    if not citation_texts:
        return (1.0 if not citation_keywords else 0.0, 1.0 if not citation_keywords else 0.0, not citation_keywords)

    if not citation_keywords:
        return 1.0, 1.0, True

    matched_citations = 0
    covered_keywords = 0

    for text in citation_texts:
        if contains_any(text, citation_keywords):
            matched_citations += 1

    all_citation_blob = "\n".join(citation_texts)
    for kw in citation_keywords:
        if kw in all_citation_blob:
            covered_keywords += 1

    precision = matched_citations / len(citation_texts)
    recall = covered_keywords / len(citation_keywords)
    hit_any = covered_keywords > 0
    return precision, recall, hit_any


def is_refusal(answer: str) -> bool:
    return contains_any(answer, REFUSAL_PATTERNS)


def compute_scores(
    status_accuracy: float,
    lexical_recall: float,
    semantic_recall: float,
    citation_hit_rate: float,
    evidence_precision: float,
    evidence_recall: float,
    false_refusal_rate: float,
    avg_latency_ms: float,
    p95_latency_ms: float,
) -> Tuple[float, float, float, float]:
    # 质量分：语义召回权重更高，兼顾状态稳定性与词面召回
    quality_score = (
        0.35 * status_accuracy
        + 0.20 * lexical_recall
        + 0.45 * semantic_recall
    )

    # 归因分：引用命中、证据精确率、证据召回，惩罚误拒答
    grounding_raw = (
        0.35 * citation_hit_rate
        + 0.35 * evidence_precision
        + 0.30 * evidence_recall
    )
    grounding_score = max(0.0, grounding_raw - 0.20 * false_refusal_rate)

    # 性能分：给定经验阈值进行线性映射（可按环境调整）
    # avg: 5s 及以内视为 1，30s 及以上视为 0
    # p95: 10s 及以内视为 1，60s 及以上视为 0
    avg_norm = 1.0 - min(max((avg_latency_ms - 5000.0) / 25000.0, 0.0), 1.0)
    p95_norm = 1.0 - min(max((p95_latency_ms - 10000.0) / 50000.0, 0.0), 1.0)
    performance_score = 0.45 * avg_norm + 0.55 * p95_norm

    overall_score = (
        DEFAULT_SCORE_WEIGHTS["quality"] * quality_score
        + DEFAULT_SCORE_WEIGHTS["grounding"] * grounding_score
        + DEFAULT_SCORE_WEIGHTS["performance"] * performance_score
    )
    return quality_score, grounding_score, performance_score, overall_score


def evaluate(base_url: str, cases: List[Dict[str, Any]], workspace_root: Path, timeout_s: float, max_citations_eval: int) -> Tuple[EvalMetrics, List[Dict[str, Any]]]:
    doc_id_cache: Dict[str, str] = {}

    total = 0
    success = 0

    status_match = 0
    citation_hit = 0
    lexical_recall_sum = 0.0
    semantic_recall_sum = 0.0

    evidence_precision_sum = 0.0
    evidence_recall_sum = 0.0

    refusal_count = 0
    false_refusal_count = 0

    latencies: List[float] = []
    details: List[Dict[str, Any]] = []

    timeout = httpx.Timeout(timeout=timeout_s)
    with httpx.Client(timeout=timeout) as client:
        for i, case in enumerate(cases, start=1):
            total += 1

            question = str(case.get("question", "")).strip()
            doc_rel = str(case.get("document_path", "")).strip()
            expected = case.get("expected", {}) or {}

            row: Dict[str, Any] = {
                "case_index": i,
                "name": case.get("name", f"case-{i:03d}"),
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
                pred_status = str(data.get("status", ""))
                answer = str(data.get("answer", ""))
                citations_raw = data.get("citations", [])

                citations_text = [
                    str(c.get("text", "")).strip()
                    for c in citations_raw
                    if isinstance(c, dict)
                ]
                citations_text = [c for c in citations_text if c][:max(1, max_citations_eval)]

                exp_status = str(expected.get("status", "")).strip()
                citation_keywords = [str(x).strip() for x in expected.get("citation_keywords", []) if str(x).strip()]
                answer_keywords = [str(x).strip() for x in expected.get("answer_keywords", []) if str(x).strip()]
                answer_groups = to_keyword_groups(expected)

                status_ok = (pred_status == exp_status) if exp_status else True
                lexical_recall = lexical_keyword_recall(answer, answer_keywords)
                semantic_recall = semantic_keyword_recall(answer, answer_groups)

                e_precision, e_recall, citation_ok = compute_evidence_stats(citations_text, citation_keywords)

                refusal = is_refusal(answer)
                should_refuse = bool(expected.get("should_refuse", False))
                false_refusal = refusal and not should_refuse

                success += 1
                status_match += 1 if status_ok else 0
                citation_hit += 1 if citation_ok else 0
                lexical_recall_sum += lexical_recall
                semantic_recall_sum += semantic_recall
                evidence_precision_sum += e_precision
                evidence_recall_sum += e_recall
                refusal_count += 1 if refusal else 0
                false_refusal_count += 1 if false_refusal else 0

                row.update(
                    {
                        "ok": True,
                        "latency_ms": round(latency_ms, 2),
                        "predicted": {
                            "status": pred_status,
                            "answer_preview": answer[:260],
                            "citation_count": len(citations_raw),
                        },
                        "checks": {
                            "status_ok": status_ok,
                            "citation_ok": citation_ok,
                            "answer_keyword_recall_lexical": round(lexical_recall, 4),
                            "answer_keyword_recall_semantic": round(semantic_recall, 4),
                            "evidence_precision": round(e_precision, 4),
                            "evidence_recall": round(e_recall, 4),
                            "is_refusal": refusal,
                            "false_refusal": false_refusal,
                        },
                    }
                )
            except Exception as exc:  # noqa: BLE001
                row["error"] = str(exc)

            details.append(row)

    status_accuracy = status_match / success if success else 0.0
    citation_hit_rate = citation_hit / success if success else 0.0
    lexical_recall_avg = lexical_recall_sum / success if success else 0.0
    semantic_recall_avg = semantic_recall_sum / success if success else 0.0
    evidence_precision_avg = evidence_precision_sum / success if success else 0.0
    evidence_recall_avg = evidence_recall_sum / success if success else 0.0
    refusal_rate = refusal_count / success if success else 0.0
    false_refusal_rate = false_refusal_count / success if success else 0.0
    avg_latency = statistics.mean(latencies) if latencies else 0.0
    p95_latency = percentile(latencies, 95.0)

    quality_score, grounding_score, performance_score, overall_score = compute_scores(
        status_accuracy=status_accuracy,
        lexical_recall=lexical_recall_avg,
        semantic_recall=semantic_recall_avg,
        citation_hit_rate=citation_hit_rate,
        evidence_precision=evidence_precision_avg,
        evidence_recall=evidence_recall_avg,
        false_refusal_rate=false_refusal_rate,
        avg_latency_ms=avg_latency,
        p95_latency_ms=p95_latency,
    )

    metrics = EvalMetrics(
        total=total,
        success=success,
        status_accuracy=status_accuracy,
        answer_keyword_recall_lexical=lexical_recall_avg,
        answer_keyword_recall_semantic=semantic_recall_avg,
        citation_hit_rate=citation_hit_rate,
        evidence_precision=evidence_precision_avg,
        evidence_recall=evidence_recall_avg,
        refusal_rate=refusal_rate,
        false_refusal_rate=false_refusal_rate,
        avg_latency_ms=avg_latency,
        p95_latency_ms=p95_latency,
        quality_score=quality_score,
        grounding_score=grounding_score,
        performance_score=performance_score,
        overall_score=overall_score,
    )

    return metrics, details


def render_markdown_report(metrics: EvalMetrics, details: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("# RAG 综合评测报告")
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|---|---:|")
    lines.append(f"| 总样本数 | {metrics.total} |")
    lines.append(f"| 成功请求数 | {metrics.success} |")
    lines.append(f"| 状态准确率(status_accuracy) | {metrics.status_accuracy:.2%} |")
    lines.append(f"| 引用命中率(citation_hit_rate) | {metrics.citation_hit_rate:.2%} |")
    lines.append(f"| 词面关键词召回(answer_keyword_recall_lexical) | {metrics.answer_keyword_recall_lexical:.2%} |")
    lines.append(f"| 语义关键词召回(answer_keyword_recall_semantic) | {metrics.answer_keyword_recall_semantic:.2%} |")
    lines.append(f"| 证据精确率(evidence_precision) | {metrics.evidence_precision:.2%} |")
    lines.append(f"| 证据召回率(evidence_recall) | {metrics.evidence_recall:.2%} |")
    lines.append(f"| 拒答率(refusal_rate) | {metrics.refusal_rate:.2%} |")
    lines.append(f"| 误拒答率(false_refusal_rate) | {metrics.false_refusal_rate:.2%} |")
    lines.append(f"| 平均时延(avg_latency_ms) | {metrics.avg_latency_ms:.2f} |")
    lines.append(f"| P95 时延(p95_latency_ms) | {metrics.p95_latency_ms:.2f} |")
    lines.append(f"| 质量分(quality_score) | {metrics.quality_score:.2%} |")
    lines.append(f"| 归因分(grounding_score) | {metrics.grounding_score:.2%} |")
    lines.append(f"| 性能分(performance_score) | {metrics.performance_score:.2%} |")
    lines.append(f"| 综合分(overall_score) | {metrics.overall_score:.2%} |")
    lines.append("")

    lines.append("## 明细")
    lines.append("")
    for row in details:
        lines.append(f"### Case {row.get('case_index')}")
        lines.append("")
        lines.append(f"- 名称: {row.get('name', '')}")
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
            lines.append(f"- answer_keyword_recall_lexical: {checks.get('answer_keyword_recall_lexical', 0)}")
            lines.append(f"- answer_keyword_recall_semantic: {checks.get('answer_keyword_recall_semantic', 0)}")
            lines.append(f"- evidence_precision: {checks.get('evidence_precision', 0)}")
            lines.append(f"- evidence_recall: {checks.get('evidence_recall', 0)}")
            lines.append(f"- is_refusal: {checks.get('is_refusal', False)}")
            lines.append(f"- false_refusal: {checks.get('false_refusal', False)}")
            lines.append(f"- 回答预览: {pred.get('answer_preview', '')}")
        else:
            lines.append(f"- 错误: {row.get('error', '')}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    workspace_root = Path(__file__).resolve().parents[1]

    cases_path = workspace_root / args.cases
    out_json = workspace_root / args.output_json
    out_md = workspace_root / args.output_md

    cases = load_cases(cases_path)
    metrics, details = evaluate(
        base_url=args.base_url,
        cases=cases,
        workspace_root=workspace_root,
        timeout_s=args.timeout,
        max_citations_eval=args.max_citations_eval,
    )

    payload = {
        "metrics": {
            "total": metrics.total,
            "success": metrics.success,
            "status_accuracy": metrics.status_accuracy,
            "citation_hit_rate": metrics.citation_hit_rate,
            "answer_keyword_recall_lexical": metrics.answer_keyword_recall_lexical,
            "answer_keyword_recall_semantic": metrics.answer_keyword_recall_semantic,
            "evidence_precision": metrics.evidence_precision,
            "evidence_recall": metrics.evidence_recall,
            "refusal_rate": metrics.refusal_rate,
            "false_refusal_rate": metrics.false_refusal_rate,
            "avg_latency_ms": metrics.avg_latency_ms,
            "p95_latency_ms": metrics.p95_latency_ms,
            "quality_score": metrics.quality_score,
            "grounding_score": metrics.grounding_score,
            "performance_score": metrics.performance_score,
            "overall_score": metrics.overall_score,
        },
        "details": details,
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown_report(metrics, details), encoding="utf-8")

    print(f"[OK] 写入 JSON: {out_json}")
    print(f"[OK] 写入 Markdown: {out_md}")
    print(f"[SUMMARY] overall_score={metrics.overall_score:.2%}, semantic_recall={metrics.answer_keyword_recall_semantic:.2%}, p95={metrics.p95_latency_ms:.2f}ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
