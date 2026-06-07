import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 颜色和样式映射
linestyles = {
    "acosp_nsg": ('b', '--', 'o'),  # 蓝色
    "nsg": ('#ff7f0e', '--', 's'),  # 橙色
    "acosp": ('g', '-.', 'x'),  # 绿色
    "nsg": ('r', '-', '^'),  # 红色
    "hnsw": ('m', ':', 'v'),  # 紫色
    "taumng": ('#8c564b', '-.', '*')  # 棕色
}

# 设定算法的显示名称
plot_labels = {
    "nsg": "NSG",
    "acosp_nsg": "ACOS"
}

# 设置全局字体
plt.rcParams['font.family'] ='sans-serif'
plt.rcParams['font.size'] = 12

if __name__ == "__main__":
    DATASETS = ["deep", "glove", "sift100K", "sift1M"]
    algorithms = ["acosp_nsg"]
    
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
            search_performances_aco = data.get("search_performances_aco", [])
            burte_force = data.get("brute_force_time")
        
            t_mrnn = [burte_force / entry.get('search_time') for entry in search_performances if 'search_time' in entry]
            recall_mrnn = [entry.get('r@k') for entry in search_performances if 'r@k' in entry]
            
            t_acos = [burte_force / entry.get('search_time') for entry in search_performances_aco if 'search_time' in entry]
            recall_acos = [entry.get('r@k') for entry in search_performances_aco if 'r@k' in entry]
            # 只保留 recall > 0.85 的数据
            threshold = 0
            filtered_t_mrnn = [t for r, t in zip(recall_mrnn, t_mrnn) if r > threshold]
            filtered_recall_mrnn = [r for r in recall_mrnn if r > threshold]
            filtered_t_acos = [t for r, t in zip(recall_acos, t_acos) if r > threshold]
            filtered_recall_acos = [r for r in recall_acos if r > threshold]
            
            
            plt.figure(figsize=(10, 7))
            color, style, marker = linestyles["nsg"]
            plt.plot(filtered_recall_mrnn, filtered_t_mrnn, label=plot_labels["nsg"], 
                     linestyle=style, marker=marker, color=color, linewidth=1.5)
            color, style, marker = linestyles["acosp_nsg"]
            plt.plot(filtered_recall_acos, filtered_t_acos, label=plot_labels["acosp_nsg"], 
                     linestyle=style, marker=marker, color=color, linewidth=1.5)
            plt.xlabel('Recall@10', fontsize=14)
            plt.ylabel('Speedup', fontsize=14)
            plt.title('Speedup vs Recall@10', fontsize=16)
            plt.legend(fontsize=12, markerscale=1.5)

            # 设置坐标轴刻度
            plt.xticks(fontsize=12)
            plt.yticks(fontsize=12)
            # plt.yscale('log')

            # # 自定义y轴刻度
            # y_ticks = np.logspace(0, 2, num=5)  # 生成从10的0次方到10的2次方的5个刻度
            # plt.yticks(y_ticks)

            # 设置网格样式
            plt.grid(True, which='major', linestyle='--', linewidth=0.8)
            plt.grid(True, which='minor', linestyle=':', linewidth=0.4)

            # 设置背景颜色
            ax = plt.gca()
            ax.set_facecolor('#f9f9f9')

            fn_out = f"benches/plot_fig/fig/speedup_vs_recall_{dataset}.png"
            print("📷 Picture saved to", fn_out)
            plt.savefig(fn_out, bbox_inches="tight", dpi=300)
            plt.show()