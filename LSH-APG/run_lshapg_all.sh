#!/usr/bin/env bash
# run_lshapg_all.sh
# 全量 5 数据集 × Recall@100 + Recall@1，num_runs=10，串行执行
# 先跑全部 Recall@100，再跑全部 Recall@1

set -uo pipefail

LSHDIR=/mnt/new/New/ACSG/LSH-APG/cppCode/LSH-APG
BIN=$LSHDIR/lgo
IDX=$LSHDIR/indexes
R=/mnt/new/New/ACSG/benches/datasets
OUT_R100=/mnt/new/New/ACSG/test/lshapg_recall100_results
OUT_R1=/mnt/new/New/ACSG/test/lshapg_recall1_results
RUNS=10

mkdir -p "$OUT_R100" "$OUT_R1"
cd $LSHDIR

LOG=/mnt/new/New/ACSG/test/lshapg_all_runs.log
exec > >(tee -a "$LOG") 2>&1

echo "========================================================"
echo "  LSH-APG 全量测试  $(date '+%Y-%m-%d %H:%M:%S')"
echo "  num_runs=$RUNS"
echo "========================================================"

# ─────────────────────────────────────────────────────────────
# run_one <dsname> <base> <query> <gt> <recall_k> <out_dir>
# ─────────────────────────────────────────────────────────────
# run_one <dsname> <base> <query> <gt> <recall_k> <out_dir> [num_runs_override]
run_one() {
    local DSNAME=$1 BASE=$2 QUERY=$3 GT=$4 RECALL_K=$5 OUT=$6
    local NR=${7:-$RUNS}   # 可选第7参数覆盖 num_runs
    local RESULT="$OUT/${DSNAME}_result.json"
    local T_START=$(date +%s)

    echo ""
    echo "========================================================"
    echo "▶  $DSNAME  [Recall@${RECALL_K}, runs=${NR}]"
    echo "   BASE  : $BASE"
    echo "   QUERY : $QUERY"
    echo "   GT    : $GT"
    echo "   OUT   : $RESULT"
    echo "========================================================"

    $BIN \
        --dataset   "$DSNAME" \
        --base      "$BASE" \
        --query     "$QUERY" \
        --gt        "$GT" \
        --index_dir "$IDX/" \
        --result    "$RESULT" \
        --recall_k  "$RECALL_K" \
        --num_runs  "$NR" \
    && echo "✅ $DSNAME Recall@${RECALL_K} done  耗时:$(($(date +%s)-T_START))s" \
    || echo "❌ $DSNAME Recall@${RECALL_K} FAILED"
}

# ═════════════════════════════════════════════════════════════
# 第一阶段：Recall@100
# ═════════════════════════════════════════════════════════════
echo ""
echo "████████████████████████████████████████████████████████"
echo "  第一阶段：Recall@100"
echo "████████████████████████████████████████████████████████"

run_one gist1M         $R/GIST1M/gist_base.fvecs          $R/GIST1M/gist_query.fvecs              $R/GIST1M/gist_groundtruth.ivecs                100 $OUT_R100
run_one sift10M        $R/SIFT10M/sift_base.fvecs          $R/SIFT10M/sift_query.fvecs             $R/SIFT10M/sift_groundtruth.ivecs               100 $OUT_R100
run_one sift10M_skewed $R/SIFT10M/sift_base.fvecs          $R/SIFT10M/sift_skewed_query.fvecs      $R/SIFT10M/sift_skewed_groundtruth.ivecs         100 $OUT_R100
run_one deep10M        $R/DEEP10M/base.10M.fvecs            $R/DEEP10M/query.public.10K.fvecs       $R/DEEP10M/groundtruth_10M_subset.ivecs          100 $OUT_R100
run_one yandex_t2i     $R/YandexT2I/base.10M.fvecs          $R/YandexT2I/query.public.100K.fvecs    $R/YandexT2I/groundtruth_10M_subset.ivecs        100 $OUT_R100 3

echo ""
echo "✅ Recall@100 全部完成  $(date '+%Y-%m-%d %H:%M:%S')"

# ═════════════════════════════════════════════════════════════
# 第二阶段：Recall@1
# ═════════════════════════════════════════════════════════════
echo ""
echo "████████████████████████████████████████████████████████"
echo "  第二阶段：Recall@1"
echo "████████████████████████████████████████████████████████"

run_one gist1M         $R/GIST1M/gist_base.fvecs          $R/GIST1M/gist_query.fvecs              $R/GIST1M/gist_groundtruth.ivecs                1 $OUT_R1
run_one sift10M        $R/SIFT10M/sift_base.fvecs          $R/SIFT10M/sift_query.fvecs             $R/SIFT10M/sift_groundtruth.ivecs               1 $OUT_R1
run_one sift10M_skewed $R/SIFT10M/sift_base.fvecs          $R/SIFT10M/sift_skewed_query.fvecs      $R/SIFT10M/sift_skewed_groundtruth.ivecs         1 $OUT_R1
run_one deep10M        $R/DEEP10M/base.10M.fvecs            $R/DEEP10M/query.public.10K.fvecs       $R/DEEP10M/groundtruth_10M_subset.ivecs          1 $OUT_R1
run_one yandex_t2i     $R/YandexT2I/base.10M.fvecs          $R/YandexT2I/query.public.100K.fvecs    $R/YandexT2I/groundtruth_10M_subset.ivecs        1 $OUT_R1 3

echo ""
echo "████████████████████████████████████████████████████████"
echo "  🎉 全部完成！  $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Recall@100 结果: $OUT_R100"
echo "  Recall@1   结果: $OUT_R1"
echo "████████████████████████████████████████████████████████"
