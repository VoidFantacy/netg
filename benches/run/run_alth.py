import subprocess
import os

# *******************************************************************************************************************
# 此方法用来构建索引
# *******************************************************************************************************************
DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]

# 设置 OpenMP 线程数
os.environ["OMP_NUM_THREADS"] = "16"

# 参数字典
params = {
    "sift10M": 15,          
    "sift10M_skewed": 15,   
    "deep10M": 0.012,       
    "yandex_t2i": 0.012,    
    "gist1M": 0.02,         
}

# 获取当前工作目录（绝对路径根目录）
current_working_dir = os.getcwd()

for dataset in DATASETS:
    # 构建绝对路径的输出目录
    OUTPUT_DIR = os.path.join(current_working_dir, "indices", f"{dataset}_index")
    # 自动创建目录（如果已存在则忽略）
    os.makedirs(OUTPUT_DIR, exist_ok=True) 
    
    print(f"📂 [Path Check] Output Directory: {OUTPUT_DIR}")

    # 从 params 获取 lambda 值
    lambda_val = params.get(dataset, 0.4) 
    print(f"Configuring {dataset}: lambda={lambda_val}")

    alpha = 1.4
    beta = 2.2
    rho = 0.15
    iterations = 20
    rejection = 10
    
    # 索引文件绝对路径
    index_file = os.path.join(OUTPUT_DIR, "acosp_nsg.json")

    # 构图参数
    R_val = 50
    L_build_val = 100  
    C_val = 512

    algorithms = [
        {
            "name": "ACO",
            "command": [
                "./build/benches/bench_ACO",
                "--alpha", str(alpha),
                "--beta", str(beta),
                "--rho", str(rho),
                "--lambda", str(lambda_val),
                "--rejection", str(rejection),
                "--iterations", str(iterations),
                "--R", str(R_val),
                "--L_build", str(L_build_val), 
                "--C", str(C_val),
                "--dataset", dataset,
                "--index_file", index_file   # 使用绝对路径
            ]
        }
    ]

    for algo in algorithms:
        print(f"Running {algo['name']} on {dataset} dataset...")
        try:
            subprocess.run(algo["command"], check=True)
            print(f"{algo['name']} completed successfully on {dataset} dataset.\n")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Error executing {algo['name']} on {dataset} dataset: {e}")
            print("Skipping this algorithm and continuing...\n")
            continue