#!/usr/bin/env python3
"""Insurance QA evaluation with baseline comparison.

This script evaluates insurance contract QA outputs using a labeled or silver-labeled set.
It supports:
- single model scoring
- baseline vs candidate comparison
- JSON + Markdown report generation

Notes:
- Full-label mode: provide answer_text / slots / numeric constraints for strict scoring.
- Silver-label mode: only provide must_include / citation_keywords / should_abstain.
    The script computes metrics on available labels and reports coverage.

Usage:
python scripts/evaluate_insurance_qa.py \
  --cases tests/insurance_qa_eval_template.json \
  --predictions tests/insurance_qa_predictions.example.json

python scripts/evaluate_insurance_qa.py \
  --cases tests/insurance_qa_eval_template.json \
  --predictions tests/candidate_predictions.json \
  --baseline-predictions tests/baseline_predictions.json
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

REFUSAL_PATTERNS = [
    "证据不足",
    "无法确定",
    "无法判断",
    "需人工",
    "无法根据",
    "未检索到",
    "建议人工核对",
]

SCORE_WEIGHTS = {
    "correctness": 0.30,
    "grounding": 0.25,
    "numeric": 0.20,
    "abstention": 0.15,
    "retrieval": 0.10,
}


@dataclass
class Metrics:
    total_cases: int = 0
    answered_cases: int = 0
    missing_predictions: int = 0

    # Label coverage (for silver/unlabeled workflows)
    text_scored_cases: int = 0
    include_scored_cases: int = 0
    slot_scored_cases: int = 0
    citation_scored_cases: int = 0
    numeric_scored_items: int = 0
    abstention_scored_cases: int = 0

    exact_match: float = 0.0
    token_f1: float = 0.0
    must_include_recall: float = 0.0
    must_not_include_violation_rate: float = 0.0

    slot_precision: float = 0.0
    slot_recall: float = 0.0
    slot_f1: float = 0.0

    citation_hit_rate: float = 0.0
    groundedness: float = 0.0

    numeric_consistency: float = 0.0

    abstention_precision: float = 0.0
    abstention_recall: float = 0.0
    abstention_f1: float = 0.0

    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0

    composite_score: float = 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate insurance QA with fixed metrics")
    parser.add_argument("--cases", required=True, help="Labeled cases JSON")
    parser.add_argument("--predictions", required=True, help="Candidate predictions JSON")
    parser.add_argument("--baseline-predictions", default="", help="Optional baseline predictions JSON")
    parser.add_argument("--output-json", default="tests/insurance_qa_eval_result.json", help="Result JSON path")
    parser.add_argument("--output-md", default="tests/insurance_qa_eval_report.md", help="Result Markdown path")
    return parser.parse_args()


def load_json_array(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON array")
    return [x for x in data if isinstance(x, dict)]


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", "", text)
    return text


def char_tokens(text: str) -> List[str]:
    return [c for c in normalize_text(text) if c]


def safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return a / b


def f1_from_counts(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    p = safe_div(tp, tp + fp)
    r = safe_div(tp, tp + fn)
    f1 = safe_div(2 * p * r, p + r) if (p + r) > 0 else 0.0
    return p, r, f1


def best_text_f1(pred: str, references: Sequence[str]) -> float:
    pred_toks = char_tokens(pred)
    if not references:
        return 0.0

    best = 0.0
    for ref in references:
        ref_toks = char_tokens(ref)
        pred_count: Dict[str, int] = {}
        ref_count: Dict[str, int] = {}
        for t in pred_toks:
            pred_count[t] = pred_count.get(t, 0) + 1
        for t in ref_toks:
            ref_count[t] = ref_count.get(t, 0) + 1

        common = 0
        for t, c in pred_count.items():
            common += min(c, ref_count.get(t, 0))

        if len(pred_toks) == 0 or len(ref_toks) == 0:
            cur = 0.0
        else:
            p = common / len(pred_toks)
            r = common / len(ref_toks)
            cur = safe_div(2 * p * r, p + r) if (p + r) > 0 else 0.0
        best = max(best, cur)

    return best


def exact_match(pred: str, references: Sequence[str]) -> bool:
    p = normalize_text(pred)
    return any(p == normalize_text(ref) for ref in references)


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(k and k in text for k in keywords)


def detect_abstention(answer: str, explicit_flag: Any) -> bool:
    if isinstance(explicit_flag, bool):
        return explicit_flag
    return contains_any(answer, REFUSAL_PATTERNS)


def percentile(values: Sequence[float], p: float) -> float:
    if not values:
        return 0.0
    vs = sorted(values)
    if len(vs) == 1:
        return float(vs[0])
    idx = int(round((p / 100.0) * (len(vs) - 1)))
    return float(vs[idx])


def evaluate(cases: List[Dict[str, Any]], predictions_by_id: Mapping[str, Dict[str, Any]]) -> Tuple[Metrics, List[Dict[str, Any]]]:
    m = Metrics(total_cases=len(cases))
    details: List[Dict[str, Any]] = []

    em_hits = 0
    text_eval_total = 0
    f1_values: List[float] = []
    include_recalls: List[float] = []
    include_eval_total = 0
    not_include_violations = 0
    not_include_eval_total = 0

    slot_tp = slot_fp = slot_fn = 0

    citation_hits = 0
    citation_eval_total = 0
    grounded_claim_hit = 0
    grounded_claim_total = 0

    numeric_ok = 0
    numeric_total = 0

    abst_tp = abst_fp = abst_fn = 0
    abst_eval_total = 0

    latencies: List[float] = []

    for case in cases:
        case_id = str(case.get("id", "")).strip()
        pred = predictions_by_id.get(case_id)
        exp = case.get("expected", {}) if isinstance(case.get("expected", {}), dict) else {}

        if not pred:
            m.missing_predictions += 1
            details.append({
                "id": case_id,
                "ok": False,
                "error": "missing_prediction",
            })
            continue

        m.answered_cases += 1

        answer = str(pred.get("answer", ""))
        citations = pred.get("citations", [])
        if not isinstance(citations, list):
            citations = []
        citations = [str(x) for x in citations]
        citation_blob = "\n".join(citations)

        aliases = [str(exp.get("answer_text", ""))]
        aliases.extend(str(x) for x in exp.get("answer_aliases", []) if str(x).strip())
        aliases = [x for x in aliases if x.strip()]

        em = None
        f1 = None
        if aliases:
            em = exact_match(answer, aliases)
            em_hits += int(em)
            text_eval_total += 1

            f1 = best_text_f1(answer, aliases)
            f1_values.append(f1)

        must_include = [str(x) for x in exp.get("must_include", []) if str(x).strip()]
        if must_include:
            hit = sum(1 for k in must_include if k in answer)
            include_recalls.append(hit / len(must_include))
            include_eval_total += 1

            grounded_claim_total += len(must_include)
            grounded_claim_hit += sum(1 for k in must_include if k in citation_blob)
        else:
            include_recalls.append(1.0)

        must_not_include = [str(x) for x in exp.get("must_not_include", []) if str(x).strip()]
        if must_not_include:
            not_include_eval_total += 1
            if any(k in answer for k in must_not_include):
                not_include_violations += 1

        exp_slots = exp.get("slots", {}) if isinstance(exp.get("slots", {}), dict) else {}
        pred_slots = pred.get("predicted_slots", {}) if isinstance(pred.get("predicted_slots", {}), dict) else {}

        exp_slot_norm = {k: normalize_text(str(v)) for k, v in exp_slots.items()}
        pred_slot_norm = {k: normalize_text(str(v)) for k, v in pred_slots.items()}

        if exp_slot_norm:
            for key, value in pred_slot_norm.items():
                if key in exp_slot_norm and value == exp_slot_norm[key]:
                    slot_tp += 1
                else:
                    slot_fp += 1
            for key, value in exp_slot_norm.items():
                if key not in pred_slot_norm or pred_slot_norm.get(key) != value:
                    slot_fn += 1

        citation_keywords = [str(x) for x in exp.get("citation_keywords", []) if str(x).strip()]
        if citation_keywords:
            citation_eval_total += 1
            if contains_any(citation_blob, citation_keywords):
                citation_hits += 1

        for rule in exp.get("numeric_constraints", []):
            if not isinstance(rule, dict):
                continue
            val = str(rule.get("value", "")).strip()
            if not val:
                continue
            numeric_total += 1
            if val in answer or val in citation_blob:
                numeric_ok += 1

        has_abst_label = "should_abstain" in exp
        should_abstain = bool(exp.get("should_abstain", False))
        abstained = detect_abstention(answer, pred.get("abstained"))
        if has_abst_label:
            abst_eval_total += 1
            if should_abstain and abstained:
                abst_tp += 1
            elif (not should_abstain) and abstained:
                abst_fp += 1
            elif should_abstain and (not abstained):
                abst_fn += 1

        latency = pred.get("latency_ms")
        if isinstance(latency, (int, float)) and latency >= 0:
            latencies.append(float(latency))

        details.append({
            "id": case_id,
            "em": em,
            "token_f1": round(f1, 4) if isinstance(f1, float) else None,
            "abstained": abstained,
            "should_abstain": should_abstain if has_abst_label else None,
        })

    m.text_scored_cases = text_eval_total
    m.include_scored_cases = include_eval_total
    m.slot_scored_cases = len([c for c in cases if isinstance(c.get("expected", {}), dict) and bool(c.get("expected", {}).get("slots", {}))])
    m.citation_scored_cases = citation_eval_total
    m.numeric_scored_items = numeric_total
    m.abstention_scored_cases = abst_eval_total

    m.exact_match = round(safe_div(em_hits, text_eval_total), 4)
    m.token_f1 = round(statistics.mean(f1_values), 4) if f1_values else 0.0
    m.must_include_recall = round(statistics.mean(include_recalls), 4) if include_recalls else 0.0
    m.must_not_include_violation_rate = round(safe_div(not_include_violations, not_include_eval_total), 4)

    p, r, f1 = f1_from_counts(slot_tp, slot_fp, slot_fn)
    m.slot_precision = round(p, 4)
    m.slot_recall = round(r, 4)
    m.slot_f1 = round(f1, 4)

    m.citation_hit_rate = round(safe_div(citation_hits, citation_eval_total), 4)
    m.groundedness = round(safe_div(grounded_claim_hit, grounded_claim_total), 4)

    m.numeric_consistency = round(safe_div(numeric_ok, numeric_total), 4)

    ap, ar, af1 = f1_from_counts(abst_tp, abst_fp, abst_fn)
    m.abstention_precision = round(ap, 4)
    m.abstention_recall = round(ar, 4)
    m.abstention_f1 = round(af1, 4)

    if latencies:
        m.avg_latency_ms = round(statistics.mean(latencies), 2)
        m.p50_latency_ms = round(percentile(latencies, 50), 2)
        m.p95_latency_ms = round(percentile(latencies, 95), 2)

    correctness_values: List[float] = []
    if text_eval_total > 0:
        correctness_values.append(0.6 * m.token_f1 + 0.4 * m.exact_match)
    if m.slot_scored_cases > 0:
        correctness_values.append(m.slot_f1)
    if include_eval_total > 0:
        correctness_values.append(m.must_include_recall)
    correctness = statistics.mean(correctness_values) if correctness_values else 0.0

    grounding_values: List[float] = []
    if grounded_claim_total > 0:
        grounding_values.append(m.groundedness)
    if citation_eval_total > 0:
        grounding_values.append(m.citation_hit_rate)
    grounding = statistics.mean(grounding_values) if grounding_values else 0.0

    active_dims: List[Tuple[str, float]] = []
    if correctness_values:
        active_dims.append(("correctness", correctness))
    if grounding_values:
        active_dims.append(("grounding", grounding))
    if numeric_total > 0:
        active_dims.append(("numeric", m.numeric_consistency))
    if abst_eval_total > 0:
        active_dims.append(("abstention", m.abstention_f1))
    if citation_eval_total > 0:
        active_dims.append(("retrieval", m.citation_hit_rate))

    if active_dims:
        weighted_sum = sum(SCORE_WEIGHTS[k] * v for k, v in active_dims)
        active_weights = sum(SCORE_WEIGHTS[k] for k, _ in active_dims)
        m.composite_score = round(safe_div(weighted_sum, active_weights), 4)
    else:
        m.composite_score = 0.0

    return m, details


def build_delta(base: Metrics, cand: Metrics) -> Dict[str, float]:
    base_d = asdict(base)
    cand_d = asdict(cand)
    delta: Dict[str, float] = {}
    for k, v in cand_d.items():
        if isinstance(v, (int, float)) and isinstance(base_d.get(k), (int, float)):
            delta[k] = round(float(v) - float(base_d[k]), 4)
    return delta


def write_reports(
    output_json: Path,
    output_md: Path,
    candidate: Metrics,
    details: List[Dict[str, Any]],
    baseline: Metrics | None,
    delta: Dict[str, float] | None,
) -> None:
    payload: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "candidate_metrics": asdict(candidate),
        "details": details,
    }
    if baseline is not None:
        payload["baseline_metrics"] = asdict(baseline)
    if delta is not None:
        payload["delta"] = delta

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines: List[str] = []
    lines.append("# Insurance QA Evaluation Report")
    lines.append("")
    lines.append(f"- Generated at: {payload['generated_at']}")
    lines.append(f"- Total cases: {candidate.total_cases}")
    lines.append(f"- Answered cases: {candidate.answered_cases}")
    lines.append(f"- Missing predictions: {candidate.missing_predictions}")
    lines.append("- Label coverage:")
    lines.append(f"  - text_scored_cases: {candidate.text_scored_cases}")
    lines.append(f"  - include_scored_cases: {candidate.include_scored_cases}")
    lines.append(f"  - slot_scored_cases: {candidate.slot_scored_cases}")
    lines.append(f"  - citation_scored_cases: {candidate.citation_scored_cases}")
    lines.append(f"  - numeric_scored_items: {candidate.numeric_scored_items}")
    lines.append(f"  - abstention_scored_cases: {candidate.abstention_scored_cases}")
    lines.append("")
    lines.append("## Candidate Metrics")
    lines.append("")

    for key, value in asdict(candidate).items():
        lines.append(f"- {key}: {value}")

    if baseline is not None and delta is not None:
        lines.append("")
        lines.append("## Baseline Comparison (candidate - baseline)")
        lines.append("")
        tracked = [
            "exact_match",
            "token_f1",
            "slot_f1",
            "citation_hit_rate",
            "groundedness",
            "numeric_consistency",
            "abstention_f1",
            "composite_score",
            "p95_latency_ms",
        ]
        for key in tracked:
            if key in delta:
                lines.append(f"- {key}: {delta[key]:+}")

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()

    cases = load_json_array(Path(args.cases))
    candidate_preds = load_json_array(Path(args.predictions))
    candidate_by_id = {str(x.get("id", "")).strip(): x for x in candidate_preds}

    candidate_metrics, details = evaluate(cases, candidate_by_id)

    baseline_metrics = None
    delta = None
    if args.baseline_predictions:
        baseline_preds = load_json_array(Path(args.baseline_predictions))
        baseline_by_id = {str(x.get("id", "")).strip(): x for x in baseline_preds}
        baseline_metrics, _ = evaluate(cases, baseline_by_id)
        delta = build_delta(baseline_metrics, candidate_metrics)

    write_reports(
        output_json=Path(args.output_json),
        output_md=Path(args.output_md),
        candidate=candidate_metrics,
        details=details,
        baseline=baseline_metrics,
        delta=delta,
    )

    print("Evaluation finished")
    print(f"Candidate composite_score: {candidate_metrics.composite_score}")
    print(f"Result JSON: {args.output_json}")
    print(f"Report MD: {args.output_md}")


if __name__ == "__main__":
    main()
