import os
import json
import struct
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import argparse
import random
import math
import sys

# ==========================================
# 1. 配置
# ==========================================

CONFIG = {
    "datasets": ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"],
    "batch_size": 512,
    "epochs": 300,
    "min_epochs": 50,
    "lr": 5e-4,             # 稍高的峰值 LR，配合 OneCycleLR
    "patience": 50,
    "temperature": 0.07,
    "residue_scale": 0.05,  # 0.1 → 0.05，防止 Hub 过度变形
    "aug_per_query": 12,
    "aug_noise_std": 0.01,
    "neg_k": 15,
    "neg_refresh_interval": 15,
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "seed": 20260825,
}

# 针对不同数据集的特殊覆盖配置
DATASET_OVERRIDES = {
    "sift10M": {
        "epochs": 500,
        "min_epochs": 100,
        "patience": 80,
        "aug_per_query": 20,
        "aug_noise_std": 0.02,
        "neg_k": 20,
        "lr": 8e-4,
    },
    "sift10M_skewed": {
        "epochs": 500,
        "min_epochs": 100,
        "patience": 80,
        "aug_per_query": 20,
        "aug_noise_std": 0.02,
        "neg_k": 20,
        "lr": 8e-4,
    },
}

def get_config(dataset_name):
    """获取合并后的配置（默认 + 数据集特殊覆盖）"""
    cfg = dict(CONFIG)
    if dataset_name in DATASET_OVERRIDES:
        cfg.update(DATASET_OVERRIDES[dataset_name])
    return cfg

class PathManager:
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        settings_path = os.path.join(self.current_dir, "../datasets/settings.json")
        if not os.path.exists(settings_path):
            settings_path = os.path.join(self.current_dir, "../../benches/datasets/settings.json")
        self.settings_path = os.path.abspath(settings_path)
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(self.settings_path), "../.."))
        with open(self.settings_path, 'r') as f:
            self.settings = json.load(f)
            
    def get_paths(self, dataset_name):
        ds_conf = self.settings["datasets"][dataset_name]
        raw_root = self.settings.get("root_dir", "./benches/datasets")
        if raw_root.startswith("./"):
            data_root = os.path.join(self.project_root, raw_root[2:])
        else:
            data_root = raw_root
        
        dataset_dir = os.path.join(data_root, ds_conf["dataset_dir"])
        
        train_filename = ds_conf.get("drl_train_query_path", "")
        if not train_filename:
            print(f"⚠️ Warning: {dataset_name} 未配置 drl_train_query_path，回退到 acpg_query_path")
            train_filename = ds_conf.get("acpg_query_path", ds_conf.get("train_path", ""))
            
        paths = {
            "base": os.path.join(dataset_dir, ds_conf["base_path"]),
            "train_vectors": os.path.join(dataset_dir, train_filename), 
            "drl_dir": os.path.join(self.project_root, f"drl/{dataset_name}_results"),
            "graph_dir": os.path.join(self.project_root, f"graph_processing/{dataset_name}_results")
        }
        return paths

def read_fvecs(filename, max_rows=None):
    if not os.path.exists(filename): return None
    file_size = os.path.getsize(filename)
    with open(filename, 'rb') as f:
        dim = struct.unpack('i', f.read(4))[0]
        vec_size = 4 + 4 * dim
        n = file_size // vec_size
        if max_rows and max_rows < n: n = max_rows
        f.seek(0)
        data = np.fromfile(f, dtype=np.float32, count=n * (dim + 1))
        data = data.reshape(n, dim + 1)[:, 1:]
    return data.copy()

def read_ivecs_labels(filename):
    if not os.path.exists(filename): return None
    with open(filename, 'rb') as f:
        header = np.fromfile(f, dtype=np.int32, count=2)
        if len(header) < 2: return None
        nq, dim = header[0], header[1]
        data = np.fromfile(f, dtype=np.int32)
    if data.size % dim == 0:
        real_nq = data.size // dim
        data = data.reshape(real_nq, dim)
    else: return None
    return data

