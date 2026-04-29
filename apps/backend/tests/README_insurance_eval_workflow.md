# Insurance QA 无标注可用流程

适用场景：没有完整人工标注集，但要先做 13B 微调前后对比。

说明：下面的脚本建议在 `baichuan-chat` 环境里运行，因为它和你的服务启动环境一致，且已包含 PyMuPDF 等依赖。

## 1) 先把已有 RAG 用例转成银标集

```bash
cd /data2/wangliangmin/snap/Baichuan/insurance_api
python scripts/convert_rag_cases_to_insurance_silver.py \
  --input tests/rag_eval_cases.100.json \
  --output tests/insurance_qa_eval_cases.silver.100.json
```

## 2) 跑基线模型，生成预测

先保证 API 已启动（默认 http://127.0.0.1:8001）。

```bash
cd /data2/wangliangmin/snap/Baichuan/insurance_api
python scripts/run_insurance_qa_batch.py \
  --cases tests/insurance_qa_eval_cases.silver.100.json \
  --workspace-root /data2/wangliangmin/snap/Baichuan/insurance_api \
  --base-url http://127.0.0.1:8001 \
  --output tests/predictions_baseline.silver.100.json
```

## 3) 切换到微调模型，再跑一次预测

```bash
cd /data2/wangliangmin/snap/Baichuan/insurance_api
python scripts/run_insurance_qa_batch.py \
  --cases tests/insurance_qa_eval_cases.silver.100.json \
  --workspace-root /data2/wangliangmin/snap/Baichuan/insurance_api \
  --base-url http://127.0.0.1:8001 \
  --output tests/predictions_finetuned.silver.100.json
```

## 4) 自动评测 + 对比

```bash
cd /data2/wangliangmin/snap/Baichuan/insurance_api
python scripts/evaluate_insurance_qa.py \
  --cases tests/insurance_qa_eval_cases.silver.100.json \
  --predictions tests/predictions_finetuned.silver.100.json \
  --baseline-predictions tests/predictions_baseline.silver.100.json \
  --output-json tests/insurance_qa_eval_result.silver.compare.json \
  --output-md tests/insurance_qa_eval_report.silver.compare.md
```

## 5) 如何看银标结果

优先看这些指标：
- must_include_recall
- citation_hit_rate
- groundedness
- abstention_f1
- p95_latency_ms
- composite_score

说明：
- 这是银标对比，适合快速迭代模型。
- 最终上线前，建议再抽样 50-100 条做人工金标复核。
