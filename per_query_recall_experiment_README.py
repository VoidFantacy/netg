# Per-Query Recall Distribution 实验说明
# ==========================================
# 目的: 验证 NETG 解决了"几何迷失 (Geometric Myopia)"问题
# 方法: 对比 NSG vs NETG 在每个查询上的 recall 分布
# 核心发现: NETG 将灾难性失败查询(Recall@10 < 0.1)减少了 40%
# 最佳展示数据集: Yandex T2I (200-d)
# ==========================================

# ============================================================
# 1. 实验概述
# ============================================================
#
# 你师兄建议: 不能只看平均 recall，需要展示 per-query recall 分布
# 来证明 NETG 确实"拯救了被几何空洞困住的查询"
#
# 实验设计:
#   - 固定图索引 (ACPG)，对比不同入口点策略:
#     - NSG (Medoid): 从图的质心单点出发
#     - NETG (AsymHNSW): 从神经折叠后的 Top-3 Hub 出发
#     - Raw HNSW (消融): 从未折叠的 Top-3 Hub 出发
#   - 在 Search_L = 64,128,200,300,400,512,800,1024 下测试
#   - 记录每个查询的 Recall@10
#   - 以不同阈值统计"失败查询"占比
#
# 核心结论:
#   Yandex T2I, L=64:
#     NSG: 6.9% 查询 recall < 0.1 (灾难性失败)
#     NETG: 4.2% (↓40% 相对改善)
#     Raw HNSW: 6.3% (几乎无改善 → 证明改善来自神经折叠)
#
# 参考论文:
#   Aumüller & Ceccarello, "The Role of Local Intrinsic Dimensionality
#   in Benchmarking Nearest Neighbor Search", 2019
#   (ridgeline plot 风格来源)

# ============================================================
# 2. 代码文件位置
# ============================================================

## --- C++ 搜索程序 (输出 per-query recall) ---
CPP_SOURCE = "/mnt/lost+found/ACSG/benches/bench_per_query_recall.cpp"
# 编译后位置: /mnt/lost+found/ACSG/build/benches/bench_per_query_recall
# CMakeLists 已更新: /mnt/lost+found/ACSG/benches/CMakeLists.txt
# 编译命令: cd /mnt/lost+found/ACSG/build && cmake .. -DCMAKE_BUILD_TYPE=Release \
#           -DFAISS_ENABLE_GPU=OFF -DFAISS_ENABLE_PYTHON=OFF \
#           -DBUILD_TESTING=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5 && make bench_per_query_recall -j8

## --- Python 运行脚本 ---
# Recall@1 版本 (已弃用，二值分布无意义):
RUN_R1 = "/mnt/lost+found/ACSG/benches/run/run_per_query_recall.py"
# Recall@10 版本 (最终使用):
RUN_R10 = "/mnt/lost+found/ACSG/benches/run/run_per_query_recall_r10.py"

## --- Python 画图脚本 ---
# Ridgeline/山脊图 (仿 Aumüller 2019 风格):
PLOT_RIDGELINE = "/mnt/lost+found/ACSG/benches/run/plot_ridgeline.py"
# 多阈值对比 + 热力图:
PLOT_MULTI_THRESHOLD = "/mnt/lost+found/ACSG/benches/run/plot_multi_threshold.py"
# 增强可视化 (折线图、柱状图、CDF 放大):
PLOT_ENHANCED = "/mnt/lost+found/ACSG/benches/run/plot_enhanced.py"
# 最终论文精品图 (Recall < 0.1 阈值):
PLOT_FINAL = "/mnt/lost+found/ACSG/benches/run/plot_final_paper.py"
# 早期 CDF 图 (效果一般):
PLOT_CDF_EARLY = "/mnt/lost+found/ACSG/benches/run/plot_per_query_recall.py"

# ============================================================
# 3. 输出数据位置
# ============================================================

## --- 原始 JSON 数据 (每个查询的 recall 值) ---
# Recall@10 数据 (最终使用):
DATA_DIR_R10 = "/mnt/lost+found/ACSG/per_query_recall_results_r10/"
# 文件: deep10M_per_query_recall_r10.json
#       sift10M_per_query_recall_r10.json
#       sift10M_skewed_per_query_recall_r10.json
#       yandex_t2i_per_query_recall_r10.json
#       gist1M_per_query_recall_r10.json

# Recall@1 数据 (已弃用):
DATA_DIR_R1 = "/mnt/lost+found/ACSG/per_query_recall_results/"

## --- 生成的图表 ---
PLOTS_DIR = "/mnt/lost+found/ACSG/per_query_recall_plots/"
# 推荐用于论文的图:
#   paper_combo_threshold01.pdf  ← 主图: 上(失败率折线) + 下(mean recall)
#   paper_bars_threshold01.pdf   ← 柱状图: 每个L的失败率对比
#   ridgeline_paper_nsg_yandex.pdf  ← Motivation 图: 展示问题存在
#   threshold_heatmap.pdf        ← 阈值选择依据 (附录)
#   ridgeline_yandex_t2i_sidebyside.pdf  ← NSG vs NETG 山脊对比

