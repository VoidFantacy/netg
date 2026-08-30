import json
import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import random
from torch.utils.data import DataLoader
from tqdm import tqdm

from cluster.model.train.model import Model
from cluster.model.train.utils import get_model_name
from cluster.model.train.dataset import get_dataset
from cluster.model.train.params import device

MODEL_PATH = os.getenv('GATE_MODEL_DIR', './models')


def eval_routing_acc(hub_model, dataset_params, device):
    """
    评估路由准确率：模型生成 hub embedding，对每条 query 选 cosine 最近的 hub，
    检查是否落在正样本集合中（与原作者 infer.py 逻辑一致）。
    """
    import struct

    def _read_fvecs(path):
        with open(path, 'rb') as f:
            d = struct.unpack('i', f.read(4))[0]
            f.seek(0, 2); n = f.tell() // (4 + 4 * d); f.seek(0)
            x = np.zeros((n, d), dtype=np.float32)
            for i in range(n):
                f.read(4); x[i] = np.frombuffer(f.read(d * 4), dtype=np.float32)
        return x

    sample_dir   = dataset_params['SAMPLE_PATH']
    hub_path     = dataset_params['HUB_PATH']
    query_path   = dataset_params['QUERY_PATH']
    subgraph_dir = dataset_params.get('SUBGRAPH_DIR', '')

    # 读取正样本集合
    pos_samples = []
    pos_file = os.path.join(sample_dir, 'pos_sample.txt')
    if not os.path.exists(pos_file):
        return 0.0
    with open(pos_file, 'r') as f:
        for line in f:
            pos_samples.append(set(map(int, line.strip().split())))
    neg_file = os.path.join(sample_dir, 'neg_sample.txt')
    with open(neg_file, 'r') as f:
        neg_counts = [len(line.strip().split()) for line in f]
    if len(pos_samples) != len(neg_counts):
        raise ValueError("validation positive/negative sample line counts differ")
    valid_query = np.array(
        [10 <= count <= 500 for count in neg_counts],
        dtype=bool,
    )
    if not valid_query.any():
        raise ValueError("validation contains no usable queries after GATE filtering")

    hubs       = _read_fvecs(hub_path)
    queries    = _read_fvecs(query_path)
    num_hubs   = len(hubs)
    if len(queries) < len(pos_samples):
        raise ValueError(
            f"validation query count {len(queries)} < sample count {len(pos_samples)}"
        )
    queries = queries[:len(pos_samples)]
    if len(queries) == 0:
        raise ValueError("validation set is empty")

    # 图特征
    from cluster.model.train.dataset import load_graph_features
    if subgraph_dir and os.path.isdir(subgraph_dir):
        graph_feats = load_graph_features(
            subgraph_dir,
            num_hubs,
            hubs,
            dataset_params.get('GRAPH2VEC_CSV'),
        )
    else:
        graph_feats = hubs.copy()

    hub_model.eval()
    with torch.no_grad():
        h_t = torch.from_numpy(hubs).to(device)
        g_t = torch.from_numpy(graph_feats).to(device)
        embs = hub_model(h_t, g_t)                     # [num_hubs, D]
        embs = F.normalize(embs, dim=1)                 # L2 归一化（cosine 搜索）

        q_t = torch.from_numpy(queries).to(device)
        # cosine similarity: [nq, num_hubs]
        sims = torch.mm(F.normalize(q_t, dim=1), embs.T)
        pred = torch.argmax(sims, dim=1).cpu().numpy()  # [nq]

    hit = sum(
        1 for q_id, p in enumerate(pred)
        if valid_query[q_id] and p in pos_samples[q_id]
    )
    acc = hit / int(valid_query.sum())
    hub_model.train()
    return acc


