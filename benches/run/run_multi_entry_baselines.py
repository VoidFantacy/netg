#!/usr/bin/env python3
"""
Multi-Entry Baselines 补充实验（极简版）
堵审稿人嘴：证明简单多起点策略不如 NETG

Baseline A: Random-3-Start（随机 3 个点）
Baseline B: K-Means-800 无投影（几何最优 800 hub，L2 路由）

对比: NSG Medoid / NETG Full
"""

import os, sys, json, struct, time
import numpy as np
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
SETTINGS_PATH = os.path.join(PROJECT_ROOT, "benches/datasets/settings.json")
DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]


def get_fvecs_meta(path):
    with open(path, 'rb') as f:
        dim = struct.unpack('i', f.read(4))[0]
    vec_size = 4 + 4 * dim
    n = os.path.getsize(path) // vec_size
    return n, dim, vec_size


def read_vecs_by_ids(path, ids, dim, vec_size):
    vecs = np.empty((len(ids), dim), dtype=np.float32)
    with open(path, 'rb') as f:
        for i, gid in enumerate(ids):
            f.seek(int(gid) * vec_size + 4)
            vecs[i] = np.fromfile(f, dtype=np.float32, count=dim)
    return vecs


def get_base_path(dataset):
    with open(SETTINGS_PATH) as f:
        s = json.load(f)
    ds = s["datasets"][dataset]
    root = s.get("root_dir", "./benches/datasets")
    if root.startswith("./"):
        root = os.path.join(PROJECT_ROOT, root[2:])
    return os.path.join(root, ds["dataset_dir"], ds["base_path"])


def save_bins(vecs, ids, out_dir, prefix):
    os.makedirs(out_dir, exist_ok=True)
    hp = os.path.join(out_dir, f"{prefix}_hubs.bin")
    ip = os.path.join(out_dir, f"{prefix}_hub_ids.bin")
    vecs.astype(np.float32).tofile(hp)
    np.array(ids, dtype=np.int32).tofile(ip)
    return hp, ip


def gen_random_hubs(dataset, base_path, k=3):
    """随机 K 个入口"""
    n, dim, vs = get_fvecs_meta(base_path)
    rng = np.random.default_rng(42)
    ids = sorted(rng.choice(n, size=k, replace=False).tolist())
    vecs = read_vecs_by_ids(base_path, ids, dim, vs)
    out_dir = os.path.join(PROJECT_ROOT, f"multi_entry_baselines/{dataset}_results")
    return save_bins(vecs, ids, out_dir, f"random{k}")


def kmeans_numpy(data, k, niter=20, seed=42):
    """纯 numpy K-Means (无 faiss/sklearn 依赖)"""
    rng = np.random.default_rng(seed)
    n, d = data.shape
    # K-Means++ 初始化
    centers = np.empty((k, d), dtype=np.float32)
    centers[0] = data[rng.integers(n)]
    for i in range(1, k):
        # 计算到最近 center 的距离
        dists = batch_min_dist(data, centers[:i])
        dists = np.maximum(dists, 0)  # 修复浮点误差导致的微小负值
        total = dists.sum()
        if total == 0:
            centers[i] = data[rng.integers(n)]
        else:
            probs = dists / total
            centers[i] = data[rng.choice(n, p=probs)]
        if (i + 1) % 100 == 0:
            print(f"      init {i+1}/{k}")
    
    # 迭代
    for it in range(niter):
        # 分配：批量计算避免 OOM
        labels = batch_assign(data, centers)
        # 更新
        new_centers = np.zeros_like(centers)
        counts = np.zeros(k, dtype=np.int64)
        for i in range(k):
            mask = labels == i
            c = mask.sum()
            if c > 0:
                new_centers[i] = data[mask].mean(axis=0)
                counts[i] = c
            else:
                new_centers[i] = centers[i]
        centers = new_centers
        if (it + 1) % 5 == 0:
            print(f"      iter {it+1}/{niter}")
    return centers


def batch_min_dist(data, centers):
    """分批计算每个点到最近 center 的距离（避免 OOM）"""
    n = len(data)
    min_d = np.full(n, np.inf, dtype=np.float32)
    batch = 10000
    for i in range(0, n, batch):
        chunk = data[i:i+batch]
        # chunk: [B, D], centers: [K, D]
        # 用广播: ||a-b||^2 = ||a||^2 + ||b||^2 - 2*a.b
        a2 = np.sum(chunk ** 2, axis=1, keepdims=True)  # [B,1]
        b2 = np.sum(centers ** 2, axis=1, keepdims=True).T  # [1,K]
        ab = chunk @ centers.T  # [B,K]
        dists = a2 + b2 - 2 * ab  # [B,K]
        min_d[i:i+batch] = dists.min(axis=1)
    return min_d


def batch_assign(data, centers):
    """分批分配标签"""
    n = len(data)
    k = len(centers)
    labels = np.empty(n, dtype=np.int32)
    batch = 10000
    b2 = np.sum(centers ** 2, axis=1)  # [K]
    for i in range(0, n, batch):
        chunk = data[i:i+batch]
        a2 = np.sum(chunk ** 2, axis=1, keepdims=True)  # [B,1]
        ab = chunk @ centers.T  # [B,K]
        dists = a2 + b2[None, :] - 2 * ab
        labels[i:i+batch] = dists.argmin(axis=1)
    return labels


