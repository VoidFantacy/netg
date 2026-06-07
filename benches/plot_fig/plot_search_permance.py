import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 颜色和样式映射
linestyles = {
    "acosp_mrnndescent": ('b', '--', 'o'),  # 蓝色
    "nsg": ('#ff7f0e', '--', 's'),  # 橙色
    "acosp": ('g', '-.', 'x'),  # 绿色
    "mrnndescent": ('r', '-', '^'),  # 红色
    "hnsw": ('m', ':', 'v'),  # 紫色
    "taumng": ('#8c564b', '-.', '*')  # 棕色
}

# 设定算法的显示名称
plot_labels = {
    "mrnndescent": "MRNN-Descent",
    "acosp_mrnndescent": "ACOS"
}

def create_plot(all_data, dataset):
    plt.figure(figsize=(10, 7))

    min_x, max_x = None, None
    handles = []

    # 获取当前 all_data 中实际有的数据，并匹配标签
    labels = [plot_labels.get(algo, algo.upper()) for algo in all_data.keys()]

    for algo in all_data.keys():
        xs = all_data[algo]['recall']
        ys = all_data[algo]['qps']

        if xs and ys:
            min_x = min([x for x in xs if x > 0], default=None)
            max_x = max([x for x in xs if x < 1], default=None)

        # 获取颜色和样式
        color, linestyle, marker = linestyles.get(algo, ('k', '-', 'o'))
        label = plot_labels.get(algo, algo.upper())  # 获取映射的名称

        (handle,) = plt.plot(xs, ys, color=color, linestyle=linestyle, label=label, marker=marker, linewidth=2.5, markersize=6, alpha=0.8)
        handles.append(handle)

    ax = plt.gca()
    ax.set_title("QPS vs Recall", fontsize=16)
    ax.set_xlabel("Recall@10", fontsize=14)
    ax.set_ylabel("Queries Per Second (QPS)", fontsize=14)

    # 仅当 min_x 和 max_x 有值时才设置 x 轴范围
    if min_x is not None and max_x is not None:
        ax.set_xlim(max(0.65, min_x), min(1, max_x))

    # 设置 X 轴刻度格式
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.xaxis.get_major_formatter().set_scientific(False)
    ax.xaxis.get_major_formatter().set_useOffset(False)

    # 调整图例
    ax.legend(handles, labels, loc="lower left", prop={"size": 12})

    # 添加网格
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)

    # 保存图片
    fn_out = f"benches/plot_fig/fig/performance_{dataset}_mrnndescent.png"
    print("📷 Picture saved to", fn_out)
    plt.savefig(fn_out)
    plt.show()

if __name__ == "__main__":
    DATASETS = ["deep"]
    algorithms = ["mrnndescent", "acosp_mrnndescent"]

    for dataset in DATASETS:
        all_data = {}

        for algorithm in algorithms:
            json_file_path = f"benches/outputs/{dataset}/{algorithm}.json"
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
            
            qps = [entry.get('qps') for entry in search_performances if 'qps' in entry]
            recall = [entry.get('r@k') for entry in search_performances if 'r@k' in entry]
            
            # 只保留 recall > 0.85 的数据
            filtered_qps = [q for r, q in zip(recall, qps) if r > 0.65]
            filtered_recall = [r for r in recall if r > 0.65]

            if filtered_qps and filtered_recall:
                all_data[algorithm] = {'qps': filtered_qps, 'recall': filtered_recall}

        if all_data:
            create_plot(all_data, dataset)
