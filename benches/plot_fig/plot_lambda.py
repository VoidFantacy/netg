import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 设定绘图样式
linestyles = {
    "0.0": ('b', '-', 'o'),    
    "0.1": ('#ff7f0e', '--', 's'),  
    "0.2": ('m', '-.', 'x'),  
    "0.3": ('r', '-', '^'),   
    "0.4": ('g', '--', 'D'),   
    "0.5": ('c', '-.', 'p'),
    "0.6": ('y', '-', '*'),
    "0.7": ('purple', '--', 'h'),
    "0.8": ('brown', '-.', 'd'),
    "0.9": ('pink', '-', 'v'),
    "1.0": ('gray', '--', '8')
}

def create_plot(all_data, dataset):
    plt.figure(figsize=(10, 7))

    min_x, max_x = None, None
    handles = []
    
    for lambda_val, (xs, ys) in all_data.items():
        if xs and ys:
            min_x = min(xs) if min_x is None else min(min_x, *[x for x in xs if x > 0])
            max_x = max(xs) if max_x is None else max(max_x, *[x for x in xs if x < 1])

        color, linestyle, marker = linestyles.get(lambda_val, ('k', '-', 'o'))
        (handle,) = plt.plot(xs, ys, color=color, linestyle=linestyle, label=f"lambda_={lambda_val}", marker=marker, linewidth=2.5, markersize=6, alpha=0.8)
        handles.append(handle)

    ax = plt.gca()
    ax.set_title("QPS vs Recall (Varying τ)", fontsize=16)
    ax.set_xlabel("Recall@10", fontsize=14)
    ax.set_ylabel("Queries Per Second (QPS)", fontsize=14)

    # 设置 X 轴范围，给一点 buffer
    if min_x and max_x:
        ax.set_xlim(min_x * 0.98, max_x * 1.02)

    # 取消科学计数法
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.xaxis.get_major_formatter().set_scientific(False)
    ax.xaxis.get_major_formatter().set_useOffset(False)

    # 添加图例
    ax.legend(handles=handles, labels=[f"lambda={lambda_val}" for lambda_val in all_data.keys()], loc="lower left", prop={"size": 12})

    # 添加网格
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)

    # 保存图片
    fn_out = f"benches/plot_fig/fig/search_performances_lambda_{dataset}.png"
    os.makedirs(os.path.dirname(fn_out), exist_ok=True)  # 确保目录存在
    plt.savefig(fn_out)
    print("✅ Picture saved to", fn_out)
    plt.show()

if __name__ == "__main__":
    DATASETS = ["sift100K"]
    lambda_values = [0.5, 0.6, 0.7, 0.8, 0.9, 1]

    for dataset in DATASETS:
        all_data = {}
        for lambda_val in lambda_values:
            json_file_path = f"benches/outputs/{dataset}/lambda/acsg_{lambda_val}.json"
            if not os.path.exists(json_file_path):
                print(f"⚠️ File not found: {json_file_path}")
                continue

            try:
                with open(json_file_path, "r") as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                print(f"❌ Error decoding JSON: {json_file_path}")
                continue
            except Exception as e:
                print(f"❌ Unexpected error reading {json_file_path}: {e}")
                continue

            search_performances = data.get("search_performances", [])
            qps = [entry['qps'] for entry in search_performances if "qps" in entry]
            recall = [entry['r@k'] for entry in search_performances if "r@k" in entry]

            # 只保留 recall > 0.90 的数据
            filtered_qps = [q for r, q in zip(recall, qps) if r > 0.90]
            filtered_recall = [r for r in recall if r > 0.90]

            if filtered_qps and filtered_recall:
                all_data[f"{lambda_val:.1f}"] = (filtered_recall, filtered_qps)

        if all_data:
            create_plot(all_data, dataset)
