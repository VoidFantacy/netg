import sys
import os
import struct
import json
import math
import queue
import numpy as np
import faiss
from tqdm import tqdm

# ==================== 配置 ====================
MAX_HOP = 5          
MAX_NODES = 1000     

# ==================== IO Functions ====================

def read_fvecs(filename):
    print(f"Loading vectors from {filename}...")
    with open(filename, 'rb') as f:
        d = struct.unpack('i', f.read(4))[0]
    raw = np.memmap(filename, mode='r', dtype=np.float32)
    if raw.size % (d + 1):
        raise ValueError(f"invalid fvecs size: {filename}")
    return raw.reshape(-1, d + 1)[:, 1:]


class CSRGraph:
    def __init__(self, offsets, neighbors):
        self.offsets = offsets
        self.neighbors = neighbors

    def __len__(self):
        return len(self.offsets) - 1

    def __getitem__(self, node):
        return self.neighbors[self.offsets[node]:self.offsets[node + 1]]

    def __iter__(self):
        for node in range(len(self)):
            yield self[node]

def load_nsg_graph(filename, expected_nodes):
    print(f"Loading NSG graph from {filename}...")
    raw = np.memmap(filename, mode='r', dtype=np.uint32)
    width, ep = map(int, raw[:2])
    offsets = np.empty(expected_nodes + 1, dtype=np.int64)
    max_neighbors = raw.size - 2 - expected_nodes
    neighbors = np.empty(max_neighbors, dtype=np.uint32)
    word = 2
    edge = 0
    offsets[0] = 0
    for node in range(expected_nodes):
        if word >= raw.size:
            raise ValueError(f"truncated graph at node {node}")
        degree = int(raw[word])
        word += 1
        if degree > width or word + degree > raw.size:
            raise ValueError(f"invalid degree {degree} at node {node}")
        neighbors[edge:edge + degree] = raw[word:word + degree]
        edge += degree
        word += degree
        offsets[node + 1] = edge
    if word != raw.size:
        raise ValueError(f"graph has trailing words: parsed={word}, total={raw.size}")
    graph = CSRGraph(offsets, neighbors[:edge])
    print(f"Graph loaded. Nodes: {len(graph)}, Edges: {edge}, Width: {width}, EP: {ep}")
    return graph

# ==================== C++ 兼容格式导出 ====================

def save_hub_info_for_cpp(output_path, hub_vecs, entry_points):
    """
    保存 C++ IndexNSG::LoadKmeans 能读取的格式
    格式:
    iter1_num iter2_num dim
    vec_0 (空格分隔)
    ...
    vec_N
    ep_id_0
    ...
    ep_id_N
    """
    if os.path.exists(output_path):
        print(f"Hub info already exists; preserving it: {output_path}")
        return

    print(f"Saving Hub info for C++ to {output_path}...")
    num_hubs, dim = hub_vecs.shape
    
    # 逻辑: 我们采用扁平结构，所以 iter1=num_hubs, iter2=1
    # 这样 C++ 那边: ep_id / 1 = ep_id (第i个Hub)
    #               ep_id % 1 = 0
    # 对应 iter2_eps[i][0]
    
    with open(output_path, 'w') as f:
        # Header: iter1_num iter2_num dim
        f.write(f"{num_hubs} 1 {dim}\n")
        
        # Iter1 Centroids (Hub Vectors)
        for i in range(num_hubs):
            vec_str = " ".join([f"{x:.6f}" for x in hub_vecs[i]])
            f.write(f"{vec_str}\n")
            
        # Iter2 Eps (Entry Point IDs)
        # 对应每个 Hub 在 NSG 图中的最近邻 ID
        for ep in entry_points:
            f.write(f"{ep}\n")
            
    print("✅ C++ compatible hub info saved.")

# ==================== Sampling Logic ====================

def compute_dynamic_sample_size(degree, min_degree, max_degree):
    """
    论文 §4.2: 动态调整采样数量 x = ceil(MinDegree(G) / MaxDegree(G) * degree(v))
    防止高度节点过采样、低度节点欠采样，确保均衡的邻域扩展。
    """
    if max_degree == 0:
        return max(1, degree)
    x = math.ceil(min_degree / max_degree * degree)
    return max(1, x)


def sample_negb_vectorized(center_id, neighbor_ids, all_vecs, sample_size):
    """
    论文 §4.2: 采样 ceil(x/2) 个最近邻和 floor(x/2) 个最远邻。
    混合采样策略兼顾短程局部结构和长程跨簇探索。
    """
    if len(neighbor_ids) == 0:
        return []
    
    valid_ids = [nid for nid in neighbor_ids if nid < len(all_vecs)]
    if not valid_ids:
        return []
        
    nb_vecs = all_vecs[valid_ids]
    center_vec = all_vecs[center_id]
    
    diff = nb_vecs - center_vec
    dists_sq = np.einsum('ij,ij->i', diff, diff)
    
    sorted_indices = np.argsort(dists_sq)
    
    K = len(valid_ids)
    if K <= sample_size:
        return [valid_ids[i] for i in sorted_indices]
    
    n_near = math.ceil(sample_size / 2)
    n_far = sample_size - n_near
    
    near_indices = sorted_indices[:n_near]
    far_indices = sorted_indices[-n_far:]
    
    selected_nids = [valid_ids[i] for i in near_indices] + [valid_ids[i] for i in far_indices]
    return selected_nids

