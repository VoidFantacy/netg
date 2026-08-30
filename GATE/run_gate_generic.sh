#!/bin/bash
# =============================================================================
# GATE 通用测试流水线 (Aligned with ACSG Params & C++ Text Format)
# 使用方法: ./run_gate_generic.sh <数据集名> <维度> <底库路径> <查询路径> [GT路径]
# =============================================================================

set -eo pipefail

DATASET_NAME=${1:-""}
DIM=${2:-""}
BASE_FILE=${3:-""}
QUERY_FILE=${4:-""}
GT_FILE=${5:-""}

if [ -z "$QUERY_FILE" ]; then
    echo "❌ 用法: ./run_gate_generic.sh <数据集名> <维度> <底库路径> <查询路径> [GT路径]"
    exit 1
fi

echo "=== 🚀 开始测试: $DATASET_NAME (Dim: $DIM) ==="
echo "📂 Base: $BASE_FILE"
echo "📂 Query: $QUERY_FILE"

# 1. 路径定义
GATE_ROOT=$(pwd)
OUT_DIR="$GATE_ROOT/output_${DATASET_NAME}"
mkdir -p "$OUT_DIR/models"
mkdir -p "$OUT_DIR/subgraphs"

# 文件路径
KNNG_PATH="$OUT_DIR/knng.graph"
NSG_PATH="$OUT_DIR/nsg.index"
HUB_PATH="$OUT_DIR/hubs.bin"
# 【新增】C++ 专用的 Hub 文本文件
HUB_TXT_PATH="$OUT_DIR/hubs.txt" 
SAMPLE_PATH="$OUT_DIR/train_samples_dir" 
mkdir -p "$SAMPLE_PATH"

EMB_PATH="$OUT_DIR/hub_embeddings.bin"
RESULT_PATH="$OUT_DIR/${DATASET_NAME}_gate_result.ivecs"
CONFIG_JSON="$OUT_DIR/config.json"

export GATE_CONFIG_PATH="$CONFIG_JSON"
export GATE_MODEL_DIR="$OUT_DIR/models"
export GATE_EMB_OUTPUT="$EMB_PATH"

# 2. 生成配置文件（若已存在则保留，不覆盖手动调参）
if [ ! -f "$CONFIG_JSON" ]; then
cat > $CONFIG_JSON <<EOF
{
    "model": {
        "name": "gate_model",
        "input_dim": $DIM,
        "hidden_dim": 1024,
        "output_dim": $DIM,
        "dropout": 0.1,
        "batch_size": 512,
        "lr": 1e-4,
        "temperature": 0.07,
        "epochs": 50
    },
    "dataset": {
        "SAMPLE_PATH": "$SAMPLE_PATH",
        "SUBGRAPH_DIR": "$OUT_DIR/subgraphs",
        "HUB_PATH": "$HUB_PATH",
        "QUERY_PATH": "$QUERY_FILE"
    }
}
EOF
    echo "    📝 已生成新配置: $CONFIG_JSON"
else
    echo "    📝 配置已存在，保留手动调参: $CONFIG_JSON"
fi

# 3. 检查与构图
if [ ! -f "$NSG_PATH" ]; then
    echo ">>> [1/7] 准备 KNN 图与 NSG 索引..."
    if [ ! -f "$KNNG_PATH" ]; then
        echo "    ⚠️ 未检测到 KNN 图，自动构建..."
        python3 -u cluster/build_knn.py \
            --base_path "$BASE_FILE" \
            --output_path "$KNNG_PATH" \
            --k 200
    fi
    echo "    >>> 构建 NSG 索引..."
    ./build/tests/test_nsg_index "$BASE_FILE" "$KNNG_PATH" 100 50 512 "$NSG_PATH"
else
    echo ">>> [1/7] NSG 索引已存在，跳过。"
fi

