#!/usr/bin/env python3
"""Quick keyword-based evaluation for LoRA insurance QA adapters.

This script computes lightweight proxy metrics for rapid A/B screening:
- must_include_recall
- citation_hit_rate
- groundedness (keyword proxy)
- abstention_f1
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

DEFAULT_SYSTEM_PROMPT = (
    "你是保险合同问答助手。只能依据给定合同/材料回答，"
    "若证据不足必须明确说明无法确认，不要编造。"
)

ABSTAIN_PATTERNS = [
    r"无法确认",
    r"证据不足",
    r"建议人工核对",
    r"无法判断",
    r"不确定",
    r"无法提供",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate LoRA adapters with quick keyword metrics")
    parser.add_argument("--model-name-or-path", default="/data2/wangliangmin/snap/Baichuan")
    parser.add_argument("--adapter-path", required=True)
    parser.add_argument("--cases", required=True, help="JSON cases with question/category/expected")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--constraint-placement", choices=["answer", "input"], default="answer")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--device", default="cuda")
    return parser.parse_args()


def read_cases(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Cases must be a JSON list")
    return [x for x in data if isinstance(x, dict)]


def as_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        s = str(item).strip()
        if s:
            out.append(s)
    return out


def build_constraints(row: Dict[str, Any]) -> List[str]:
    expected = row.get("expected", {}) if isinstance(row.get("expected", {}), dict) else {}
    must_include = as_list(expected.get("must_include", []))
    citation_keywords = as_list(expected.get("citation_keywords", []))
    should_abstain = bool(expected.get("should_abstain", False))

    parts: List[str] = []
    if must_include:
        parts.append("必须包含：" + "、".join(must_include[:6]))
    if citation_keywords:
        parts.append("引用线索：" + "、".join(citation_keywords[:6]))
    if should_abstain:
        parts.append("若合同证据不足，明确拒答并提示人工核对。")
    return parts


def build_prompt(row: Dict[str, Any], constraint_placement: str) -> str:
    question = str(row.get("question", "")).strip()
    category = str(row.get("category", "")).strip()

    lines: List[str] = [DEFAULT_SYSTEM_PROMPT]
    if category:
        lines.append(f"场景：{category}")
    if constraint_placement == "input":
        lines.extend(build_constraints(row))
    lines.append(f"问题：{question}")
    lines.append("回答：")
    return "\n".join(lines)


def is_abstained(text: str) -> bool:
    return any(re.search(p, text) for p in ABSTAIN_PATTERNS)


def main() -> None:
    args = parse_args()
    cases = read_cases(Path(args.cases))

    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.float16 if args.device.startswith("cuda") and torch.cuda.is_available() else None
    base = AutoModelForCausalLM.from_pretrained(
        args.model_name_or_path,
        trust_remote_code=True,
        torch_dtype=dtype,
    )
    model = PeftModel.from_pretrained(base, args.adapter_path)
    model.eval()
    if hasattr(model.config, "_attn_implementation"):
        model.config._attn_implementation = "eager"
    model.config.use_cache = False
    if args.device.startswith("cuda") and torch.cuda.is_available():
        model = model.cuda()

    must_include_total = 0
    must_include_hit = 0
    citation_total = 0
    citation_hit = 0
    grounded_total = 0
    grounded_hit = 0

    abstain_tp = 0
    abstain_fp = 0
    abstain_fn = 0

    details: List[Dict[str, Any]] = []

    for row in cases:
        expected = row.get("expected", {}) if isinstance(row.get("expected", {}), dict) else {}
        must_include = as_list(expected.get("must_include", []))
        citation_keywords = as_list(expected.get("citation_keywords", []))
        should_abstain = bool(expected.get("should_abstain", False))

        prompt = build_prompt(row, args.constraint_placement)
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=args.max_length)
        if args.device.startswith("cuda") and torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                temperature=1.0,
                use_cache=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        gen_ids = out[0][inputs["input_ids"].shape[1] :]
        answer = tokenizer.decode(gen_ids, skip_special_tokens=True).strip()

        for kw in must_include:
            must_include_total += 1
            if kw in answer:
                must_include_hit += 1

        if citation_keywords:
            citation_total += 1
            if any(kw in answer for kw in citation_keywords):
                citation_hit += 1

        if must_include or citation_keywords:
            grounded_total += 1
            if ("条款" in answer) or ("根据合同" in answer) or any(kw in answer for kw in citation_keywords):
                grounded_hit += 1

        pred_abstain = is_abstained(answer)
        if pred_abstain and should_abstain:
            abstain_tp += 1
        elif pred_abstain and not should_abstain:
            abstain_fp += 1
        elif (not pred_abstain) and should_abstain:
            abstain_fn += 1

        details.append(
            {
                "id": row.get("id", ""),
                "question": row.get("question", ""),
                "should_abstain": should_abstain,
                "pred_abstain": pred_abstain,
                "answer_preview": answer[:300],
            }
        )

    must_include_recall = (must_include_hit / must_include_total) if must_include_total else 0.0
    citation_hit_rate = (citation_hit / citation_total) if citation_total else 0.0
    groundedness = (grounded_hit / grounded_total) if grounded_total else 0.0

    abstain_precision = abstain_tp / (abstain_tp + abstain_fp) if (abstain_tp + abstain_fp) else 0.0
    abstain_recall = abstain_tp / (abstain_tp + abstain_fn) if (abstain_tp + abstain_fn) else 0.0
    abstention_f1 = (
        2 * abstain_precision * abstain_recall / (abstain_precision + abstain_recall)
        if (abstain_precision + abstain_recall)
        else 0.0
    )

    result = {
        "cases": len(cases),
        "metrics": {
            "must_include_recall": round(must_include_recall, 4),
            "citation_hit_rate": round(citation_hit_rate, 4),
            "groundedness": round(groundedness, 4),
            "abstention_f1": round(abstention_f1, 4),
        },
        "abstention_detail": {
            "tp": abstain_tp,
            "fp": abstain_fp,
            "fn": abstain_fn,
            "precision": round(abstain_precision, 4),
            "recall": round(abstain_recall, 4),
        },
        "details": details,
    }

    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["metrics"], ensure_ascii=False))


if __name__ == "__main__":
    main()
