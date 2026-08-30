#!/bin/bash
# =============================================================================
# GATE 剩余数据集补跑脚本
# 跳过已完成：deep10M、sift10M
# 补跑：sift10M_skewed、yandex_t2i、gist1M
#
# 用法：
#   nohup bash run_gate_remaining.sh > gate_remaining.log 2>&1 &
# =============================================================================

set -e
cd /mnt/new/New/ACSG/GATE
chmod +x run_gate_generic.sh

DATASET_ROOT="/mnt/new/New/ACSG/benches/datasets"
LOG_DIR="/mnt/new/New/ACSG/GATE/logs"
mkdir -p "$LOG_DIR"

# ── 数据集配置（只剩余 3 个）────────────────────────────────────────────────
declare -A BASE_FILES=(
    [sift10M_skewed]="$DATASET_ROOT/SIFT10M/sift_base.fvecs"
    [yandex_t2i]="$DATASET_ROOT/YandexT2I/base.10M.fvecs"
    [gist1M]="$DATASET_ROOT/GIST1M/gist_base.fvecs"
)
declare -A QUERY_FILES=(
    [sift10M_skewed]="$DATASET_ROOT/SIFT10M/sift_skewed_query.fvecs"
    [yandex_t2i]="$DATASET_ROOT/YandexT2I/query.public.100K.fvecs"
    [gist1M]="$DATASET_ROOT/GIST1M/gist_query.fvecs"
)
declare -A GT_FILES=(
    [sift10M_skewed]="$DATASET_ROOT/SIFT10M/sift_skewed_groundtruth.ivecs"
    [yandex_t2i]="$DATASET_ROOT/YandexT2I/groundtruth_10M_subset.ivecs"
    [gist1M]="$DATASET_ROOT/GIST1M/gist_groundtruth.ivecs"
)
declare -A DIMS=(
    [sift10M_skewed]=128
    [yandex_t2i]=200
    [gist1M]=960
)

DATASETS=("sift10M_skewed" "yandex_t2i" "gist1M")

# ── 清理各数据集的旧脏数据（样本/模型/embedding）────────────────────────────
echo "========================================================"
echo "  [Cleanup] Removing stale data for remaining datasets"
echo "========================================================"
for ds in "${DATASETS[@]}"; do
    OUT="/mnt/new/New/ACSG/GATE/output_${ds}"
    SAMPLE_DIR="${OUT}/train_samples_dir"
    MODELS_DIR="${OUT}/models"

    echo "  [$ds] Cleaning..."
    [ -f "${OUT}/hub_embeddings.bin" ]      && rm -v "${OUT}/hub_embeddings.bin"
    [ -f "${SAMPLE_DIR}/pos_sample.txt" ]   && rm -v "${SAMPLE_DIR}/pos_sample.txt"
    [ -f "${SAMPLE_DIR}/neg_sample.txt" ]   && rm -v "${SAMPLE_DIR}/neg_sample.txt"
    [ -f "${OUT}/graph2vec_embedding.csv" ] && rm -v "${OUT}/graph2vec_embedding.csv"
    find "$MODELS_DIR" -name "*.pth" 2>/dev/null | while read f; do rm -v "$f"; done
    mkdir -p "$SAMPLE_DIR" "$MODELS_DIR"
done
echo ""

# ── 逐数据集运行 ─────────────────────────────────────────────────────────────
SUCCESS=()
FAILED=()
START_ALL=$(date +%s)

for ds in "${DATASETS[@]}"; do
    BASE="${BASE_FILES[$ds]}"
    QUERY="${QUERY_FILES[$ds]}"
    GT="${GT_FILES[$ds]}"
    DIM="${DIMS[$ds]}"
    DS_LOG="${LOG_DIR}/${ds}.log"

    echo "========================================================"
    echo "  Starting: $ds (dim=$DIM)"
    echo "  Base : $BASE"
    echo "  Query: $QUERY"
    echo "  GT   : $GT"
    echo "  Log  : $DS_LOG"
    echo "========================================================"

    if [ ! -f "$BASE" ]; then
        echo "  Base file not found: $BASE — Skipping."
        FAILED+=("$ds"); continue
    fi
    if [ ! -f "$QUERY" ]; then
        echo "  Query file not found: $QUERY — Skipping."
        FAILED+=("$ds"); continue
    fi

    GT_ARG=""
    [ -f "$GT" ] && GT_ARG="$GT"

    START_DS=$(date +%s)
    if stdbuf -oL bash run_gate_generic.sh "$ds" "$DIM" "$BASE" "$QUERY" "$GT_ARG" 2>&1 | tee "$DS_LOG"; then
        END_DS=$(date +%s)
        ELAPSED=$(( (END_DS - START_DS) / 60 ))
        echo "  $ds finished in ${ELAPSED} min"
        SUCCESS+=("$ds")
    else
        echo "  $ds FAILED. See $DS_LOG"
        FAILED+=("$ds")
    fi
    echo ""
done

# ── 汇总 ─────────────────────────────────────────────────────────────────────
END_ALL=$(date +%s)
TOTAL=$(( (END_ALL - START_ALL) / 60 ))
echo "========================================================"
echo "  All done. Total: ${TOTAL} min"
echo "  Success: ${SUCCESS[*]}"
echo "  Failed : ${FAILED[*]}"
echo "========================================================"
