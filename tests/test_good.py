import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import CountVectorizer
import umap

# 1. 读取数据
df = pd.read_csv("tests/(sample)sam_tianchi_mum_baby_trade_history.csv", sep=",")

# 2. 确保 property 列存在
print("列名：", df.columns)

# 3. 处理缺失值
df['property'] = df['property'].fillna('')

# 4. 解析 property 字段
df['property_tokens'] = df['property'].astype(str).apply(lambda x: x.replace(";", " ").replace(":", "_"))

# 5. 使用 CountVectorizer 向量化
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(df['property_tokens'])

# 6. UMAP 降维
reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, metric='cosine', random_state=42)
embedding = reducer.fit_transform(X)

# 7. 添加坐标到原始数据
df['x'] = embedding[:, 0]
df['y'] = embedding[:, 1]

# 8. 可视化
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='x', y='y', hue='cat1', palette='tab20', legend=False, s=30)
plt.title("Visualization of User Click Behavior Attribute Embeddings (UMAP)", fontsize=14)
plt.xlabel("UMAP-1")
plt.ylabel("UMAP-2")
plt.grid(True)
plt.tight_layout()
plt.savefig("tests/umap_visualization.pdf", dpi=300)
plt.show()