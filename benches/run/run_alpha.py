import subprocess
import os
from itertools import product
from tqdm import tqdm

# 数据集列表
DATASETS = ["glove"]
os.environ["OMP_NUM_THREADS"] = "16"

# 参数搜索空间
alpha_list = [1.4, 2.2, 3.5, 4.0]
beta_list = [0, 1.4, 2.0, 3.3, 4.2]
rho_list = [0.3]
# rho_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
lambda_list = [0.3]
rejection_list = [10]
iterations = 20

# 计算总组合数
total_combinations = len(alpha_list) * len(beta_list) * len(rho_list) * len(lambda_list) * len(rejection_list)

for dataset in DATASETS:
    OUTPUT_DIR = f"benches/outputs/{dataset}/parameters"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\n🚀 Starting experiments on dataset: {dataset} (Total: {total_combinations} runs)")

    for alpha, beta, rho, lambda_val, rejection in tqdm(
        product(alpha_list, beta_list, rho_list, lambda_list, rejection_list),
        total=total_combinations
    ):
        suffix = f"a{alpha}_b{beta}_r{rho}_l{lambda_val}_rej{rejection}"
        fn_result = f"{OUTPUT_DIR}/acosp_nsg_{suffix}.json"

        # 跳过已完成的
        if os.path.exists(fn_result):
            print(f"⏭️ Skipping {suffix}, already exists.")
            continue

        command = [
            "./build/benches/bench_ACO",
            "--alpha", str(alpha),
            "--beta", str(beta),
            "--rho", str(rho),
            "--lambda", str(lambda_val),
            "--rejection", str(rejection),
            "--iterations", str(iterations),
            "--dataset", dataset,
            "--fn_result", fn_result
        ]

        print(f"🔍 Running ACO on {dataset} with {suffix}")
        try:
            subprocess.run(command, check=True)
            print(f"✅ Completed: {suffix}\n")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error on {dataset} {suffix}: {e}. Skipping...\n")
            with open("failed_runs.txt", "a") as f:
                f.write(f"{dataset},{suffix}\n")
            continue
