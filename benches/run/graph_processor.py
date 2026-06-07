import subprocess
import os
import datetime
import json

# 数据集配置
DATASET_CONFIG = {
  "root_dir": "./benches/datasets",
  "datasets": {
    "siftsmall": {
      "dataset_dir": "siftsmall",
      "train_path": "siftsmall_learn.fvecs",
      "base_path": "siftsmall_base.fvecs",
      "query_path": "siftsmall_query.fvecs",
      "gt_path": "siftsmall_groundtruth.ivecs"
    },
    "sift100K": {
      "dataset_dir": "SIFT100K",
      "train_path": "sift_learn_filtered.fvecs",
      "base_path": "sift_base.fvecs",
      "query_path": "sift_query.fvecs",
      "gt_path": "sift_groundtruth_100k.ivecs",
      "train_gt_path": "sift100K_train_gt.ivecs"
    },
    "sift1M": {
      "dataset_dir": "SIFT1M",
      "train_path": "sift_learn.fvecs",
      "base_path": "sift_base.fvecs",
      "query_path": "sift_query.fvecs",
      "gt_path": "sift_groundtruth_100k.ivecs",
      "train_gt_path": "train_gt.ivecs"
    },
    "sift10M": {
      "dataset_dir": "SIFT10M",
      "train_path": "sift_learn.fvecs",
      "base_path": "sift_base.fvecs",
      "query_path": "sift_query.fvecs",
      "gt_path": "sift_groundtruth_100k.ivecs",
      "train_gt_path": "train_gt.ivecs"
    },
    "deep": {
      "dataset_dir": "DEEP100K",
      "train_path": "deep_learn.fvecs",
      "base_path": "deep_base.fvecs",
      "query_path": "deep_query.fvecs",
      "gt_path": "deep_groundtruth_100k.ivecs",
      "train_gt_path": "deep_train_gt.ivecs"
    },
    "gist": {
      "dataset_dir": "GIST1M",
      "train_path": "gist_learn.fvecs",
      "base_path": "gist_base.fvecs",
      "query_path": "gist_query.fvecs",
      "gt_path": "gist_groundtruth.ivecs",
      "train_gt_path": "gist_train_gt.ivecs"
    },
    "glove": {
      "dataset_dir": "GLOVE100K",
      "train_path": "glove_learn_filtered.fvecs",
      "base_path": "glove_base.fvecs",
      "query_path": "glove_query.fvecs",
      "gt_path": "glove_groundtruth_100K.ivecs",
      "train_gt_path": "train_gt_filtered.ivecs"
    }
  }
}

