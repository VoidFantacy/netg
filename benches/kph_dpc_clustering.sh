#!/bin/bash
set -e

# =============================================
# KPH-DPC 分层聚类算法测试脚本
# =============================================

# 测试用参数，可根据需要调整
DATASET="test_dataset"
#ACPG_FILE="path/to/your/acpg_index_file.acpg"  # 需要替换为实际的ACPG文件路径
#OUTPUT_FILE="benches/outputs/${DATASET}/kph_dpc_clustering_results.json"
NUM_THREADS=16

# 线程配置
export OMP_NUM_THREADS=${NUM_THREADS}

# 创建输出目录（如果不存在）
mkdir -p "benches/outputs/${DATASET}"

echo "============================================="
echo "KPH-DPC 分层聚类算法测试开始"
echo "============================================="
echo "数据集: ${DATASET}"
echo "ACPG索引文件: ${ACPG_FILE}"
echo "输出文件: ${OUTPUT_FILE}"
echo "线程数: ${NUM_THREADS}"
echo "============================================="

# 检查可执行文件是否存在
if [ ! -f "./build/benches/kph_dpc_clustering" ]; then
    echo "错误: 可执行文件 ./build/benches/kph_dpc_clustering 不存在"
    echo "请先编译项目: mkdir build && cd build && cmake .. && make -j"
    exit 1
fi

# 检查ACPG文件是否存在
if [ ! -f "${ACPG_FILE}" ]; then
    echo "错误: ACPG索引文件 ${ACPG_FILE} 不存在"
    echo "请提供正确的ACPG文件路径"
    exit 1
fi

# 执行DPC聚类程序
echo "开始执行KPH-DPC分层聚类..."
./build/benches/kph_dpc_clustering \
    --acpg_file "${ACPG_FILE}" \
    --output_file "${OUTPUT_FILE}" \
    --num_threads ${NUM_THREADS}

# 检查执行结果
if [ $? -eq 0 ]; then
    echo "============================================="
    echo "KPH-DPC聚类完成!"
    echo "聚类结果已保存至: ${OUTPUT_FILE}"
    echo "============================================="
else
    echo "============================================="
    echo "KPH-DPC聚类执行失败!"
    echo "============================================="
    exit 1
fi