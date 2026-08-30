#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

result_dir="${RESULT_DIR:-fast_entry_benchmark_results}"
seeds_csv="${SEEDS:-20260828,20260829,20260830}"
internal_runs="${NUM_RUNS:-3}"
max_queries="${MAX_QUERIES:-10000}"
force="${FORCE:-0}"
IFS=',' read -r -a seeds <<< "$seeds_csv"

if [[ "$internal_runs" -lt 3 || "$max_queries" != "10000" ]]; then
  echo "Protocol requires NUM_RUNS>=3 and MAX_QUERIES=10000." >&2
  exit 2
fi

mkdir -p "$result_dir/raw"
echo "Two-dataset benchmark: WebVid + Yandex, runs=${internal_runs}, seeds=${seeds_csv}"
echo "Estimated wall time on the current host: about 90-120 minutes."
echo "Outputs are resumable under $result_dir; set FORCE=1 to rerun completed stages."

run_stage() {
  local name="$1" log="$2" time_file="$3"
  shift 3
  echo "[$(date --iso-8601=seconds)] START $name"
  /usr/bin/time -v -o "$time_file" "$@" >"$log" 2>&1
  echo "[$(date --iso-8601=seconds)] DONE  $name"
}

json_matches() {
  local path="$1" dataset="$2" top_k="$3"
  [[ -f "$path" ]] || return 1
  jq -e --arg ds "$dataset" --argjson k "$top_k" --argjson q "$max_queries" \
    --argjson runs "$internal_runs" \
    '.dataset==$ds and .split=="held-out-test" and .top_k==$k and
     .num_queries==$q and .num_runs==$runs and (.results|length)==3' \
    "$path" >/dev/null
}

tail_matches() {
  local path="$1" dataset="$2"
  [[ -f "$path" ]] || return 1
  jq -e --arg ds "$dataset" \
    '.dataset==$ds and .split=="held-out-test" and .top_k==10 and
     .num_queries==10000 and
     ([.methods[].search_results[].per_query_recalls_aligned|length]|all(.==10000))' \
    "$path" >/dev/null
}

