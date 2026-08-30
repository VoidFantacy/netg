import argparse
import numpy as np
import os
import struct
import heapq
from tqdm import tqdm


def read_fvecs(filename):
    """读取 fvecs 格式文件"""
    with open(filename, 'rb') as f:
        header = f.read(4)
        if not header:
            return np.array([])
        d = struct.unpack('i', header)[0]
        f.seek(0, 2)
        n = f.tell() // (4 + 4 * d)
        f.seek(0)
        x = np.zeros((n, d), dtype=np.float32)
        for i in range(n):
            f.read(4)
            x[i] = np.frombuffer(f.read(d * 4), dtype=np.float32)
    return x


def load_nsg_graph(filename):
    """读取 NSG 二进制图文件"""
    graph = []
    with open(filename, 'rb') as f:
        width = struct.unpack('i', f.read(4))[0]
        ep = struct.unpack('i', f.read(4))[0]
        while True:
            chunk = f.read(4)
            if not chunk:
                break
            k = struct.unpack('i', chunk)[0]
            ids = struct.unpack(f'{k}i', f.read(4 * k))
            graph.append(list(ids))
    return graph, ep


def read_hub_entry_points(hub_txt_path):
    """从 hubs.txt 中读取 Hub 的 entry point ID（NSG 图中的节点 ID）"""
    with open(hub_txt_path, 'r') as f:
        header = f.readline().strip().split()
        iter1_num = int(header[0])
        iter2_num = int(header[1])
        # dim = int(header[2])  # 不需要
        # 跳过 Hub 向量行
        for _ in range(iter1_num):
            f.readline()
        # 读取 Entry Point IDs
        entry_points = []
        for _ in range(iter1_num * iter2_num):
            line = f.readline().strip()
            if line:
                entry_points.append(int(line))
    return entry_points


def bfs_find_nearest_hubs(undirected_graph, gt_nn, hub_ep_set, max_depth=6, max_visited=200000):
    """
    论文 Definition 4 的高效近似实现：
    从 gt_nn 出发在无向图上 BFS，记录每个 Hub 被首次发现时的深度。

    关键优化（防止 10M 图上指数爆炸）：
    - max_depth=6: 在 avg_degree~50 的图上，6 层 BFS 覆盖 ~10^8 条边路径，
      足以发现附近的 Hub（512 个 Hub 均匀分布在 10M 节点中 ≈ 1:20000 密度）
    - max_visited=200000: 硬限制访问节点总数，保证每个 query < 0.1s
    - 找到 ≥3 个 Hub 即提前终止

    Returns:
        hub_depths: dict {hub_entry_point_id: depth}
    """
    n_nodes = len(undirected_graph)
    visited = {gt_nn}
    frontier = [gt_nn]
    hub_depths = {}
    total_visited = 1

    if gt_nn in hub_ep_set:
        hub_depths[gt_nn] = 0

    for depth in range(1, max_depth + 1):
        next_frontier = []
        for node in frontier:
            if node >= n_nodes:
                continue
            for neighbor in undirected_graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    total_visited += 1
                    if neighbor in hub_ep_set:
                        hub_depths[neighbor] = depth
                    next_frontier.append(neighbor)
                    if total_visited >= max_visited:
                        break
            if total_visited >= max_visited:
                break
        frontier = next_frontier
        if not frontier or total_visited >= max_visited:
            break
        if len(hub_depths) >= 3:
            break

    return hub_depths


def write_sample_file(file_path, samples):
    """写入样本文件 (空格分隔)"""
    with open(file_path, 'w') as f:
        for eps in samples:
            f.write(f"{' '.join(map(str, eps))}\n")


