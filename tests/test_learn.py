import numpy as np
import matplotlib.pyplot as plt
import umap
import struct
from tqdm import tqdm

def read_fvecs(filename):
    print(f"Loading {filename} ...")
    with open(filename, 'rb') as f:
        data = f.read()
        vectors = []
        pos = 0
        while pos < len(data):
            d = struct.unpack('i', data[pos:pos + 4])[0]  # 读取维度
            pos += 4
            vector = np.frombuffer(data[pos:pos + d * 4], dtype=np.float32)  # 读取向量数据
            pos += d * 4
            vectors.append(vector)
        print(f"Loaded {len(vectors)} vectors from {filename}")
        return np.array(vectors)

# 使用
vectors = read_fvecs('benches/datasets/SIFT100K/sift_learn_filtered.fvecs')
print('读取完成，形状:', vectors.shape)


# UMAP降维
reducer = umap.UMAP(random_state=42)
embedding = reducer.fit_transform(vectors)

# 计算每个点的密度
kde = KernelDensity(bandwidth=0.5)
kde.fit(embedding)
log_density = kde.score_samples(embedding)
density = np.exp(log_density)

# 绘制带密度着色的散点图
plt.figure(figsize=(10, 8))
sns.scatterplot(x=embedding[:, 0], y=embedding[:, 1], hue=density, palette='viridis', s=5, linewidth=0)
plt.title('UMAP Projection of Learning Vectors with Density Coloring')
plt.xlabel('UMAP Dimension 1')
plt.ylabel('UMAP Dimension 2')
plt.legend(title="Density")
plt.colorbar(plt.cm.ScalarMappable(cmap='viridis'), label='Density')
plt.grid(True)
plt.savefig("tests/base_umap_visualization.png", dpi=300)
plt.tight_layout()
plt.show()
