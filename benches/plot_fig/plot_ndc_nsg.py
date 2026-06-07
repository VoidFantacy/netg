import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 颜色和样式映射
linestyles = {
    "acosp_nsg": ('b', '--', 'o'),  # 蓝色
    "taumng": ('#ff7f0e', '--', 's'),  # 橙色
    "acosp": ('g', '-.', 'x'),  # 绿色
    "nsg": ('r', '-', '^'),  # 红色
    "acosp_mrnndescent": ('m', '-', 'v'),  # 紫色
    "taumng": ('#8c564b', '-.', '*')  # 棕色
}

# 设定算法的显示名称
plot_labels = {
    "nsg": "NSG",
    "acosp_nsg": "QDAES"
}

# 设置全局字体
plt.rcParams['font.family'] ='sans-serif'
plt.rcParams['font.size'] = 12

if __name__ == "__main__":
    DATASETS = ["sift1M","deep","sift100K","glove"]
    algorithms = ["acosp_nsg"]
    
    for dataset in DATASETS:
        all_data = {}

        for algorithm in algorithms:
            json_file_path = f"benches/outputs/{dataset}/{algorithm}_NDC.json"
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
            
            NDC_mrnn = [200 * 1000000 / entry.get('NDC') for entry in search_performances if 'NDC' in entry]
            rderr_mrnn = [entry.get('rderr') for entry in search_performances if 'rderr' in entry]
    
            NDC_acos = [200 * 1000000 / entry.get('NDC') for entry in search_performances_aco if 'NDC' in entry]
            rderr_acos = [entry.get('rderr') for entry in search_performances_aco if 'rderr' in entry]
            # 只保留 recall > 0.85 的数据
            
            
            plt.figure(figsize=(10, 7))
            color, style, marker = linestyles["nsg"]
            plt.plot(rderr_mrnn, NDC_mrnn, label=plot_labels["nsg"], 
                     linestyle=style, marker=marker, color=color, linewidth=1.5)
            color, style, marker = linestyles["acosp_nsg"]
            plt.plot(rderr_acos, NDC_acos, label=plot_labels["acosp_nsg"], 
                     linestyle=style, marker=marker, color=color, linewidth=1.5)
            plt.xlabel('relative distance error', fontsize=14)
            plt.ylabel('speedup', fontsize=14)
            plt.title('speedup vs rderr', fontsize=16)
             
            # 设置坐标轴刻度
            plt.xticks(fontsize=12)
            plt.yticks(fontsize=12)
            plt.legend(loc='upper left', fontsize=12, markerscale=1.5) 
            
            # plt.xscale('log')

            # # 自定义y轴刻度
            # y_ticks = np.logspace(0, 2, num=5)  # 生成从10的0次方到10的2次方的5个刻度
            # plt.yticks(y_ticks)

            # 设置网格样式
            plt.grid(True, which='major', linestyle='--', linewidth=0.8)
            plt.grid(True, which='minor', linestyle=':', linewidth=0.4)

            fn_out = f"benches/plot_fig/fig/ndc_vs_rderr_{dataset}.pdf"
            print("📷 Picture saved to", fn_out)
            plt.savefig(fn_out, bbox_inches="tight", dpi=300)
            plt.show()