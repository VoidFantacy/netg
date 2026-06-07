import os
import json
import matplotlib.pyplot as plt
from itertools import product

# 固定参数
DATASET = "glove"
INPUT_DIR = f"benches/outputs/{DATASET}/parameters"
rho = 0.3
lambda_val = 0.3
rejection = 10

# 参数组合
alpha_list = [1.4, 2.2, 3.5, 4.0]
beta_list = [0, 1.4, 2.0, 3.3, 4.2]

# 更适合论文的宽度：宽 10 英寸，高 6 英寸（两行两列）
fig, axes = plt.subplots(2, 2, figsize=(11,9), sharey=True)
axes = axes.flatten()

for idx, alpha in enumerate(alpha_list):
    ax = axes[idx]
    for beta in beta_list:
        filename = f"acosp_nsg_a{alpha}_b{beta}_r{rho}_l{lambda_val}_rej{rejection}.json"
        filepath = os.path.join(INPUT_DIR, filename)
        if not os.path.exists(filepath):
            print(f"⚠️ 缺失文件: {filename}")
            continue

        with open(filepath, "r") as f:
            data = json.load(f)

        if "search_performances_aco" not in data:
            print(f"⚠️ 缺字段: {filename}")
            continue

        recall_qps = [(entry["r@k"], entry["qps"]) for entry in data["search_performances_aco"]]
        recall_qps.sort()
        recalls, qpss = zip(*recall_qps)

        ax.plot(recalls, qpss, label=f"β={beta}", linewidth=1.0)

    ax.set_title(f"α={alpha}", fontsize=10)
    ax.set_xlabel("Recall@10", fontsize=9)
    if idx % 2 == 0:
        ax.set_ylabel("QPS", fontsize=9)
    ax.grid(True, linewidth=0.4)
    ax.legend(fontsize=6, frameon=False)

# 总标题 & 紧凑排版
plt.suptitle("QPS vs Recall@10 (Varying β)", fontsize=11, y=0.93)

# 导出文件（适配论文插图）
plt.savefig(f"{INPUT_DIR}/aco_alpha2x2_compact.pdf", dpi=300, bbox_inches="tight")
plt.savefig(f"{INPUT_DIR}/aco_alpha2x2_compact.png", dpi=600, bbox_inches="tight")
plt.show()