class LightRouter(nn.Module):
    """
    适中容量非对称 MLP（2 层 hidden，无 Dropout）。
    推理时 Query 保持原始向量，Hub 用 MLP 变换后的坐标。

    网络设计：
      - 宽度: max(384, input_dim * 2)，比最初版略宽
      - 深度: 2 层 hidden（简洁高效，适合小数据量）
      - 无 Dropout（~1 万条数据不需要正则化，反而阻碍收敛）
      - residue_scale=0.05（通过 CONFIG 控制，防止过度变形）
    """
    def __init__(self, input_dim, output_dim=None, residue_scale=0.05):
        super().__init__()

        if output_dim is None:
            output_dim = input_dim

        hidden_dim = max(384, input_dim * 2)
        self.residue_scale = residue_scale

        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, output_dim)
        )

        # 最后一层初始化为零 → 初始时输出为纯残差（恒等映射）
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)

    def forward(self, x):
        warp = self.net(x)
        return x + self.residue_scale * warp


class QueryOracleDataset(Dataset):
    """
    非对称训练数据集（动态 Semi-Hard Negative Mining 版）：

    - Anchor  : raw query（不经过 MLP，与推理时完全一致）
    - Positive: oracle_hub 的原始向量（经过 MLP）
    - Hard Neg: 从 Top-K 难负例中随机采样（每 N epoch 动态更新）

    数据增强：对 query 向量加小噪声，扩充样本数量。
    """
    def __init__(self, query_vecs, hub_vecs, pairs, aug_per_query=8, aug_noise_std=0.01, neg_k=10):
        # 过滤 fallback（cost == -1）样本
        valid_mask = pairs[:, 2] != -1
        pairs = pairs[valid_mask]
        print(f"   📊 有效标签样本: {len(pairs)}")

        self.query_vecs = query_vecs.astype(np.float32)
        self.hub_vecs   = hub_vecs.astype(np.float32)
        self.H = len(hub_vecs)
        self.neg_k = min(neg_k, self.H - 1)  # 不能超过 hub 总数 - 1

        self.q_idxs      = pairs[:, 0]
        self.oracle_idxs = pairs[:, 1]
        self.N             = len(pairs)
        self.aug_per_query = aug_per_query
        self.aug_noise_std = aug_noise_std
        self.q_mean_norm   = float(np.linalg.norm(query_vecs, axis=1).mean())

        # 初始化：用原始 hub 向量做第一轮 hard negative mining
        self.hard_neg_topk = np.zeros((self.N, self.neg_k), dtype=np.int32)
        print(f"   🔧 初始 Hard Negative Mining (Top-{self.neg_k}, H={self.H})...")
        self._mine_negatives_from_embeddings(hub_vecs)

        print(f"   ✅ QueryOracle 数据集: {self.N} 条 × {aug_per_query} 增强 = {self.N * aug_per_query} 样本 (Top-{self.neg_k} 动态负例)")

    def _mine_negatives_from_embeddings(self, hub_embeddings):
        """用给定的 hub embeddings 重新挖掘每个 query 的 Top-K 难负例"""
        hub_emb = hub_embeddings.astype(np.float32)
        hub_norms = np.linalg.norm(hub_emb, axis=1, keepdims=True) + 1e-8
        hub_n = hub_emb / hub_norms  # [H, D]

        q_vecs_sel = self.query_vecs[self.q_idxs].astype(np.float32)
        q_norms = np.linalg.norm(q_vecs_sel, axis=1, keepdims=True) + 1e-8
        q_n = q_vecs_sel / q_norms  # [N, D]

        # 批量计算余弦相似度
        cos_sim = q_n @ hub_n.T  # [N, H]

        # 屏蔽 oracle hub，然后取 Top-K
        for i in range(self.N):
            cos_sim[i, self.oracle_idxs[i]] = -2.0

        # argpartition 取最大的 K 个（即最难的负例）
        topk_indices = np.argpartition(-cos_sim, self.neg_k, axis=1)[:, :self.neg_k]
        # 对这 K 个再排序，确保最难的在前面
        for i in range(self.N):
            topk_i = topk_indices[i]
            sims_i = cos_sim[i, topk_i]
            sorted_order = np.argsort(-sims_i)
            self.hard_neg_topk[i] = topk_i[sorted_order]

    def update_hard_negatives(self, model, device):
        """用当前模型重新变换所有 hub，然后重新挖掘难负例"""
        model.eval()
        with torch.no_grad():
            hub_tensor = torch.from_numpy(self.hub_vecs).to(device)
            transformed = model(hub_tensor).cpu().numpy()
        model.train()
        self._mine_negatives_from_embeddings(transformed)

    def __len__(self):
        return self.N * self.aug_per_query

    def __getitem__(self, idx):
        base_idx = idx % self.N
        q_vec   = self.query_vecs[self.q_idxs[base_idx]].copy()
        pos_vec = self.hub_vecs[self.oracle_idxs[base_idx]].copy()

        # 从 Top-K 难负例中随机采样 1 个（增加多样性）
        neg_choice = np.random.randint(0, self.neg_k)
        neg_hub_idx = self.hard_neg_topk[base_idx, neg_choice]
        neg_vec = self.hub_vecs[neg_hub_idx].copy()

        # 数据增强：对 query 加小噪声（第一轮原始样本不加）
        if idx >= self.N:
            noise = np.random.randn(*q_vec.shape).astype(np.float32)
            q_vec = q_vec + noise * self.aug_noise_std * self.q_mean_norm

        return (
            torch.from_numpy(q_vec),
            torch.from_numpy(pos_vec),
            torch.from_numpy(neg_vec),
        )

