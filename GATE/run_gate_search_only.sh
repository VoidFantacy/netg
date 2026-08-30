#!/bin/bash
# =============================================================================
# GATE 纯搜索评测脚本（跳过训练，直接用已有 hub_embeddings.bin 测试）
# 覆盖：deep10M / sift10M / sift10M_skewed / yandex_t2i / gist1M
#
# 用法：
#   nohup bash run_gate_search_only.sh > run_from_step3_full_recall1.log 2>&1 &
# =============================================================================

set -e
cd /mnt/new/New/ACSG/GATE

DATASET_ROOT="/mnt/new/New/ACSG/benches/datasets"
BINARY="./build/tests/test_gate_search"

if [ ! -f "$BINARY" ]; then
    echo "❌ 找不到可执行文件: $BINARY，请先编译！"
    exit 1
fi

# ── 数据集配置 ────────────────────────────────────────────────────────────────
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

DATASETS=("deep10M" "sift10M" "sift10M_skewed" "yandex_t2i" "gist1M")

echo "========================================================"
echo "  GATE Search-Only Benchmark (Recall@1)"
echo "  Time: $(date)"
echo "  Binary: $BINARY"
echo "========================================================"

SUCCESS=()
FAILED=()
START_ALL=$(date +%s)

for ds in "${DATASETS[@]}"; do
    OUT="/mnt/new/New/ACSG/GATE/output_${ds}"
    BASE="${BASE_FILES[$ds]}"
    QUERY="${QUERY_FILES[$ds]}"
    GT="${GT_FILES[$ds]}"
    NSG="${OUT}/nsg.index"
    HUB_TXT="${OUT}/hubs.txt"
    EMB="${OUT}/hub_embeddings.bin"
    RESULT="${OUT}/${ds}_gate_result.ivecs"

    echo ""
    echo "========================================================"
    echo "  Dataset: $ds"
    echo "========================================================"

    # 检查必要文件
    SKIP=0
    for f in "$BASE" "$QUERY" "$NSG" "$HUB_TXT" "$EMB"; do
        if [ ! -f "$f" ]; then
            echo "  ❌ 缺少文件: $f — 跳过"
            SKIP=1; break
        fi
    done
    [ $SKIP -eq 1 ] && FAILED+=("$ds") && continue

    START_DS=$(date +%s)

    if [ -f "$GT" ]; then
        $BINARY "$BASE" "$QUERY" "$NSG" 100 1 "$HUB_TXT" "$EMB" "$RESULT" "$GT"
    else
        echo "  ⚠️  GT 文件不存在，跳过 Recall 计算"
        $BINARY "$BASE" "$QUERY" "$NSG" 100 1 "$HUB_TXT" "$EMB" "$RESULT"
    fi

    END_DS=$(date +%s)
    ELAPSED=$(( END_DS - START_DS ))
    echo "  ✅ $ds 完成，耗时 ${ELAPSED}s"
    SUCCESS+=("$ds")
done

END_ALL=$(date +%s)
TOTAL=$(( END_ALL - START_ALL ))
echo ""
echo "========================================================"
echo "  全部完成。总耗时: ${TOTAL}s"
echo "  ✅ 成功: ${SUCCESS[*]}"
echo "  ❌ 跳过: ${FAILED[*]}"
echo "========================================================"
