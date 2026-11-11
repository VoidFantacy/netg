"""
cluster/kmeans.py
实现论文 Algorithm 2: Hierarchical Balanced K-Means (HBKM)

论文核心逻辑:
  l_max = ceil(log_k(n_c))
  每一层对所有当前叶子簇各自执行 balanced K-Means(k 分支):
    分配准则: j* = argmin_j { ||x - μ_ij||² + λ * (|C_ij| - |C_i|/k)² }
  最终叶子簇数量 = k^l_max (≥ n_c，超出时截取前 n_c 个最大簇)

Definition 3 (Hub Nodes):
  对每个叶子簇 C_i，选择距质心最近的点作为 Hub: V_i = argmin_{x∈C_i} ||x - μ_i||²
"""

import argparse
import math
import struct
import numpy as np
from tqdm import tqdm


# ==================== IO ====================

def read_fvecs(filename):
    with open(filename, 'rb') as f:
        d = struct.unpack('i', f.read(4))[0]
        f.seek(0, 2)
        n = f.tell() // (4 + 4 * d)
        f.seek(0)
        x = np.zeros((n, d), dtype=np.float32)
        for i in range(n):
            f.read(4)
            x[i] = np.frombuffer(f.read(d * 4), dtype=np.float32)
    return x


def write_fvecs(filename, data):
    print(f"Writing {data.shape[0]} vectors (dim={data.shape[1]}) to {filename}...")
    with open(filename, 'wb') as f:
        d = data.shape[1]
        vec_d = np.array([d], dtype=np.int32)
        for vec in data:
            f.write(vec_d.tobytes())
            f.write(vec.astype(np.float32).tobytes())


# ==================== HBKM Core ====================

def _init_centroids_kmeanspp(X, k, rng, max_sample=50000):
    """
    K-Means++ 初始化。对大型子簇随机采样 max_sample 个点加速初始化。
    """
    N = len(X)
    if N <= k:
        return X.copy()

    # 大簇时采样加速距离计算
    if N > max_sample:
        sample_idx = rng.choice(N, max_sample, replace=False)
        X_s = X[sample_idx]
    else:
        X_s = X

    n_s = len(X_s)
    first = rng.integers(0, n_s)
    centroids = [X_s[first].copy()]

    for _ in range(1, k):
        # 计算每个采样点到已有质心集合的最小平方距离
        min_dists = np.full(n_s, np.inf, dtype=np.float64)
        c = centroids[-1]
        diff = X_s - c
        d2 = np.einsum('ij,ij->i', diff, diff).astype(np.float64)
        min_dists = np.minimum(min_dists, d2)
        for prev_c in centroids[:-1]:
            diff2 = X_s - prev_c
            d2_prev = np.einsum('ij,ij->i', diff2, diff2).astype(np.float64)
            min_dists = np.minimum(min_dists, d2_prev)

        probs = min_dists / (min_dists.sum() + 1e-12)
        chosen = rng.choice(n_s, p=probs)
        centroids.append(X_s[chosen].copy())

    return np.array(centroids, dtype=np.float32)


def _assign_balanced(X, centroids, lambda_penalty, sizes, target, batch_size=65536):
    """
    带均衡惩罚的批量分配（论文 penalty 项的批量近似版本）。

    分配准则（批量近似）:
        j* = argmin_j { ||x - μ_j||² + λ * (|C_j| - target)² }
    其中 sizes 使用上一次迭代的结果（批量近似 vs. 论文在线顺序更新）。

    Returns: new_labels [N,]
    """
    N, D = X.shape
    k = len(centroids)

    del sizes, target, batch_size
    # Algorithm 2 assigns points sequentially while cluster sizes change. A
    # stale-size batched penalty oscillates catastrophically at million scale.
    # We use the standard balanced optimal-transport relaxation instead: rows
    # (clusters) and columns (points) are normalized with Sinkhorn, then the
    # highest balanced responsibility becomes the hard assignment.
    c_sq = np.einsum('kd,kd->k', centroids, centroids)
    responsibilities = 2.0 * (X @ centroids.T) - c_sq[None, :]
    epsilon = max(2.0 * lambda_penalty, 0.005)
    responsibilities /= epsilon
    responsibilities -= responsibilities.max(axis=1, keepdims=True)
    np.exp(responsibilities, out=responsibilities)
    responsibilities = responsibilities.T                       # [k, N]
    responsibilities /= np.maximum(responsibilities.sum(), 1e-30)
    for _ in range(10):
        responsibilities /= np.maximum(responsibilities.sum(axis=1, keepdims=True), 1e-30)
        responsibilities /= k
        responsibilities /= np.maximum(responsibilities.sum(axis=0, keepdims=True), 1e-30)
        responsibilities /= N
    return np.argmax(responsibilities, axis=0).astype(np.int32)