def train_dataset(dataset_name, path_mgr):
    print(f"\n{'='*60}")
    print(f"🚀 [非对称单塔 Neural Router] 训练: {dataset_name}")
    print(f"{'='*60}")
    
    cfg = get_config(dataset_name)
    random.seed(cfg["seed"])
    np.random.seed(cfg["seed"])
    torch.manual_seed(cfg["seed"])
    if dataset_name in DATASET_OVERRIDES:
        print(f"   ⚡ 使用数据集特化配置: epochs={cfg['epochs']}, lr={cfg['lr']}, patience={cfg['patience']}")
    
    paths = path_mgr.get_paths(dataset_name)
    os.makedirs(paths["drl_dir"], exist_ok=True)
    
    label_path = os.path.join(paths["drl_dir"], "topo_aware_labels.ivecs")
    print(f"Reading labels from: {label_path}")
    pairs = read_ivecs_labels(label_path)
    if pairs is None: 
        print(f"❌ 标签文件读取失败或不存在: {label_path}")
        return
    
    train_vec_path = paths["train_vectors"]
    print(f"Reading train vectors from: {train_vec_path}")
    
    max_q_idx = np.max(pairs[:, 0])
    query_vecs = read_fvecs(train_vec_path, max_rows=max_q_idx + 1) 
    
    if query_vecs is None: 
        print(f"❌ 训练向量读取失败: {train_vec_path}")
        return
        
    print(f"Loaded {len(query_vecs)} query vectors. Max label index: {max_q_idx}")

    entry_file_local = os.path.join(paths["graph_dir"], "entry_points.json")
    if not os.path.exists(entry_file_local):
         entry_file_local = os.path.join(path_mgr.project_root, f"dpc/{dataset_name}_results/dpc_hierarchical_results.json")

    if not os.path.exists(entry_file_local):
        print(f"❌ 找不到 entry_points.json: {entry_file_local}")
        return

    with open(entry_file_local, 'r') as f:
        data = json.load(f)
        if "combined_centers" in data:
            hub_ids = data["combined_centers"]
        elif "top_centers" in data:
            hub_ids = list(set(data["top_centers"] + data["bottom_centers"]))
            hub_ids.sort()
        else:
            print("❌ 无法找到 Hubs ID")
            return
    
    print(f"Reading base vectors from: {paths['base']}")
    base_vecs = read_fvecs(paths["base"])
    if base_vecs is None:
        print(f"❌ Base 向量读取失败: {paths['base']}")
        return

    try:
        hub_vecs = base_vecs[hub_ids]
    except IndexError:
        print(f"❌ Hub ID 越界，请检查 base 文件与 entry_points 是否匹配")
        return
    del base_vecs 
    
    input_dim  = hub_vecs.shape[1]
    target_dim = input_dim

    # 数据集规模自适应配置
    n_labels = int((pairs[:, 2] != -1).sum())
    aug_per_query = cfg["aug_per_query"]
    if n_labels < 2000:
        aug_per_query = max(16, aug_per_query * 2)
        print(f"   ⚡ 小数据集（{n_labels} 条），增强倍数提升至 {aug_per_query}x")

    dataset = QueryOracleDataset(
        query_vecs, hub_vecs, pairs,
        aug_per_query=aug_per_query,
        aug_noise_std=cfg["aug_noise_std"],
        neg_k=cfg["neg_k"]
    )
    generator = torch.Generator()
    generator.manual_seed(cfg["seed"])
    loader = DataLoader(dataset, batch_size=cfg["batch_size"], shuffle=True,
                        num_workers=4, pin_memory=True, drop_last=True, generator=generator)

    print(f"🔧 开启非对称模式，Neural Router 输出维度: {target_dim}")
    model = LightRouter(input_dim, target_dim, residue_scale=cfg["residue_scale"]).to(cfg["device"])
    n_params = sum(p.numel() for p in model.parameters())
    print(f"   📐 模型参数量: {n_params/1e3:.1f}K")
    optimizer = optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=1e-4)
    steps_per_epoch = max(1, len(dataset) // cfg["batch_size"])
    scheduler = optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=cfg["lr"],
        epochs=cfg["epochs"], steps_per_epoch=steps_per_epoch,
        pct_start=0.1, anneal_strategy='cos', div_factor=10, final_div_factor=100
    )

    print(f"🧠 开始训练 ({cfg['epochs']} Epochs, OneCycleLR) — Query-Guided Asymmetric InfoNCE + Dynamic Semi-Hard Mining (refresh every {cfg['neg_refresh_interval']} ep)...")
    model.train()

    best_loss = float('inf')
    patience_counter = 0
    pos_sim_last = neg_sim_last = None

    for epoch in range(cfg["epochs"]):
        # === 动态 Semi-Hard Negative Mining ===
        # 每隔 N epoch 用当前模型重新挖掘难负例（第 0 epoch 已在 __init__ 中用原始 hub 初始化）
        if epoch > 0 and epoch % cfg["neg_refresh_interval"] == 0:
            print(f"   🔄 Epoch {epoch+1}: 动态更新 Top-{cfg['neg_k']} Hard Negatives...")
            dataset.update_hard_negatives(model, cfg["device"])

        total_loss = 0
        steps = 0
        pos_sim_last = neg_sim_last = None

        for q_raw, pos_raw, neg_raw in loader:
            q_raw   = q_raw.to(cfg["device"], non_blocking=True)
            pos_raw = pos_raw.to(cfg["device"], non_blocking=True)
            neg_raw = neg_raw.to(cfg["device"], non_blocking=True)
            B = q_raw.size(0)

            optimizer.zero_grad()

            # ============================================================
            # 核心：非对称 Query-Guided 训练
            # Query 保持原始向量（0ms overhead），Hub 经过 MLP
            # 目标：cosine(raw_q, MLP(oracle_hub)) > cosine(raw_q, MLP(other_hub))
            # ============================================================

            pos_emb = model(pos_raw)
            neg_emb = model(neg_raw)

            q_n   = F.normalize(q_raw,   p=2, dim=1)
            pos_n = F.normalize(pos_emb, p=2, dim=1)
            neg_n = F.normalize(neg_emb, p=2, dim=1)

            # In-Batch InfoNCE：batch 内所有 hub 互为负例
            all_hub_n = torch.cat([pos_n, neg_n], dim=0)  # [2B, D]
            sim_matrix = torch.mm(q_n, all_hub_n.t()) / cfg["temperature"]  # [B, 2B]
            labels_nce = torch.arange(B, device=cfg["device"])
            loss_nce = F.cross_entropy(sim_matrix, labels_nce)

            # Hard Negative Triplet：强化 oracle vs geometric trap 分离
            pos_sim = (q_n * pos_n).sum(dim=1)
            neg_sim = (q_n * neg_n).sum(dim=1)
            loss_triplet = F.relu(neg_sim - pos_sim + 0.1).mean()

            loss = loss_nce + loss_triplet
            if not torch.isfinite(loss):
                raise RuntimeError(
                    f"Router epoch {epoch + 1} produced a non-finite loss"
                )
            loss.backward()
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            if not torch.isfinite(grad_norm):
                raise RuntimeError(
                    f"Router epoch {epoch + 1} produced a non-finite gradient norm"
                )
            optimizer.step()
            scheduler.step()  # OneCycleLR 每 step 更新
            total_loss += loss.item()
            steps += 1
            pos_sim_last = pos_sim.detach()
            neg_sim_last = neg_sim.detach()

        if steps == 0:
            print("⚠️ Warning: No steps in this epoch!")
            break

        avg_loss = total_loss / steps
        if not math.isfinite(avg_loss):
            raise RuntimeError(f"Router epoch {epoch + 1} average loss is non-finite")

        correct = (
            (pos_sim_last > neg_sim_last).float().mean().item()
            if pos_sim_last is not None else 0.0
        )
        if not math.isfinite(correct) or not 0.0 <= correct <= 1.0:
            raise RuntimeError(f"Router epoch {epoch + 1} accuracy diagnostic is invalid")
        print(
            f"ROUTER_SANITY Epoch={epoch + 1} Loss={avg_loss:.8f} "
            f"OracleGTNeg={correct:.8f} Steps={steps}"
        )

        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"   Epoch {epoch+1:03d} | Loss: {avg_loss:.4f} | "
                  f"Oracle>HardNeg: {correct*100:.1f}% | LR: {optimizer.param_groups[0]['lr']:.1e}")

        if avg_loss < best_loss - 1e-4:
            best_loss = avg_loss
            patience_counter = 0
        else:
            patience_counter += 1

        if patience_counter >= cfg["patience"]:
            if (epoch + 1) >= cfg["min_epochs"]:
                print(f"🛑 Early Stopping at Epoch {epoch+1}. Best Loss: {best_loss:.4f}")
                break
            elif patience_counter == cfg["patience"]:
                print(f"   [Info] Loss 已 {cfg['patience']} epoch 未改善，继续保底训练至 {cfg['min_epochs']} epoch。")

    print("💾 计算并保存非对称 Hub Embeddings...")
    model.eval()
    
    os.makedirs(paths["drl_dir"], exist_ok=True)
    hub_embs_path = os.path.join(paths["drl_dir"], "transformed_hubs.bin")
    hub_ids_path = os.path.join(paths["drl_dir"], "transformed_hub_ids.bin")
    raw_hubs_path = os.path.join(paths["drl_dir"], "raw_hubs.bin") 
    
    with torch.no_grad():
        all_hubs_tensor = torch.from_numpy(hub_vecs).to(cfg["device"])
        transformed_hubs = model(all_hubs_tensor).cpu().numpy()
        if not np.isfinite(transformed_hubs).all():
            raise RuntimeError("Router produced non-finite transformed hub vectors")

        # ============================================================
        # 【关键修复】训练目标是余弦空间，推理时 HNSW 也需要用内积。
        # 为保证 searchKnn (InnerProductSpace) 等价于余弦相似度，
        # 必须对 Hub 做 L2 归一化后再存储。
        # Query 在推理时也需归一化，但 Query 不经过 MLP，
        # 可以在 C++ 搜索前做归一化（零额外模型开销）。
        # ============================================================
        raw_norms_before = np.linalg.norm(transformed_hubs, axis=1)
        transformed_hubs_normed = transformed_hubs / (raw_norms_before[:, None] + 1e-8)
        transformed_norms = np.linalg.norm(transformed_hubs_normed, axis=1)
        if not np.isfinite(transformed_norms).all() or not np.allclose(
            transformed_norms, 1.0, atol=1e-4, rtol=1e-4
        ):
            raise RuntimeError(
                "Router transformed hub normalization failed: "
                f"min={transformed_norms.min()}, max={transformed_norms.max()}"
            )

        # Task5 存归一化后的 Hub（与 InnerProductSpace 匹配）
        transformed_hubs_normed.astype(np.float32).tofile(hub_embs_path)

        # Task2 存原始 Hub（不归一化，与 L2Space 匹配）
        hub_vecs.astype(np.float32).tofile(raw_hubs_path)
        np.array(hub_ids, dtype=np.int32).tofile(hub_ids_path)

        # 📊 变换幅度诊断
        diff = np.linalg.norm(transformed_hubs - hub_vecs, axis=1)
        raw_norms = np.linalg.norm(hub_vecs, axis=1)
        print(f"\n   📊 Hub 变换诊断:")
        print(f"      原始 Hub 范数: mean={raw_norms.mean():.3f}, std={raw_norms.std():.3f}")
        print(f"      变换幅度 (L2 diff): mean={diff.mean():.4f}, max={diff.max():.4f}")
        print(f"      归一化后 Hub 范数: mean={np.linalg.norm(transformed_hubs_normed, axis=1).mean():.4f} (应≈1.0)")

        # 🎯 核心诊断：oracle hub 在变换后（归一化后）的排名
        valid_pairs = pairs[pairs[:, 2] != -1]
        sample_size = min(500, len(valid_pairs))
        sample_idx  = np.random.choice(len(valid_pairs), sample_size, replace=False)
        sample_pairs = valid_pairs[sample_idx]

        q_sample  = query_vecs[sample_pairs[:, 0]].astype(np.float32)
        # 用归一化后的 Hub 计算排名（与推理时一致）
        h_n_np    = transformed_hubs_normed  # 已经归一化
        q_n_np    = q_sample / (np.linalg.norm(q_sample, axis=1, keepdims=True) + 1e-8)
        sims      = q_n_np @ h_n_np.T  # [sample, H]，等价于余弦相似度

        ranks = []
        for i in range(sample_size):
            oracle_sim = sims[i, sample_pairs[i, 1]]
            rank = int((sims[i] > oracle_sim).sum()) + 1
            ranks.append(rank)
        ranks = np.array(ranks)
        print(f"\n   🎯 Oracle Hub 排名（越低越好，理想是 Top-1）:")
        print(f"      Top-1 命中率: {(ranks==1).mean()*100:.1f}%")
        print(f"      Top-5 命中率: {(ranks<=5).mean()*100:.1f}%")
        print(f"      Top-10 命中率: {(ranks<=10).mean()*100:.1f}%")
        print(f"      平均排名: {ranks.mean():.1f} / {len(hub_ids)}")
        
    print(f"✅ 非对称 Hub 特征 (Neural) 已保存至: {hub_embs_path}")
    print(f"✅ 原始 Hub 特征 (Raw Baseline) 已保存至: {raw_hubs_path}")
    print(f"✅ Hub IDs 已保存至: {hub_ids_path}")
    print(f"✅ {dataset_name} 完成!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=CONFIG["datasets"])
    args = parser.parse_args()
    path_mgr = PathManager()
    failed = False
    for ds in args.datasets:
        try:
            train_dataset(ds, path_mgr)
        except Exception as e:
            failed = True
            print(f"⚠️ {ds} 异常: {e}")
            import traceback
            traceback.print_exc()
    if failed:
        sys.exit(1)