def gen_kmeans_hubs(dataset, base_path, k=800, sample_n=500000):
    """K-Means 几何聚类 → medoid（纯 numpy，无外部依赖）"""
    n, dim, vs = get_fvecs_meta(base_path)
    
    # 子采样
    rng = np.random.default_rng(123)
    sample_n = min(sample_n, n)
    sample_idx = np.sort(rng.choice(n, size=sample_n, replace=False))
    print(f"   读取 {sample_n} 条子采样...")
    sample_vecs = read_vecs_by_ids(base_path, sample_idx, dim, vs)
    
    # K-Means
    print(f"   K-Means k={k}, 20 iter...")
    centroids = kmeans_numpy(sample_vecs, k, niter=20, seed=42)
    
    # 找每个 centroid 最近的实际向量 (medoid)
    print(f"   找 medoid...")
    # centroids: [K, D], sample_vecs: [N, D]
    c2 = np.sum(centroids ** 2, axis=1, keepdims=True)  # [K,1]
    best_ids = np.full(k, -1, dtype=np.int64)
    best_dists = np.full(k, np.inf, dtype=np.float32)
    batch = 50000
    for i in range(0, sample_n, batch):
        chunk = sample_vecs[i:i+batch]
        a2 = np.sum(chunk ** 2, axis=1, keepdims=True)  # [B,1]
        ab = chunk @ centroids.T  # [B,K]
        dists = a2 + c2.T - 2 * ab  # [B,K]
        local_min_idx = dists.argmin(axis=0)  # [K] - 每列最小行
        local_min_dist = dists.min(axis=0)    # [K]
        improved = local_min_dist < best_dists
        best_dists[improved] = local_min_dist[improved]
        best_ids[improved] = local_min_idx[improved] + i
    
    # 映射回全局 ID + 去重
    hub_ids = list(dict.fromkeys(sample_idx[best_ids].tolist()))
    print(f"   hub 数: {len(hub_ids)}")
    
    hub_vecs = read_vecs_by_ids(base_path, hub_ids, dim, vs)
    out_dir = os.path.join(PROJECT_ROOT, f"multi_entry_baselines/{dataset}_results")
    return save_bins(hub_vecs, hub_ids, out_dir, "kmeans800")


def run_bench(dataset, hubs_path, ids_path, name):
    """调用 C++ test"""
    exe = os.path.join(PROJECT_ROOT, "build/benches/test")
    acpg = os.path.join(PROJECT_ROOT, f"acpg/{dataset}_index/acpg_nsg.json")
    out_dir = os.path.join(PROJECT_ROOT, f"multi_entry_baselines/{dataset}_results")
    os.makedirs(out_dir, exist_ok=True)
    result = os.path.join(out_dir, f"{name}.json")
    
    cmd = [exe, "--dataset", dataset, "--acpg_file", acpg,
           "--fn_result", result, "--test_scope", "routing",
           "--num_runs", "3", "--R", "32",
           "--search_Ls", "32,64,128,200",
           "--raw_hubs", hubs_path, "--transformed_ids", ids_path]
    
    print(f"   跑 {name}...")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, cwd=PROJECT_ROOT)
    if proc.returncode != 0:
        print(f"   ❌ 失败: {proc.stderr[:200]}")
        return None
    print(f"   ✅ {result}")
    return result


def main():
    print("=" * 50)
    print("Multi-Entry Baselines 补充实验")
    print("=" * 50)
    
    for dataset in DATASETS:
        print(f"\n>>> {dataset}")
        base_path = get_base_path(dataset)
        if not os.path.exists(base_path):
            print(f"   跳过: base 不存在"); continue
        
        # Baseline A: Random-3-Start
        hp, ip = gen_random_hubs(dataset, base_path, k=3)
        run_bench(dataset, hp, ip, "random3")
        
        # Baseline B: K-Means-800
        hp, ip = gen_kmeans_hubs(dataset, base_path, k=800)
        run_bench(dataset, hp, ip, "kmeans800")
    
    # 打印汇总
    print(f"\n\n{'='*50}")
    print("📊 结果汇总 (L=64)")
    print(f"{'='*50}")
    print(f"{'Dataset':<18} {'Random-3':<12} {'KMeans-800':<12}")
    
    for dataset in DATASETS:
        row = f"{dataset:<18}"
        for name in ["random3", "kmeans800"]:
            rf = os.path.join(PROJECT_ROOT, f"multi_entry_baselines/{dataset}_results/{name}.json")
            if os.path.exists(rf):
                with open(rf) as f:
                    data = json.load(f)
                for r in data.get("results", []):
                    for p in r.get("performance", []):
                        if p["search_L"] == 64:
                            row += f"{p['recall']:.4f}      "
                            break
                    break
            else:
                row += "N/A         "
        print(row)


if __name__ == "__main__":
    main()
