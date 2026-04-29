#!/usr/bin/env python3
"""LoRA fine-tuning for insurance QA.

This script trains a causal language model on local insurance QA data.
It accepts JSON or JSONL files whose rows contain at least:
- question
- expected.answer_text

Optional fields such as citation_keywords, must_include, should_abstain,
and answer_aliases are folded into the supervised target when present.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

import torch
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)


DEFAULT_SYSTEM_PROMPT = (
    "你是保险合同问答助手。只能依据给定合同/材料回答，"
    "若证据不足必须明确说明无法确认，不要编造。"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune insurance QA model with LoRA")
    parser.add_argument("--model-name-or-path", default="/data2/wangliangmin/snap/Baichuan", help="Base model path or Hugging Face model id")
    parser.add_argument("--train-file", required=True, help="Training data JSON/JSONL path")
    parser.add_argument("--eval-file", default="", help="Optional eval data JSON/JSONL path")
    parser.add_argument("--output-dir", default="outputs/insurance_lora", help="Output directory")
    parser.add_argument("--max-length", type=int, default=1024, help="Token sequence length")
    parser.add_argument("--epochs", type=float, default=3.0, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=2, help="Per-device batch size")
    parser.add_argument("--grad-accum", type=int, default=8, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora-alpha", type=int, default=32, help="LoRA alpha")
    parser.add_argument("--lora-dropout", type=float, default=0.05, help="LoRA dropout")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--bf16", action="store_true", help="Use bf16 if available")
    parser.add_argument("--fp16", action="store_true", help="Use fp16")
    parser.add_argument("--save-steps", type=int, default=50, help="Save checkpoint every N steps")
    parser.add_argument("--logging-steps", type=int, default=5, help="Log every N steps")
    parser.add_argument("--warmup-ratio", type=float, default=0.03, help="Warmup ratio")
    parser.add_argument("--weight-decay", type=float, default=0.0, help="Weight decay")
    parser.add_argument("--load-in-4bit", action="store_true", help="Load base model in 4-bit if bitsandbytes is installed")
    parser.add_argument("--max-steps", type=int, default=-1, help="Optional max training steps for smoke tests")
    parser.add_argument("--attn-implementation", default="eager", help="Attention implementation to use when loading the base model")
    parser.add_argument(
        "--target-modules",
        default="q_proj,k_proj,v_proj,o_proj",
        help="Comma-separated LoRA target modules",
    )
    parser.add_argument(
        "--constraint-placement",
        choices=["answer", "input"],
        default="answer",
        help="Place business constraints in answer text or input instruction",
    )
    return parser.parse_args()


def read_rows(path: Path) -> List[Dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if not stripped:
        return []
    if stripped.startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("JSON train file must be an array")
        return [x for x in data if isinstance(x, dict)]

    rows: List[Dict[str, Any]] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        obj = json.loads(s)
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


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
    aliases = as_list(expected.get("answer_aliases", []))
    must_include = as_list(expected.get("must_include", []))
    citation_keywords = as_list(expected.get("citation_keywords", []))
    should_abstain = bool(expected.get("should_abstain", False))

    parts: List[str] = []
    if aliases:
        parts.append("可接受表述：" + "；".join(aliases[:3]))
    if must_include:
        parts.append("必须包含：" + "、".join(must_include[:6]))
    if citation_keywords:
        parts.append("引用线索：" + "、".join(citation_keywords[:6]))
    if should_abstain:
        parts.append("若合同证据不足，明确拒答并提示人工核对。")
    return parts


def build_answer(row: Dict[str, Any], include_constraints: bool) -> str:
    expected = row.get("expected", {}) if isinstance(row.get("expected", {}), dict) else {}
    answer = str(expected.get("answer_text", "")).strip()
    parts = [answer] if answer else []
    if include_constraints:
        parts.extend(build_constraints(row))
    return "\n".join(parts).strip()


def format_example(row: Dict[str, Any], constraint_placement: str) -> str:
    question = str(row.get("question", "")).strip()
    category = str(row.get("category", "")).strip()
    instruction = [DEFAULT_SYSTEM_PROMPT]
    if category:
        instruction.append(f"场景：{category}")
    if constraint_placement == "input":
        constraints = build_constraints(row)
        if constraints:
            instruction.extend(constraints)
    instruction.append(f"问题：{question}")
    instruction.append("回答：")

    answer = build_answer(row, include_constraints=(constraint_placement == "answer"))
    return "\n".join(instruction) + answer


def to_dataset(rows: List[Dict[str, Any]], constraint_placement: str) -> Dataset:
    records: List[Dict[str, str]] = []
    for row in rows:
        question = str(row.get("question", "")).strip()
        expected = row.get("expected", {}) if isinstance(row.get("expected", {}), dict) else {}
        answer_text = str(expected.get("answer_text", "")).strip()
        if not question or not answer_text:
            continue
        records.append({"text": format_example(row, constraint_placement=constraint_placement)})
    if not records:
        raise ValueError("No valid training records found")
    return Dataset.from_list(records)


def tokenize_dataset(dataset: Dataset, tokenizer, max_length: int) -> Dataset:
    def _tokenize(batch: Dict[str, List[str]]) -> Dict[str, Any]:
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=max_length,
            padding=False,
            return_attention_mask=True,
        )

    tokenized = dataset.map(_tokenize, batched=True, remove_columns=dataset.column_names)
    tokenized.set_format(type="torch")
    return tokenized


def resolve_dtype(args: argparse.Namespace):
    if args.bf16 and torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        return torch.bfloat16
    if args.fp16:
        return torch.float16
    return None


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)

    train_rows = read_rows(Path(args.train_file))
    train_ds = to_dataset(train_rows, constraint_placement=args.constraint_placement)

    eval_ds = None
    if args.eval_file:
        eval_rows = read_rows(Path(args.eval_file))
        eval_ds = to_dataset(eval_rows, constraint_placement=args.constraint_placement)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    dtype = resolve_dtype(args)
    model_kwargs: Dict[str, Any] = {"trust_remote_code": True}
    if dtype is not None:
        model_kwargs["torch_dtype"] = dtype
    if args.load_in_4bit:
        model_kwargs["load_in_4bit"] = True
    if args.attn_implementation:
        model_kwargs["attn_implementation"] = args.attn_implementation

    try:
        model = AutoModelForCausalLM.from_pretrained(args.model_name_or_path, **model_kwargs)
    except TypeError:
        model_kwargs.pop("attn_implementation", None)
        model = AutoModelForCausalLM.from_pretrained(args.model_name_or_path, **model_kwargs)
    if hasattr(model.config, "_attn_implementation"):
        model.config._attn_implementation = args.attn_implementation
    model.config.use_cache = False
    model.gradient_checkpointing_enable()

    target_modules = [x.strip() for x in args.target_modules.split(",") if x.strip()]
    if not target_modules:
        raise ValueError("--target-modules cannot be empty")

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=target_modules,
    )
    model = get_peft_model(model, lora_config)
    print(f"Using target_modules={target_modules}, constraint_placement={args.constraint_placement}")
    model.print_trainable_parameters()

    train_tokenized = tokenize_dataset(train_ds, tokenizer, args.max_length)
    eval_tokenized = tokenize_dataset(eval_ds, tokenizer, args.max_length) if eval_ds is not None else None

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        warmup_ratio=args.warmup_ratio,
        weight_decay=args.weight_decay,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        save_total_limit=2,
        eval_strategy="steps" if eval_tokenized is not None else "no",
        eval_steps=args.save_steps if eval_tokenized is not None else None,
        report_to="none",
        bf16=args.bf16,
        fp16=args.fp16 and not args.bf16,
        optim="adamw_torch",
        remove_unused_columns=False,
        dataloader_pin_memory=False,
        gradient_checkpointing=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_tokenized,
        eval_dataset=eval_tokenized,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )

    trainer.train()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)


if __name__ == "__main__":
    main()