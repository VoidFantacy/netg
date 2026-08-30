#!/bin/bash
set -e
cd /mnt/new/New/ACSG/GATE

LOG="gate_batch_retrain_2.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG
}

# ============================================
# 1. 等 sift10M_skewed 训练进程完成
# ============================================
TRAIN_PID=1491545
if kill -0 $TRAIN_PID 2>/dev/null; then
    log "⏳ 等待 sift10M_skewed 训练进程 (PID $TRAIN_PID) 完成..."
    while kill -0 $TRAIN_PID 2>/dev/null; do
        sleep 30
    done
    log "✅ sift10M_skewed 训练进程已结束"
else
    log "ℹ️  sift10M_skewed 训练进程已不存在，直接继续"
fi

# ============================================
# 2. sift10M_skewed 推理 + 搜索
# ============================================
log "🔧 [sift10M_skewed] 开始推理..."
export GATE_CONFIG_PATH="output_sift10M_skewed/config.json"
export GATE_MODEL_DIR="output_sift10M_skewed/models"
export GATE_EMB_OUTPUT="output_sift10M_skewed/hub_embeddings.bin"

if [ ! -f "$GATE_EMB_OUTPUT" ]; then
    python3 -m cluster.model.train.infer 2>&1 | tee -a $LOG
fi

log "🔍 [sift10M_skewed] 开始搜索..."
./build/tests/test_gate_search \
    "/mnt/new/New/ACSG/benches/datasets/SIFT10M/sift_base.fvecs" \
    "/mnt/new/New/ACSG/benches/datasets/SIFT10M/sift_skewed_query.fvecs" \
    "output_sift10M_skewed/nsg.index" 100 100 \
    "output_sift10M_skewed/hubs.txt" \
    "output_sift10M_skewed/hub_embeddings.bin" \
    "output_sift10M_skewed/sift10M_skewed_gate_result.ivecs" \
    "/mnt/new/New/ACSG/benches/datasets/SIFT10M/sift_skewed_groundtruth.ivecs" 2>&1 | tee -a $LOG

log "✅ sift10M_skewed 完成！"

# ============================================
# 3. yandex_t2i 训练 + 推理 + 搜索 (batch_size=1024)
# ============================================
log "🚀 [yandex_t2i] 开始..."
./run_gate_generic.sh yandex_t2i 200 \
    "/mnt/new/New/ACSG/benches/datasets/YandexT2I/base.10M.fvecs" \
    "/mnt/new/New/ACSG/benches/datasets/YandexT2I/query.public.100K.fvecs" \
    "/mnt/new/New/ACSG/benches/datasets/YandexT2I/groundtruth_10M_subset.ivecs" 2>&1 | tee -a $LOG

log "✅ yandex_t2i 完成！"

# ============================================
# 4. gist1M 全流程
# ============================================
log "🚀 [gist1M] 开始..."
./run_gate_generic.sh gist1M 960 \
    "/mnt/new/New/ACSG/benches/datasets/GIST1M/gist_base.fvecs" \
    "/mnt/new/New/ACSG/benches/datasets/GIST1M/gist_query.fvecs" \
    "/mnt/new/New/ACSG/benches/datasets/GIST1M/gist_groundtruth.ivecs" 2>&1 | tee -a $LOG

log "✅ gist1M 完成！"

log "🎉 所有剩余任务完成！"