def _balanced_kmeans_single(X, k, lambda_penalty, max_iters, rng):
    """
    单层 Balanced K-Means（HBKM 的基本单元）。
    对子簇 X 划分为 k 个均衡子簇，返回 (labels [N,], centroids [k, D])。
    """
    N, D = X.shape
    if N <= k:
        # 点数不够，每个点自成一簇
        labels = np.arange(N, dtype=np.int32)
        return labels, X.copy()

    target = N / k
    centroids = _init_centroids_kmeanspp(X, k, rng)             # [k, D]
    sizes  = np.full(k, target, dtype=np.float64)               # 初始假设均衡
    labels = np.full(N, -1, dtype=np.int32)

    for t in range(max_iters):
        new_labels = _assign_balanced(X, centroids, lambda_penalty, sizes, target)

        # 更新质心与簇大小
        new_centroids = np.zeros((k, D), dtype=np.float32)
        new_sizes     = np.zeros(k, dtype=np.float64)

        for j in range(k):
            mask = new_labels == j
            cnt  = int(mask.sum())
            new_sizes[j] = cnt
            if cnt > 0:
                new_centroids[j] = X[mask].mean(axis=0)
            else:
                # 空簇：重新随机初始化到一个远点
                new_centroids[j] = X[rng.integers(0, N)]

        if np.array_equal(new_labels, labels):
            break  # 已收敛

        labels    = new_labels
        sizes     = new_sizes
        centroids = new_centroids

    nonempty = np.unique(labels).size
    if nonempty != k:
        raise RuntimeError(f"balanced k-means collapsed: {nonempty}/{k} non-empty clusters")
    return labels, centroids


def hbkm(X, k_branch, n_c, lambda_penalty=0.01, max_iters=20, random_seed=42):
    """
    Algorithm 2 (GATE 论文): Hierarchical Balanced K-Means

    Args:
        X            : [N, D] float32 数据集
        k_branch     : 每层分支数（branching factor k）
        n_c          : 目标叶子簇数量
        lambda_penalty: 均衡惩罚系数 λ
        max_iters    : 每层 K-Means 最大迭代次数 T
        random_seed  : 随机种子

    Returns:
        cluster_indices: list of n_c 个 np.ndarray，每个是该簇内点在 X 中的索引
    """
    rng   = np.random.default_rng(random_seed)
    l_max = math.ceil(math.log(n_c) / math.log(k_branch))

    print(f"[HBKM] n_c={n_c}, k_branch={k_branch}, l_max={l_max}, λ={lambda_penalty}, T={max_iters}")
    print(f"[HBKM] Expected leaf clusters after hierarchy: {k_branch}^{l_max} = {k_branch**l_max}")

    # 初始：整个数据集为一个簇
    cluster_indices = [np.arange(len(X), dtype=np.int64)]

    for level in range(l_max):
        print(f"\n[HBKM] ── Level {level + 1}/{l_max}: splitting {len(cluster_indices)} cluster(s) ──")
        new_cluster_indices = []

        for cidx in tqdm(cluster_indices, desc=f"Level {level + 1}"):
            sub_X = X[cidx]                                      # 子簇向量
            N_sub = len(sub_X)

            if N_sub == 0:
                continue
            if N_sub <= k_branch:
                # 子簇太小，每个点直接作为一个叶子
                for i in range(N_sub):
                    new_cluster_indices.append(cidx[[i]])
                continue

            labels, _ = _balanced_kmeans_single(sub_X, k_branch, lambda_penalty, max_iters, rng)

            for j in range(k_branch):
                mask = labels == j
                if mask.sum() > 0:
                    new_cluster_indices.append(cidx[mask])

        cluster_indices = new_cluster_indices
        print(f"[HBKM] After level {level + 1}: {len(cluster_indices)} clusters")

    # 若叶子数超过 n_c（k^l_max > n_c 时），取最大的 n_c 个簇
    if len(cluster_indices) > n_c:
        cluster_indices.sort(key=lambda c: -len(c))
        cluster_indices = cluster_indices[:n_c]
        print(f"[HBKM] Trimmed to {n_c} largest clusters.")

    print(f"\n[HBKM] ✅ Done. Final cluster count: {len(cluster_indices)}")
    sizes = [len(c) for c in cluster_indices]
    print(f"[HBKM] Cluster sizes — min: {min(sizes)}, max: {max(sizes)}, "
          f"mean: {np.mean(sizes):.1f}, std: {np.std(sizes):.1f}")

    return cluster_indices


