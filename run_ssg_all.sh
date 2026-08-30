#!/usr/bin/env bash
# run_ssg_all.sh
# 全量 5 数据集 × Recall@100 + Recall@1，num_runs=10，串行执行
# 先跑全部 Recall@100，再跑全部 Recall@1

set -uo pipefail
cd /mnt/new/New/ACSG

BENCH=./build/benches/bench_ssg
OUT_R100=./test/ssg_final_results
OUT_R1=./test/ssg_recall1_results
SSG_IDX=./ssg_index
DRL=./drl
RUNS=10

mkdir -p "$OUT_R100" "$OUT_R1"

LOG="./test/ssg_all_runs.log"
exec > >(tee -a "$LOG") 2>&1

echo "========================================================"
echo "  SSG 全量测试  $(date '+%Y-%m-%d %H:%M:%S')"
echo "  num_runs=$RUNS"
echo "========================================================"

# ─────────────────────────────────────────────────────────────
# 通用执行函数
#   run_one <dataset> <ssg_file> <hub_dir> <recall_k> <out_dir>
# ─────────────────────────────────────────────────────────────
run_one() {
    local DS=$1 SSG=$2 HUB_DIR=$3 RECALL_K=$4 OUT=$5
    local RESULT="$OUT/${DS}_result.json"

    echo ""
    echo "========================================================"
    echo "▶  $DS  [Recall@${RECALL_K}, runs=${RUNS}]"
    echo "   SSG  : $SSG"
    echo "   HUBS : $DRL/$HUB_DIR/transformed_hubs.bin"
    echo "   OUT  : $RESULT"
    echo "========================================================"

    $BENCH \
        --dataset          "$DS" \
        --ssg_file         "$SSG" \
        --fn_result        "$RESULT" \
        --transformed_hubs "$DRL/$HUB_DIR/transformed_hubs.bin" \
        --transformed_ids  "$DRL/$HUB_DIR/transformed_hub_ids.bin" \
        --num_runs         "$RUNS" \
        --recall_k         "$RECALL_K" \
    && echo "✅ $DS Recall@${RECALL_K} done" \
    || echo "❌ $DS Recall@${RECALL_K} FAILED"
}

# ═════════════════════════════════════════════════════════════
# 第一阶段：Recall@100
# ═════════════════════════════════════════════════════════════
echo ""
echo "████████████████████████████████████████████████████████"
echo "  第一阶段：Recall@100"
echo "████████████████████████████████████████████████████████"

run_one gist1M         $SSG_IDX/gist1M.ssg      gist1M_ssg_results         100 $OUT_R100
run_one sift10M        $SSG_IDX/sift10M.ssg     sift10M_ssg_results        100 $OUT_R100
run_one sift10M_skewed $SSG_IDX/sift10M.ssg     sift10M_skewed_ssg_results 100 $OUT_R100
run_one deep10M        $SSG_IDX/deep10M.ssg     deep10M_ssg_results        100 $OUT_R100
run_one yandex_t2i     $SSG_IDX/yandex_t2i.ssg  yandex_t2i_ssg_results     100 $OUT_R100

echo ""
echo "✅ Recall@100 全部完成  $(date '+%Y-%m-%d %H:%M:%S')"

# ═════════════════════════════════════════════════════════════
# 第二阶段：Recall@1
# ═════════════════════════════════════════════════════════════
echo ""
echo "████████████████████████████████████████████████████████"
echo "  第二阶段：Recall@1"
echo "████████████████████████████████████████████████████████"

run_one gist1M         $SSG_IDX/gist1M.ssg      gist1M_ssg_results         1 $OUT_R1
run_one sift10M        $SSG_IDX/sift10M.ssg     sift10M_ssg_results        1 $OUT_R1
run_one sift10M_skewed $SSG_IDX/sift10M.ssg     sift10M_skewed_ssg_results 1 $OUT_R1
run_one deep10M        $SSG_IDX/deep10M.ssg     deep10M_ssg_results        1 $OUT_R1
run_one yandex_t2i     $SSG_IDX/yandex_t2i.ssg  yandex_t2i_ssg_results     1 $OUT_R1

echo ""
echo "████████████████████████████████████████████████████████"
echo "  🎉 全部完成！  $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Recall@100 结果: $OUT_R100"
echo "  Recall@1   结果: $OUT_R1"
echo "████████████████████████████████████████████████████████"
