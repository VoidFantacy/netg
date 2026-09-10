import matplotlib.pyplot as plt
import os
import numpy as np

# 第一组数据
data1 = [
    {"L": 1, "NDC": 3265887, "mean_rdrr": 0.0172265},
    {"L": 2, "NDC": 3265887, "mean_rdrr": 0.0172265},
    {"L": 4, "NDC": 3265887, "mean_rdrr": 0.0172265},
    {"L": 8, "NDC": 3265887, "mean_rdrr": 0.0172265},
    {"L": 16, "NDC": 4173947, "mean_rdrr": 0.00732222},
    {"L": 32, "NDC": 6421348, "mean_rdrr": 0.00244759},
    {"L": 64, "NDC": 10486012, "mean_rdrr": 0.000699466},
    {"L": 128, "NDC": 17579410, "mean_rdrr": 0.000164958},
    {"L": 256, "NDC": 29771296, "mean_rdrr": 3.94002e-05},
    {"L": 512, "NDC": 50366954, "mean_rdrr": 1.02357e-05},
    {"L": 1024, "NDC": 85012718, "mean_rdrr": 2.75617e-06}
]

# 第二组数据
data2 = [
    {"L": 1, "NDC": 3544338, "mean_rdrr": 0.0175832},
    {"L": 2, "NDC": 3544338, "mean_rdrr": 0.0175832},
    {"L": 4, "NDC": 3544338, "mean_rdrr": 0.0175832},
    {"L": 8, "NDC": 3544338, "mean_rdrr": 0.0175832},
    {"L": 16, "NDC": 4456925, "mean_rdrr": 0.00761678},
    {"L": 32, "NDC": 6700713, "mean_rdrr": 0.00245805},
    {"L": 64, "NDC": 10316327, "mean_rdrr": 0.000790567},
    {"L": 128, "NDC": 17329630, "mean_rdrr": 0.000166199},
    {"L": 256, "NDC": 29549163, "mean_rdrr": 3.91991e-05},
    {"L": 512, "NDC": 50409205, "mean_rdrr": 1.02357e-05},
    {"L": 1024, "NDC": 85572003, "mean_rdrr": 2.75617e-06}
]

# 提取 L 值
L_values = sorted(set([item["L"] for item in data1 + data2]))

# 设置条形宽度
bar_width = 0.35

# 设置 X 轴位置
index1 = np.arange(len(L_values))
index2 = [i + bar_width for i in index1]

# 提取第一组数据的 NDC 和 mean_rdrr
NDC1 = [item["NDC"] for item in data1]
mean_rdrr1 = [item["mean_rdrr"] for item in data1]

# 提取第二组数据的 NDC 和 mean_rdrr
NDC2 = [item["NDC"] for item in data2]
mean_rdrr2 = [item["mean_rdrr"] for item in data2]


# 设置图片清晰度
plt.rcParams['figure.dpi'] = 300
# 设置图形大小
plt.figure(figsize=(10, 6))

# 绘制调整后的第一组数据的 NDC 条形图
plt.bar(index1, adjusted_NDC1, width=bar_width, label='Data1 NDC', color='skyblue')
# 绘制第二组数据的 NDC 条形图
plt.bar(index2, NDC2, width=bar_width, label='Data2 NDC', color='lightcoral')

# 添加 X 轴标签
plt.xticks([i + bar_width / 2 for i in index1], L_values)
plt.xlabel('L')
plt.ylabel('NDC')
plt.title('Comparison of NDC for Two Datasets (Scaled Difference)')
plt.legend()
plt.show()

os.makedirs("results/fig", exist_ok=True)

# 保存图片
fn_out = f"results/fig/test1.png"
print("📷 Picture saved to", fn_out)
plt.savefig(fn_out, bbox_inches="tight", dpi=300)

# 重新设置图形
plt.figure(figsize=(10, 6))

# 绘制调整后的第一组数据的 mean_rdrr 条形图
plt.bar(index1, adjusted_mean_rdrr1, width=bar_width, label='Data1 mean_rdrr', color='lightgreen')
# 绘制第二组数据的 mean_rdrr 条形图
plt.bar(index2, mean_rdrr2, width=bar_width, label='Data2 mean_rdrr', color='lightpink')

# 添加 X 轴标签
plt.xticks([i + bar_width / 2 for i in index1], L_values)
plt.xlabel('L')
plt.ylabel('mean_rdrr')
plt.title('Comparison of mean_rdrr for Two Datasets (Scaled Difference)')
plt.legend()
plt.show()

os.makedirs("results/fig", exist_ok=True)

# 保存图片
fn_out = f"results/fig/test.png"
print("📷 Picture saved to", fn_out)
plt.savefig(fn_out, bbox_inches="tight", dpi=300)