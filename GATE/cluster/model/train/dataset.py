import torch
import numpy as np
import os
import struct
import json
import random
from torch.utils.data import Dataset
from tqdm import tqdm

def read_fvecs(filename):
    with open(filename, 'rb') as f:
        header = f.read(4)
        if not header: return np.array([])
        d = struct.unpack('i', header)[0]
        f.seek(0, 2)
        n = f.tell() // (4 + 4 * d)
        f.seek(0)
        x = np.zeros((n, d), dtype=np.float32)
        for i in range(n):
            f.read(4)
            x[i] = np.frombuffer(f.read(d * 4), dtype=np.float32)
    return x


def _graph2vec_embed(subgraph_dir, num_hubs, hub_vecs, output_dim):
    """
    用 karateclub Graph2Vec 对子图 JSON 生成图级嵌入（与原作者一致）。
    输入：subgraph_dir 下的 {i}.json（edges + features）
    输出：np.ndarray [num_hubs, output_dim]
    """
    try:
        from karateclub import Graph2Vec
        import networkx as nx
    except ImportError:
        return None

    graphs = []
    valid_indices = []
    for i in range(num_hubs):
        json_path = os.path.join(subgraph_dir, f'{i}.json')
        if not os.path.exists(json_path):
            continue
        try:
            with open(json_path, 'r') as f:
                sub = json.load(f)
            G = nx.Graph()
            nodes = list(sub.get('features', {}).keys()) or sub.get('nodes', [])
            
            # karateclub requires nodes to be indexed continuously from 0 to N-1
            node_mapping = {int(n): idx for idx, n in enumerate(nodes)}
            
            G.add_nodes_from(range(len(nodes)))
            for e in sub.get('edges', []):
                if len(e) == 2:
                    u, v = int(e[0]), int(e[1])
                    if u in node_mapping and v in node_mapping:
                        G.add_edge(node_mapping[u], node_mapping[v])
                        
            if G.number_of_nodes() > 0:
                graphs.append(G)
                valid_indices.append(i)
        except Exception:
            continue

    if not graphs:
        return None

    print(f"[Dataset] Running Graph2Vec on {len(graphs)} subgraphs (dim={output_dim})...")
    model = Graph2Vec(dimensions=output_dim, workers=4, epochs=10, min_count=1)
    model.fit(graphs)
    embs = model.get_embedding()   # [len(graphs), output_dim]

    graph_feats = np.zeros((num_hubs, output_dim), dtype=np.float32)
    for idx, hub_id in enumerate(valid_indices):
        graph_feats[hub_id] = embs[idx]
    # 未能生成的 hub 用原始向量填充
    for i in range(num_hubs):
        if i not in valid_indices:
            # 截断或填零到 output_dim
            v = hub_vecs[i]
            graph_feats[i] = v[:output_dim] if len(v) >= output_dim else np.pad(v, (0, output_dim - len(v)))
    return graph_feats


def load_graph_features(subgraph_dir, num_hubs, hub_vecs, graph2vec_csv=None):
    """
    加载子图拓扑特征（与原作者方法一致）：

    优先级：
      1. graph2vec_csv 文件存在 → 直接读 CSV（原作者方法，最优）
      2. karateclub 可用 → 在线跑 Graph2Vec 生成嵌入，并缓存为 CSV
      3. 兜底 → 均值池化（最次，仅用于 Graph2Vec 不可用时）
    """
    output_dim = hub_vecs.shape[1]

    # ── 优先级 1：读取已有 CSV ──
    csv_path = graph2vec_csv or os.path.join(os.path.dirname(subgraph_dir), 'graph2vec_embedding.csv')
    if os.path.exists(csv_path):
        print(f"[Dataset] Loading Graph2Vec embeddings from {csv_path} ...")
        import pandas as pd
        x_data = pd.read_csv(csv_path, index_col=0)
        try:
            x_data.index = x_data.index.astype(int)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Graph2Vec CSV has non-integer row IDs: {csv_path}") from exc
        if x_data.index.tolist() != list(range(num_hubs)):
            raise ValueError(
                f"Graph2Vec CSV row IDs must be exactly 0..{num_hubs - 1}: {csv_path}"
            )
        embs = x_data.to_numpy(dtype=np.float32)
        if embs.shape != (num_hubs, output_dim):
            raise ValueError(
                f"Graph2Vec shape {embs.shape} != expected {(num_hubs, output_dim)}: {csv_path}"
            )
        if not np.isfinite(embs).all():
            raise ValueError(f"Graph2Vec CSV contains non-finite values: {csv_path}")
        print(f"[Dataset] Graph2Vec embeddings loaded. Shape: {embs.shape}")
        return embs

    # ── 优先级 2：在线跑 Graph2Vec 并缓存 ──
    print(f"[Dataset] graph2vec_embedding.csv not found. Trying karateclub Graph2Vec...")
    embs = _graph2vec_embed(subgraph_dir, num_hubs, hub_vecs, output_dim)
    if embs is not None:
        # 缓存 CSV 供下次使用
        import pandas as pd
        df = pd.DataFrame(embs)
        df.to_csv(csv_path)
        print(f"[Dataset] Graph2Vec embeddings cached to {csv_path}")
        return embs

    # ── 优先级 3：均值池化兜底 ──
    print(f"[Dataset] ⚠️  karateclub not available. Falling back to mean pooling.")
    graph_feats = np.zeros_like(hub_vecs)
    for i in tqdm(range(num_hubs), desc="Mean-pool subgraph features"):
        json_path = os.path.join(subgraph_dir, f'{i}.json')
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    subgraph = json.load(f)
                feat_list = list(subgraph['features'].values())
                if feat_list:
                    graph_feats[i] = np.mean(feat_list, axis=0).astype(np.float32)
                    continue
            except Exception:
                pass
        graph_feats[i] = hub_vecs[i]
    print(f"[Dataset] Graph features loaded (mean-pool). Shape: {graph_feats.shape}")
    return graph_feats


