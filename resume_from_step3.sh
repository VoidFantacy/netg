#!/bin/bash
set -e

timer_start() { step_start_time=$(date +%s); }
timer_end() {
    step_end_time=$(date +%s)
    step_duration=$((step_end_time - step_start_time))
    echo "⏱️  耗时: ${step_duration}秒 ($((step_duration / 60))分 $((step_duration % 60))秒)"
    echo "--------------------------------------------------------"
}

total_start_time=$(date +%s)
echo "========================================================"
echo "🚀 从 Step 3 恢复执行 NETG 训练流程"
echo "🕒 开始时间: $(date)"
echo "========================================================"

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

# --- 第五步: 挪移文件位置 ---
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

# --- 第六步: 训练单塔非对称 Router & 落盘特征 ---
echo "▶️ [Step 6] Running train_router.py (Neural Manifold Folding)..."
timer_start
python3 -u benches/run/train_router.py > output_train_router.log 2>&1
echo "✅ Step 6 Completed. (.bin 特征已生成)"
timer_end

# --- 第七步: 快速冒烟测试 ---
echo "▶️ [Step 7] Quick Smoke Test (单数据集, 1次运行)..."
timer_start

EXECUTABLE="./build/test"
if [ ! -f "$EXECUTABLE" ]; then
    EXECUTABLE="./build/benches/test"
fi

if [ -f "$EXECUTABLE" ]; then
    SMOKE_DATASET=""
    for ds in sift10M deep10M gist1M sift10M_skewed yandex_t2i; do
        if [ -f "acpg/${ds}_index/acpg_nsg.json" ]; then
            SMOKE_DATASET="$ds"
            break
        fi
    done

    if [ -n "$SMOKE_DATASET" ]; then
        echo "  🔍 使用数据集: ${SMOKE_DATASET} 进行冒烟测试..."
        mkdir -p test/${SMOKE_DATASET}_results

        SMOKE_CMD="$EXECUTABLE --dataset $SMOKE_DATASET \
            --acpg_file acpg/${SMOKE_DATASET}_index/acpg_nsg.json \
            --fn_result test/${SMOKE_DATASET}_results/smoke_test.json \
            --test_scope all \
            --num_runs 1 \
            --R 32"

        if [ -f "drl/${SMOKE_DATASET}_results/transformed_hubs.bin" ] && \
           [ -f "drl/${SMOKE_DATASET}_results/transformed_hub_ids.bin" ]; then
            SMOKE_CMD="$SMOKE_CMD \
                --transformed_hubs drl/${SMOKE_DATASET}_results/transformed_hubs.bin \
                --transformed_ids drl/${SMOKE_DATASET}_results/transformed_hub_ids.bin"
            echo "  🚀 已挂载 transformed_hubs (非对称路由)"
        fi

        if [ -f "drl/${SMOKE_DATASET}_results/raw_hubs.bin" ]; then
            SMOKE_CMD="$SMOKE_CMD --raw_hubs drl/${SMOKE_DATASET}_results/raw_hubs.bin"
            echo "  📊 已挂载 raw_hubs (消融对照)"
        fi

        eval $SMOKE_CMD > output_smoke_test.log 2>&1 && \
            echo "  ✅ 冒烟测试通过! 流程跑通。" || \
            echo "  ❌ 冒烟测试失败! 请查看 output_smoke_test.log"
    else
        echo "  ⚠️ 未找到任何可用的索引文件，跳过冒烟测试"
    fi
else
    echo "  ⚠️ 未找到 C++ 可执行文件，跳过冒烟测试 (请先编译)"
fi

echo "✅ Step 7 Completed."
timer_end

# 计算总耗时
total_end_time=$(date +%s)
total_duration=$((total_end_time - total_start_time))
hours=$((total_duration / 3600))
minutes=$(((total_duration % 3600) / 60))
seconds=$((total_duration % 60))

echo "========================================================"
echo "🎉 NETG 训练流程 (Step 3-7) 结束 - End Time: $(date)"
echo "⏱️  总耗时: ${hours}小时 ${minutes}分 ${seconds}秒"
echo "========================================================"
