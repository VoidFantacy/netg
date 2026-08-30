#!/bin/bash

# 遇到错误立即停止脚本
set -e

# 定义计时函数
timer_start() {
    step_start_time=$(date +%s)
}

timer_end() {
    step_end_time=$(date +%s)
    step_duration=$((step_end_time - step_start_time))
    echo "⏱️  耗时: ${step_duration}秒 ($((step_duration / 60))分 $((step_duration % 60))秒)"
    echo "--------------------------------------------------------"
}

total_start_time=$(date +%s)

echo "========================================================"
echo "🚀 开始执行 NETG 全流程脚本 (0ms 非对称路由版)"
echo "🕒 开始时间: $(date)"
echo "========================================================"

# --- 第一步: 运行 ACO 拓扑骨架提取 ---
echo "▶️ [Step 1] Running run_alth.py (ACO Backbone Extraction)..."
timer_start
python3 -u benches/run/run_alth.py > output_alth.log 2>&1
echo "✅ Step 1 Completed."
timer_end

# --- 第二步: 运行 train --- (注：如果是旧逻辑，确认是否还需要)
echo "▶️ [Step 2] Running train.py..."
timer_start
python3 -u benches/run/train.py > output_train.log 2>&1
echo "✅ Step 2 Completed."
timer_end

# --- 第三步: 运行 DPC 聚类找 Hub ---
echo "▶️ [Step 3] Running dpc.py (Weighted DPC Clustering)..."
timer_start
python3 -u benches/run/dpc.py > output_dpc.log 2>&1
echo "✅ Step 3 Completed."
timer_end

# --- 第四步: 生成导航标签 ---
echo "▶️ [Step 4] Running run_gen_labels.py (Mining Ground Truth)..."
timer_start
python3 -u benches/run/run_gen_labels.py > output_g_labels.log 2>&1
echo "✅ Step 4 Completed."
timer_end

# --- 第五步: 挪移文件位置 (提前到 train_router 之前，因为 router 强依赖 entry_points) ---
echo "▶️ [Step 5] Moving and renaming DPC files..."
timer_start
for dataset in deep10M sift10M sift10M_skewed yandex_t2i gist1M; do
    mkdir -p graph_processing/${dataset}_results
    if [ -f "dpc/${dataset}_results/dpc_hierarchical_results.json" ]; then
        cp dpc/${dataset}_results/dpc_hierarchical_results.json graph_processing/${dataset}_results/entry_points.json
        echo "  -> [${dataset}] ✅ DPC 结果已就位 -> entry_points.json"
    else
        echo "  -> [${dataset}] ⚠️ 未找到 DPC 结果，请确认"
    fi
done
echo "✅ Step 5 Completed."
timer_end

# --- 第六步: 训练单塔非对称 Router & 落盘特征 (核心步骤) ---
echo "▶️ [Step 6] Running train_router.py (Neural Manifold Folding)..."
timer_start
python3 -u benches/run/train_router.py > output_train_router.log 2>&1
echo "✅ Step 6 Completed. (.bin 特征已生成)"
timer_end

# ==========================================================
# 🛑 核心精简区: 
# 旧版的 Step 7 (run_neural_graph_pipeline) 和 Step 8 (generate_all_graphs) 
# 如果只是为了生成旧的神经网络物理边或 ONNX 图，现在已被彻底废弃！
# 新架构的 Micro-HNSW 是在 C++ 中通过读取 .bin 实时建图的。
# （如果这两步还包含生成底层基础图的逻辑，请保留；如果不包含，直接删除）
# ==========================================================

# --- 最后一步: C++ 基准压测 ---
echo "▶️ [Final Step] Running Test (Benchmarking Tasks)..."
timer_start
# 绑定 CPU 0-5 保证测试稳定性
taskset -c 0-5 python3 -u benches/run/test.py > output_test.log 2>&1
echo "✅ All Steps Completed Successfully!"
timer_end

# 计算总耗时
total_end_time=$(date +%s)
total_duration=$((total_end_time - total_start_time))
hours=$((total_duration / 3600))
minutes=$(((total_duration % 3600) / 60))
seconds=$((total_duration % 60))

echo "========================================================"
echo "🎉 NETG 任务结束 - End Time: $(date)"
echo "⏱️  总耗时: ${hours}小时 ${minutes}分 ${seconds}秒"
echo "========================================================"