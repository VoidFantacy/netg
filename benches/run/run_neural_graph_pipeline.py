import subprocess
import os
import datetime
import sys
import json
import struct
import numpy as np

# 尝试导入 onnxruntime
try:
    import onnxruntime as ort
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False
    print("⚠️  Warning: 'onnxruntime' 未安装。将跳过 Neural 坐标生成步骤。")

def run_command(cmd, log_file):
    print(f"执行: {' '.join(cmd)}")
    log_file.write(f"CMD: {' '.join(cmd)}\n")
    log_file.flush()
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in process.stdout:
        print(line, end="")
        log_file.write(line)
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)

def read_fvecs(filename):
    if not os.path.exists(filename): return None
    file_size = os.path.getsize(filename)
    with open(filename, 'rb') as f:
        dim_bytes = f.read(4)
        if not dim_bytes: return None
        dim = struct.unpack('i', dim_bytes)[0]
        vec_size = 4 + 4 * dim
        n = file_size // vec_size
        f.seek(0)
        data = np.fromfile(f, dtype=np.float32, count=n * (dim + 1))
        data = data.reshape(n, dim + 1)[:, 1:] 
    return data

def generate_neural_coords(dataset, base_dir, paths):
    if not HAS_ONNX: return
    
    # 1. 检查模型
    onnx_model_path = f"drl/{dataset}_results/ae_encoder.onnx"
    norm_path = f"drl/{dataset}_results/ae_norm.json"
    
    if not os.path.exists(onnx_model_path):
        print(f"   [Neural Coords] ℹ️  未找到 Router 模型 ({onnx_model_path})。跳过生成。")
        return

    print(f"   [Neural Coords] 🔄 检测到 Router 模型，正在生成 Neural 坐标图...")

    # 2. 读取归一化参数
    try:
        with open(norm_path, 'r') as f:
            norm_data = json.load(f)
            mean = np.array(norm_data["mean"], dtype=np.float32)
            std = np.array(norm_data["std"], dtype=np.float32)
    except Exception as e:
        print(f"   ❌ 读取归一化参数失败: {e}")
        return

    # 3. 读取聚类中心
    if not os.path.exists(paths["cluster"]):
        print(f"   ❌ 找不到聚类文件: {paths['cluster']}")
        return
        
    with open(paths["cluster"], 'r') as f:
        entry_data = json.load(f)
    hub_ids = entry_data["combined_centers"]

    # 4. 智能定位 settings.json 和 Base 路径
    # 获取脚本所在目录 (code/benches/run)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 尝试寻找 settings.json
    possible_settings = [
        os.path.abspath(os.path.join(script_dir, "../datasets/settings.json")), # 相对脚本位置
        "/path/to/ACSG/benches/datasets/settings.json",                 # 绝对路径
        "benches/datasets/settings.json",                                       # 相对CWD
        "../datasets/settings.json"                                             # 相对CWD
    ]
    
    settings_path = None
    for p in possible_settings:
        if os.path.exists(p):
            settings_path = p
            break
            
    if not settings_path:
        print("   ❌ 错误: 无法找到 settings.json，无法定位原始数据。")
        return
    else:
        print(f"   -> 加载配置文件: {settings_path}")

    try:
        with open(settings_path, "r") as f:
            settings = json.load(f)
        
        ds_conf = settings["datasets"].get(dataset)
        if not ds_conf:
            print(f"   ❌ settings.json 中未找到 {dataset} 的配置")
            return

        # 拼接 Base 路径：settings所在目录 / dataset_dir / base_path
        settings_dir = os.path.dirname(settings_path)
        base_path = os.path.join(settings_dir, ds_conf["dataset_dir"], ds_conf["base_path"])
        
    except Exception as e:
        print(f"   ❌ 配置文件解析错误: {e}")
        return

    print(f"   -> 读取原始向量: {base_path}")
    if not os.path.exists(base_path):
        print(f"   ❌ 错误: Base 向量文件不存在")
        return

    base_vecs = read_fvecs(base_path)
    if base_vecs is None:
        print(f"   ❌ 错误: 读取失败")
        return

    try:
        hub_vecs = base_vecs[hub_ids]
    except IndexError:
        print(f"   ❌ 索引越界")
        return
    del base_vecs 
    
    # 5. 归一化 & 推理
    hub_vecs = (hub_vecs - mean) / (std + 1e-6)

    try:
        sess = ort.InferenceSession(onnx_model_path)
        input_name = sess.get_inputs()[0].name
        output_name = sess.get_outputs()[0].name
        reduced_hubs = sess.run([output_name], {input_name: hub_vecs})[0]
    except Exception as e:
        print(f"   ❌ ONNX 推理失败: {e}")
        return

    # 6. 保存
    entry_data["centers_reduced"] = reduced_hubs.tolist()
    neural_entry_path = os.path.join(base_dir, "neural_entry_points.json")
    
    with open(neural_entry_path, 'w') as f:
        json.dump(entry_data, f)
        
    print(f"   ✅ [成功] Neural 坐标图已生成: {neural_entry_path}")