def main():
    # 使用配置中的数据集列表
    DATASETS = ["glove", "sift1M", "sift10M", "sift100K", "deep", "gist"]
    os.environ["OMP_NUM_THREADS"] = "16"
    
    print("Prepare to generate 12K-NN graph and 1024 entry points with parameter a measurement...\n")

    for dataset in DATASETS:
        print(f"\n{'='*50}")
        print(f"Processing {dataset} dataset...")
        print(f"{'='*50}")

        # 检查数据集是否在配置中
        if dataset not in DATASET_CONFIG["datasets"]:
            print(f"❌ Error: Dataset {dataset} not found in configuration")
            print("Skipping this dataset and continuing...\n")
            continue

        # 获取数据集配置
        dataset_config = DATASET_CONFIG["datasets"][dataset]
        root_dir = DATASET_CONFIG["root_dir"]
        
        # 构建完整的文件路径
        acpg_file = f"acpg/{dataset}_index/acpg_nsg.json"
        clustering_file = f"dpc/{dataset}_results/dpc_hierarchical_results.json"
        query_file = os.path.join(root_dir, dataset_config["dataset_dir"], dataset_config["query_path"])
        
        # [修改] 添加模型文件路径
        drl_model_file = f"drl/{dataset}_results/ae_encoder.onnx"
        
        # 输出目录
        output_dir = f"graph_processing/{dataset}_results/"
        os.makedirs(output_dir, exist_ok=True)

        # 检查输入文件是否存在
        missing_files = []
        if not os.path.exists(acpg_file):
            missing_files.append(f"ACPG file: {acpg_file}")
        
        if not os.path.exists(clustering_file):
            missing_files.append(f"Clustering results: {clustering_file}")
            
        if not os.path.exists(query_file):
            missing_files.append(f"Query file: {query_file}")

        # [修改] 检查模型文件是否存在
        if not os.path.exists(drl_model_file):
            missing_files.append(f"ONNX Model file: {drl_model_file}")

        if missing_files:
            print(f"❌ Error: Missing required files for {dataset}:")
            for file in missing_files:
                print(f"  - {file}")
            
            if f"ACPG file: {acpg_file}" in missing_files:
                print("  Please run ACO_TEST first to generate ACPG files")
            if f"Clustering results: {clustering_file}" in missing_files:
                print("  Please run KPH-DPC clustering first")
            if f"Query file: {query_file}" in missing_files:
                print("  Please check dataset configuration and file paths")
            # [修改] 添加模型缺失提示
            if f"ONNX Model file: {drl_model_file}" in missing_files:
                print("  Please run train_router.py first to generate the ONNX model")
                
            print("Skipping this dataset and continuing...\n")
            continue

        # [修改] 构建命令 - 现在需要5个参数：ACPG文件、聚类结果、查询文件、输出目录、ONNX模型
        cmd = [
            "./build/benches/graph_processor",
            acpg_file,
            clustering_file,
            query_file,
            output_dir,
            drl_model_file  # <-- 这里是新增的第5个参数
        ]

        print(f"Command: {' '.join(cmd)}")
        print(f"Input files:")
        print(f"  - ACPG file: {acpg_file}")
        print(f"  - Clustering results: {clustering_file}")
        print(f"  - Query file: {query_file} (for parameter a measurement)")
        print(f"  - ONNX Model: {drl_model_file}")
        print(f"Output directory: {output_dir}")

        try:
            # 实时读取输出
            log_path = f"graph_processing_{dataset}.log"
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n{'='*100}\n")
                log_file.write(f"[START Graph Processing] Dataset: {dataset} | Time: {datetime.datetime.now()}\n")
                log_file.write(f"Command: {' '.join(cmd)}\n")
                log_file.write(f"Query file for parameter a: {query_file}\n")
                log_file.write("--- Real-time Output ---\n")

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                for line in process.stdout:
                    print(line, end="")
                    log_file.write(line)
                    log_file.flush()

                returncode = process.wait()

            if returncode != 0:
                raise subprocess.CalledProcessError(returncode, cmd)
            else:
                print(f"✅ Graph processing completed successfully on {dataset} dataset!")
                
                # 检查输出文件是否生成
                entry_points_file = f"{output_dir}/entry_points.json"
                knn_12k_file = f"{output_dir}/knn_12k_graph.json"
                
                files_generated = []
                if os.path.exists(entry_points_file):
                    file_size = os.path.getsize(entry_points_file)
                    files_generated.append(f"✅ Entry points: {entry_points_file} ({file_size} bytes)")
                    
                    # 检查是否包含参数a
                    try:
                        with open(entry_points_file, 'r') as f:
                            data = json.load(f)
                        if "parameter_a" in data:
                            parameter_a = data["parameter_a"]
                            files_generated.append(f"✅ Parameter a: {parameter_a}")
                        else:
                            files_generated.append("⚠️  Parameter a not found in output")
                    except:
                        files_generated.append("⚠️  Could not read parameter a from output")
                else:
                    files_generated.append(f"❌ Entry points file missing: {entry_points_file}")
                
                if os.path.exists(knn_12k_file):
                    file_size = os.path.getsize(knn_12k_file)
                    files_generated.append(f"✅ 12K-NN graph: {knn_12k_file} ({file_size} bytes)")
                else:
                    files_generated.append(f"❌ 12K-NN graph file missing: {knn_12k_file}")
                
                # 打印文件生成状态
                print("Generated files:")
                for status in files_generated:
                    print(f"  {status}")
                
                # 验证输出文件内容
                validate_output_files(entry_points_file, knn_12k_file, dataset)

        except subprocess.CalledProcessError as e:
            print(f"⚠️ Error executing graph processing on {dataset} dataset:")
            print(f"Return code: {e.returncode}")
            print("Skipping this dataset and continuing...\n")

            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n--- Graph Processing Error Detected ---\n")
                log_file.write(f"Return code: {e.returncode}\n")
                log_file.write(f"{'='*100}\n")

        except FileNotFoundError:
            print(f"⚠️ Error: Graph processor executable not found -> {cmd[0]}")
            print("Hint: Recompile first with 'cd build && make graph_processor'")
            print("Skipping all datasets and exiting...\n")
            break

        except Exception as e:
            print(f"⚠️ Unknown error on {dataset} dataset: {str(e)}")
            print("Skipping this dataset and continuing...\n")

    print("\nAll datasets processed for graph processing.")

