#!/usr/bin/env bash
set -euo pipefail

cd /data2/wangliangmin/snap/Baichuan/insurance_api
mkdir -p outputs/ablation reports/ablation
EVAL_CASES=tests/insurance_qa_eval_cases.silver.100.json
GPU_ID=0

EXPS=$(cat <<'EOF'
baseline_attn_answer|q_proj,k_proj,v_proj,o_proj|answer
layer_wpack_answer|W_pack|answer
layer_attn_mlp_answer|q_proj,k_proj,v_proj,o_proj,up_proj,down_proj|answer
biz_input_constraints|q_proj,k_proj,v_proj,o_proj|input
biz_input_constraints_mlp|q_proj,k_proj,v_proj,o_proj,up_proj,down_proj|input
EOF
)

while IFS='|' read -r name mods place; do
  [[ -z "$name" ]] && continue
  outdir="outputs/ablation/$name"
  report="reports/ablation/${name}.json"
  if [[ ! -f "$outdir/checkpoint-40/trainer_state.json" ]]; then
    echo "===== TRAIN $name ====="
    if ! CUDA_VISIBLE_DEVICES=$GPU_ID conda run -n baichuan-chat python scripts/train_insurance_lora.py \
      --train-file data/insurance_lora_train.demo.json \
      --model-name-or-path /data2/wangliangmin/snap/Baichuan \
      --output-dir "$outdir" \
      --max-length 256 \
      --batch-size 1 \
      --grad-accum 1 \
      --epochs 1 \
      --max-steps 40 \
      --logging-steps 10 \
      --save-steps 40 \
      --fp16 \
      --attn-implementation eager \
      --target-modules "$mods" \
      --constraint-placement "$place"; then
      echo "!!!!! TRAIN FAILED $name, continue !!!!!"
      continue
    fi
  else
    echo "===== SKIP TRAIN $name (already exists) ====="
  fi

  if [[ -f "$report" ]]; then
    echo "===== SKIP EVAL $name (already exists) ====="
  else
    echo "===== EVAL $name ====="
    if ! CUDA_VISIBLE_DEVICES=$GPU_ID conda run -n baichuan-chat python scripts/eval_lora_keyword_metrics.py \
      --model-name-or-path /data2/wangliangmin/snap/Baichuan \
      --adapter-path "$outdir" \
      --cases "$EVAL_CASES" \
      --constraint-placement "$place" \
      --output-json "$report"; then
      echo "!!!!! EVAL FAILED $name, continue !!!!!"
      continue
    fi
  fi
done <<< "$EXPS"

python - <<'PY'
import glob
import json
import os

rows = []
for p in sorted(glob.glob('reports/ablation/*.json')):
    d = json.load(open(p, 'r', encoding='utf-8'))
    m = d['metrics']
    name = os.path.splitext(os.path.basename(p))[0]
    rows.append((name, m['must_include_recall'], m['citation_hit_rate'], m['groundedness'], m['abstention_f1']))

print('name,must_include_recall,citation_hit_rate,groundedness,abstention_f1')
for r in rows:
    print(','.join(str(x) for x in r))
PY
