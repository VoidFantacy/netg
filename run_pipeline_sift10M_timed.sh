#!/bin/bash
# run_pipeline_sift10M_timed.sh
# NETG 完整流程 —— 仅 sift10M，全程计时
# 与 run_pipeline_timed.sh 结构对齐，用于统计各步骤耗时

set -e
cd /mnt/new/New/ACSG

# ── 计时函数 ──────────────────────────────────────────────────────
timer_start() { step_start_time=$(date +%s); }
timer_end() {
    local d=$(( $(date +%s) - step_start_time ))
    echo "⏱️  耗时: ${d}秒 ($((d/60))分 $((d%60))秒)"
    echo "--------------------------------------------------------"
}

total_start_time=$(date +%s)
LOG=./run_sift10M_timed.log
exec > >(tee "$LOG") 2>&1

echo "========================================================"
echo "🚀 NETG 全流程 (sift10M only)"
echo "🕒 开始: $(date)"
echo "========================================================"

# ── 临时 patch helper：把 py 脚本里的 DATASETS 改成只跑 sift10M ──
# 用环境变量传入，各 py 脚本若支持则优先使用；否则用 sed 临时替换
patch_dataset() {
    local f=$1
    # 备份
    cp "$f" "${f}.bak_sift"
    # 替换所有 DATASETS = [...] 为只含 sift10M
    sed -i 's/DATASETS\s*=\s*\[.*\]/DATASETS = ["sift10M"]/' "$f"
    # train_router.py 用的是 "datasets" key in dict
    sed -i 's/"datasets": \["deep10M".*\]/"datasets": ["sift10M"]/' "$f"
}
restore_dataset() {
    local f=$1
    mv "${f}.bak_sift" "$f"
}

PY_FILES=(
    benches/run/run_alth.py
    benches/run/train.py
    benches/run/dpc.py
    benches/run/run_gen_labels.py
    benches/run/train_router.py
)

echo "📝 临时 patch DATASETS → [sift10M]"
for f in "${PY_FILES[@]}"; do patch_dataset "$f"; done

# ── 出错时自动恢复 ────────────────────────────────────────────────
trap 'echo "❌ 出错！正在恢复原始 py 文件..."; for f in "${PY_FILES[@]}"; do restore_dataset "$f" 2>/dev/null || true; done' ERR

# ── Step 1: ACO 拓扑骨架提取（NSG 建图 + ACO walk） ──────────────
echo ""
echo "▶️  [Step 1] ACO Backbone Extraction (run_alth.py)..."
echo "    (包含 NSG 建图 + ACO walk，Construction Time 会打印在 log 里)"
timer_start
python3 -u benches/run/run_alth.py 2>&1 | tee output_alth_sift.log
echo "✅ Step 1 完成"
timer_end

# ── Step 2: NETG 权重训练（ACO → edge weights） ──────────────────
echo "▶️  [Step 2] NETG Training (train.py)..."
timer_start
python3 -u benches/run/train.py > output_train_sift.log 2>&1
echo "✅ Step 2 完成"
timer_end

# ── Step 3: DPC 聚类找 Hub ────────────────────────────────────────
echo "▶️  [Step 3] DPC Clustering (dpc.py)..."
timer_start
python3 -u benches/run/dpc.py > output_dpc_sift.log 2>&1
echo "✅ Step 3 完成"
timer_end

# ── Step 4: 生成导航标签 ─────────────────────────────────────────
echo "▶️  [Step 4] Gen Labels (run_gen_labels.py)..."
timer_start
python3 -u benches/run/run_gen_labels.py > output_g_labels_sift.log 2>&1
echo "✅ Step 4 完成"
timer_end

# ── Step 5: 移动 DPC 文件 ────────────────────────────────────────
echo "▶️  [Step 5] Move DPC files..."
timer_start
mkdir -p graph_processing/sift10M_results
if [ -f "dpc/sift10M_results/dpc_hierarchical_results.json" ]; then
    cp dpc/sift10M_results/dpc_hierarchical_results.json \
       graph_processing/sift10M_results/entry_points.json
    echo "  -> sift10M ✅ entry_points.json 就位"
else
    echo "  -> sift10M ⚠️ 未找到 DPC 结果"
fi
echo "✅ Step 5 完成"
timer_end

# ── Step 6: 训练 Router（非对称单塔 + .bin 特征落盘） ─────────────
echo "▶️  [Step 6] Train Router (train_router.py)..."
timer_start
python3 -u benches/run/train_router.py > output_train_router_sift.log 2>&1
echo "✅ Step 6 完成"
timer_end

# ── 恢复原始 py 文件 ─────────────────────────────────────────────
echo ""
echo "🔄 恢复原始 py 文件..."
for f in "${PY_FILES[@]}"; do restore_dataset "$f"; done
echo "✅ 已恢复"

# ── 汇总 ─────────────────────────────────────────────────────────
total_d=$(( $(date +%s) - total_start_time ))
h=$((total_d/3600)); m=$(((total_d%3600)/60)); s=$((total_d%60))

echo ""
echo "========================================================"
echo "🎉 sift10M 全流程完成  $(date)"
echo "⏱️  总耗时: ${h}小时 ${m}分 ${s}秒"
echo "========================================================"
echo ""
echo "各步骤日志:"
echo "  Step1 (ACO/建图): output_alth_sift.log"
echo "  Step2 (NETG训练): output_train_sift.log"
echo "  Step3 (DPC):      output_dpc_sift.log"
echo "  Step4 (Labels):   output_g_labels_sift.log"
echo "  Step6 (Router):   output_train_router_sift.log"
echo "  全流程日志:        $LOG"
echo "========================================================"
