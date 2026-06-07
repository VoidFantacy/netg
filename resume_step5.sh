#!/bin/bash

# 遇到错误立即停止脚本
set -e

# ==========================================
# 辅助函数 (必须保留，否则后面会报错)
# ==========================================
timer_start() {
    step_start_time=$(date +%s)
}

timer_end() {
    step_end_time=$(date +%s)
    step_duration=$((step_end_time - step_start_time))
    echo "⏱️  耗时: ${step_duration}秒 ($((step_duration / 60))分 $((step_duration % 60))秒)"
    echo "--------------------------------------------------------"
}

# 记录续跑开始时间
total_start_time=$(date +%s)

echo "========================================================"
echo "🚀 正在恢复任务 (从 Step 5 开始)"
echo "🕒 开始时间: $(date)"
echo "========================================================"

# ==========================================
# 这里跳过了 Step 1 ~ Step 4
# ==========================================

# --- 第五步: 训练路由 ---
echo "▶️ [Step 5] Resuming: Running train_router.py..."
timer_start
# 这里的 -u 参数是为了让日志实时输出
python3 -u benches/run/train_router.py > output_train_router.log 2>&1
echo "✅ Step 5 Completed."
timer_end


# --- 第六步: 挪移文件位置 ---
echo "▶️ [Step 6] Moving and renaming files..."
timer_start
for dataset in deep10M sift10M sift10M_skewed yandex_t2i gist1M; do
    # 确保目标目录存在
    mkdir -p graph_processing/${dataset}_results
    
    # 复制 DPC 结果并重命名为 entry_points.json
    # 注意：这里依赖 Step 3 的结果，您之前的日志显示 Step 3 已经完成，所以文件应该在
    if [ -f "dpc/${dataset}_results/dpc_hierarchical_results.json" ]; then
        cp dpc/${dataset}_results/dpc_hierarchical_results.json graph_processing/${dataset}_results/entry_points.json
        echo "  -> [${dataset}] ✅ DPC 聚类结果已就位 -> entry_points.json"
    else
        echo "  -> [${dataset}] ⚠️ 未找到 DPC 结果，请检查路径: dpc/${dataset}_results/"
    fi
done
echo "✅ Step 6 Completed."
timer_end

# --- 第七步: 神经图构建流程 ---
echo "▶️ [Step 7] Running run_neural_graph_pipeline.py..."
timer_start
python3 -u benches/run/run_neural_graph_pipeline.py > output_neural_pipeline.log 2>&1
echo "✅ Step 7 Completed."
timer_end

# --- 第八步: 生成所有图 ---
echo "▶️ [Step 8] Running generate_all_graphs.py..."
timer_start
python3 benches/run/generate_all_graphs.py > output_generate_graphs.log 2>&1
echo "✅ Step 8 Completed."
timer_end

# --- 最后一步: 测试 ---
echo "▶️ [Final Step] Running Test (Bound to CPU 0-5)..."
timer_start
taskset -c 0-5 python3 -u benches/run/test.py > output_test.log 2>&1
echo "✅ All Steps Completed Successfully!"
timer_end

# 计算本次续跑总耗时
total_end_time=$(date +%s)
total_duration=$((total_end_time - total_start_time))
hours=$((total_duration / 3600))
minutes=$(((total_duration % 3600) / 60))
seconds=$((total_duration % 60))

echo "========================================================"
echo "🎉 续跑任务结束 - End Time: $(date)"
echo "⏱️  本次运行耗时: ${hours}小时 ${minutes}分 ${seconds}秒"
echo "========================================================"