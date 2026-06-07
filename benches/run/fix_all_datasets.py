import os
import shutil
import struct
import numpy as np
import time

# 尝试导入 faiss
try:
    import faiss
    HAS_FAISS = True
    print("✅ Faiss detected (CPU/GPU). Generation will be FAST.")
except ImportError:
    HAS_FAISS = False
    from sklearn.neighbors import NearestNeighbors
    print("⚠️ Faiss not found. Using Scikit-Learn. (Running 'pip install faiss-cpu' is highly recommended!)")

# ================== 配置路径 ==================
# 假设脚本在项目根目录运行
ROOT = "benches/datasets"

TASKS = [
    # 1. Deep10M: 需要重算子集 GT
    {
        "name": "deep10M",
        "base": f"{ROOT}/DEEP10M/base.10M.fvecs",
        "query": f"{ROOT}/DEEP10M/query.public.10K.fvecs",
        "out_gt": f"{ROOT}/DEEP10M/groundtruth_10M_subset.ivecs", # 新文件名
        "k": 100
    },
    # 2. Yandex: 需要重算子集 GT
    {
        "name": "yandex_t2i",
        "base": f"{ROOT}/YandexT2I/base.10M.fvecs",
        "query": f"{ROOT}/YandexT2I/query.public.100K.fvecs",
        "out_gt": f"{ROOT}/YandexT2I/groundtruth_10M_subset.ivecs", # 新文件名
        "k": 100
    },
    # 3. SIFT10M: 缺失 GT，需要生成
    {
        "name": "sift10M",
        "base": f"{ROOT}/SIFT10M/sift_base.fvecs",
        "query": f"{ROOT}/SIFT10M/sift_query.fvecs",
        "out_gt": f"{ROOT}/SIFT10M/sift_groundtruth.ivecs", # 补全原名
        "k": 100
    }
]

# 4. SIFT10M_Skewed 的特殊补全逻辑
SKEWED_TASK = {
    "src_query": f"{ROOT}/SIFT10M/sift_query.fvecs",
    "dst_query": f"{ROOT}/SIFT10M/sift_skewed_query.fvecs",
    "src_gt": f"{ROOT}/SIFT10M/sift_groundtruth.ivecs",
    "dst_gt": f"{ROOT}/SIFT10M/sift_skewed_groundtruth.ivecs"
}
# ============================================

def read_fvecs(filename):
    print(f"   -> Reading {os.path.basename(filename)}...")
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
        
    file_size = os.path.getsize(filename)
    with open(filename, 'rb') as f:
        d_bytes = f.read(4)
        d = struct.unpack('i', d_bytes)[0]
    
    vec_size = 4 + d * 4
    n = file_size // vec_size
    
    # 使用 memmap 模式读取，防止内存爆炸
    x = np.memmap(filename, dtype='float32', mode='r', shape=(n, d + 1))
    # 返回连续内存数组 (去掉第一列维度)
    return np.ascontiguousarray(x[:, 1:])

def write_ivecs(filename, data):
    print(f"   -> Saving GT to {os.path.basename(filename)}...")
    n, k = data.shape
    with open(filename, 'wb') as f:
        for i in range(n):
            f.write(struct.pack('i', k))
            f.write(data[i].astype('int32').tobytes())

def compute_gt(base_path, query_path, out_path, k=100):
    if os.path.exists(out_path):
        # 简单检查一下文件大小是否合理，防止重复计算
        print(f"   ⏩ GT exists: {os.path.basename(out_path)}, checking validity...")
        if os.path.getsize(out_path) > 0:
            print("      File seems valid. Skipping generation.")
            return
        print("      File empty. Regenerating...")

    print(f"   ⚡ Computing GT for {os.path.basename(base_path)}...")
    
    # 1. Load Data
    t0 = time.time()
    xb = read_fvecs(base_path)
    xq = read_fvecs(query_path)
    d = xb.shape[1]
    
    # 2. Search
    print(f"      Base: {xb.shape}, Query: {xq.shape}")
    t1 = time.time()
    
    if HAS_FAISS:
        index = faiss.IndexFlatL2(d)
        index.add(xb)
        _, I = index.search(xq, k)
    else:
        # Fallback
        nbrs = NearestNeighbors(n_neighbors=k, algorithm='brute', metric='l2', n_jobs=-1)
        nbrs.fit(xb)
        _, I = nbrs.kneighbors(xq)
        
    print(f"      Search done in {time.time()-t1:.2f}s")
    
    # 3. Save
    write_ivecs(out_path, I)
    print(f"   ✅ Saved {os.path.basename(out_path)}")

def fix_skewed_dataset():
    print(f"\n🔧 Patching sift10M_skewed...")
    # 如果没有 skewed query，就复制标准的过来先跑通
    if not os.path.exists(SKEWED_TASK["dst_query"]):
        if os.path.exists(SKEWED_TASK["src_query"]):
            print(f"   -> Copying standard Query to {os.path.basename(SKEWED_TASK['dst_query'])}")
            shutil.copy(SKEWED_TASK["src_query"], SKEWED_TASK["dst_query"])
        else:
            print("   ❌ Cannot patch: Standard SIFT query also missing!")
            return

    # 复制 GT (既然 Query 一样，GT 也一样)
    if not os.path.exists(SKEWED_TASK["dst_gt"]):
         if os.path.exists(SKEWED_TASK["src_gt"]):
            print(f"   -> Copying generated GT to {os.path.basename(SKEWED_TASK['dst_gt'])}")
            shutil.copy(SKEWED_TASK["src_gt"], SKEWED_TASK["dst_gt"])
    print("   ✅ sift10M_skewed is now ready (using standard data).")

def main():
    print(f"🚀 Starting Comprehensive Dataset Repair...\n")
    
    # 1. 处理所有主要数据集的 GT
    for task in TASKS:
        print(f"📦 Dataset: {task['name']}")
        try:
            compute_gt(task['base'], task['query'], task['out_gt'], task['k'])
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print("-" * 50)

    # 2. 修复 Skewed 数据集
    try:
        fix_skewed_dataset()
    except Exception as e:
        print(f"   ❌ Error patching skewed: {e}")

    print("\n🎉 All done! Now update your settings.json.")

if __name__ == "__main__":
    main()