def main():
    DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 自动寻找 build 目录
    possible_build_dirs = [
        "../../build/benches", # 相对 run/ 目录
        "../build/benches",    # 相对 benches/
        "./build/benches",     # 相对根目录
        "/path/to/ACSG/build/benches"
    ]
    BUILD_DIR = "./build/benches"
    for d in possible_build_dirs:
        if os.path.exists(d):
            BUILD_DIR = d
            break
            
    executables = {
        "gen_data": f"{BUILD_DIR}/bench_generate_graph_train_data",
        "processor": f"{BUILD_DIR}/graph_processor"
    }
    
    for name, path in executables.items():
        if not os.path.exists(path):
            print(f"❌ 错误: 找不到可执行文件 {path}")
            return

    os.environ["OMP_NUM_THREADS"] = "16"
    print("🚀 启动神经建图全流程 (Fast Mode)...\n")
    
    for dataset in DATASETS:
        print(f"\n{'='*60}\n处理数据集: {dataset}\n{'='*60}")
        base_dir = f"graph_processing/{dataset}_results"
        os.makedirs(base_dir, exist_ok=True)
        
        paths = {
            "acpg": f"acpg/{dataset}_index/acpg_nsg.json",
            "cluster": f"{base_dir}/entry_points.json",
            "train_edges": f"{base_dir}/edges_train.txt",
            "neural_graph": f"{base_dir}/neural_graph.txt",
            "pca_model": f"{base_dir}/pca_transform.bin"
        }
        
        if not os.path.exists(paths["acpg"]):
            print(f"⚠️  跳过 {dataset}: 缺少 ACPG 索引")
            continue
        if not os.path.exists(paths["cluster"]):
            print(f"⚠️  跳过 {dataset}: 缺少聚类文件")
            continue
        
        log_path = f"{base_dir}/neural_pipeline.log"
        with open(log_path, "w", encoding="utf-8") as log:
            try:
               
                print("\n>>> Step 1: 挖掘黄金边...")
                run_command([
                    executables["gen_data"], 
                    "--dataset", dataset, 
                    "--cluster_file", paths["cluster"], 
                    "--output_file", paths["train_edges"], 
                    "--query_type", "acpg"
                ], log)
                
                # Step 2
                print("\n>>> Step 2: 训练建图模型 & 生成 PCA...")
                run_command([
                    "python3", f"{SCRIPT_DIR}/build_neural_graph.py",
                    "--data_file", paths["train_edges"],
                    "--output_graph", paths["neural_graph"],
                    "--output_pca", paths["pca_model"],
                    "--K", "32"
                ], log)
                
                # Step 3
                print("\n>>> Step 3: 打包最终索引...")
                if not os.path.exists(paths["pca_model"]):
                    print("❌ 错误: PCA 文件未生成")
                    continue

                run_command([
                    executables["processor"],
                    "--acpg", paths["acpg"],
                    "--cluster", paths["cluster"],
                    "--out", base_dir,
                    "--neural_graph", paths["neural_graph"],
                    "--model", paths["pca_model"], 
                    "--use_pca" 
                ], log)
                
                # Step 4
                print("\n>>> Step 4: 检查并生成 Neural Router 坐标...")
                generate_neural_coords(dataset, base_dir, paths)
                
                print(f"\n✅ {dataset} 处理完毕！")
            except Exception as e:
                print(f"\n❌ {dataset} 处理失败: {e}")
                import traceback
                traceback.print_exc()

    print("\n所有数据集处理完毕。")

if __name__ == "__main__":
    main()