# ============================================================
# 4. 复现步骤
# ============================================================
#
# Step 1: 编译 C++ (如果 build 目录被清理)
#   cd /mnt/lost+found/ACSG/build
#   cmake .. -DCMAKE_BUILD_TYPE=Release -DFAISS_ENABLE_GPU=OFF \
#            -DFAISS_ENABLE_PYTHON=OFF -DBUILD_TESTING=OFF \
#            -DCMAKE_POLICY_VERSION_MINIMUM=3.5
#   make bench_per_query_recall -j8
#
# Step 2: 运行实验 (约 30-60 分钟)
#   cd /mnt/lost+found/ACSG
#   python3 benches/run/run_per_query_recall_r10.py
#
# Step 3: 画图
#   python3 benches/run/plot_ridgeline.py       # 山脊图
#   python3 benches/run/plot_multi_threshold.py  # 多阈值热力图
#   python3 benches/run/plot_final_paper.py      # 最终论文图
#   python3 benches/run/plot_enhanced.py         # 其他辅助图
#
# 依赖: pip3 install matplotlib scipy numpy

# ============================================================
# 5. JSON 数据结构说明
# ============================================================
#
# 每个 {dataset}_per_query_recall_r10.json 结构:
# {
#   "dataset": "yandex_t2i",
#   "num_queries": 10000,
#   "top_k": 10,
#   "methods": [
#     {
#       "method": "NSG_Medoid",
#       "search_results": [
#         {
#           "search_L": 64,
#           "mean_recall": 0.7636,
#           "p5": 0.0,            // 第 5 百分位
#           "p10": 0.2,           // 第 10 百分位
#           "p25": 0.6,
#           "median": 0.9,
#           "pct_below_50": 16.0, // recall < 0.5 的查询占比
#           "pct_below_80": 32.2,
#           "pct_below_90": 43.1,
#           "pct_perfect": 39.2,  // recall = 1.0 的查询占比
#           "per_query_recalls": [0.0, 0.1, 0.3, ..., 1.0, 1.0]  // 每个查询的 recall
#         },
#         ...  // 其他 search_L
#       ]
#     },
#     ...  // NETG_AsymHNSW, Raw_HNSW_Ablation
#   ]
# }

# ============================================================
# 6. C++ 程序参数说明
# ============================================================
#
# ./build/benches/bench_per_query_recall \
#   --dataset yandex_t2i \
#   --acpg_file acpg/yandex_t2i_index/acpg_nsg.json \
#   --output_file per_query_recall_results_r10/yandex_t2i_per_query_recall_r10.json \
#   --search_L "64,128,200,300,400,512,800,1024" \
#   --top_k 10 \
#   --transformed_hubs drl/yandex_t2i_results/transformed_hubs.bin \
#   --transformed_ids drl/yandex_t2i_results/transformed_hub_ids.bin \
#   --raw_hubs drl/yandex_t2i_results/raw_hubs.bin
#
# 参数:
#   --dataset: 数据集名 (deep10M/sift10M/sift10M_skewed/yandex_t2i/gist1M)
#   --acpg_file: ACPG 图索引路径
#   --output_file: 结果输出 JSON 路径
#   --search_L: 逗号分隔的搜索深度列表
#   --top_k: Recall@K 中的 K (用 10)
#   --transformed_hubs: 神经折叠后的 Hub 向量 (.bin)
#   --transformed_ids: Hub ID 映射 (.bin)
#   --raw_hubs: 原始 Hub 向量 (.bin, 用于消融实验)

# ============================================================
# 7. 关键发现总结 (可直接用于论文)
# ============================================================
#
# Dataset: Yandex T2I (200-d, 跨模态嵌入)
# Threshold: Recall@10 < 0.1 (灾难性失败: top-10 中 0 个正确结果)
#
# | Search_L | NSG   | NETG  | Raw HNSW | 相对改善 |
# |----------|-------|-------|----------|---------|
# | 64       | 6.9%  | 4.2%  | 6.3%     | ↓40%   |
# | 128      | 4.0%  | 2.5%  | 3.6%     | ↓37%   |
# | 200      | 2.9%  | 1.8%  | 2.5%     | ↓39%   |
# | 300      | 2.1%  | 1.2%  | 1.8%     | ↓40%   |
# | 400      | 1.5%  | 1.0%  | 1.3%     | ↓38%   |
# | 512      | 1.2%  | 0.8%  | 1.1%     | ↓37%   |
# | 800      | 0.7%  | 0.5%  | 0.6%     | ↓34%   |
# | 1024     | 0.5%  | 0.3%  | 0.5%     | ↓36%   |
#
# 结论:
# 1. NETG 在所有搜索预算下一致性地减少灾难性失败 34-40%
# 2. Raw HNSW (不做神经折叠) 几乎无改善 → 证明是坐标折叠起作用
# 3. 阈值越低 (越严重的失败), NETG 相对改善越大 (热力图验证)
# 4. 改善集中在跨模态嵌入 (Yandex T2I), SIFT 等规整数据集无此问题
