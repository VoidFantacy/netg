import numpy as np
import faiss
import os
import time
import json
import sys
from tqdm import tqdm

# 禁用 FAISS 内部多线程警告
faiss.omp_set_num_threads(16) 

# ----------------------------------------------------------------
# 1. 生成参数配置 (已更新)
# ----------------------------------------------------------------
GEN_PARAMS = {
    "sift100k": {"dim": 128, "noise_ratio": 0.05, "n_total_queries": 10000},
    "sift1m":   {"dim": 128, "noise_ratio": 0.05, "n_total_queries": 20000},
    "sift10m":  {"dim": 128, "noise_ratio": 0.05, "n_total_queries": 100000}, 
    "deep":     {"dim": 96,  "noise_ratio": 0.02, "n_total_queries": 10000}, 
    "glove":    {"dim": 300, "noise_ratio": 0.02, "n_total_queries": 10000}, 
    "gist":     {"dim": 960, "noise_ratio": 0.02, "n_total_queries": 20000},
}

# ----------------------------------------------------------------
# 2. 通用配置 (已更新)
# ----------------------------------------------------------------
COMMON_CONFIG = {
    "skew_ratio": 0.8,            
    "n_clusters": 100,            
    "n_hot_clusters": 5,          
    "min_cluster_size_ratio": 0.2,
    "topk": 100,                  
    "seed": 2025,
    "ratio_acpg": 0.80,        # 80% 用于 ACPG 训练
    "ratio_drl_train": 0.00,   # 0% 用于 DRL 训练
    "ratio_drl_test": 0.20,    # 20% 用于测试
}

# ----------------------------------------------------------------
# 3. 路径定位核心逻辑
# ----------------------------------------------------------------

# 1. 获取脚本所在的 'run' 目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 获取上一级 'benches' 目录
BENCHES_DIR = os.path.dirname(SCRIPT_DIR)

# 3. 拼接出 'datasets' 目录
DATASETS_ROOT = os.path.join(BENCHES_DIR, "datasets")

def load_project_settings(json_name="settings.json"):
    # 直接去 datasets 目录找 json
    json_path = os.path.join(DATASETS_ROOT, json_name)
    
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"未找到配置文件: {json_path}")
            
    with open(json_path, 'r', encoding='utf-8') as f:
        print(f">>> 加载配置文件: {json_path}")
        return json.load(f)

def get_dataset_paths(settings, dataset_key):
    """
    直接使用计算好的 DATASETS_ROOT
    """
    if dataset_key not in settings:
        return None, None
    
    ds_conf = settings[dataset_key]
    dataset_dir_name = ds_conf.get("dataset_dir", "")
    base_filename = ds_conf.get("base_path", "")
    
    # 路径拼接
    base_full_path = os.path.join(DATASETS_ROOT, dataset_dir_name, base_filename)
    output_dir = os.path.join(DATASETS_ROOT, dataset_dir_name)
    
    return base_full_path, output_dir

def read_fvecs(filename):
    if not os.path.exists(filename):
        print(f"    [Error] 文件不存在: {filename}")
        raise FileNotFoundError(f"文件系统找不到: {filename}")
    file_size = os.path.getsize(filename)
    with open(filename, 'rb') as f:
        dim = np.fromfile(f, dtype=np.int32, count=1)[0]
        n_vecs = file_size // (4 + 4 * dim)
        f.seek(0)
        raw = np.fromfile(f, dtype=np.int32)
    return raw.reshape(n_vecs, dim + 1)[:, 1:].view(np.float32)

def write_fvecs(filename, data):
    # data.shape[1] 这里如果是 (0,) 形状就会报错
    # 所以传入前必须保证是 (N, dim) 形状
    dim = data.shape[1]
    header = np.array([dim], dtype=np.int32)
    with open(filename, 'wb') as f:
        for vec in data:
            f.write(header.tobytes())
            f.write(vec.tobytes())

def write_ivecs(filename, data):
    n_rows, n_cols = data.shape
    header = np.array([n_cols], dtype=np.int32)
    with open(filename, 'wb') as f:
        for i in range(n_rows):
            f.write(header.tobytes())
            f.write(data[i].astype(np.int32).tobytes())

def estimate_avg_norm(data, sample_size=5000):
    n = min(len(data), sample_size)
    if n <= 0: return 0.0
    indices = np.random.choice(len(data), n, replace=False)
    sample = data[indices]
    norms = np.linalg.norm(sample, axis=1)
    return float(np.mean(norms))

