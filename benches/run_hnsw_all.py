#      nohup python3 -u benches/run_hnsw_all.py > output_run_hnsw_all.log 2>&1 &

import os
import subprocess
import sys
import time

# ==========================================
# 配置区域
# ==========================================

# 待测试的数据集列表 (请确保 settings.json 里有这些名字)
DATASETS = [
    "deep10M",
    "sift10M", 
    "sift10M_skewed", 
    "yandex_t2i", 
    "gist1M"
]

# HNSW 参数
M = 32
EF_CONSTRUCTION = 200  # [修改] 建议改成 200 以加快构建速度 (与 C++ 默认保持一致)

# [新增] 每个 ef 参数重复运行次数 (取平均值)
NUM_RUNS = 10

# 线程数 (虽然 C++ 代码里现在会自动控制，但设一下也不碍事)
NUM_THREADS = 16

# 路径配置
BINARY_PATH = "build/benches/bench_hnsw"
OUTPUT_ROOT = "./benches/outputs"

# ==========================================
# 主逻辑
# ==========================================

def run_benchmark():
    # 1. 检查二进制文件是否存在
    if not os.path.exists(BINARY_PATH):
        print(f"❌ 错误: 找不到可执行文件: {BINARY_PATH}")
        print("请先编译: cd build && make bench_hnsw -j")
        sys.exit(1)

    # 2. 设置环境变量
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(NUM_THREADS)
    
    print(f"🚀 开始 HNSW 基准测试")
    print(f"📌 参数: M={M}, efConstruction={EF_CONSTRUCTION}, Runs={NUM_RUNS}")
    print(f"📂 列表: {DATASETS}")
    print("-" * 60)

    for dataset in DATASETS:
        print(f"\n▶️  正在处理数据集: {dataset} ...")
        
        # 准备输出目录
        dataset_out_dir = os.path.join(OUTPUT_ROOT, dataset)
        os.makedirs(dataset_out_dir, exist_ok=True)
        
        # 结果文件路径
        result_json = os.path.join(dataset_out_dir, "hnsw.json")
        
        # 构造命令
        # [修改] 增加了 --num_runs 参数
        cmd = [
            BINARY_PATH,
            "--dataset", dataset,
            "--fn_result", result_json,
            "--M", str(M),
            "--efConstruction", str(EF_CONSTRUCTION),
            "--num_runs", str(NUM_RUNS)
        ]
        
        start_time = time.time()
        
        try:
            # 执行命令
            subprocess.run(cmd, env=env, check=True)
            
            elapsed = time.time() - start_time
            print(f"✅ 完成 {dataset} (耗时: {elapsed:.2f}s)")
            print(f"📄 结果已保存: {result_json}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ {dataset} 运行失败 (Exit Code: {e.returncode})")
        except Exception as e:
            print(f"❌ {dataset} 发生未知错误: {e}")

    print("\n" + "="*60)
    print("🎉 所有任务执行完毕！")

if __name__ == "__main__":
    if not os.path.exists("build"):
        print("⚠️  警告: 未检测到 build 目录，请确保您在项目根目录下运行此脚本。")
    
    run_benchmark()