def train(model_params, dataset_params):
    seed = int(model_params.get('seed', 42))
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    input_dim  = model_params['input_dim']
    hidden_dim = model_params['hidden_dim']
    output_dim = model_params['output_dim']
    dropout    = model_params['dropout']
    lr         = model_params['lr']
    epochs     = model_params['epochs']
    batch_size = model_params['batch_size']

    hub_model = Model(input_dim, hidden_dim, output_dim, dropout).to(device)

    # TripletMarginWithDistanceLoss (余弦距离) — 与作者原始实现完全一致
    criterion = nn.TripletMarginWithDistanceLoss(
        distance_function=lambda x, y: 1.0 - F.cosine_similarity(x, y)
    ).to(device)

    optimizer = optim.Adam(hub_model.parameters(), lr=lr)

    print(f'>>> Training Start (Single-Tower + TripletLoss). Params: {model_params}')

    dataset    = get_dataset(dataset_params)
    efficient_unique_hubs = bool(model_params.get('efficient_unique_hubs', False))
    if efficient_unique_hubs and not dataset.return_hub_id:
        raise ValueError("efficient_unique_hubs requires dataset RETURN_HUB_ID=true")
    all_hubs = torch.from_numpy(dataset.hubs).to(device)
    all_graph_feats = torch.from_numpy(dataset.graph_feats).to(device)
    loader_generator = torch.Generator()
    loader_generator.manual_seed(seed)
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=(device.type == 'cuda'),
        generator=loader_generator,
    )

    os.makedirs(MODEL_PATH, exist_ok=True)

    # ── 原作者方法：按路由准确率（而非 loss）保存最优模型 ──
    best_acc  = -1.0
    best_loss = float('inf')
    best_epoch = 0
    epochs_without_improvement = 0
    early_stopping_patience = int(model_params.get('early_stopping_patience', 0))
    history = []
    model_path = f"{MODEL_PATH}/{get_model_name(model_params)}.pth"
    if os.path.exists(model_path):
        raise FileExistsError(f"refusing to overwrite existing model: {model_path}")

    validation_params = dataset_params.copy()
    validation_sample_path = dataset_params.get('VALIDATION_SAMPLE_PATH')
    validation_query_path = dataset_params.get('VALIDATION_QUERY_PATH')
    if bool(validation_sample_path) != bool(validation_query_path):
        raise ValueError("VALIDATION_SAMPLE_PATH and VALIDATION_QUERY_PATH must be supplied together")
    if validation_sample_path:
        validation_params['SAMPLE_PATH'] = validation_sample_path
        validation_params['QUERY_PATH'] = validation_query_path
        print(f">>> Selecting checkpoints on independent validation samples: {validation_sample_path}")
    else:
        print(">>> WARNING: selecting checkpoints on training samples (legacy GATE behavior)")

    for epoch in range(epochs):
        hub_model.train()
        running_loss = 0.0

        for batch in dataloader:
            if efficient_unique_hubs:
                ep_ids, pos_query, neg_query = [t.to(device) for t in batch]
                unique_ep_ids, inverse = torch.unique(ep_ids, sorted=True, return_inverse=True)
                unique_hub_emb = hub_model(
                    all_hubs[unique_ep_ids],
                    all_graph_feats[unique_ep_ids],
                )
                hub_emb = unique_hub_emb[inverse]
            else:
                node_feature, graph_feature, pos_query, neg_query = [t.to(device) for t in batch]
                hub_emb = hub_model(node_feature, graph_feature)
            loss = criterion(hub_emb, pos_query, neg_query)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

        avg_loss = running_loss / len(dataloader)

        # 每轮评估路由准确率（与原作者 infer() 每 epoch 调用一致）
        cur_acc = eval_routing_acc(hub_model, validation_params, device)

        if cur_acc > best_acc:
            best_acc = cur_acc
            best_epoch = epoch + 1
            epochs_without_improvement = 0
            torch.save(hub_model, model_path)   # 保存最优 acc 的模型（与原作者一致）
        else:
            epochs_without_improvement += 1

        print(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.4f}, "
              f"RouteAcc: {cur_acc:.4f}, Best: {best_acc:.4f}")
        history.append({
            'epoch': epoch + 1,
            'loss': avg_loss,
            'validation_route_acc': cur_acc,
            'best_validation_route_acc': best_acc,
        })
        if early_stopping_patience > 0 and epochs_without_improvement >= early_stopping_patience:
            print(f"Early stopping: no validation improvement for "
                  f"{early_stopping_patience} epochs (best epoch={best_epoch}).")
            break

    print(f"✅ Training finished. Best RouteAcc={best_acc:.4f}. Model saved to {model_path}")
    report = {
        'schema_version': 1,
        'model_params': model_params,
        'dataset_params': dataset_params,
        'triplet_count': len(dataset),
        'completed_epochs': len(history),
        'requested_max_epochs': epochs,
        'early_stopping_patience': early_stopping_patience,
        'early_stopped': len(history) < epochs,
        'best_epoch': best_epoch,
        'best_validation_route_acc': best_acc,
        'checkpoint': model_path,
        'history': history,
    }
    with open(os.path.join(MODEL_PATH, 'training_report.json'), 'w') as f:
        json.dump(report, f, indent=2)
        f.write('\n')


if __name__ == '__main__':
    config_path = os.getenv('GATE_CONFIG_PATH')
    if not config_path:
        raise ValueError("Please set env var GATE_CONFIG_PATH")

    with open(config_path, 'r') as f:
        conf = json.load(f)

    train(conf['model'], conf['dataset'])