# ----------------------------------------------------------------
# 子集生成逻辑
# ----------------------------------------------------------------
def generate_skewed_subset(set_name, base_data, hot_base_indices, dim, n_total, noise_ratio, avg_norm_cache):
    noise_std = (avg_norm_cache * noise_ratio) / np.sqrt(dim)
    
    queries = []
    n_base = base_data.shape[0]
    
    if n_total > 0:
        n_hot_queries = int(n_total * COMMON_CONFIG['skew_ratio'])
        n_cold_queries = n_total - n_hot_queries
        
        # Hot
        if n_hot_queries > 0:
            seed_indices = np.random.choice(hot_base_indices, size=n_hot_queries, replace=True) 
            for idx in tqdm(seed_indices, desc=f"[{set_name}] Gen Hot ({n_hot_queries})", file=sys.stderr):
                seed_vec = base_data[idx]
                noise = np.random.normal(0, noise_std, dim).astype(np.float32)
                queries.append(seed_vec + noise)
            
        # Cold
        if n_cold_queries > 0:
            cold_indices = np.random.choice(n_base, n_cold_queries, replace=False)
            for idx in tqdm(cold_indices, desc=f"[{set_name}] Gen Cold ({n_cold_queries})", file=sys.stderr):
                seed_vec = base_data[idx]
                noise = np.random.normal(0, noise_std, dim).astype(np.float32)
                queries.append(seed_vec + noise)
        
    queries = np.array(queries, dtype=np.float32)
    np.random.shuffle(queries)
    
    # ------------------ [关键修复] 防止 0 查询导致崩溃 ------------------
    if len(queries) == 0:
        print(f"[{set_name}] Skipping GT generation (0 queries)")
        
        # [核心修正]：显式 reshape 为 (0, dim)，确保有 2 个维度
        # 这样 write_fvecs 里的 data.shape[1] 才能正确取到 dim
        queries = queries.reshape(0, dim)
        
        # 返回空的查询和空的 GT
        return queries, np.zeros((0, COMMON_CONFIG['topk']), dtype=np.int32)
    # ------------------------------------------------------------------
    
    # GT - 强制使用 CPU
    sys.stderr.write(f"[{set_name}] Computing GT (CPU Mode)...\n")
    
    # 直接初始化 CPU 索引
    index_gt = faiss.IndexFlatL2(dim)
    index_gt.add(base_data)
    
    gt_indices = []
    batch_size = 1000
    for i in range(0, len(queries), batch_size):
        batch_q = queries[i : i+batch_size]
        _, batch_I = index_gt.search(batch_q, COMMON_CONFIG['topk'])
        gt_indices.append(batch_I)
    
    gt_indices = np.vstack(gt_indices)
    # 删除索引释放内存
    del index_gt 
    return queries, gt_indices