def validate_output_files(entry_points_file, knn_12k_file, dataset):
    """验证生成的输出文件内容"""
    print(f"\nValidating output files for {dataset}...")
    
    try:
        # 验证入口点文件
        if os.path.exists(entry_points_file):
            with open(entry_points_file, 'r') as f:
                entry_data = json.load(f)
            
            # 新的字段名称
            combined_centers = entry_data.get('combined_centers', [])
            entry_points = entry_data.get('entry_points', [])
            parameter_a = entry_data.get('parameter_a', 'Not found')
            
            print(f"  - Combined centers: {len(combined_centers)}")
            print(f"  - Entry points per center: {len(entry_points[0]) if entry_points else 0}")
            print(f"  - Total entry points: {sum(len(ep) for ep in entry_points)}")
            print(f"  - Parameter a: {parameter_a}")
            
            # 检查全局gamma最高节点信息
            if 'global_top_gamma_local_index' in entry_data:
                print(f"  - Global top gamma node - Local index: {entry_data['global_top_gamma_local_index']}")
                print(f"  - Global top gamma node - Original ID: {entry_data['global_top_gamma_original_id']}")
                print(f"  - Global top gamma value: {entry_data['global_top_gamma_value']}")
        
        # 验证12K近邻图文件
        if os.path.exists(knn_12k_file):
            with open(knn_12k_file, 'r') as f:
                knn_data = json.load(f)
            
            neighbors = knn_data.get('knn_12k_graph', [])
            print(f"  - 12K-NN graph nodes: {len(neighbors)}")
            print(f"  - Neighbors per node: {len(neighbors[0]) if neighbors else 0}")
            
    except Exception as e:
        print(f"  ⚠️ Validation error: {str(e)}")

def check_graph_processor_executable():
    """检查图处理器可执行文件是否存在"""
    processor_executable = "./build/benches/graph_processor"
    if not os.path.exists(processor_executable):
        print(f"❌ Graph processor executable not found: {processor_executable}")
        print("Please compile the graph processing code first.")
        return False
    return True

def create_sample_config():
    """创建示例配置文件"""
    config = {
        "datasets": ["glove", "sift1M", "sift10M", "sift100K", "deep", "gist"],
        "threads": 16,
        "input_paths": {
            "acpg_file": "acpg/{dataset}_index/acpg_nsg.json",
            "clustering": "dpc/{dataset}_results/dpc_hierarchical_results.json",
            "query_file": "benches/datasets/{dataset_dir}/{query_path}"  # 完整的查询文件路径
        },
        "output_path": "graph_processing/{dataset}_results/",
        "expected_outputs": [
            "entry_points.json",
            "knn_12k_graph.json"
        ]
    }
    
    with open("graph_processing_config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("✅ Sample configuration file created: graph_processing_config.json")

if __name__ == "__main__":
    # 创建输出主目录
    os.makedirs("graph_processing", exist_ok=True)
    
    # 创建示例配置文件
    create_sample_config()
    
    if check_graph_processor_executable():
        main()