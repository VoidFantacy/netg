import os
import json
import struct
import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader as TorchDataLoader
from sklearn.metrics import pairwise_distances

# ==========================================
#            暂时用不上这个代码

# 1. Python版 DataLoader (严格复刻 C++ 逻辑)  
# ==========================================

class DatasetReader:
    """基础文件二进制读取工具"""
    
    @staticmethod
    def read_fvecs(filename):
        if not os.path.exists(filename):
            raise FileNotFoundError(f"文件不存在: {filename}")
        
        file_size = os.path.getsize(filename)
        with open(filename, 'rb') as f:
            # 读取维度 d
            dim_bytes = f.read(4)
            dim = struct.unpack('i', dim_bytes)[0]
            
            # 计算向量个数
            vector_size = 4 + 4 * dim
            n_vecs = file_size // vector_size
            
            # 读取所有数据
            f.seek(0)
            raw_data = f.read()
            
        data = np.frombuffer(raw_data, dtype=np.float32)
        data = data.reshape(-1, dim + 1)
        return data[:, 1:].copy() # 去掉每行开头的维度信息

    @staticmethod
    def read_ivecs(filename):
        if not os.path.exists(filename):
            raise FileNotFoundError(f"文件不存在: {filename}")
            
        file_size = os.path.getsize(filename)
        with open(filename, 'rb') as f:
            dim_bytes = f.read(4)
            dim = struct.unpack('i', dim_bytes)[0]
            
            vector_size = 4 + 4 * dim
            n_vecs = file_size // vector_size
            
            f.seek(0)
            raw_data = f.read()
            
        data = np.frombuffer(raw_data, dtype=np.int32)
        data = data.reshape(-1, dim + 1)
        return data[:, 1:].copy()

class DataLoader:
    """
    复刻 C++ DataLoader 的 Python 实现
    逻辑：读取 settings.json -> 解析路径 -> 根据 type 加载对应文件
    """
    def __init__(self, dataset_name):
        # 1. 确定路径 (假设脚本在 code/benches/run/ 下)
        # 需要向上定位到 code/benches/datasets/settings.json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # base_root 对应代码项目的根目录 (例如 /path/to/ACSG)
        self.base_root = os.path.abspath(os.path.join(current_dir, "../../.."))
        
        settings_path = os.path.join(self.base_root, "code/benches/datasets/settings.json")
        if not os.path.exists(settings_path):
             # 尝试另一种常见路径结构
             settings_path = os.path.join(self.base_root, "benches/datasets/settings.json")
        
        if not os.path.exists(settings_path):
            raise FileNotFoundError(f"找不到配置文件: {settings_path}")

        # 2. 读取配置
        with open(settings_path, 'r') as f:
            settings = json.load(f)

        if dataset_name not in settings["datasets"]:
            raise ValueError(f"数据集 '{dataset_name}' 未在 settings.json 中定义")

        self.dataset_name = dataset_name
        self.dataset_settings = settings["datasets"][dataset_name]
        
        # root_dir 处理
        root_dir_rel = settings.get("root_dir", "./benches/datasets")
        # 将 root_dir 转换为绝对路径
        self.root_dir = os.path.abspath(os.path.join(self.base_root, root_dir_rel))
        
        # dataset_dir 处理
        self.dataset_dir = os.path.join(self.root_dir, self.dataset_settings["dataset_dir"])
        
        # 3. 缓存 Base Path (用于获取维度和中心点坐标)
        if "base_path" not in self.dataset_settings:
            raise ValueError(f"设置中缺少 'base_path' (Dataset: {dataset_name})")
            
        self.base_path = os.path.join(self.dataset_dir, self.dataset_settings["base_path"])
        
        # 4. 读取维度 d
        if os.path.exists(self.base_path):
            with open(self.base_path, 'rb') as f:
                self.d = struct.unpack('i', f.read(4))[0]
        else:
            print(f"⚠️ 警告: 底库文件不存在 {self.base_path}, 无法自动获取维度")
            self.d = 0

    def load_base(self):
        print(f"📥 加载底库 (Base): {self.base_path}")
        return DatasetReader.read_fvecs(self.base_path)

    def load_query(self, type_prefix=""):
        """
        对应 C++: auto [nq, xq] = data_loader.load_query("drl_train");
        逻辑: key = type_prefix + "_query_path"
        """
        key = "query_path" if type_prefix == "" else f"{type_prefix}_query_path"
        
        if key not in self.dataset_settings:
            raise ValueError(f"配置项 '{key}' 未在 {self.dataset_name} 中找到")
            
        rel_path = self.dataset_settings[key]
        full_path = os.path.join(self.dataset_dir, rel_path)
        
        print(f"📥 加载查询 ({key}): {full_path}")
        return DatasetReader.read_fvecs(full_path)

    def load_gt(self, type_prefix=""):
        """
        对应 C++: auto [k, gt] = data_loader.load_gt("drl_test");
        """
        key = "gt_path" if type_prefix == "" else f"{type_prefix}_gt_path"
        
        if key not in self.dataset_settings:
            # 尝试兼容 train_gt_path
            if type_prefix == "train" and "train_gt_path" in self.dataset_settings:
                key = "train_gt_path"
            else:
                raise ValueError(f"配置项 '{key}' 未在 {self.dataset_name} 中找到")

        rel_path = self.dataset_settings[key]
        full_path = os.path.join(self.dataset_dir, rel_path)
        
        print(f"📥 加载 GT ({key}): {full_path}")
        return DatasetReader.read_ivecs(full_path)

    def get_entry_points_path(self):
        # C++ graph_processor 的固定输出路径结构
        # code/graph_processing/{dataset}_results/entry_points.json
        # 注意：这里假设运行目录结构一致
        path = os.path.join(self.base_root, f"graph_processing/{self.dataset_name}_results/entry_points.json")
        # 尝试另一种可能的路径（如果是在 build 目录下运行）
        if not os.path.exists(path):
             path = os.path.join(self.base_root, f"code/graph_processing/{self.dataset_name}_results/entry_points.json")
        return path

    def get_model_output_dir(self):
        path = os.path.join(self.base_root, f"drl/{self.dataset_name}_results")
        os.makedirs(path, exist_ok=True)
        return path

