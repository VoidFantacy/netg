import json
import os
import torch
import numpy as np
import struct
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

from cluster.model.train.model import Model
from cluster.model.train.dataset import load_graph_features
from cluster.model.train.utils import get_model_name
from cluster.model.train.params import device

# 动态获取模型路径
MODEL_DIR = os.getenv('GATE_MODEL_DIR', './models')


def read_fvecs(filename):
    """读取 fvecs 格式"""
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


def write_fvecs(filename, data):
    """写入 fvecs 格式"""
    print(f"Writing {data.shape[0]} vectors of dim {data.shape[1]} to {filename}...")
    with open(filename, 'wb') as f:
        d = data.shape[1]
        vec_d = np.array([d], dtype=np.int32)
        for vec in data:
            f.write(vec_d.tobytes())
            f.write(vec.astype(np.float32).tobytes())


def infer_and_save(model_params, dataset_params, output_path):
    input_dim  = model_params['input_dim']
    hidden_dim = model_params['hidden_dim']
    output_dim = model_params['output_dim']
    dropout    = model_params['dropout']

    # 1. 加载 Hub Tower 模型（单塔模型，与作者实现一致，使用 torch.save(model) 格式）
    model_name = get_model_name(model_params)
    model_path = f"{MODEL_DIR}/{model_name}.pth"

    if not os.path.exists(model_path):
        print(f"❌ Error: Hub model file not found at {model_path}")
        return

    print(f">>> Loading hub model from {model_path}...")
    loaded = torch.load(model_path, map_location=device, weights_only=False)
    # 兼容 torch.save(model) 和 torch.save(state_dict) 两种格式
    if isinstance(loaded, Model):
        hub_model = loaded.to(device)
    else:
        hub_model = Model(input_dim, hidden_dim, output_dim, dropout).to(device)
        hub_model.load_state_dict(loaded)

    hub_model.eval()

    # 2. 加载 Hub Node Feature
    hub_path = dataset_params['HUB_PATH']
    print(f">>> Loading Hubs for inference from {hub_path}...")
    hubs = read_fvecs(hub_path)
    num_hubs = len(hubs)

    # 3. 加载 Hub Graph Feature（与训练时保持一致，从子图 JSON 均值池化）
    subgraph_dir = dataset_params.get('SUBGRAPH_DIR', '')
    if subgraph_dir and os.path.isdir(subgraph_dir):
        graph_feats = load_graph_features(
            subgraph_dir,
            num_hubs,
            hubs,
            dataset_params.get('GRAPH2VEC_CSV'),
        )
    else:
        print(">>> ⚠️  SUBGRAPH_DIR not found, using node features as graph features.")
        graph_feats = hubs.copy()

    # 4. 构建 DataLoader（node + graph 拼成 pair）
    hubs_tensor  = torch.from_numpy(hubs)
    graph_tensor = torch.from_numpy(graph_feats)
    infer_dataset = TensorDataset(hubs_tensor, graph_tensor)
    dataloader = DataLoader(
        infer_dataset,
        batch_size=model_params['batch_size'] * 2,
        shuffle=False
    )

    all_embeddings = []

    # 5. 执行推理
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Inferring Hub Embeddings"):
            node_feature  = batch[0].to(device)   # [B, D]
            graph_feature = batch[1].to(device)    # [B, D]
            emb = hub_model(node_feature, graph_feature)
            all_embeddings.append(emb.cpu().numpy())

    # 6. 保存 Hub Embeddings（不做 L2 归一化，因为 C++ 使用 CosSpace 自动计算余弦距离）
    final_embeddings = np.concatenate(all_embeddings, axis=0)
    print(f">>> Generated Hub Embeddings Shape: {final_embeddings.shape}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    write_fvecs(output_path, final_embeddings)
    print(f"✅ Hub Embeddings saved to {output_path}")
    # 注：单塔模型，搜索时直接用原始 query 在 CosSpace 中路由，不需要 QueryEncoder


if __name__ == '__main__':
    config_path    = os.getenv('GATE_CONFIG_PATH')
    output_emb_path = os.getenv('GATE_EMB_OUTPUT')

    if not config_path or not output_emb_path:
        raise ValueError("Please set env vars: GATE_CONFIG_PATH and GATE_EMB_OUTPUT")

    with open(config_path, 'r') as f:
        conf = json.load(f)

    infer_and_save(conf['model'], conf['dataset'], output_emb_path)