def main():
    parser = argparse.ArgumentParser(
        description="GATE §4.2: Query-aware Sample Generation"
    )
    parser.add_argument('--hub_path', required=True, help='Path to hubs.bin (fvecs)')
    parser.add_argument('--query_path', required=True, help='Path to query.fvecs')
    parser.add_argument('--sample_output_dir', required=True, help='Directory to save train samples')
    parser.add_argument('--nsg_path', default='', help='Path to NSG index (binary)')
    parser.add_argument('--base_path', default='', help='Path to base vectors (fvecs)')
    parser.add_argument('--hub_txt_path', default='', help='Path to hubs.txt (entry point IDs)')
    parser.add_argument('--t_pos', type=int, default=3,
                        help='Positive sample tolerance (Definition 4, default=3)')
    parser.add_argument('--t_neg', type=int, default=15,
                        help='Negative sample threshold (default=15)')
    args = parser.parse_args()

    print(f"[GenSamples] Loading Hubs from {args.hub_path}...")
    hubs = read_fvecs(args.hub_path)
    print(f"[GenSamples] Loading Queries from {args.query_path}...")
    queries = read_fvecs(args.query_path)

    if len(hubs) == 0 or len(queries) == 0:
        print("Error: Hubs or Queries are empty!")
        return

    num_hubs = len(hubs)
    num_queries = len(queries)
    np.random.seed(42)

    # ================================================================
    # 判断是否启用图跳数模式 (论文 Definition 4)
    # ================================================================
    use_graph_hops = (
        args.nsg_path and os.path.exists(args.nsg_path) and
        args.base_path and os.path.exists(args.base_path) and
        args.hub_txt_path and os.path.exists(args.hub_txt_path)
    )

    pos_sample_ids = []
    neg_sample_ids = []

    if use_graph_hops:
        print(f"\n[GenSamples] Graph-hop mode (Definition 4)")
        print(f"   t_pos={args.t_pos}, t_neg={args.t_neg}")

        # 阶段 1: 先算 GT top-1（需要 base 向量 + faiss，完成后立刻释放）
        print(f"[GenSamples] Phase 1: Computing GT top-1 NNs...")
        import faiss
        import gc
        base_vecs = read_fvecs(args.base_path)
        print(f"   Base loaded: {base_vecs.shape}")
        dim = base_vecs.shape[1]
        faiss_index = faiss.IndexFlatL2(dim)
        faiss_index.add(base_vecs)
        _, gt_I = faiss_index.search(queries, 1)
        gt_nns = gt_I.flatten()
        del faiss_index, base_vecs, gt_I
        gc.collect()
        print(f"   GT computed. Memory released.")

        # 阶段 2: 加载 NSG 图并构建无向邻接（不需要 base 向量）
        print(f"[GenSamples] Phase 2: Loading NSG graph...")
        nsg_graph, nsg_ep = load_nsg_graph(args.nsg_path)
        n_nodes = len(nsg_graph)
        print(f"   NSG nodes: {n_nodes}")

        # 直接在原始 nsg_graph 上添加反向边（节省一倍内存，不创建新 set 列表）
        print("[GenSamples] Adding reverse edges (in-place)...")
        # 先收集反向边，避免在遍历时修改
        reverse_edges = [[] for _ in range(n_nodes)]
        for u in tqdm(range(n_nodes), desc="Scan edges", mininterval=60):
            for v in nsg_graph[u]:
                if v < n_nodes:
                    reverse_edges[v].append(u)
        # 合并反向边到原图（去重）
        for u in tqdm(range(n_nodes), desc="Merge edges", mininterval=60):
            if reverse_edges[u]:
                merged = set(nsg_graph[u])
                merged.update(reverse_edges[u])
                nsg_graph[u] = list(merged)
        del reverse_edges
        gc.collect()
        undirected_graph = nsg_graph  # 原地修改，无额外内存
        print(f"   Undirected graph ready.")

        # 3. 读取 Hub entry points
        entry_points = read_hub_entry_points(args.hub_txt_path)
        hub_ep_set = set(entry_points)
        ep_to_hub_idx = {ep: idx for idx, ep in enumerate(entry_points)}

        # 4. BFS 为每个 query 生成正/负样本
        print("[GenSamples] BFS sampling from GT NNs...")
        fallback_count = 0
        for qi in tqdm(range(num_queries), desc="Sampling", mininterval=30):
            gt_nn = int(gt_nns[qi])
            hub_depths = bfs_find_nearest_hubs(
                undirected_graph, gt_nn, hub_ep_set,
                max_depth=6, max_visited=200000
            )

            if not hub_depths:
                # 极罕见：BFS 未找到任何 Hub -> L2 兜底
                fallback_count += 1
                q_sq = np.sum(queries[qi] ** 2)
                h_sq = np.sum(hubs ** 2, axis=1)
                dists = q_sq + h_sq - 2 * np.dot(queries[qi], hubs.T)
                pos_sample_ids.append([int(np.argmin(dists))])
                neg_sample_ids.append(
                    np.random.choice(num_hubs, 32, replace=True).tolist()
                )
                continue

            min_depth = min(hub_depths.values())

            # 正样本: depth <= min_depth + t_pos
            pos_hubs = [
                ep_to_hub_idx[ep]
                for ep, d in hub_depths.items()
                if d <= min_depth + args.t_pos
            ]
            if not pos_hubs:
                closest_ep = min(hub_depths, key=hub_depths.get)
                pos_hubs = [ep_to_hub_idx[closest_ep]]
            pos_sample_ids.append([pos_hubs[0]])

            # 负样本: depth > t_neg 或 BFS 未发现的 Hub
            neg_hubs = [
                ep_to_hub_idx[ep]
                for ep, d in hub_depths.items()
                if d > args.t_neg
            ]
            found_idxs = set(ep_to_hub_idx[ep] for ep in hub_depths)
            unfound = [i for i in range(num_hubs) if i not in found_idxs]
            all_neg = neg_hubs + unfound
            if len(all_neg) < 32:
                pos_set = set(pos_hubs)
                all_neg = [i for i in range(num_hubs) if i not in pos_set]
            if len(all_neg) >= 32:
                chosen = np.random.choice(len(all_neg), 32, replace=False)
            else:
                chosen = np.random.choice(len(all_neg), 32, replace=True)
            neg_sample_ids.append([all_neg[c] for c in chosen])

        if fallback_count > 0:
            print(f"   [Info] {fallback_count}/{num_queries} queries used L2 fallback")
        del undirected_graph

    else:
        # ================================================================
        # 兜底模式：L2 距离
        # ================================================================
        print(f"\n[GenSamples] L2 distance fallback mode")
        print(f"   Tip: pass --nsg_path, --base_path, --hub_txt_path for graph-hop mode")

        batch_size = 1000
        for i in range(0, num_queries, batch_size):
            q_batch = queries[i: min(i + batch_size, num_queries)]
            q_sq = np.sum(q_batch ** 2, axis=1, keepdims=True)
            h_sq = np.sum(hubs ** 2, axis=1)
            dists = q_sq + h_sq - 2 * np.dot(q_batch, hubs.T)
            nearest = np.argmin(dists, axis=1)
            for idx in nearest:
                pos_sample_ids.append([int(idx)])
                neg_sample_ids.append(
                    np.random.choice(num_hubs, 32, replace=True).tolist()
                )

    # 保存
    os.makedirs(args.sample_output_dir, exist_ok=True)
    pos_file = os.path.join(args.sample_output_dir, 'pos_sample.txt')
    neg_file = os.path.join(args.sample_output_dir, 'neg_sample.txt')
    write_sample_file(pos_file, pos_sample_ids)
    write_sample_file(neg_file, neg_sample_ids)

    print(f"\n Training samples saved ({len(pos_sample_ids)} queries)")
    print(f"   Positives: {pos_file}")
    print(f"   Negatives: {neg_file}")
    mode = "Graph-hop" if use_graph_hops else "L2-fallback"
    print(f"   Mode: {mode}")


if __name__ == '__main__':
    main()