def hbkm_two_level(X, k1, k2, lambda_penalty=0.01, max_iters=20, random_seed=42):
    """
    两层 HBKM（论文 Algorithm 2 的精确实现）：
      Level-1: 将整个数据集分成 k1 个粗粒度簇
      Level-2: 将每个 Level-1 簇继续分成 k2 个细粒度簇
      最终叶子簇数量 = k1 × k2

    与通用 hbkm() 的区别：
      通用版本用同一个 k_branch 递归分裂，层数自动计算；
      本函数严格按照两层结构，Level-1 用 k1 分支，Level-2 用 k2 分支。
    """
    rng = np.random.default_rng(random_seed)
    n_c = k1 * k2

    print(f"[HBKM-2L] Two-level mode: k1={k1}, k2={k2}, total clusters={n_c}")
    print(f"[HBKM-2L] λ={lambda_penalty}, T={max_iters}")

    # ── Level 1: 全局分为 k1 个粗簇 ──
    print(f"\n[HBKM-2L] ── Level 1: Splitting into {k1} coarse clusters ──")
    labels_l1, centroids_l1 = _balanced_kmeans_single(X, k1, lambda_penalty, max_iters, rng)

    # 统计 Level-1 簇大小
    l1_sizes = [int((labels_l1 == i).sum()) for i in range(k1)]
    print(f"[HBKM-2L] Level 1 done. Cluster sizes — min: {min(l1_sizes)}, "
          f"max: {max(l1_sizes)}, mean: {np.mean(l1_sizes):.1f}")

    # ── Level 2: 对每个 Level-1 簇再分为 k2 个子簇 ──
    print(f"\n[HBKM-2L] ── Level 2: Splitting each coarse cluster into {k2} fine clusters ──")
    cluster_indices = []

    for i in tqdm(range(k1), desc="Level 2"):
        indices_i = np.where(labels_l1 == i)[0]
        n_sub = len(indices_i)

        if n_sub == 0:
            continue
        if n_sub <= k2:
            # 簇太小，每个点自成一簇
            for idx in indices_i:
                cluster_indices.append(np.array([idx], dtype=np.int64))
            continue

        sub_X = X[indices_i]
        labels_l2, _ = _balanced_kmeans_single(sub_X, k2, lambda_penalty, max_iters, rng)

        for j in range(k2):
            sub_mask = labels_l2 == j
            if sub_mask.sum() > 0:
                cluster_indices.append(indices_i[sub_mask])

    print(f"\n[HBKM-2L] ✅ Done. Final cluster count: {len(cluster_indices)}")
    if len(cluster_indices) != n_c:
        raise RuntimeError(f"HBKM produced {len(cluster_indices)} clusters, expected {n_c}")
    sizes = [len(c) for c in cluster_indices]
    print(f"[HBKM-2L] Cluster sizes — min: {min(sizes)}, max: {max(sizes)}, "
          f"mean: {np.mean(sizes):.1f}, std: {np.std(sizes):.1f}")

    return cluster_indices


