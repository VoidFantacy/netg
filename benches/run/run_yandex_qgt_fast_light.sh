#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

dataset="yandex_t2i_official10M_ip_v1"
seed="${SEED:-20260829}"
target_hubs="${TARGET_HUBS:-821}"
max_queries="${MAX_QUERIES:-10000}"
num_runs="${NUM_RUNS:-1}"
force="${FORCE:-0}"
out_dir="fast_entry_variants/${dataset}_seed${seed}"

echo "Yandex QGT-only light validation: seed=${seed}, hubs=${target_hubs}, queries=${max_queries}"
echo "Estimated wall time on the current host: about 8 minutes."
echo "Existing outputs are reused; set FORCE=1 to rerun."
mkdir -p "$out_dir"

if [[ "$force" == "1" ]] || ! jq -e --argjson seed "$seed" --argjson hubs "$target_hubs" \
    '.qgt_only == true and .target_hubs == $hubs and .variants.qgt_cover.seed == $seed' \
    "$out_dir/manifest.json" >/dev/null 2>&1; then
  OPENBLAS_NUM_THREADS=16 OMP_NUM_THREADS=16 \
    /usr/bin/time -v -o "$out_dir/build.time.txt" \
    .venv_cpu/bin/python benches/run/build_fast_entry_variants.py \
    --dataset "$dataset" --qgt-only --target-hubs "$target_hubs" \
    --seed "$seed" --output-dir "$PWD/$out_dir" \
    2>&1 | tee "$out_dir/build.log"
fi

json_matches() {
  local path="$1" top_k="$2"
  [[ -f "$path" ]] || return 1
  jq -e --arg ds "$dataset" --argjson k "$top_k" --argjson q "$max_queries" \
    --argjson runs "$num_runs" \
    '.dataset == $ds and .top_k == $k and .num_queries == $q and .num_runs == $runs' \
    "$path" >/dev/null
}

common=(
  build/benches/test --dataset "$dataset"
  --acpg_file "indices/${dataset}_index/acosp_nsg.json"
  --raw_hubs "$out_dir/qgt_cover_hubs.bin"
  --transformed_hubs "$out_dir/qgt_gt_basin_prototype_hubs.bin"
  --transformed_ids "$out_dir/qgt_cover_hub_ids.bin"
  --test_scope routing --num_runs "$num_runs" --max_queries "$max_queries"
)
if [[ "$force" == "1" ]] || ! json_matches "$out_dir/eval_r1_light.json" 1; then
  /usr/bin/time -v -o "$out_dir/eval_r1_light.time.txt" \
    "${common[@]}" --top_k 1 --search_Ls 64,128,200,400,800 \
    --fn_result "$out_dir/eval_r1_light.json" \
    2>&1 | tee "$out_dir/eval_r1_light.log"
fi
if [[ "$force" == "1" ]] || ! json_matches "$out_dir/eval_r100_light.json" 100; then
  /usr/bin/time -v -o "$out_dir/eval_r100_light.time.txt" \
    "${common[@]}" --top_k 100 --search_Ls 100,128,200,400,800 \
    --fn_result "$out_dir/eval_r100_light.json" \
    2>&1 | tee "$out_dir/eval_r100_light.log"
fi
if [[ "$force" == "1" || ! -f "$out_dir/per_query_r10_light.json" ]]; then
  /usr/bin/time -v -o "$out_dir/per_query_r10_light.time.txt" \
    build/benches/bench_per_query_recall --dataset "$dataset" \
    --acpg_file "indices/${dataset}_index/acosp_nsg.json" \
    --output_file "$out_dir/per_query_r10_light.json" \
    --transformed_hubs "$out_dir/qgt_gt_basin_prototype_hubs.bin" \
    --transformed_ids "$out_dir/qgt_cover_hub_ids.bin" \
    --raw_hubs "$out_dir/qgt_cover_hubs.bin" \
    --search_L 64,128,200,400,800 --top_k 10 --max_queries "$max_queries" \
    2>&1 | tee "$out_dir/per_query_r10_light.log"
fi

.venv_cpu/bin/python benches/run/summarize_fast_entry_light.py --fast-dir "$out_dir"
echo "Done. See $out_dir/evaluation_summary.json"
