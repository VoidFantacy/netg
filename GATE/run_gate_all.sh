#!/bin/bash
# =============================================================================
# GATE 全量重跑脚本（修复版）
# 覆盖所有 5 个数据集：deep10M / sift10M / sift10M_skewed / yandex_t2i / gist1M
#
# 修复内容：
#   1. 样本生成改为原作者方法（每 Hub 为入口跑 NSG 搜索 → 真实跳数）
#   2. 训练按路由准确率保存最优模型（而非 loss）
#   3. 超参：batch_size=512, lr=1e-4, dropout=0.1, epochs=50
#
# 用法：
#   nohup bash run_gate_all.sh > gate_run_all.log 2>&1 &
# =============================================================================

set -e
cd /mnt/new/New/ACSG/GATE
chmod +x run_gate_generic.sh

DATASET_ROOT="/mnt/new/New/ACSG/benches/datasets"
LOG_DIR="/mnt/new/New/ACSG/GATE/logs"
mkdir -p "$LOG_DIR"

# ── 数据集配置 ──────────────────────────────────────────────────────────────
declare -A BASE_FILES=(
    [deep10M]="$DATASET_ROOT/DEEP10M/base.10M.fvecs"
    [sift10M]="$DATASET_ROOT/SIFT10M/sift_base.fvecs"
    [sift10M_skewed]="$DATASET_ROOT/SIFT10M/sift_base.fvecs"
    [yandex_t2i]="$DATASET_ROOT/YandexT2I/base.10M.fvecs"
    [gist1M]="$DATASET_ROOT/GIST1M/gist_base.fvecs"
)
declare -A QUERY_FILES=(
    [deep10M]="$DATASET_ROOT/DEEP10M/query.public.10K.fvecs"
    [sift10M]="$DATASET_ROOT/SIFT10M/sift_query.fvecs"
    [sift10M_skewed]="$DATASET_ROOT/SIFT10M/sift_skewed_query.fvecs"
    [yandex_t2i]="$DATASET_ROOT/YandexT2I/query.public.100K.fvecs"
    [gist1M]="$DATASET_ROOT/GIST1M/gist_query.fvecs"
)
declare -A GT_FILES=(
    [deep10M]="$DATASET_ROOT/DEEP10M/groundtruth_10M_subset.ivecs"
    [sift10M]="$DATASET_ROOT/SIFT10M/sift_groundtruth.ivecs"
    [sift10M_skewed]="$DATASET_ROOT/SIFT10M/sift_skewed_groundtruth.ivecs"
    [yandex_t2i]="$DATASET_ROOT/YandexT2I/groundtruth_10M_subset.ivecs"
    [gist1M]="$DATASET_ROOT/GIST1M/gist_groundtruth.ivecs"
)
declare -A DIMS=(
    [deep10M]=96
    [sift10M]=128
    [sift10M_skewed]=128
    [yandex_t2i]=200
    [gist1M]=960
)

DATASETS=("deep10M" "sift10M" "sift10M_skewed" "yandex_t2i" "gist1M")

# ── 清理旧的脏数据（避免被跳过逻辑复用旧的错误结果）─────────────────────────
echo "========================================================"
echo "  [Cleanup] Removing stale samples / models / embeddings"
echo "========================================================"
for ds in "${DATASETS[@]}"; do
    OUT="/mnt/new/New/ACSG/GATE/output_${ds}"
    SAMPLE_DIR="${OUT}/train_samples_dir"
    MODELS_DIR="${OUT}/models"
    CFG="${OUT}/config.json"

    echo "  [$ds] Cleaning..."

    # 删除旧的 hub_embeddings（用旧超参/旧样本生成的）
    [ -f "${OUT}/hub_embeddings.bin" ]        && rm -v "${OUT}/hub_embeddings.bin"

    # 删除旧的训练样本（BFS 错误方法生成的）
    [ -f "${SAMPLE_DIR}/pos_sample.txt" ]     && rm -v "${SAMPLE_DIR}/pos_sample.txt"
    [ -f "${SAMPLE_DIR}/neg_sample.txt" ]     && rm -v "${SAMPLE_DIR}/neg_sample.txt"

    # 删除旧的 Graph2Vec CSV 缓存（避免 hub 变更后复用旧向量）
    [ -f "${OUT}/graph2vec_embedding.csv" ]   && rm -v "${OUT}/graph2vec_embedding.csv"

    # 删除旧模型
    find "$MODELS_DIR" -name "*.pth" 2>/dev/null | while read f; do rm -v "$f"; done

    # 保留 config.json（已手动对齐论文超参，不删除）
    # [ -f "$CFG" ]                           && rm -v "$CFG"

    mkdir -p "$SAMPLE_DIR" "$MODELS_DIR"
done
echo ""

# ── 逐数据集运行 ──────────────────────────────────────────────────────────
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
    echo "  🚀 Starting: $ds (dim=$DIM)"
    echo "  Base : $BASE"
    echo "  Query: $QUERY"
    echo "  GT   : $GT"
    echo "  Log  : $DS_LOG"
    echo "========================================================"

    # 检查必要文件是否存在
    if [ ! -f "$BASE" ]; then
        echo "  ❌ Base file not found: $BASE — Skipping."
        FAILED+=("$ds")
        continue
    fi
    if [ ! -f "$QUERY" ]; then
        echo "  ❌ Query file not found: $QUERY — Skipping."
        FAILED+=("$ds")
        continue
    fi

    GT_ARG=""
    [ -f "$GT" ] && GT_ARG="$GT"

    START_DS=$(date +%s)

    if stdbuf -oL bash run_gate_generic.sh "$ds" "$DIM" "$BASE" "$QUERY" "$GT_ARG" 2>&1 | tee "$DS_LOG"; then
        END_DS=$(date +%s)
        ELAPSED=$(( (END_DS - START_DS) / 60 ))
        echo "  ✅ $ds finished in ${ELAPSED} min"
        SUCCESS+=("$ds")
    else
        echo "  ❌ $ds FAILED. See $DS_LOG"
        FAILED+=("$ds")
    fi

    echo ""
done

# ── 汇总 ─────────────────────────────────────────────────────────────────
END_ALL=$(date +%s)
TOTAL=$(( (END_ALL - START_ALL) / 60 ))
echo "========================================================"
echo "  📊 All done.  Total time: ${TOTAL} min"
echo "  ✅ Success: ${SUCCESS[*]}"
echo "  ❌ Failed : ${FAILED[*]}"
echo "========================================================"
