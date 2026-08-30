#!/bin/bash

# 遇到错误立即停止
set -e

# ==================== 计时工具 ====================
timer_start() { step_start_time=$(date +%s); }

timer_end() {
    local step_end_time=$(date +%s)
    local step_duration=$((step_end_time - step_start_time))
    echo "⏱️  耗时: ${step_duration}秒 ($((step_duration / 60))分 $((step_duration % 60))秒)"
    echo "--------------------------------------------------------"
}

total_start_time=$(date +%s)

echo "========================================================"
echo "🚀 NETG 流程脚本 (从 Step 3 DPC 聚类开始)"
echo "🕒 开始时间: $(date)"
echo "📦 数据集: deep10M sift10M sift10M_skewed yandex_t2i gist1M"
echo "========================================================"

# --- Step 3: DPC 聚类找 Hub ---
echo ""
echo "▶️  [Step 3] Running dpc.py ... (实时日志: dpc_output.log)"
timer_start
python3 -u benches/run/dpc.py 2>&1 | tee dpc_output.log
echo "✅ Step 3 Completed."
timer_end

# --- Step 4: 生成拓扑感知导航标签 ---
echo ""
echo "▶️  [Step 4] Running run_gen_labels.py ... (实时日志: output_gen_labels.log)"
timer_start
python3 -u benches/run/run_gen_labels.py 2>&1 | tee output_gen_labels.log
echo "✅ Step 4 Completed."
timer_end

# --- Step 5: 对齐文件路径 (DPC 结果 -> entry_points.json) ---
echo ""
echo "▶️  [Step 5] Moving DPC results to graph_processing/..."
timer_start
for dataset in deep10M sift10M sift10M_skewed yandex_t2i gist1M; do
    mkdir -p graph_processing/${dataset}_results
    src="dpc/${dataset}_results/dpc_hierarchical_results.json"
    dst="graph_processing/${dataset}_results/entry_points.json"
    if [ -f "$src" ]; then
        cp "$src" "$dst"
        echo "  -> [${dataset}] ✅ $dst"
    else
        echo "  -> [${dataset}] ⚠️  未找到 $src，跳过"
    fi
done
echo "✅ Step 5 Completed."
timer_end

# --- Step 6: 训练 LightRouter，生成 transformed_hubs.bin ---
echo ""
echo "▶️  [Step 6] Running train_router.py ... (实时日志: output_train_router.log)"
timer_start
python3 -u benches/run/train_router.py 2>&1 | tee output_train_router.log
echo "✅ Step 6 Completed."
timer_end

# --- Final: C++ 基准压测 ---
echo ""
echo "▶️  [Final] Running test.py ... (实时日志: test.py 自带各数据集 log)"
timer_start
taskset -c 0-5 python3 -u benches/run/test.py
echo "✅ Final Step Completed."
timer_end

# --- 总耗时统计 ---
total_end_time=$(date +%s)
total_duration=$((total_end_time - total_start_time))
hours=$((total_duration / 3600))
minutes=$(((total_duration % 3600) / 60))
seconds=$((total_duration % 60))

echo ""
echo "========================================================"
echo "🎉 全流程结束 - End Time: $(date)"
echo "⏱️  总耗时: ${hours}小时 ${minutes}分 ${seconds}秒"
echo "========================================================"