def sample_graph(ep, g, fvecs, min_degree, max_degree, include_features=True) -> dict:
    visited = set()
    visited.add(ep)
    
    q = queue.Queue()
    q.put((ep, 0))
    
    edges = []
    
    while not q.empty():
        if len(visited) >= MAX_NODES:
            break
            
        curr_id, hop = q.get()
        
        if hop >= MAX_HOP:
            continue
        
        if curr_id >= len(g): continue
        neighbors = g[curr_id]
        
        x = compute_dynamic_sample_size(len(neighbors), min_degree, max_degree)
        sampled_neighbors = sample_negb_vectorized(curr_id, neighbors, fvecs, x)
        
        for nx in sampled_neighbors:
            if nx not in visited:
                if len(visited) >= MAX_NODES:
                    break
                visited.add(nx)
                q.put((nx, hop + 1))
    
    sorted_visited = sorted(list(visited))
    visited_set = set(sorted_visited)
    
    features = {}
    
    for point in sorted_visited:
        if include_features:
            vec = fvecs[point]
            features[str(point)] = vec.tolist()
        
        if point < len(g):
            real_neighbors = g[point]
            for nx in real_neighbors:
                if nx in visited_set:
                    edges.append([int(point), int(nx)])

    # numpy scalar IDs are not JSON serializable.  Keep the topology-only
    # contract plain and language-neutral by materializing Python ints here.
    result = {"edges": edges, "nodes": [int(node) for node in sorted_visited]}
    if include_features:
        result["features"] = features
    return result

# ==================== Main ====================

def main():
    if len(sys.argv) < 5:
        print("Usage: python3 subgraph2json.py <nsg> <base> <hub> <out> [hub_ids.int32]")
        sys.exit(1)

    nsg_path = sys.argv[1]
    base_path = sys.argv[2]
    hub_path = sys.argv[3]
    output_dir = sys.argv[4]
    topology_only = '--topology-only' in sys.argv[6:]

    print(f"[Subgraph] Settings: HOP={MAX_HOP}, LIMIT={MAX_NODES}")
    if os.path.exists(output_dir) and os.listdir(output_dir):
        raise FileExistsError(f"refusing to overwrite non-empty output directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    base_vecs = read_fvecs(base_path)
    hub_vecs = read_fvecs(hub_path)
    nsg_graph = load_nsg_graph(nsg_path, len(base_vecs))

    if len(sys.argv) >= 6:
        entry_points = np.fromfile(sys.argv[5], dtype=np.int32)
        if len(entry_points) != len(hub_vecs):
            raise ValueError(f"hub ID count {len(entry_points)} != hub count {len(hub_vecs)}")
        if np.any(entry_points < 0) or np.any(entry_points >= len(base_vecs)):
            raise ValueError("hub IDs outside base range")
        if not np.array_equal(base_vecs[entry_points], hub_vecs):
            raise ValueError("hub vectors do not exactly match the supplied base IDs")
        print("Using exact Hub base IDs; no metric-dependent remapping.")
    else:
        print("Mapping Hubs to Graph Nodes with legacy L2 fallback...")
        d = base_vecs.shape[1]
        index = faiss.IndexFlatL2(d)
        index.add(base_vecs)
        _, I = index.search(hub_vecs, 1)
        entry_points = I.flatten()
    
    # 【新增】导出 C++ 需要的 Hub Info 文件
    # 我们将其保存为 hubs.txt，放在 output_dir 的父目录（即 output_deep10M/hubs.txt）
    # 或者为了方便，直接用一个约定好的名字
    hub_info_path = os.path.join(os.path.dirname(output_dir), "hubs.txt")
    save_hub_info_for_cpp(hub_info_path, hub_vecs, entry_points)

    # 计算全局 MinDegree 和 MaxDegree（论文 §4.2 中的动态采样参数）
    degrees = [len(neighbors) for neighbors in nsg_graph]
    non_zero_degrees = [d for d in degrees if d > 0]
    min_degree = min(non_zero_degrees) if non_zero_degrees else 1
    max_degree = max(non_zero_degrees) if non_zero_degrees else 1
    print(f"Graph degree stats: min={min_degree}, max={max_degree}, "
          f"avg={np.mean(degrees):.1f}")

    print(f"Generating subgraphs for {len(entry_points)} hubs...")
    
    for hub_idx, ep_node_id in enumerate(tqdm(entry_points, desc='Sampling', mininterval=10)):
        json_obj = sample_graph(
            ep_node_id, nsg_graph, base_vecs, min_degree, max_degree,
            include_features=not topology_only,
        )
        save_path = os.path.join(output_dir, f"{hub_idx}.json")
        with open(save_path, 'w') as fp:
            json.dump(json_obj, fp) 

    print("✅ All subgraphs generated.")

if __name__ == '__main__':
    main()