# 4. 提取 Hub（使用论文 Algorithm 2: HBKM 两层聚类）
# k1=32 (Level-1 粗粒度簇), k2=16 (Level-2 叶子簇), 总 Hub = 32×16 = 512
if [ ! -f "$HUB_PATH" ]; then
    echo ">>> [2/7] 提取 Hub 节点 (HBKM 两层: k1=32, k2=16, 总512)..."
    python3 -u -m cluster.kmeans "$BASE_FILE" "$HUB_PATH" --k 512 --k1 32 --k2 16 --lambda_p 0.01 --max_iters 20
fi

# 5. 子图生成 (并生成 hubs.txt)
# 注意：我们依靠 subgraph2json.py 来生成 hubs.txt
if [ -z "$(ls -A $OUT_DIR/subgraphs)" ] || [ ! -f "$HUB_TXT_PATH" ]; then
    echo ">>> [3/7] 生成子图 (及 C++ Hub Info)..."
    python3 -u -m cluster.subgraph2json "$NSG_PATH" "$BASE_FILE" "$HUB_PATH" "$OUT_DIR/subgraphs"
fi

# 6. 生成训练样本（原作者正确方法：对每个Hub为入口跑NSG搜索，得真实跳数）
if [ ! -f "$SAMPLE_PATH/pos_sample.txt" ]; then
    echo ">>> [4/7] 生成训练样本 (Hub-based hop-search mode)..."
    python3 -u -m cluster.experiment.gen_samples_by_hopsearch \
        --nsg_path   "$NSG_PATH" \
        --base_path  "$BASE_FILE" \
        --hub_path   "$HUB_PATH" \
        --hub_txt    "$HUB_TXT_PATH" \
        --query_path "$QUERY_FILE" \
        --output_dir "$SAMPLE_PATH" \
        --search_L   100 \
        --t_pos      3 \
        --neg_size   64 \
        --workers    "$(nproc)"
fi

# 7. 训练模型（如果已有 Embedding 则跳过训练和推理）
if [ -f "$EMB_PATH" ]; then
    echo ">>> [5/7] Hub Embedding 已存在 ($EMB_PATH)，跳过训练和推理。"
else
    # 查找是否已有训练好的模型
    MODEL_EXISTS=$(find "$OUT_DIR/models" -name "*.pth" 2>/dev/null | head -1)
    if [ -n "$MODEL_EXISTS" ]; then
        echo ">>> [5/7] 模型已存在 ($MODEL_EXISTS)，跳过训练。"
    else
        echo ">>> [5/7] 训练 GATE 模型..."
        python3 -u -m cluster.model.train
    fi

    # 8. 推理 Embedding
    echo ">>> [6/7] 生成 Hub Embeddings..."
    python3 -u -m cluster.model.train.infer
fi

# 9. 搜索
echo ">>> [7/7] 执行 GATE 搜索..."
if [ ! -f "$EMB_PATH" ]; then
    echo "❌ 错误：Embedding 未生成，无法搜索！"
    exit 1
fi

# 【关键修改】使用 HUB_TXT_PATH (hubs.txt) 而不是 HUB_PATH (hubs.bin)
# 因为 C++ LoadKmeans 只吃文本格式
# 单塔模型：直接用原始 query 在 CosSpace 中路由（与作者原始实现一致）

if [ -n "$GT_FILE" ] && [ -f "$GT_FILE" ]; then
    ./build/tests/test_gate_search "$BASE_FILE" "$QUERY_FILE" "$NSG_PATH" 100 100 "$HUB_TXT_PATH" "$EMB_PATH" "$RESULT_PATH" "$GT_FILE"
else
    echo "⚠️  Warning: No GT file provided, recall will not be computed."
    ./build/tests/test_gate_search "$BASE_FILE" "$QUERY_FILE" "$NSG_PATH" 100 100 "$HUB_TXT_PATH" "$EMB_PATH" "$RESULT_PATH"
fi

echo "✅ $DATASET_NAME 测试完成！"