# ==========================================
# 2. 分类器模型定义
# ==========================================

class EntryPointClassifier(nn.Module):
    def __init__(self, input_dim, num_classes):
        super().__init__()
        # 简单的3层MLP，输入查询 -> 输出每个中心的概率Logits
        self.net = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.3),
            
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(256, num_classes) 
        )
        
    def forward(self, x):
        return self.net(x)

# ==========================================
# 3. 训练与测试流程
# ==========================================

def train_and_test(dataset_name):
    print(f"\n{'='*60}")
    print(f"🚀 处理数据集: {dataset_name}")
    print(f"{'='*60}")
    
    # 1. 初始化 DataLoader
    try:
        loader = DataLoader(dataset_name)
    except Exception as e:
        print(f"❌ DataLoader 初始化失败: {e}")
        return

    # 2. 准备聚类中心数据
    # 需要加载 entry_points.json 获取中心 ID，再加载 base 获取向量
    ep_path = loader.get_entry_points_path()
    if not os.path.exists(ep_path):
        print(f"❌ 找不到入口点文件: {ep_path}，请先运行 graph_processor")
        return
        
    print(f"📥 读取聚类中心索引: {ep_path}")
    with open(ep_path, 'r') as f:
        entry_data = json.load(f)
        center_ids = entry_data.get('combined_centers', [])
        
    if not center_ids:
        print("❌ 聚类中心列表为空！")
        return

    # 加载底库向量以获取中心的坐标
    base_vectors = loader.load_base()
    center_vectors = base_vectors[center_ids]
    num_centers = len(center_ids)
    print(f"✅ 提取中心向量: {num_centers} 个, 维度 {loader.d}")
    
    # 释放大内存
    del base_vectors

    # 3. 加载训练数据 (DRL TRAIN)
    print("--- 准备训练数据 ---")
    train_queries = loader.load_query("drl_train")
    
    print(f"🏷️  生成训练标签 (计算每个训练查询离哪个中心最近)...")
    t0 = time.time()
    # 计算欧氏距离
    dists = pairwise_distances(train_queries, center_vectors, metric='euclidean', n_jobs=-1)
    # 这里的 labels 就是 0 到 num_centers-1 的整数
    train_labels = np.argmin(dists, axis=1)
    print(f"   耗时: {time.time() - t0:.2f}s")

    # 4. 训练模型
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"💻 训练设备: {device}")

    X_train = torch.FloatTensor(train_queries).to(device)
    y_train = torch.LongTensor(train_labels).to(device)
    
    dataset = TensorDataset(X_train, y_train)
    train_loader = TorchDataLoader(dataset, batch_size=256, shuffle=True)
    
    model = EntryPointClassifier(input_dim=loader.d, num_classes=num_centers).to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()
    
    print("\n🧠 开始训练...")
    model.train()
    epochs = 30
    for epoch in range(epochs):
        total_loss = 0
        correct = 0
        total = 0
        
        for bx, by in train_loader:
            optimizer.zero_grad()
            out = model(bx)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            _, preds = torch.max(out, 1)
            correct += (preds == by).sum().item()
            total += by.size(0)
            
        if (epoch+1) % 5 == 0:
            print(f"   Epoch {epoch+1:02d}/{epochs} | Loss: {total_loss/len(train_loader):.4f} | Train Acc: {correct/total:.2%}")

    # 5. 测试数据评估 (DRL TEST)
    print("\n--- 准备测试数据 ---")
    test_queries = loader.load_query("drl_test")
    
    # 生成测试集的“标准答案”用于计算准确率
    # (注意：这只是为了评估分类器准不准，实际搜索效果取决于C++部分)
    print("🏷️  生成测试集基准标签...")
    dists_test = pairwise_distances(test_queries, center_vectors, metric='euclidean', n_jobs=-1)
    test_labels_true = np.argmin(dists_test, axis=1)
    
    model.eval()
    X_test = torch.FloatTensor(test_queries).to(device)
    
    print("⚡ 执行预测...")
    with torch.no_grad():
        logits = model(X_test)
        probs = torch.softmax(logits, dim=1)
        # 获取 Top-1 和 Top-3 预测
        _, top3_indices = torch.topk(probs, k=3, dim=1)
        top3_indices = top3_indices.cpu().numpy()
        
    # 计算准确率
    # Top-1: 预测的第1个就是最近的中心
    top1_correct = np.sum(top3_indices[:, 0] == test_labels_true)
    # Top-3: 最近的中心在预测的前3个里
    top3_correct = 0
    for i in range(len(test_labels_true)):
        if test_labels_true[i] in top3_indices[i]:
            top3_correct += 1
            
    print(f"\n📊 分类器性能评估 (相对于几何最近中心):")
    print(f"   Top-1 Accuracy: {top1_correct / len(test_queries):.2%}")
    print(f"   Top-3 Accuracy: {top3_correct / len(test_queries):.2%}")
    
    # 6. 保存模型
    output_dir = loader.get_model_output_dir()
    
    # 保存 PyTorch 权重
    pth_path = os.path.join(output_dir, "classifier_model.pth")
    torch.save(model.state_dict(), pth_path)
    print(f"\n💾 模型已保存: {pth_path}")
    
    # 导出 ONNX (供 C++ 部署使用)
    onnx_path = os.path.join(output_dir, "drl_policy.onnx") # 沿用旧名称方便 C++ 识别，或者改名
    dummy_input = torch.randn(1, loader.d).to(device)
    
    torch.onnx.export(model, dummy_input, onnx_path, 
                      input_names=['query'],     # 输入名
                      output_names=['logits'],   # 输出名 (注意 C++ 推理代码需匹配此名称)
                      dynamic_axes={'query': {0: 'batch'}, 'logits': {0: 'batch'}},
                      opset_version=11)
                      
    print(f"✅ ONNX模型已导出: {onnx_path}")
    print(f"   (C++ inference 应该加载此模型，输入查询，输出 logits)")

if __name__ == "__main__":
    # 设置线程，防止 numpy 占满 CPU
    os.environ["OMP_NUM_THREADS"] = "16"
    
    # 定义要运行的数据集
    # DATASETS = ["sift100K", "sift1M", "glove", "gist", "deep"]
    DATASETS = ["sift100K", "glove"] # 示例：先跑两个
    
    for ds in DATASETS:
        try:
            train_and_test(ds)
        except Exception as e:
            print(f"⚠️  跳过 {ds}: {e}")
            # import traceback
            # traceback.print_exc()