#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
source .venv_cpu/bin/activate

dataset="webvid2_5m_light_v1"
log_dir="logs/${dataset}"
start_stage="${START_STAGE:-0}"
end_stage="${END_STAGE:-7}"
eval_max_queries="${EVAL_MAX_QUERIES:-10000}"
eval_num_runs="${EVAL_NUM_RUNS:-1}"
eval_search_ls="${EVAL_SEARCH_LS:-64,128,200,400}"

mkdir -p "$log_dir" "indices/${dataset}_index" "acpg/${dataset}_index" \
  "dpc/${dataset}_results" "drl/${dataset}_results" "test/${dataset}_results" \
  "per_query_recall_results_r10/${dataset}"

run_stage() {
  local stage="$1"
  shift
  echo "[$(date --iso-8601=seconds)] START ${stage}"
  /usr/bin/time -v -o "${log_dir}/${stage}.time.txt" "$@" \
    2>&1 | tee "${log_dir}/${stage}.log"
  echo "[$(date --iso-8601=seconds)] DONE ${stage}"
}

if (( start_stage <= 0 && end_stage >= 0 )); then
  run_stage prepare_data python benches/run/prepare_webvid2_5m_light.py
fi

if (( start_stage <= 1 && end_stage >= 1 )); then
  run_stage build_nsg build/benches/bench_ACO \
    --alpha 1.4 --beta 2.2 --rho 0.15 --lambda 0.012 --rejection 10 --iterations 20 \
    --R 64 --L_build 100 --C 512 --dataset "$dataset" \
    --index_file "indices/${dataset}_index/acosp_nsg.json"
fi

if (( start_stage <= 2 && end_stage >= 2 )); then
  run_stage train_aco build/benches/bench_ACO_TEST \
    --index_file "indices/${dataset}_index/acosp_nsg.json" \
    --dataset "$dataset" --fn_result "acpg/${dataset}_index/acsg_aco_results.json" \
    --trials 1 --num_aco 1 --acpg_file "acpg/${dataset}_index/acpg_nsg.json" \
    --alpha 0.01 --beta 10.0 --rho 0.15 --lambda 0.4 --rejection 20 \
    --iterations 50 --L 400
  python benches/run/validate_training_stage.py aco \
    --log "${log_dir}/train_aco.log" --expected-iterations 50 \
    --require-first-nonzero | tee "${log_dir}/train_aco.validation.json"
fi

# Gate: measure whether the frozen graph has a meaningful held-out tail before
# spending time on DPC/labels/Router.  Resume later with START_STAGE=4.
if (( start_stage <= 3 && end_stage >= 3 )); then
  run_stage baseline_tail build/benches/bench_per_query_recall \
    --dataset "$dataset" --acpg_file "acpg/${dataset}_index/acpg_nsg.json" \
    --output_file "per_query_recall_results_r10/${dataset}/${dataset}_baseline_light.json" \
    --search_L "$eval_search_ls" --top_k 10 --max_queries "$eval_max_queries"
fi

if (( start_stage <= 4 && end_stage >= 4 )); then
  run_stage dpc build/benches/kph_dpc_clustering \
    --acpg_file "acpg/${dataset}_index/acpg_nsg.json" \
    --output_file "dpc/${dataset}_results/dpc_hierarchical_results.json" \
    --num_threads 8
  python benches/run/validate_training_stage.py dpc \
    --path "dpc/${dataset}_results/dpc_hierarchical_results.json" \
    --base-count 2505000 | tee "${log_dir}/dpc.validation.json"
fi

if (( start_stage <= 5 && end_stage >= 5 )); then
  run_stage labels build/benches/bench_generate_labels \
    --dataset "$dataset" --index_file "acpg/${dataset}_index/acpg_nsg.json" \
    --cluster_file "dpc/${dataset}_results/dpc_hierarchical_results.json" \
    --output_file "drl/${dataset}_results/topo_aware_labels.ivecs" \
    --limit 30000 --query_type drl_train --L 300
  hub_count="$(jq '[.top_centers[], .bottom_centers[]] | unique | length' \
    "dpc/${dataset}_results/dpc_hierarchical_results.json")"
  python benches/run/validate_training_stage.py labels \
    --path "drl/${dataset}_results/topo_aware_labels.ivecs" \
    --expected-rows 30000 --query-count 30000 --hub-count "$hub_count" \
    --min-valid-ratio 0.8 | tee "${log_dir}/labels.validation.json"
fi

if (( start_stage <= 6 && end_stage >= 6 )); then
  run_stage router python benches/run/train_router.py --datasets "$dataset"
  python benches/run/validate_training_stage.py router \
    --hub-ids "drl/${dataset}_results/transformed_hub_ids.bin" \
    --raw-hubs "drl/${dataset}_results/raw_hubs.bin" \
    --transformed-hubs "drl/${dataset}_results/transformed_hubs.bin" \
    --dim 512 | tee "${log_dir}/router.validation.json"
fi

common_test=(
  build/benches/test --dataset "$dataset"
  --acpg_file "acpg/${dataset}_index/acpg_nsg.json"
  --cluster_pca "dpc/${dataset}_results/dpc_hierarchical_results.json"
  --transformed_hubs "drl/${dataset}_results/transformed_hubs.bin"
  --transformed_ids "drl/${dataset}_results/transformed_hub_ids.bin"
  --raw_hubs "drl/${dataset}_results/raw_hubs.bin"
  --test_scope all --num_runs "$eval_num_runs" --max_queries "$eval_max_queries"
)

if (( start_stage <= 7 && end_stage >= 7 )); then
  run_stage eval_r1 "${common_test[@]}" --top_k 1 \
    --search_Ls "$eval_search_ls" \
    --fn_result "test/${dataset}_results/${dataset}_recall1_light.json"
  run_stage eval_r100 "${common_test[@]}" --top_k 100 \
    --search_Ls "100,128,200,400" \
    --fn_result "test/${dataset}_results/${dataset}_recall100_light.json"
  run_stage per_query_r10 build/benches/bench_per_query_recall \
    --dataset "$dataset" --acpg_file "acpg/${dataset}_index/acpg_nsg.json" \
    --output_file "per_query_recall_results_r10/${dataset}/${dataset}_per_query_recall_r10_light.json" \
    --transformed_hubs "drl/${dataset}_results/transformed_hubs.bin" \
    --transformed_ids "drl/${dataset}_results/transformed_hub_ids.bin" \
    --raw_hubs "drl/${dataset}_results/raw_hubs.bin" \
    --search_L "$eval_search_ls" --top_k 10 --max_queries "$eval_max_queries"
fi
