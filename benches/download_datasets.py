import os
import requests
import struct
import numpy as np
import shutil
from tqdm import tqdm

# ================= 配置区 =================
# 最终修正：所有 GT 都使用 .ibin 链接，并由脚本自动转换
DATASETS = {
    "DEEP10M": {
        "base_url": "https://storage.yandexcloud.net/yandex-research/ann-datasets/DEEP/base.10M.fbin",
        "query_url": "https://storage.yandexcloud.net/yandex-research/ann-datasets/DEEP/query.public.10K.fbin",
        "gt_url": "https://storage.yandexcloud.net/yandex-research/ann-datasets/DEEP/groundtruth.public.10K.ibin", 
    },
    "MSTuring": {
        # MSTuring 已经成功，这里保留以防万一
        "base_url": "https://storage.yandexcloud.net/yandex-research/ann-datasets/MSTuring/base.10M.fbin",
        "query_url": "https://storage.yandexcloud.net/yandex-research/ann-datasets/MSTuring/query.public.100K.fbin",
        "gt_url": "https://storage.yandexcloud.net/yandex-research/ann-datasets/MSTuring/groundtruth.public.100K.ibin",
    },
    "YandexT2I": {
        "base_url": "https://storage.yandexcloud.net/yandex-research/ann-datasets/T2I/base.10M.fbin",
        "query_url": "https://storage.yandexcloud.net/yandex-research/ann-datasets/T2I/query.public.100K.fbin",
        "gt_url": "https://storage.yandexcloud.net/yandex-research/ann-datasets/T2I/groundtruth.public.100K.ibin",
    }
}

ROOT_DIR = "benches/datasets"

# ================= 核心功能函数 =================

def download_file(url, dest_path):
    if os.path.exists(dest_path):
        print(f"🔄 File exists, skipping download: {dest_path}")
        return True

    print(f"⬇️ Downloading {url} to {dest_path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status() # 遇到 404 会报错
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024 
        progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)
        
        with open(dest_path, 'wb') as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()
        return True
    except Exception as e:
        print(f"❌ Download failed for {url}: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False

def convert_bin_to_vecs(bin_path, vecs_path, is_int=False):
    if os.path.exists(vecs_path):
        print(f"🔄 Converted file exists, skipping: {vecs_path}")
        return

    print(f"⚙️ Converting {bin_path} -> {vecs_path} ...")
    
    try:
        # ibin 是 int32, fbin 是 float32
        dtype = np.int32 if is_int else np.float32
        
        with open(bin_path, 'rb') as f_in, open(vecs_path, 'wb') as f_out:
            # 读取头部
            header_bytes = f_in.read(8)
            if len(header_bytes) < 8:
                print("❌ Error: File too short.")
                return
            
            n_points = struct.unpack('I', header_bytes[0:4])[0]
            n_dim = struct.unpack('I', header_bytes[4:8])[0]
            
            print(f"   Meta: N={n_points}, d={n_dim}")
            
            # fvecs/ivecs 头部
            vec_header = struct.pack('i', n_dim)
            
            chunk_size = 10000 
            bytes_per_vec = n_dim * 4
            
            for _ in tqdm(range(0, n_points, chunk_size), desc="Converting"):
                current_chunk = min(chunk_size, n_points - _)
                data = f_in.read(current_chunk * bytes_per_vec)
                
                if not data:
                    break
                    
                vectors = np.frombuffer(data, dtype=dtype).reshape(-1, n_dim)
                for vec in vectors:
                    f_out.write(vec_header)
                    f_out.write(vec.tobytes())
                    
        print(f"✅ Conversion successful.")
        
    except Exception as e:
        print(f"❌ Error converting {bin_path}: {e}")

def main():
    if not os.path.exists(ROOT_DIR):
        os.makedirs(ROOT_DIR)
        
    for ds_name, urls in DATASETS.items():
        print(f"\n{'='*60}")
        print(f"📦 Processing Dataset: {ds_name}")
        print(f"{'='*60}")
        
        ds_dir = os.path.join(ROOT_DIR, ds_name)
        if not os.path.exists(ds_dir):
            os.makedirs(ds_dir)
            
        # 1. Base Vectors
        base_bin = os.path.join(ds_dir, "base.10M.fbin")
        base_vecs = os.path.join(ds_dir, "base.10M.fvecs")
        if download_file(urls["base_url"], base_bin):
            convert_bin_to_vecs(base_bin, base_vecs, is_int=False)
        
        # 2. Query Vectors
        query_bin = os.path.join(ds_dir, os.path.basename(urls["query_url"]))
        query_vecs = query_bin.replace(".fbin", ".fvecs")
        if download_file(urls["query_url"], query_bin):
            convert_bin_to_vecs(query_bin, query_vecs, is_int=False)
        
        # 3. Ground Truth (bin -> ivecs)
        gt_bin = os.path.join(ds_dir, os.path.basename(urls["gt_url"]))
        gt_vecs = gt_bin.replace(".ibin", ".ivecs") # 强制转换
        
        if download_file(urls["gt_url"], gt_bin):
            convert_bin_to_vecs(gt_bin, gt_vecs, is_int=True)

    print(f"\n{'='*60}")
    print("🎉 All datasets processed!")

if __name__ == "__main__":
    main()