#!/bin/bash
# Multi-Entry Baselines 补充实验
# 用法: cd 项目根目录 && bash run_multi_entry_baselines.sh
set -e

echo "🧪 Multi-Entry Baselines 实验"
echo "   Baseline A: Random-3-Start"
echo "   Baseline B: K-Means-800 (无投影)"
echo ""

[ -f "./build/benches/test" ] || { echo "❌ 先编译: cd build && make test"; exit 1; }

mkdir -p multi_entry_baselines
python3 -u benches/run/run_multi_entry_baselines.py 2>&1 | tee multi_entry_baselines/run.log

echo "✅ 完成。结果在 multi_entry_baselines/"
