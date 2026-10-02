#!/usr/bin/env bash
# LSH-APG Recall@100 全量测试，使用与 NSG/SSG bench 相同的标准查询集
set -uo pipefail

LSHDIR=/mnt/new/New/ACSG/LSH-APG/cppCode/LSH-APG
BIN=$LSHDIR/lgo
IDX=$LSHDIR/indexes
DS_ROOT=/mnt/new/New/ACSG/benches/datasets
OUT=/mnt/new/New/ACSG/test/lshapg_recall100_results
RUNS=10

mkdir -p $OUT
cd $LSHDIR

run_one() {
    local DSNAME=$1 BASE=$2 QUERY=$3 GT=$4
    echo "" && echo "======== $DSNAME ========"
    $BIN \
        --dataset   "$DSNAME" \
        --base      "$BASE" \
        --query     "$QUERY" \
        --gt        "$GT" \
        --index_dir "$IDX/" \
        --result    "$OUT/${DSNAME}_result.json" \
        --recall_k  100 \
        --num_runs  $RUNS \
    && echo "✅ $DSNAME done" || echo "❌ $DSNAME FAILED"
}

R=/mnt/new/New/ACSG/benches/datasets

# 与 settings.json 中的 query_path / gt_path 完全对齐
run_one gist1M         $R/GIST1M/gist_base.fvecs        $R/GIST1M/gist_query.fvecs              $R/GIST1M/gist_groundtruth.ivecs
run_one sift10M        $R/SIFT10M/sift_base.fvecs        $R/SIFT10M/sift_query.fvecs             $R/SIFT10M/sift_groundtruth.ivecs
run_one sift10M_skewed $R/SIFT10M/sift_base.fvecs        $R/SIFT10M/sift_skewed_query.fvecs      $R/SIFT10M/sift_skewed_groundtruth.ivecs
run_one deep10M        $R/DEEP10M/base.10M.fvecs          $R/DEEP10M/query.public.10K.fvecs       $R/DEEP10M/groundtruth_10M_subset.ivecs
run_one yandex_t2i     $R/YandexT2I/base.10M.fvecs        $R/YandexT2I/query.public.100K.fvecs    $R/YandexT2I/groundtruth_10M_subset.ivecs

echo "" && echo "🎉 全部完成！结果在 $OUT/"