# 每个 Hub 最多匹配的正/负样本数量限制（与作者原始代码一致）
SAMPLE_NUM = 50
FILTER_NUM = 500


class GATEDataset(Dataset):
    """
    与作者原始实现完全一致的 Triplet 数据集。

    作者设计（见原始 dataset.py）：
    - 以 (ep_id, pos_query_id, neg_query_id) 三元组为训练样本
    - Anchor = Hub embedding, Positive = 跳数最小的 query, Negative = 跳数最大的 query
    - 每个 Hub 的正负样本对做笛卡尔积

    __getitem__ 返回:
        (node_feature, graph_feature, pos_query, neg_query)
    """
    def __init__(self, params):
        self.params = params

        # 1. 加载样本索引
        sample_dir = params['SAMPLE_PATH']
        with open(os.path.join(sample_dir, 'pos_sample.txt'), 'r') as f:
            pos_samples = [list(map(int, line.strip().split())) for line in f]
        with open(os.path.join(sample_dir, 'neg_sample.txt'), 'r') as f:
            neg_samples = [list(map(int, line.strip().split())) for line in f]
        if len(pos_samples) != len(neg_samples) or not pos_samples:
            raise ValueError("positive/negative sample files must have the same non-zero line count")

        # 2. 加载 Query
        print(f"[Dataset] Loading Queries from {params['QUERY_PATH']}...")
        self.queries = read_fvecs(params['QUERY_PATH'])
        if len(self.queries) < len(pos_samples):
            raise ValueError(
                f"query count {len(self.queries)} < sample count {len(pos_samples)}"
            )
        self.queries = self.queries[:len(pos_samples)]

        # 3. 加载 Hub Node Feature（原始向量）
        print(f"[Dataset] Loading Hubs from {params['HUB_PATH']}...")
        self.hubs = read_fvecs(params['HUB_PATH'])
        self.num_hubs = len(self.hubs)

        # 4. 加载 Hub Graph Feature（从子图 JSON 均值池化）
        subgraph_dir = params.get('SUBGRAPH_DIR', '')
        if subgraph_dir and os.path.isdir(subgraph_dir):
            self.graph_feats = load_graph_features(
                subgraph_dir,
                self.num_hubs,
                self.hubs,
                params.get('GRAPH2VEC_CSV'),
            )
        else:
            print("[Dataset] SUBGRAPH_DIR not found, falling back to node features.")
            self.graph_feats = self.hubs.copy()

        # 5. 构建 (ep_id, pos_query_id, neg_query_id) 三元组
        #    与作者原始代码完全一致的配对逻辑
        ep2query_pos = [[] for _ in range(self.num_hubs)]
        ep2query_neg = [[] for _ in range(self.num_hubs)]

        # 过滤不合格的 query（负样本太多 > FILTER_NUM 或太少 < 10）
        dummy_query_ids = set()
        for query_id, (poses, negs) in enumerate(zip(pos_samples, neg_samples)):
            if len(negs) > FILTER_NUM or len(negs) < 10:
                dummy_query_ids.add(query_id)
                continue
            for ep_id in poses:
                if ep_id < self.num_hubs:
                    ep2query_pos[ep_id].append(query_id)

        for query_id, negs in enumerate(neg_samples):
            for ep_id in negs:
                if query_id in dummy_query_ids:
                    continue
                if ep_id < self.num_hubs:
                    ep2query_neg[ep_id].append(query_id)

        # 笛卡尔积生成三元组 (截断到 SAMPLE_NUM)
        pairs = []
        rng = random.Random(int(params.get('DATASET_SEED', 42)))
        for ep_id, (poses, negs) in enumerate(zip(ep2query_pos, ep2query_neg)):
            rng.shuffle(negs)
            rng.shuffle(poses)
            negs = negs[:SAMPLE_NUM]
            poses = poses[:SAMPLE_NUM]
            for neg in negs:
                for pos in poses:
                    pairs.append((ep_id, pos, neg))

        self.pairs = pairs
        self.return_hub_id = bool(params.get('RETURN_HUB_ID', False))
        print(f"[Dataset] Generated {len(self.pairs)} triplet pairs "
              f"(from {self.num_hubs} hubs, {len(self.queries)} queries)")

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        ep_id, pos_query_id, neg_query_id = self.pairs[idx]

        if self.return_hub_id:
            return (
                torch.tensor(ep_id, dtype=torch.long),
                torch.from_numpy(self.queries[pos_query_id]),
                torch.from_numpy(self.queries[neg_query_id]),
            )

        node_feature  = self.hubs[ep_id]
        graph_feature = self.graph_feats[ep_id]
        pos_query     = self.queries[pos_query_id]
        neg_query     = self.queries[neg_query_id]

        return (
            torch.from_numpy(node_feature),
            torch.from_numpy(graph_feature),
            torch.from_numpy(pos_query),
            torch.from_numpy(neg_query),
        )


def get_dataset(params):
    return GATEDataset(params)
