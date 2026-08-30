#!/usr/bin/env bash
# run_ssg_recall1.sh — 全量 5 个数据集 × Recall@1，num_runs=10

set -uo pipefail
cd /mnt/new/New/ACSG

BENCH=./build/benches/bench_ssg
OUT=./test/ssg_recall1_results
SSG_IDX=./ssg_index
DRL=./drl
RUNS=10
RECALL_K=1

run_one() {
    local DS=$1 SSG=$2 HUB_DIR=$3
    echo ""
    echo "========================================================"
    echo "▶  Dataset: $DS  [Recall@${RECALL_K}, runs=${RUNS}]"
    echo "========================================================"
    $BENCH \
        --dataset     "$DS" \
        --ssg_file    "$SSG" \
        --fn_result   "$OUT/${DS}_result.json" \
        --transformed_hubs "$DRL/$HUB_DIR/transformed_hubs.bin" \
        --transformed_ids  "$DRL/$HUB_DIR/transformed_hub_ids.bin" \
        --num_runs    "$RUNS" \
        --recall_k    "$RECALL_K" \
    && echo "✅ $DS done" \
    || echo "❌ $DS FAILED"
}

# sift10M_skewed 与 sift10M base 相同，复用 sift10M.ssg
run_one gist1M         $SSG_IDX/gist1M.ssg     gist1M_ssg_results
run_one sift10M        $SSG_IDX/sift10M.ssg    sift10M_ssg_results
run_one sift10M_skewed $SSG_IDX/sift10M.ssg    sift10M_skewed_ssg_results
run_one deep10M        $SSG_IDX/deep10M.ssg    deep10M_ssg_results
run_one yandex_t2i     $SSG_IDX/yandex_t2i.ssg yandex_t2i_ssg_results

echo ""
echo "🎉 全部完成！结果在 $OUT/"
