#!/usr/bin/env bash
set -euo pipefail

# One-click crawl + local search UI launcher.
# Usage:
#   bash scripts/one_click_crawl.sh
#   bash scripts/one_click_crawl.sh /path/to/sites.txt data/output.jsonl

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

SITES_FILE="${1:-$PROJECT_DIR/seeds_insurance.txt}"
OUTPUT_JSONL="${2:-$PROJECT_DIR/data/insurance_contract_chunks.jsonl}"
MAX_PAGES="${MAX_PAGES:-300}"
MAX_DEPTH="${MAX_DEPTH:-2}"
DELAY="${DELAY:-0.4}"
MIN_KEYWORD_HITS="${MIN_KEYWORD_HITS:-2}"
SERVE_HOST="${SERVE_HOST:-127.0.0.1}"
SERVE_PORT="${SERVE_PORT:-8098}"
ULTRA_CLEAN="${ULTRA_CLEAN:-1}"

if [[ ! -f "$SITES_FILE" ]]; then
  echo "[error] sites file not found: $SITES_FILE"
  echo "Please create it with one URL per line."
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_JSONL")"

CMD=(
  conda run -n baichuan-chat python "$SCRIPT_DIR/auto_crawl_and_serve_search.py"
  --sites-file "$SITES_FILE"
  --output-jsonl "$OUTPUT_JSONL"
  --max-pages "$MAX_PAGES"
  --max-depth "$MAX_DEPTH"
  --delay "$DELAY"
  --min-keyword-hits "$MIN_KEYWORD_HITS"
  --serve
  --serve-host "$SERVE_HOST"
  --serve-port "$SERVE_PORT"
)

if [[ "$ULTRA_CLEAN" == "1" ]]; then
  CMD+=(--ultra-clean)
fi

echo "[run] sites_file=$SITES_FILE"
echo "[run] output_jsonl=$OUTPUT_JSONL"
echo "[run] ui=http://$SERVE_HOST:$SERVE_PORT"
"${CMD[@]}"
