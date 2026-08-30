#!/bin/bash
# ============================================================
# GATE 正确的正负样本生成脚本（原作者方法）
# 原作者: 对每个 Hub 为入口跑 NSG 搜索 → 真实跳数 → 正负样本
# ============================================================
set -e

DATASET=${1:-"sift10M"}
BASE_FILE=${2:-"/mnt/new/New/ACSG/benches/datasets/SIFT10M/sift_base.fvecs"}
QUERY_FILE=${3:-"/mnt/new/New/ACSG/benches/datasets/SIFT10M/sift_query.fvecs"}

OUTPUT_DIR="/mnt/new/New/ACSG/GATE/output_${DATASET}"
NSG_PATH="${OUTPUT_DIR}/nsg.index"
HUB_BIN="${OUTPUT_DIR}/hubs.bin"
HUB_TXT="${OUTPUT_DIR}/hubs.txt"
SAMPLE_DIR="${OUTPUT_DIR}/train_samples_dir_v2"
HOP_DIR="${OUTPUT_DIR}/hop_counts"
SEARCH_L=100
SEARCH_K=1

mkdir -p "$SAMPLE_DIR"
mkdir -p "$HOP_DIR"

echo "=== Dataset: $DATASET ==="
echo "=== Step 1: Run NSG search from each Hub entry point ==="

# 读取 Hub 数量（从 hubs.txt header 第一个数字）
NUM_HUBS=$(head -1 "$HUB_TXT" | awk '{print $1}')
echo "  Number of Hubs: $NUM_HUBS"

# 临时构造单 Hub hubs.txt 并批量运行 test_nsg_search
# 但更简单的方法：直接调用现有 test_nsg_search，传入完整 hubs.txt
# test_nsg_search 的逻辑是：用 HNSW 找 top-3 最近 hub 作入口
# 我们需要的是：强制每次只用第 i 个 Hub 出发

# 实际上原作者用的是另一种方式：
# 对每个 hub_id (0..511)，调用 set_ep(hub_id) 然后搜索
# 这需要修改 C++，或者用我们的 Python 模拟器

echo "=== Step 2: Using Python hop-search simulator ==="
echo "  (512 hubs × $(wc -l < "$QUERY_FILE" 2>/dev/null || echo 'N') queries)"

cd /mnt/new/New/ACSG/GATE

python3 -m cluster.experiment.gen_samples_by_hopsearch \
    --nsg_path   "$NSG_PATH" \
    --base_path  "$BASE_FILE" \
    --hub_path   "$HUB_BIN" \
    --hub_txt    "$HUB_TXT" \
    --query_path "$QUERY_FILE" \
    --output_dir "$SAMPLE_DIR" \
    --search_L   $SEARCH_L \
    --t_pos      3 \
    --neg_size   64

echo ""
echo "✅ Samples generated at $SAMPLE_DIR"
echo "   pos_sample.txt: $(wc -l < $SAMPLE_DIR/pos_sample.txt) lines"
echo "   neg_sample.txt: $(wc -l < $SAMPLE_DIR/neg_sample.txt) lines"
