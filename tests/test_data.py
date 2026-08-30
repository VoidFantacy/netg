import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import CountVectorizer
import umap

# 1. 读取数据（假设你已经加载成 pandas DataFrame）
df = pd.read_csv("C:/Users/15876/Downloads.csv", sep="\t")  # 或者换成你读取的方式

# 2. 解析 property 字段为多值（类似“词袋模型”处理）
df['property_tokens'] = df['property'].astype(str).apply(lambda x: x.replace(";", " ").replace(":", "_"))

# 3. 使用 CountVectorizer 生成稀疏向量（每条点击记录 = 一个向量）
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(df['property_tokens'])

# 4. UMAP 降维（保持局部结构）
reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, metric='cosine', random_state=42)
embedding = reducer.fit_transform(X)

# 5. 添加到原始数据
df['x'] = embedding[:, 0]
df['y'] = embedding[:, 1]

# 6. 可视化（按 cat1 或 user_id 聚类观察聚集性）
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='x', y='y', hue='cat1', palette='tab20', legend=False, s=30)
plt.title("用户点击行为属性嵌入可视化 (UMAP)", fontsize=14)
plt.xlabel("UMAP-1")
plt.ylabel("UMAP-2")
plt.grid(True)
plt.tight_layout()
plt.show()
