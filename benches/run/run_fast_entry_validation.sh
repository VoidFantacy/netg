#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

dataset="${DATASET:-webvid2_5m_light_v1}"
seeds_csv="${SEEDS:-20260828,20260829,20260830}"
num_runs="${NUM_RUNS:-3}"
max_queries="${MAX_QUERIES:-10000}"
target_hubs="${TARGET_HUBS:-815}"
force="${FORCE:-0}"
IFS=',' read -r -a seeds <<< "$seeds_csv"

if [[ "$dataset" != "webvid2_5m_light_v1" ]]; then
  echo "This validated one-click workflow currently supports webvid2_5m_light_v1 only." >&2
  exit 2
fi
if [[ "$num_runs" != "3" || "$max_queries" != "10000" ]]; then
  echo "The current multi-seed summarizer requires NUM_RUNS=3 and MAX_QUERIES=10000." >&2
  exit 2
fi

required=(
  build/benches/test
  build/benches/bench_per_query_recall
  indices/${dataset}_index/acosp_nsg.json
)
for path in "${required[@]}"; do
  [[ -e "$path" ]] || { echo "Missing required path: $path" >&2; exit 2; }
done

eta_minutes=$(( ${#seeds[@]} * 8 ))
echo "Fast-entry validation: dataset=${dataset}, seeds=${seeds_csv}, hubs=${target_hubs}, 3 runs/seed"
echo "Estimated wall time on the current 16-vCPU host: about ${eta_minutes} minutes."
echo "Existing contract-matching outputs are reused; set FORCE=1 to rerun them."

json_matches() {
  local path="$1" top_k="$2"
  [[ -f "$path" ]] || return 1
  jq -e --arg ds "$dataset" --argjson k "$top_k" \
    --argjson q "$max_queries" --argjson runs "$num_runs" \
    '.dataset == $ds and .top_k == $k and .num_queries == $q and .num_runs == $runs' \
    "$path" >/dev/null
}

for seed in "${seeds[@]}"; do
  out_dir="fast_entry_variants/${dataset}_seed${seed}"
  mkdir -p "$out_dir"
  if [[ "$force" == "1" ]] || ! jq -e --argjson seed "$seed" --argjson hubs "$target_hubs" \
      '.qgt_only == true and .target_hubs == $hubs and .variants.qgt_cover.seed == $seed' \
      "$out_dir/manifest.json" >/dev/null 2>&1; then
    OPENBLAS_NUM_THREADS=16 OMP_NUM_THREADS=16 \
      .venv_cpu/bin/python benches/run/build_fast_entry_variants.py \
      --dataset "$dataset" --qgt-only --target-hubs "$target_hubs" \
      --seed "$seed" --output-dir "$PWD/$out_dir" \
      2>&1 | tee "$out_dir/build.log"
  fi

  common=(
    build/benches/test --dataset "$dataset"
    --acpg_file "indices/${dataset}_index/acosp_nsg.json"
    --raw_hubs "$out_dir/qgt_cover_hubs.bin"
    --transformed_hubs "$out_dir/qgt_gt_basin_prototype_hubs.bin"
    --transformed_ids "$out_dir/qgt_cover_hub_ids.bin"
    --test_scope routing --num_runs "$num_runs" --max_queries "$max_queries"
  )
  if [[ "$force" == "1" ]] || ! json_matches "$out_dir/eval_r1_3run.json" 1; then
    /usr/bin/time -v -o "$out_dir/eval_r1_3run.time.txt" \
      "${common[@]}" --top_k 1 --search_Ls 64,128,200,400 \
      --fn_result "$out_dir/eval_r1_3run.json" \
      2>&1 | tee "$out_dir/eval_r1_3run.log"
  fi
  if [[ "$force" == "1" ]] || ! json_matches "$out_dir/eval_r100_3run.json" 100; then
    /usr/bin/time -v -o "$out_dir/eval_r100_3run.time.txt" \
      "${common[@]}" --top_k 100 --search_Ls 100,128,200,400 \
      --fn_result "$out_dir/eval_r100_3run.json" \
      2>&1 | tee "$out_dir/eval_r100_3run.log"
  fi
  if [[ "$force" == "1" || ! -f "$out_dir/per_query_r10.json" ]]; then
    /usr/bin/time -v -o "$out_dir/per_query_r10.time.txt" \
      build/benches/bench_per_query_recall --dataset "$dataset" \
      --acpg_file "indices/${dataset}_index/acosp_nsg.json" \
      --output_file "$out_dir/per_query_r10.json" \
      --transformed_hubs "$out_dir/qgt_gt_basin_prototype_hubs.bin" \
      --transformed_ids "$out_dir/qgt_cover_hub_ids.bin" \
      --raw_hubs "$out_dir/qgt_cover_hubs.bin" \
      --search_L 64,128,200,400 --top_k 10 --max_queries "$max_queries" \
      2>&1 | tee "$out_dir/per_query_r10.log"
  fi
done

.venv_cpu/bin/python benches/run/summarize_fast_entry_multiseed.py \
  --dataset "$dataset" --seeds "$seeds_csv"
echo "Done. See fast_entry_variants/${dataset}_multiseed_summary.json"
