#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

dataset="laion10m_acsg_v1"
variant_name="${dataset}_validation"
seeds_csv="${SEEDS:-20260828,20260829,20260830}"
num_runs="${NUM_RUNS:-3}"
max_queries="${MAX_QUERIES:-10000}"
target_hubs="${TARGET_HUBS:-821}"
force="${FORCE:-0}"
log_dir="logs/${variant_name}"
IFS=',' read -r -a seeds <<< "$seeds_csv"

if [[ "$num_runs" != "3" || "$max_queries" != "10000" ]]; then
  echo "LAION formal validation requires NUM_RUNS=3 and MAX_QUERIES=10000." >&2
  exit 2
fi

required=(
  build/benches/test
  build/benches/bench_per_query_recall
  benches/datasets/LAION10M_acsg_v1/manifest.json
  indices/${dataset}_index/acosp_nsg.json
  indices/${dataset}_index/acosp_nsg.json.info
)
for path in "${required[@]}"; do
  [[ -e "$path" ]] || { echo "Missing required path: $path" >&2; exit 2; }
done

mkdir -p "$log_dir"
exec 9>"${log_dir}/pipeline.lock"
if ! flock -n 9; then
  echo "another LAION Fast validation owns ${log_dir}/pipeline.lock" >&2
  exit 1
fi
printf '%s\n' "$$" > "${log_dir}/pipeline.pid"

json_matches() {
  local path="$1" top_k="$2"
  [[ -f "$path" ]] || return 1
  jq -e --arg ds "$dataset" --arg split "validation" --argjson k "$top_k" \
    --argjson q "$max_queries" --argjson runs "$num_runs" \
    '.dataset == $ds and .split == $split and .top_k == $k and
     .num_queries == $q and .num_runs == $runs' "$path" >/dev/null
}

echo "[$(date --iso-8601=seconds)] LAION Fast validation start"
echo "dataset=${dataset} split=validation seeds=${seeds_csv} hubs=${target_hubs} runs=${num_runs}"

for seed in "${seeds[@]}"; do
  out_dir="fast_entry_variants/${variant_name}_seed${seed}"
  mkdir -p "$out_dir"

  if [[ "$force" == "1" ]] || ! jq -e --argjson seed "$seed" --argjson hubs "$target_hubs" \
      --arg ds "$dataset" \
      '.dataset == $ds and .qgt_only == true and .target_hubs == $hubs and
       .variants.qgt_cover.seed == $seed' \
      "$out_dir/manifest.json" >/dev/null 2>&1; then
    OPENBLAS_NUM_THREADS=16 OMP_NUM_THREADS=16 \
      /usr/bin/time -v -o "$out_dir/build.time.txt" \
      .venv_cpu/bin/python benches/run/build_fast_entry_variants.py \
      --dataset "$dataset" --qgt-only --target-hubs "$target_hubs" \
      --seed "$seed" --output-dir "$PWD/$out_dir" \
      > "$out_dir/build.log" 2>&1
  fi

  common=(
    build/benches/test --dataset "$dataset"
    --query_split validation
    --acpg_file "indices/${dataset}_index/acosp_nsg.json"
    --raw_hubs "$out_dir/qgt_cover_hubs.bin"
    --transformed_hubs "$out_dir/qgt_gt_basin_prototype_hubs.bin"
    --transformed_ids "$out_dir/qgt_cover_hub_ids.bin"
    --test_scope comparison --num_runs "$num_runs" --max_queries "$max_queries"
  )
  if [[ "$force" == "1" ]] || ! json_matches "$out_dir/eval_r1_3run.json" 1; then
    /usr/bin/time -v -o "$out_dir/eval_r1_3run.time.txt" \
      "${common[@]}" --top_k 1 --search_Ls 64,128,200,400 \
      --fn_result "$out_dir/eval_r1_3run.json" \
      > "$out_dir/eval_r1_3run.log" 2>&1
  fi
  if [[ "$force" == "1" ]] || ! json_matches "$out_dir/eval_r100_3run.json" 100; then
    /usr/bin/time -v -o "$out_dir/eval_r100_3run.time.txt" \
      "${common[@]}" --top_k 100 --search_Ls 100,128,200,400 \
      --fn_result "$out_dir/eval_r100_3run.json" \
      > "$out_dir/eval_r100_3run.log" 2>&1
  fi
  if [[ "$force" == "1" ]] || ! jq -e --arg ds "$dataset" --arg split "validation" \
      --argjson q "$max_queries" \
      '.dataset == $ds and .split == $split and .top_k == 10 and .num_queries == $q' \
      "$out_dir/per_query_r10.json" >/dev/null 2>&1; then
    /usr/bin/time -v -o "$out_dir/per_query_r10.time.txt" \
      build/benches/bench_per_query_recall --dataset "$dataset" \
      --query_split validation \
      --acpg_file "indices/${dataset}_index/acosp_nsg.json" \
      --output_file "$out_dir/per_query_r10.json" \
      --transformed_hubs "$out_dir/qgt_gt_basin_prototype_hubs.bin" \
      --transformed_ids "$out_dir/qgt_cover_hub_ids.bin" \
      --raw_hubs "$out_dir/qgt_cover_hubs.bin" \
      --search_L 64,128,200,400 --top_k 10 --max_queries "$max_queries" \
      > "$out_dir/per_query_r10.log" 2>&1
  fi
  echo "[$(date --iso-8601=seconds)] seed=${seed} complete"
done

.venv_cpu/bin/python benches/run/summarize_fast_entry_multiseed.py \
  --dataset "$dataset" --variant-name "$variant_name" \
  --split validation --seeds "$seeds_csv"
echo "[$(date --iso-8601=seconds)] LAION Fast validation complete"
