#!/usr/bin/env bash
# run_ssg_recall1_final.sh
# SSG + SSG+NETG  Recall@1  全量5数据集，num_runs=10，串行执行
# 输出风格对齐 ssg_test_results.log

set -uo pipefail
cd /mnt/new/New/ACSG

BENCH=./build/benches/bench_ssg
OUT=./test/ssg_recall1_results
SSG_IDX=./ssg_index
DRL=./drl
RUNS=10
LOG=./ssg_test_results_recall_1.log

mkdir -p "$OUT"

exec > >(tee "$LOG") 2>&1

echo "====================================================="
echo " SSG 搜索测试 Recall@1（Baseline + NETG）: $(date)"
echo "====================================================="

run_one() {
    local DS=$1
    local SSG=$2
    local HUB_DIR=$3
    local T_START=$(date +%s)

    echo ""
    echo "########################################"
    echo "📦 [$DS] 开始测试"
    echo "########################################"
    echo "🔗 Router: $DRL/$HUB_DIR"
    echo ""

    $BENCH \
        --dataset          "$DS" \
        --ssg_file         "$SSG" \
        --fn_result        "$OUT/${DS}_result.json" \
        --transformed_hubs "$DRL/$HUB_DIR/transformed_hubs.bin" \
        --transformed_ids  "$DRL/$HUB_DIR/transformed_hub_ids.bin" \
        --num_runs         "$RUNS" \
        --recall_k         1

    local T_END=$(date +%s)
    echo "⏱️  [$DS] 耗时: $((T_END - T_START))s"
}

run_one gist1M         $SSG_IDX/gist1M.ssg      gist1M_ssg_results
run_one sift10M        $SSG_IDX/sift10M.ssg     sift10M_ssg_results
run_one sift10M_skewed $SSG_IDX/sift10M.ssg     sift10M_skewed_ssg_results
run_one deep10M        $SSG_IDX/deep10M.ssg     deep10M_ssg_results
run_one yandex_t2i     $SSG_IDX/yandex_t2i.ssg  yandex_t2i_ssg_results

echo ""
echo "====================================================="
echo " 🎉 全部完成！$(date)"
echo " 结果: $OUT"
echo " 日志: $LOG"
echo "====================================================="