for dataset in webvid2_5m_light_v1 yandex_t2i_official10M_ip_v1; do
  case "$dataset" in
    webvid2_5m_light_v1)
      target_hubs=815
      search_l_r1="64,128,200,400"
      search_l_r100="100,128,200,400"
      search_l_tail="64,128,200,400"
      ;;
    yandex_t2i_official10M_ip_v1)
      target_hubs=821
      search_l_r1="64,128,200,400,800"
      search_l_r100="100,128,200,400,800"
      search_l_tail="64,128,200,400,800"
      ;;
  esac
  raw_dir="$result_dir/raw/$dataset"
  mkdir -p "$raw_dir"
  index="indices/${dataset}_index/acosp_nsg.json"
  dpc="dpc/${dataset}_results/dpc_hierarchical_results.json"
  formal_raw="drl/${dataset}_results/raw_hubs.bin"
  formal_transformed="drl/${dataset}_results/transformed_hubs.bin"
  formal_ids="drl/${dataset}_results/transformed_hub_ids.bin"
  for required in "$index" "$dpc" "$formal_raw" "$formal_transformed" "$formal_ids"; do
    [[ -f "$required" ]] || { echo "Missing required artifact: $required" >&2; exit 2; }
  done

  formal_common=(
    build/benches/test --dataset "$dataset" --acpg_file "$index"
    --cluster_pca "$dpc" --raw_hubs "$formal_raw"
    --transformed_hubs "$formal_transformed" --transformed_ids "$formal_ids"
    --test_scope comparison --num_runs "$internal_runs" --max_queries "$max_queries"
  )
  if [[ "$force" == "1" ]] || ! json_matches "$raw_dir/formal_r1.json" "$dataset" 1; then
    run_stage "$dataset formal Recall@1" "$raw_dir/formal_r1.log" "$raw_dir/formal_r1.time.txt" \
      "${formal_common[@]}" --top_k 1 --search_Ls "$search_l_r1" \
      --fn_result "$raw_dir/formal_r1.json"
  fi
  if [[ "$force" == "1" ]] || ! json_matches "$raw_dir/formal_r100.json" "$dataset" 100; then
    run_stage "$dataset formal Recall@100" "$raw_dir/formal_r100.log" "$raw_dir/formal_r100.time.txt" \
      "${formal_common[@]}" --top_k 100 --search_Ls "$search_l_r100" \
      --fn_result "$raw_dir/formal_r100.json"
  fi
  if [[ "$force" == "1" ]] || ! tail_matches "$raw_dir/formal_tail_r10.json" "$dataset"; then
    run_stage "$dataset formal tail" "$raw_dir/formal_tail_r10.log" "$raw_dir/formal_tail_r10.time.txt" \
      build/benches/bench_per_query_recall --dataset "$dataset" --acpg_file "$index" \
      --output_file "$raw_dir/formal_tail_r10.json" --raw_hubs "$formal_raw" \
      --transformed_hubs "$formal_transformed" --transformed_ids "$formal_ids" \
      --search_L "$search_l_tail" --top_k 10 --max_queries "$max_queries"
  fi

  for seed in "${seeds[@]}"; do
    variant_dir="fast_entry_variants/${dataset}_seed${seed}"
    mkdir -p "$variant_dir"
    if [[ "$force" == "1" ]] || ! jq -e --argjson seed "$seed" --argjson hubs "$target_hubs" \
        '.qgt_only==true and .target_hubs==$hubs and .variants.qgt_cover.seed==$seed' \
        "$variant_dir/manifest.json" >/dev/null 2>&1; then
      run_stage "$dataset build seed $seed" "$raw_dir/build_seed${seed}.log" "$raw_dir/build_seed${seed}.time.txt" \
        env OPENBLAS_NUM_THREADS=16 OMP_NUM_THREADS=16 \
        .venv_cpu/bin/python benches/run/build_fast_entry_variants.py \
        --dataset "$dataset" --qgt-only --target-hubs "$target_hubs" \
        --seed "$seed" --output-dir "$PWD/$variant_dir"
    fi
    fast_common=(
      build/benches/test --dataset "$dataset" --acpg_file "$index"
      --raw_hubs "$variant_dir/qgt_cover_hubs.bin"
      --transformed_hubs "$variant_dir/qgt_gt_basin_prototype_hubs.bin"
      --transformed_ids "$variant_dir/qgt_cover_hub_ids.bin"
      --test_scope comparison --num_runs "$internal_runs" --max_queries "$max_queries"
    )
    if [[ "$force" == "1" ]] || ! json_matches "$raw_dir/fast_seed${seed}_r1.json" "$dataset" 1; then
      run_stage "$dataset fast seed $seed Recall@1" "$raw_dir/fast_seed${seed}_r1.log" "$raw_dir/fast_seed${seed}_r1.time.txt" \
        "${fast_common[@]}" --top_k 1 --search_Ls "$search_l_r1" \
        --fn_result "$raw_dir/fast_seed${seed}_r1.json"
    fi
    if [[ "$force" == "1" ]] || ! json_matches "$raw_dir/fast_seed${seed}_r100.json" "$dataset" 100; then
      run_stage "$dataset fast seed $seed Recall@100" "$raw_dir/fast_seed${seed}_r100.log" "$raw_dir/fast_seed${seed}_r100.time.txt" \
        "${fast_common[@]}" --top_k 100 --search_Ls "$search_l_r100" \
        --fn_result "$raw_dir/fast_seed${seed}_r100.json"
    fi
    if [[ "$force" == "1" ]] || ! tail_matches "$raw_dir/fast_seed${seed}_tail_r10.json" "$dataset"; then
      run_stage "$dataset fast seed $seed tail" "$raw_dir/fast_seed${seed}_tail_r10.log" "$raw_dir/fast_seed${seed}_tail_r10.time.txt" \
        build/benches/bench_per_query_recall --dataset "$dataset" --acpg_file "$index" \
        --output_file "$raw_dir/fast_seed${seed}_tail_r10.json" \
        --raw_hubs "$variant_dir/qgt_cover_hubs.bin" \
        --transformed_hubs "$variant_dir/qgt_gt_basin_prototype_hubs.bin" \
        --transformed_ids "$variant_dir/qgt_cover_hub_ids.bin" \
        --search_L "$search_l_tail" --top_k 10 --max_queries "$max_queries"
    fi
  done
done

.venv_cpu/bin/python benches/run/summarize_two_dataset_fast_benchmark.py \
  --result-dir "$result_dir" --seeds "$seeds_csv" --internal-runs "$internal_runs"
echo "Final report: $result_dir/benchmark_summary.md"
