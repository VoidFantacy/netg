import matplotlib.pyplot as plt
import os
import json
import numpy as np

# 定义数据集和算法列表
DATASETS = ["sift100K"]
algorithms = ["nsg", "acos_nsg"]
all_data = {}

plot_labels = {
    "nsg": "NSG",
    "acos_nsg": "ACOS"
}

# 仅处理第一个数据集
dataset = DATASETS[0]

for algorithm in algorithms:
    json_file_path = f"results/{dataset}/{algorithm}.json"
    if not os.path.exists(json_file_path):
        print(f"⚠️ File not found: {json_file_path}")
        continue
    try:
        with open(json_file_path, "r") as file:
            all_data[algorithm] = json.load(file)
    except json.JSONDecodeError:
        print(f"❌ Error decoding JSON: {json_file_path}")
    except Exception as e:
        print(f"❌ Unexpected error reading {json_file_path}: {e}")

# 提取数据并绘图
if len(all_data) == 2:
    algo1, algo2 = list(all_data.keys())

    x= [item["mean_rdrr"] for item in all_data[algo1]]
    y1 = [1000000000 / item["NDC"] for item in all_data[algo1]]  # 取自然对数
    y2 = [1000000000 / item["NDC"] for item in all_data[algo2]]  # 取自然对数

    # 设置图片清晰度
    plt.rcParams['figure.dpi'] = 300

    # 创建图形
    fig, ax = plt.subplots(figsize=(10, 6))

    # 绘制折线图
    ax.plot(x, y1, marker='o', linestyle='-', color='blue', label=plot_labels.get(algo1))
    ax.plot(x, y2, marker='s', linestyle='--', color='orange', label=plot_labels.get(algo2))

    # 设置 X 轴为对数刻度
    ax.set_xscale('log')

    # 设置 Y 轴
    ax.set_ylabel('ln(Number of Distance Computations)', fontsize=12)

    # 添加标题
    ax.set_title('ln(NDC) Comparison (Line Chart)', fontsize=14)

    # 添加图例
    ax.legend(loc="upper left", fontsize=10, edgecolor='black')

    # 显示网格
    ax.grid(axis='y', linestyle="--", linewidth=0.5)

    # 确保目录存在
    os.makedirs("results/fig", exist_ok=True)

    # 保存图片
    fn_out = f"results/fig/ln_ndc_line_{dataset}.png"
    print("📷 Picture saved to", fn_out)
    fig.savefig(fn_out, bbox_inches="tight", dpi=300)  # 保存高清图片
    plt.show()
else:
    print("Not enough valid data to plot.")