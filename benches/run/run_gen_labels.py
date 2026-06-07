import subprocess
import os
import datetime
import json

# ==========================================
# 配置区域
# ==========================================
MAX_TRAIN_SAMPLES = 30000
DATASETS = [ "deep10M","sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
os.environ["OMP_NUM_THREADS"] = "16"

# 【新增】针对不同数据集的参数配置
# L 值越大，Oracle 找到真值的成功率越高，但生成速度越慢
# GIST 维度高(960d)，必须给很大的 L 才能保证连通性
DATASET_PARAMS = {
    # --- 您的数据集 ---
    "sift10M":        {"L": 100},  # SIFT 比较规整，100 足够
    "sift10M_skewed": {"L": 100},  # 偏斜主要影响分布，100 步通常能走到
    "deep10M":        {"L": 100},  # Deep 难度中等，100 足够
    
    "yandex_t2i":     {"L": 300},  # Yandex 维度较高(200d)且分布复杂，给 300 比较稳
    "gist1M":         {"L": 500},  # GIST 960d 极难，必须给大 L，如果 500 不行说明图质量不够
    
    # --- 默认/其他 ---
    "sift1M":   {"L": 50},
    "sift100K": {"L": 50},
    "deep":     {"L": 50},
    "glove":    {"L": 200},   # Glove 也是高维难啃的骨头
    "gist":     {"L": 500},
}

DEFAULT_L = 100  # 默认兜底值

def main():
    executable = "./build/benches/bench_generate_labels"
    if not os.path.exists(executable):
        print(f"❌ 错误: 找不到 {executable}")
        return

    print(f"🚀 准备生成大规模训练标签 (Target: {MAX_TRAIN_SAMPLES})...")
    print(f"🎯 目标数据集来源: acpg_query_path (定制偏斜查询)")

    total_start = datetime.datetime.now()

    for dataset in DATASETS:
        print(f"\n{'='*60}")
        print(f"👉 Processing dataset: {dataset}")
        print(f"{'='*60}")

        # 1. 获取特定参数
        params = DATASET_PARAMS.get(dataset, {"L": DEFAULT_L})
        current_L = params["L"]
        print(f"🔧 配置搜索深度 L = {current_L}")

        # 2. 准备路径
        acpg_file = f"acpg/{dataset}_index/acpg_nsg.json"
        cluster_file = f"dpc/{dataset}_results/dpc_hierarchical_results.json"
        output_dir = f"drl/{dataset}_results/"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "topo_aware_labels.ivecs")

        # 3. 构造命令
        # C++ DataLoader 会自动读取 settings.json 中的 "acpg_query_path"
        cmd = [
            executable,
            "--dataset", dataset,
            "--index_file", acpg_file,
            "--cluster_file", cluster_file,
            "--output_file", output_file,
            "--limit", str(MAX_TRAIN_SAMPLES),
            "--query_type", "acpg",
            "--L", str(current_L)  # <--- 【新增】传入动态 L 参数
        ]

        print(f"执行命令: {' '.join(cmd)}")

        # 4. 运行
        try:
            subprocess.run(cmd, check=True)
            if os.path.exists(output_file):
                size_mb = os.path.getsize(output_file) / (1024 * 1024)
                print(f"✅ {dataset} 完成! 标签文件: {size_mb:.2f} MB")
            else:
                print(f"❌ {dataset} 失败: 未生成文件")
        except subprocess.CalledProcessError:
            print(f"❌ {dataset} C++ 执行出错")

    print(f"\n🎉 全部完成! 总耗时: {(datetime.datetime.now() - total_start).total_seconds():.2f}s")

if __name__ == "__main__":
    main()