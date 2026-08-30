#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
source .venv_cpu/bin/activate

dataset="yandex_t2i_official10M_ip_v1"
log_dir="logs/${dataset}"
eval_max_queries="${EVAL_MAX_QUERIES:-10000}"
eval_num_runs="${EVAL_NUM_RUNS:-3}"
eval_search_ls="${EVAL_SEARCH_LS:-64,128,200,400,800}"
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

run_stage prepare_data python benches/run/prepare_yandex_official10m_ip.py

run_stage build_nsg build/benches/bench_ACO \
  --alpha 1.4 --beta 2.2 --rho 0.15 --lambda 0.012 --rejection 10 --iterations 20 \
  --R 64 --L_build 100 --C 512 --dataset "$dataset" \
  --index_file "indices/${dataset}_index/acosp_nsg.json"

run_stage train_aco build/benches/bench_ACO_TEST \
  --index_file "indices/${dataset}_index/acosp_nsg.json" \
  --dataset "$dataset" --fn_result "acpg/${dataset}_index/acsg_aco_results.json" \
  --trials 1 --num_aco 1 --acpg_file "acpg/${dataset}_index/acpg_nsg.json" \
  --alpha 0.01 --beta 10.0 --rho 0.15 --lambda 0.4 --rejection 20 \
  --iterations 50 --L 400

run_stage dpc build/benches/kph_dpc_clustering \
  --acpg_file "acpg/${dataset}_index/acpg_nsg.json" \
  --output_file "dpc/${dataset}_results/dpc_hierarchical_results.json" \
  --num_threads 8

run_stage labels build/benches/bench_generate_labels \
  --dataset "$dataset" --index_file "acpg/${dataset}_index/acpg_nsg.json" \
  --cluster_file "dpc/${dataset}_results/dpc_hierarchical_results.json" \
  --output_file "drl/${dataset}_results/topo_aware_labels.ivecs" \
  --limit 30000 --query_type drl_train --L 300

run_stage router python benches/run/train_router.py --datasets "$dataset"

common_test=(
  build/benches/test --dataset "$dataset"
  --acpg_file "acpg/${dataset}_index/acpg_nsg.json"
  --cluster_pca "dpc/${dataset}_results/dpc_hierarchical_results.json"
  --transformed_hubs "drl/${dataset}_results/transformed_hubs.bin"
  --transformed_ids "drl/${dataset}_results/transformed_hub_ids.bin"
  --raw_hubs "drl/${dataset}_results/raw_hubs.bin"
  --test_scope all --num_runs "$eval_num_runs" --max_queries "$eval_max_queries"
)

run_stage recall1 "${common_test[@]}" --top_k 1 \
  --search_Ls "$eval_search_ls" \
  --fn_result "test/${dataset}_results/${dataset}_recall1.json"
run_stage recall100 "${common_test[@]}" --top_k 100 \
  --search_Ls "$eval_search_ls" \
  --fn_result "test/${dataset}_results/${dataset}_recall100.json"

run_stage per_query_r10 build/benches/bench_per_query_recall \
  --dataset "$dataset" --acpg_file "acpg/${dataset}_index/acpg_nsg.json" \
  --output_file "per_query_recall_results_r10/${dataset}/${dataset}_per_query_recall_r10.json" \
  --transformed_hubs "drl/${dataset}_results/transformed_hubs.bin" \
  --transformed_ids "drl/${dataset}_results/transformed_hub_ids.bin" \
  --raw_hubs "drl/${dataset}_results/raw_hubs.bin" \
  --search_L "$eval_search_ls" --top_k 10 --max_queries "$eval_max_queries"

run_stage compare python benches/run/compare_yandex_protocols.py \
  --old-main test/yandex_t2i_results/yandex_t2i_final_report.json \
  --old-tail per_query_recall_results_r10/yandex_t2i_per_query_recall_r10.json \
  --new-r1 "test/${dataset}_results/${dataset}_recall1.json" \
  --new-r100 "test/${dataset}_results/${dataset}_recall100.json" \
  --new-tail "per_query_recall_results_r10/${dataset}/${dataset}_per_query_recall_r10.json" \
  --output "test/${dataset}_results/protocol_comparison.json"
