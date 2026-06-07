import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import argparse
import os
import faiss 

# ==========================================
# 1. 模型定义
# ==========================================
class InteractionLinkScorer(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.feature_dim = input_dim * 4 
        self.net = nn.Sequential(
            nn.Linear(self.feature_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
    
    def forward(self, u, v):
        interaction = u * v
        diff = torch.abs(u - v)
        x = torch.cat([u, v, interaction, diff], dim=1)
        return self.net(x)

def load_data(filename):
    print(f"Loading data from {filename}...")
    with open(filename, 'r') as f:
        header = f.readline().split()
        if not header: raise ValueError("Empty file!")
        dim, num_centers = map(int, header)
        vecs = []
        for _ in range(num_centers):
            vecs.append(list(map(float, f.readline().split())))
        vecs = np.array(vecs, dtype=np.float32)
        edges = []
        for line in f:
            parts = list(map(int, line.split()))
            if len(parts) >= 2: edges.append(parts[:2])
    return vecs, np.array(edges)

# ==========================================
# 2. 混合建图核心逻辑 (高速版)
# ==========================================
def build_hybrid_graph(model, vecs_tensor, K_total, device):
    """
    构建混合图: 几何邻居 + 神经邻居 (Candidate Selection优化版)
    """
    num_nodes, dim = vecs_tensor.shape
    vecs_np = vecs_tensor.cpu().numpy()
    
    # 候选集参数 (减少计算量)
    K_candidates_geo = 150 
    K_candidates_rand = 50 
    
    print(f"   [Hybrid] Computing Geometric KNN candidates (K={K_candidates_geo})...")
    index = faiss.IndexFlatL2(dim)
    if device == "cuda": 
        res = faiss.StandardGpuResources()
        index = faiss.index_cpu_to_gpu(res, 0, index)
    
    index.add(vecs_np)
    _, geo_candidates_all = index.search(vecs_np, K_candidates_geo + 1)
    
    print(f"   [Hybrid] Computing Neural Shortcuts (Batch Eval)...")
    model.eval()
    
    final_adj = []
    batch_size = 256
    
    with torch.no_grad():
        for i in range(0, num_nodes, batch_size):
            end_i = min(i + batch_size, num_nodes)
            current_bs = end_i - i
            
            # 准备数据
            batch_u = vecs_tensor[i:end_i] 
            
            # 候选集构建
            curr_geo_idx = geo_candidates_all[i:end_i, 1:] # 几何候选
            curr_rand_idx = np.random.randint(0, num_nodes, (current_bs, K_candidates_rand)) # 随机候选
            combined_idx = np.hstack([curr_geo_idx, curr_rand_idx])
            
            flat_idx = torch.LongTensor(combined_idx.flatten()).to(device)
            flat_v = vecs_tensor[flat_idx]
            
            num_cand = combined_idx.shape[1]
            flat_u = batch_u.repeat_interleave(num_cand, dim=0)
            
            # 批量推理
            scores = model(flat_u, flat_v).squeeze()
            scores = scores.view(current_bs, num_cand)
            
            # Top-K
            topk_vals, topk_local_indices = torch.topk(scores, k=K_total, dim=1)
            topk_local_indices = topk_local_indices.cpu().numpy()
            
            # 结果组装
            for local_r in range(current_bs):
                global_u_idx = i + local_r
                best_neural_id_indices = topk_local_indices[local_r]
                neural_global_ids = combined_idx[local_r][best_neural_id_indices]
                
                K_geo_keep = K_total // 2
                combined_neighbors = set()
                
                # 1. 几何保底
                geo_list = geo_candidates_all[global_u_idx][1:]
                for gid in geo_list[:K_geo_keep]:
                    combined_neighbors.add(int(gid))
                
                # 2. 神经捷径
                for nid in neural_global_ids:
                    if len(combined_neighbors) >= K_total: break
                    if int(nid) != global_u_idx:
                        combined_neighbors.add(int(nid))
                
                # 3. 补齐
                idx_ptr = K_geo_keep
                while len(combined_neighbors) < K_total and idx_ptr < len(geo_list):
                    gid = geo_list[idx_ptr]
                    if int(gid) != global_u_idx:
                        combined_neighbors.add(int(gid))
                    idx_ptr += 1
                
                final_adj.append(list(combined_neighbors))
            
            if (i // batch_size) % 10 == 0 or end_i == num_nodes:
                print(f"    Processed {end_i}/{num_nodes} nodes...", flush=True)

    return final_adj

def train_and_save_pca(vecs, output_path, target_dim=32):
    print(f"\n>>> Training PCA ({vecs.shape[1]} -> {target_dim})...", flush=True)
    mat = faiss.PCAMatrix(vecs.shape[1], target_dim)
    mat.train(vecs)
    faiss.write_VectorTransform(mat, output_path)

def build_graph(args):
    vecs, pos_edges = load_data(args.data_file)
    print("Normalizing vectors (L2)...")
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    vecs = vecs / (norms + 1e-10)
    
    if args.output_pca:
        train_and_save_pca(vecs, args.output_pca, target_dim=32)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}", flush=True)
    
    vecs_tensor = torch.FloatTensor(vecs).to(device)
    
    # 构造训练样本
    num_nodes = vecs.shape[0]
    num_pos = len(pos_edges)
    if num_pos == 0: pos_edges = np.zeros((1, 2), dtype=int); num_pos = 1
    
    neg_u = np.random.randint(0, num_nodes, num_pos)
    neg_v = np.random.randint(0, num_nodes, num_pos)
    
    train_u = torch.LongTensor(np.concatenate([pos_edges[:,0], neg_u])).to(device)
    train_v = torch.LongTensor(np.concatenate([pos_edges[:,1], neg_v])).to(device)
    labels = torch.cat([torch.ones(num_pos), torch.zeros(num_pos)]).to(device).unsqueeze(1)
    
    model = InteractionLinkScorer(vecs.shape[1]).to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.BCELoss()
    
    print(f"\n>>> Training Neural Scorer on {len(labels)} samples (Fast Mode)...", flush=True)
    batch_size = 8192
    model.train()
    
    # [优化] 将 Epochs 从 15 减少到 5，大幅缩短时间
    # 5轮足以让模型学到基本的交互模式
    EPOCHS = 30
    for epoch in range(EPOCHS):
        perm = torch.randperm(len(labels))
        total_loss = 0; steps = 0
        for i in range(0, len(labels), batch_size):
            idx = perm[i:i+batch_size]
            preds = model(vecs_tensor[train_u[idx]], vecs_tensor[train_v[idx]])
            loss = criterion(preds, labels[idx])
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item(); steps += 1
        print(f"Epoch {epoch+1:02d}: Loss = {total_loss/steps:.4f}", flush=True)

    print(f"\n>>> Building Hybrid Graph (K={args.K})...", flush=True)
    adj_list = build_hybrid_graph(model, vecs_tensor, args.K, device)

    print(f"Saving graph to {args.output_graph}...", flush=True)
    with open(args.output_graph, 'w') as f:
        f.write(f"{num_nodes} {args.K}\n")
        for neighbors in adj_list:
            f.write(" ".join(map(str, neighbors)) + "\n")
    print("Done!", flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_file", required=True)
    parser.add_argument("--output_graph", required=True)
    parser.add_argument("--output_pca", default="")
    parser.add_argument("--K", type=int, default=32)
    args = parser.parse_args()
    build_graph(args)