#!/usr/bin/env python3
"""使用 RAGAS 框架进行 RAG 评估。

功能：
1) 调用现有 API 获取问答结果
2) 用 RAGAS 计算: Faithfulness, Answer Relevance, Context Relevance, Context Precision
3) 生成 JSON + Markdown 报告

RAGAS 指标说明：
- Faithfulness: 答案是否由上下文支持（0-1，越高越好）
- Answer Relevance: 答案与问题的相关性（0-1，越高越好）
- Context Relevance: 上下文与问题的相关性（0-1，越高越好）
- Context Precision: 上下文的精确率（0-1，越高越好）

用法示例：
python scripts/evaluate_rag_with_ragas.py \
  --cases tests/rag_eval_cases.sample.json \
  --base-url http://127.0.0.1:8001 \
  --llm-model http://localhost:8000/v1
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import httpx
from ragas import evaluate
from ragas.metrics import (
    answer_relevance,
    context_precision,
    context_relevance,
    faithfulness,
)
from ragas.llm import LangchainLLM
from langchain_openai import ChatOpenAI


@dataclass
class RAGASMetrics:
    total: int = 0
    success: int = 0

    # RAGAS 指标
    faithfulness: float = 0.0
    answer_relevance: float = 0.0
    context_relevance: float = 0.0
    context_precision: float = 0.0
    ragas_score: float = 0.0  # 综合分（四个指标的平均）

    # 性能
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


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    values_sorted = sorted(values)
    idx = int(round((p / 100.0) * (len(values_sorted) - 1)))
    return values_sorted[idx]


def extract_context_from_citations(citations: List[Dict[str, Any]]) -> str:
    """从 citations 提取原始上下文。"""
    context_parts = [str(c.get("text", "")).strip() for c in citations if isinstance(c, dict)]
    return "\n".join(context_parts)


def ensure_service_ready(base_url: str) -> None:
    timeout = httpx.Timeout(timeout=5.0)
    with httpx.Client(timeout=timeout) as client:
        root = client.get(f"{base_url}/")
        root.raise_for_status()


def evaluate_with_ragas(
    base_url: str,
    cases: List[Dict[str, Any]],
    workspace_root: Path,
    llm_api_url: str,
) -> Tuple[RAGASMetrics, List[Dict[str, Any]]]:
    """使用 RAGAS 评估 RAG 系统。

    Args:
        base_url: API 服务地址
        cases: 测试用例列表
        workspace_root: 项目根目录
        llm_api_url: LLM API 地址（用于 RAGAS 评估）
    """

    # 配置 RAGAS 的 LLM 评估器（指向 vLLM）
    evaluator_llm = ChatOpenAI(
        model="baichuan",  # 或你的模型名称
        base_url=f"{llm_api_url}/chat/completions" if "/v1" in llm_api_url else llm_api_url,
        temperature=0.0,
    )
    ragas_llm = LangchainLLM(llm=evaluator_llm)

    doc_id_cache: Dict[str, str] = {}

    total = 0
    success = 0

    faithful_sum = 0.0
    relevance_sum = 0.0
    context_rel_sum = 0.0
    context_prec_sum = 0.0

    latencies: List[float] = []
    details: List[Dict[str, Any]] = []

    timeout = httpx.Timeout(timeout=180.0)
    with httpx.Client(timeout=timeout) as client:
        for i, case in enumerate(cases, start=1):
            total += 1
            question = str(case.get("question", "")).strip()
            doc_rel = str(case.get("document_path", "")).strip()

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
                answer = str(data.get("answer", ""))
                citations = data.get("citations", [])
                context = extract_context_from_citations(citations)

                # 使用 RAGAS 评估这个样本
                print(f"[{i}/{len(cases)}] 评估中: {question[:50]}...")

                try:
                    # RAGAS 的评估（每个样本单独评估）
                    faithful_score = faithfulness.score(
                        {
                            "question": question,
                            "contexts": [context] if context else [],
                            "answer": answer,
                        },
                        llm=ragas_llm,
                    )

                    answer_rel_score = answer_relevance.score(
                        {
                            "question": question,
                            "answer": answer,
                        },
                        llm=ragas_llm,
                    )

                    context_rel_score = context_relevance.score(
                        {
                            "question": question,
                            "contexts": [context] if context else [],
                        },
                        llm=ragas_llm,
                    )

                    context_prec_score = context_precision.score(
                        {
                            "question": question,
                            "contexts": [context] if context else [],
                        },
                        llm=ragas_llm,
                    )

                    # 累加
                    success += 1
                    faithful_sum += faithful_score
                    relevance_sum += answer_rel_score
                    context_rel_sum += context_rel_score
                    context_prec_sum += context_prec_score

                    row.update(
                        {
                            "ok": True,
                            "latency_ms": round(latency_ms, 2),
                            "answer_preview": answer[:200],
                            "ragas_metrics": {
                                "faithfulness": round(faithful_score, 4),
                                "answer_relevance": round(answer_rel_score, 4),
                                "context_relevance": round(context_rel_score, 4),
                                "context_precision": round(context_prec_score, 4),
                            },
                        }
                    )
                except Exception as e:
                    print(f"  RAGAS 评估失败: {e}")
                    raise

            except Exception as exc:
                row["error"] = str(exc)

            details.append(row)

    # 计算平均值
    avg_faithful = faithful_sum / success if success > 0 else 0.0
    avg_relevance = relevance_sum / success if success > 0 else 0.0
    avg_context_rel = context_rel_sum / success if success > 0 else 0.0
    avg_context_prec = context_prec_sum / success if success > 0 else 0.0

    # 综合分（四个指标的加权平均）
    ragas_overall = (
        0.25 * avg_faithful
        + 0.25 * avg_relevance
        + 0.25 * avg_context_rel
        + 0.25 * avg_context_prec
    )

    metrics = RAGASMetrics(
        total=total,
        success=success,
        faithfulness=avg_faithful,
        answer_relevance=avg_relevance,
        context_relevance=avg_context_rel,
        context_precision=avg_context_prec,
        ragas_score=ragas_overall,
        avg_latency_ms=(sum(latencies) / len(latencies) if latencies else 0.0),
        p95_latency_ms=percentile(latencies, 95.0),
    )

    return metrics, details


def render_markdown_report(metrics: RAGASMetrics, details: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("# RAGAS 评测报告")
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|---|---:|")
    lines.append(f"| 总样本数 | {metrics.total} |")
    lines.append(f"| 成功评估数 | {metrics.success} |")
    lines.append(f"| Faithfulness (可信度) | {metrics.faithfulness:.4f} |")
    lines.append(f"| Answer Relevance (答案相关性) | {metrics.answer_relevance:.4f} |")
    lines.append(f"| Context Relevance (上下文相关性) | {metrics.context_relevance:.4f} |")
    lines.append(f"| Context Precision (上下文精确率) | {metrics.context_precision:.4f} |")
    lines.append(f"| **RAGAS 综合分** | **{metrics.ragas_score:.4f}** |")
    lines.append(f"| 平均时延(ms) | {metrics.avg_latency_ms:.2f} |")
    lines.append(f"| P95 时延(ms) | {metrics.p95_latency_ms:.2f} |")
    lines.append("")

    lines.append("## RAGAS 指标说明")
    lines.append("")
    lines.append("- **Faithfulness**: 答案是否由上下文支持（是否编造信息）。范围 [0, 1]，越高越好。")
    lines.append("- **Answer Relevance**: 答案与问题的相关性。范围 [0, 1]，越高越好。")
    lines.append("- **Context Relevance**: 检索上下文与问题的相关性。范围 [0, 1]，越高越好。")
    lines.append("- **Context Precision**: 检索上下文中有用内容的比例。范围 [0, 1]，越高越好。")
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
            metrics = row.get("ragas_metrics", {})
            lines.append(f"- 时延(ms): {row.get('latency_ms', 0)}")
            lines.append(f"- Faithfulness: {metrics.get('faithfulness', 0):.4f}")
            lines.append(f"- Answer Relevance: {metrics.get('answer_relevance', 0):.4f}")
            lines.append(f"- Context Relevance: {metrics.get('context_relevance', 0):.4f}")
            lines.append(f"- Context Precision: {metrics.get('context_precision', 0):.4f}")
            lines.append(f"- 回答预览: {row.get('answer_preview', '')}")
        else:
            lines.append(f"- 错误: {row.get('error', '')}")
        lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="使用 RAGAS 评测 RAG 系统")
    parser.add_argument("--cases", required=True, help="测试用例 JSON 文件路径")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="API 地址")
    parser.add_argument(
        "--llm-model",
        default="http://localhost:8000/v1",
        help="LLM API 地址（用于 RAGAS 评估）",
    )
    parser.add_argument(
        "--output-json",
        default="tests/rag_eval_result_ragas.json",
        help="评测明细输出 JSON 路径",
    )
    parser.add_argument(
        "--output-md",
        default="tests/rag_eval_report_ragas.md",
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

    print(f"开始 RAGAS 评测，共 {len(cases)} 个样本...")
    metrics, details = evaluate_with_ragas(
        base_url=args.base_url,
        cases=cases,
        workspace_root=workspace_root,
        llm_api_url=args.llm_model,
    )

    result = {
        "metrics": {
            "total": metrics.total,
            "success": metrics.success,
            "faithfulness": metrics.faithfulness,
            "answer_relevance": metrics.answer_relevance,
            "context_relevance": metrics.context_relevance,
            "context_precision": metrics.context_precision,
            "ragas_score": metrics.ragas_score,
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


if __name__ == "__main__":
    main()
