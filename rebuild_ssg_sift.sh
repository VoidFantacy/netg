#!/bin/bash
# SSG 重建 sift10M：放宽角度阈值 + 增大 R，修复 recall 饱和问题
# 原始参数: L=100 R=50 A=60 → recall@100 天花板 0.9614
# 新参数:   L=100 R=70 A=45 → 保留更多邻居
cd /mnt/new/New/ACSG

SSG_BUILD="SSG/build/tests/test_ssg_index"
BENCH_SSG="./build/benches/bench_ssg"
SSG_DIR="ssg_index"

L=100
R=70
A=45

BASE="benches/datasets/SIFT10M/sift10m_base.fvecs"
KNNG="GATE/output_sift10M/knng.graph"
OUTPUT="${SSG_DIR}/sift10M_R${R}_A${A}.ssg"

echo "===================================================="
echo " SSG sift10M 重建: L=${L} R=${R} A=${A}"
echo " 原始: R=50 A=60 → recall@100 天花板 0.9614"
echo "===================================================="

# ═══ Phase 1: 建图（多线程）═══
export OMP_NUM_THREADS=$(nproc)

if [ -f "$OUTPUT" ]; then
    echo "✅ SSG 图已存在: $OUTPUT，跳过建图"
else
    echo "🔨 开始建图..."
    START=$(date +%s)
    $SSG_BUILD "$BASE" "$KNNG" "$L" "$R" "$A" "$OUTPUT"
    END=$(date +%s)
    echo "⏱️ 建图耗时: $((END-START))s"
fi

# ═══ Phase 2: 搜索测试（单线程）═══
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

for DS in sift10M sift10M_skewed; do
    echo ""
    echo "########################################"
    echo "📦 [$DS] 开始测试"
    echo "########################################"

    OUTDIR="test/${DS}_ssg_results"
    mkdir -p "$OUTDIR"

    for K in 100 1; do
        echo ""
        echo ">>> [$DS] Recall@${K}"
        $BENCH_SSG \
            --dataset "$DS" \
            --ssg_file "$OUTPUT" \
            --fn_result "${OUTDIR}/${DS}_ssg_R${R}_A${A}_recall${K}.json" \
            --num_runs 3 \
            --recall_k "$K"
    done
done

echo ""
echo "🎉 完成! $(date)"
