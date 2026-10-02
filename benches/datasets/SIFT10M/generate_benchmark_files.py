import numpy as np
import faiss
import shutil

# ---------------------- 修复：正确读写fvecs/ivecs格式 ----------------------
def read_fvecs(file_path):
    """正确读取.fvecs格式：维度是int32，向量数据是float32"""
    with open(file_path, 'rb') as f:
        import os
        file_size = os.path.getsize(file_path)
        
        dim = np.fromfile(f, dtype=np.int32, count=1)[0]
        if dim <= 0:
            raise ValueError(f"无效的维度值：{dim}，文件可能损坏或格式错误")
        
        vec_size_bytes = 4 + 4 * dim
        n_vecs = file_size // vec_size_bytes
        
        f.seek(0)
        data = np.fromfile(f, dtype=np.uint8)
        
        vecs = []
        for i in range(n_vecs):
            start = i * vec_size_bytes + 4
            end = start + 4 * dim
            vec = data[start:end].view(np.float32)
            vecs.append(vec)
        
        return np.array(vecs, dtype=np.float32)

def write_fvecs(file_path, vecs):
    """写入.fvecs格式"""
    dim = vecs.shape[1]
    n_vecs = vecs.shape[0]
    with open(file_path, 'wb') as f:
        for i in range(n_vecs):
            f.write(np.array([dim], dtype=np.int32).tobytes())
            f.write(vecs[i].astype(np.float32).tobytes())

def write_ivecs(file_path, vecs):
    """写入.ivecs格式"""
    dim = vecs.shape[1]
    n_vecs = vecs.shape[0]
    with open(file_path, 'wb') as f:
        for i in range(n_vecs):
            f.write(np.array([dim], dtype=np.int32).tobytes())
            f.write(vecs[i].astype(np.int32).tobytes())


# ---------------------- 生成流程：查询集随机取样 ----------------------
try:
    # 1. 读取基础数据库
    base_path = "sift10m_base.fvecs"
    base = read_fvecs(base_path)
    n_samples, dim = base.shape
    print(f"基础数据库规模：{n_samples}条，{dim}维（正确解析）")

    # 2. 生成训练集（sift_learn.fvecs）：前200万条（连续取，也可改为随机，视需求）
    learn_size = 2000000    
    if learn_size > n_samples:
        learn_size = n_samples  
    learn = base[:learn_size]
    write_fvecs("sift_learn.fvecs", learn)
    print("已生成 sift_learn.fvecs")

    # 3. 生成查询集（sift_query.fvecs）：随机无放回取样，且不与训练集重叠
    query_size = 5000  
    # 生成不与训练集重叠的随机索引
    all_indices = np.arange(n_samples)
    train_indices = all_indices[:learn_size]
    remaining_indices = all_indices[learn_size:]  # 排除训练集
    # 从剩余索引中随机选query_size个
    np.random.seed(42)  # 设置随机种子，保证结果可复现
    query_indices = np.random.choice(remaining_indices, size=query_size, replace=False)
    query = base[query_indices]
    write_fvecs("sift_query.fvecs", query)
    print("已生成 sift_query.fvecs（随机取样，与训练集无重叠）")

    # 4. 生成真实最近邻标签（sift_groundtruth_100k.ivecs）
    k = 100  
    index = faiss.IndexFlatL2(dim)  
    index.add(base)
    _, groundtruth = index.search(query, k)
    write_ivecs("sift_groundtruth_100k.ivecs", groundtruth)
    print("已生成 sift_groundtruth_100k.ivecs")

    # 5. 生成训练集的最近邻标签（train_gt.ivecs）
    index_learn = faiss.IndexFlatL2(dim)
    index_learn.add(learn)
    _, train_gt = index_learn.search(learn, 1)  
    write_ivecs("train_gt.ivecs", train_gt)
    print("已生成 train_gt.ivecs")

    # 6. 复制基础数据库文件
    shutil.copyfile("sift10m_base.fvecs", "sift_base.fvecs")
    print("已生成 sift_base.fvecs")

except Exception as e:
    print(f"错误：{e}")
    print("请检查'sift10m_base.fvecs'是否存在且格式正确（应为128维SIFT特征）")