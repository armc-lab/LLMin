# 保险问答 LoRA 微调

这是一个本地可跑的最小微调入口，目标是先把保险问答能力在现有 Baichuan 底座上做监督微调，再接回现有评测流程。

## 1. 环境依赖

当前环境里已有 `transformers`、`datasets` 和 `accelerate`，缺少 `peft`。先安装：

```bash
cd /data2/wangliangmin/snap/Baichuan/insurance_api
conda run -n baichuan-chat python -m pip install peft
```

如果你要 4-bit 训练，再补：

```bash
conda run -n baichuan-chat python -m pip install bitsandbytes
```

## 2. 训练数据

建议先用现有模板数据起步：

```bash
python - <<'PY'
import json
from pathlib import Path

src = Path('tests/insurance_qa_eval_template.json')
dst = Path('data/insurance_lora_train.json')
rows = json.loads(src.read_text(encoding='utf-8'))
dst.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
print(dst)
PY
```

你后续也可以把 `convert_rag_cases_to_insurance_silver.py` 生成的银标样本直接作为训练集输入。

## 3. 开始训练

```bash
cd /data2/wangliangmin/snap/Baichuan/insurance_api
conda run -n baichuan-chat python scripts/train_insurance_lora.py \
  --train-file data/insurance_lora_train.json \
  --model-name-or-path /data2/wangliangmin/snap/Baichuan \
  --output-dir outputs/insurance_lora_demo \
  --epochs 3 \
  --batch-size 2 \
  --grad-accum 8 \
  --max-length 1024 \
  --fp16
```

## 4. 训练后怎么接回服务

训练完成后，`outputs/insurance_lora_demo` 会保存 LoRA 权重和 tokenizer。接回推理服务时，需要在 `main_api.py` 或启动脚本里把底座模型和 LoRA adapter 一起加载。

## 5. 建议的下一步

1. 先用 8 条模板样本跑通脚本，确认训练流程没问题。
2. 再把银标评测集扩到 100 条以上，做一轮真正的保险域微调。
3. 微调后跑 [tests/README_insurance_eval_workflow.md](../tests/README_insurance_eval_workflow.md) 里的评测流程，比对基线和微调结果。