def extract_hub_nodes(X, cluster_indices):
    """
    Definition 3 (GATE 论文): 对每个簇，选择距质心最近的点作为 Hub Node。
        V_i = argmin_{x ∈ C_i} ||x - μ_i||²
    返回 hub 向量 [n_c, D]（真实数据点，不是质心本身）。
    """
    hubs = []
    hub_ids = []
    for cidx in tqdm(cluster_indices, desc="Extracting Hub Nodes"):
        sub_X    = X[cidx]
        centroid = sub_X.mean(axis=0)
        diff     = sub_X - centroid
        dists_sq = np.einsum('id,id->i', diff, diff)
        hub_local_idx = np.argmin(dists_sq)
        hubs.append(sub_X[hub_local_idx])
        hub_ids.append(cidx[hub_local_idx])
    return np.array(hubs, dtype=np.float32), np.array(hub_ids, dtype=np.int32)


# ==================== Main ====================

def main():
    parser = argparse.ArgumentParser(
        description="Hierarchical Balanced K-Means (HBKM) — GATE Paper Algorithm 2"
    )
    parser.add_argument('input_path',  type=str, help='Input data path (fvecs format)')
    parser.add_argument('output_path', type=str, help='Output hub vectors path (fvecs format)')
    parser.add_argument('--k',        type=int,   default=512,  help='Target number of hub nodes / clusters (n_c)')
    parser.add_argument('--k_branch', type=int,   default=8,    help='Branching factor per level (default: 8)')
    parser.add_argument('--k1',       type=int,   default=0,    help='Level-1 branching factor for two-level HBKM (0=disabled)')
    parser.add_argument('--k2',       type=int,   default=0,    help='Level-2 branching factor for two-level HBKM (0=disabled)')
    parser.add_argument('--lambda_p', type=float, default=0.01, help='Balance penalty coefficient λ (default: 0.01)')
    parser.add_argument('--max_iters',type=int,   default=20,   help='Max K-Means iterations per level T (default: 20)')
    parser.add_argument('--seed',     type=int,   default=42,   help='Random seed')
    parser.add_argument('--ids-output', type=str, default='', help='Optional raw int32 base IDs for exact hub identity')
    args = parser.parse_args()

    print(f"[HBKM] Loading data from {args.input_path} ...")
    X = read_fvecs(args.input_path)
    print(f"[HBKM] Loaded {X.shape[0]} vectors of dim {X.shape[1]}")

    # Step 1: HBKM 层次聚类
    if args.k1 > 0 and args.k2 > 0:
        # 两层模式：Level-1 分 k1 簇，Level-2 每个再分 k2 簇
        print(f"[HBKM] Using TWO-LEVEL mode: k1={args.k1}, k2={args.k2}")
        cluster_indices = hbkm_two_level(
            X,
            k1            = args.k1,
            k2            = args.k2,
            lambda_penalty= args.lambda_p,
            max_iters     = args.max_iters,
            random_seed   = args.seed,
        )
    else:
        # 通用模式：同一 k_branch 递归分裂
        print(f"[HBKM] Using GENERAL mode: k_branch={args.k_branch}, n_c={args.k}")
        cluster_indices = hbkm(
            X,
            k_branch      = args.k_branch,
            n_c           = args.k,
            lambda_penalty= args.lambda_p,
            max_iters     = args.max_iters,
            random_seed   = args.seed,
        )

    # Step 2: 从每个簇中抽取 Hub 节点（最近质心点，Definition 3）
    hubs, hub_ids = extract_hub_nodes(X, cluster_indices)
    print(f"\n[HBKM] Hub nodes extracted: {hubs.shape}")

    write_fvecs(args.output_path, hubs)
    if args.ids_output:
        hub_ids.tofile(args.ids_output)
        print(f"[HBKM] Exact hub IDs saved to {args.ids_output}")
    print(f"[HBKM] ✅ Hub nodes saved to {args.output_path}")


if __name__ == '__main__':
    main()