# ----------------------------------------------------------------
# 核心处理函数
# ----------------------------------------------------------------
def process_single_dataset(key_name, gen_params, datasets_config):
    # 1. 解析路径
    base_path, output_dir = get_dataset_paths(datasets_config, key_name)
    if not base_path:
        print(f"!!! 跳过 '{key_name}': 未找到配置。")
        return

    print("\n" + "#"*60)
    print(f" >>> 开始处理任务: {key_name.upper()}")
    print(f"     检测路径: {base_path}")
    print("#"*60)

    # 2. 读取数据
    try:
        base = read_fvecs(base_path)
    except Exception as e:
        print(f"!!! 读取错误: {e}")
        return

    n_base, dim = base.shape
    if dim != gen_params['dim']:
        print(f"!!! 维度警告: 配置({gen_params['dim']}) vs 实际({dim})")

    # [1/4] 分析数据统计特性
    print(f"\n>>> [1/4] 分析数据统计特性...")
    avg_norm = estimate_avg_norm(base)
    target_std = (avg_norm * gen_params['noise_ratio']) / np.sqrt(dim)
    
    print("-" * 50)
    print(f"   [Data Analysis] 向量平均模长 (Avg Norm) : {avg_norm:.4f}")
    print(f"   [Calculated]    应用的高斯噪声 (Std)    : {target_std:.4f}")
    print("-" * 50)

    # [2/4] 均衡聚类
    print(f"\n>>> [2/4] 执行均衡 K-Means (K={COMMON_CONFIG['n_clusters']})...")
    avg_cluster_size = n_base / COMMON_CONFIG['n_clusters']
    min_points = int(avg_cluster_size * COMMON_CONFIG['min_cluster_size_ratio'])
    
    kmeans = faiss.Kmeans(dim, COMMON_CONFIG['n_clusters'], niter=20, verbose=False, min_points_per_centroid=min_points, seed=COMMON_CONFIG['seed'])
    kmeans.train(base)
    
    index_flat = faiss.IndexFlatL2(dim)
    index_flat.add(kmeans.centroids)
    _, cluster_assignments = index_flat.search(base, 1) 
    cluster_assignments = cluster_assignments.flatten()
    
    # [3/4] 选择热点
    print(f"\n>>> [3/4] 选择热点区域...")
    unique, counts = np.unique(cluster_assignments, return_counts=True)
    cluster_sizes = dict(zip(unique, counts))
    
    safe_threshold = max(50, int(avg_cluster_size * 0.1))
    valid_candidates = [cid for cid, size in cluster_sizes.items() if size >= safe_threshold]
    
    if len(valid_candidates) < COMMON_CONFIG['n_hot_clusters']:
        valid_candidates = list(cluster_sizes.keys())
        
    hot_cluster_ids = np.random.choice(valid_candidates, COMMON_CONFIG['n_hot_clusters'], replace=False)
    
    hot_base_indices = []
    for cid in hot_cluster_ids:
        indices = np.where(cluster_assignments == cid)[0]
        hot_base_indices.extend(indices)
    hot_base_indices = np.array(hot_base_indices)
    
    print(f"   选中热点簇 ID: {hot_cluster_ids}")
    print(f"   热点样本池大小: {len(hot_base_indices)}")

    # [4/4] 生成与保存
    print(f"\n>>> [4/4] 生成查询集并保存...")
    sets_to_generate = [
        ("acpg", COMMON_CONFIG['ratio_acpg']),
        ("drl_train", COMMON_CONFIG['ratio_drl_train']),
        ("drl_test", COMMON_CONFIG['ratio_drl_test'])
    ]
    
    base_filename = os.path.basename(base_path)
    prefix = base_filename.replace("_base.fvecs", "").replace(".fvecs", "")
    if "base" in prefix: prefix = prefix.replace("_base", "") 
    
    for suffix, ratio in sets_to_generate:
        n_queries = int(gen_params['n_total_queries'] * ratio)
        out_q_name = f"{prefix}_{suffix}_query.fvecs"
        out_gt_name = f"{prefix}_{suffix}_groundtruth.ivecs"
        
        queries, gt = generate_skewed_subset(
            suffix.upper(), base, hot_base_indices, dim, n_queries, gen_params['noise_ratio'], avg_norm
        )
        
        write_fvecs(os.path.join(output_dir, out_q_name), queries)
        write_ivecs(os.path.join(output_dir, out_gt_name), gt)
        print(f"   -> 已保存: {out_q_name}")

# ----------------------------------------------------------------
# 主入口
# ----------------------------------------------------------------
def run_batch_job():
    print(f"脚本目录: {SCRIPT_DIR}")
    print(f"数据目录: {DATASETS_ROOT}")
    
    if not os.path.exists(DATASETS_ROOT):
        print(f"!!! 严重错误: 无法找到数据目录: {DATASETS_ROOT}")
        return

    try:
        full_settings = load_project_settings()
    except Exception as e:
        print(f"错误: {e}")
        return

    if "datasets" in full_settings:
        datasets_config = full_settings["datasets"]
    else:
        datasets_config = full_settings

    TARGET_DATASETS = [k for k in GEN_PARAMS.keys()] 
    
    start_time = time.time()
    for key in TARGET_DATASETS:
        if key not in GEN_PARAMS: continue
            
        gen_params = GEN_PARAMS[key]
        
        found_key = None
        if key in datasets_config:
            found_key = key
        else:
            for sk in datasets_config.keys():
                if sk.lower() == key.lower():
                    found_key = sk
                    break
        
        if found_key:
            process_single_dataset(found_key, gen_params, datasets_config)
        else:
            print(f"跳过 '{key}': 配置文件中未找到。")

    print(f"\n全部完成。总耗时: {time.time() - start_time:.2f}s")

if __name__ == "__main__":
    np.random.seed(COMMON_CONFIG['seed'])
    run_batch_job()