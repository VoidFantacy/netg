import subprocess
import os
import datetime

def decide_parameters(dataset_name):
    """
    根据数据集名称自动决定最佳 ACO 训练参数。
    策略：
    1. SIFT 类 (几何分布): Beta 较低 (4.5)，Alpha 适中 (0.2)，收敛较快。
    2. Deep/Glove/Gist 类 (高维/语义分布): Beta 较高 (10.0) 以减少震荡，Alpha 极低 (0.01) 以减少盲目随机性。
    """
    dataset = dataset_name.lower()
    
    # --- 默认参数 (兜底) ---
    params = {
        "alpha": "1.0",
        "beta": "5.0",
        "rho": "0.1",
        "lambda": "0.5",
        "rejection": "20",
        "iterations": "30",
        "L": "400"
    }

    # --- 策略 A: SIFT 系列 (Sift1M, Sift10M, Sift100K) ---
    if "sift" in dataset:
        params.update({
            "alpha": "0.2",
            "beta": "4.5",      # 经实验验证的最佳值
            "rho": "0.1",
            "lambda": "0.5",
            "rejection": "20",
            "iterations": "25", # SIFT 收敛快，25 次足够
            "L": "400"
        })
        print(f"👉 [Auto-Config] Detected SIFT-like dataset '{dataset_name}'. Using GEOMETRIC strategy.")

    # --- 策略 B: Deep / Glove / Yandex / Gist (深度/高维特征) ---
    elif any(x in dataset for x in ["deep", "glove", "gist", "yandex", "text", "audio"]):
        params.update({
            "alpha": "0.01",    # 降低随机扰动，防止在复杂高维空间迷路
            "beta": "10.0",     # ⚠️ 关键：大幅提高信息素权重，强迫蚂蚁跟随已发现的优良路径，抑制震荡
            "rho": "0.15",      # 加快挥发，迅速淘汰差路径
            "lambda": "0.4",    # 稍微降低启发式更新的平滑度
            "rejection": "20",
            "iterations": "50", # Deep 数据集较难收敛，增加迭代次数
            "L": "400"          # 保持较大的搜索深度
        })
        print(f"👉 [Auto-Config] Detected Deep/Embedding dataset '{dataset_name}'. Using ROBUST/DEEP strategy.")
    
    else:
        print(f"⚠️ [Auto-Config] Unknown dataset type '{dataset_name}'. Using DEFAULT parameters.")

    return params

def main():
    # 在这里列出你想跑的所有数据集
    DATASETS = [ "deep10M","sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
    
    os.environ["OMP_NUM_THREADS"] = "16"
    trials = 1
    num_aco = 1
    
    print("Prepare to train with Auto-Adaptive Parameters...\n")

    for dataset in DATASETS:
        print(f"\n{'='*60}")
        print(f"🚀 Processing dataset: {dataset}")
        print(f"{'='*60}")

        # 1. 自动决定参数 [核心修改]
        current_params = decide_parameters(dataset)
        
        # 打印当前使用的参数供确认
        print(f"⚙️  Active Params: {current_params}")

        OUTPUT_DIR = f"acpg/{dataset}_index"
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        index_file = f"indices/{dataset}_index/acosp_nsg.json"
        acpg_file = f"{OUTPUT_DIR}/acpg_nsg.json"
        fn_result = f"{OUTPUT_DIR}/acsg_aco_results.json"

        # 构建基础命令
        cmd = [
            "./build/benches/bench_ACO_TEST",
            "--index_file", index_file,
            "--dataset", dataset,
            "--fn_result", fn_result,
            "--trials", str(trials),
            "--num_aco", str(num_aco),
            "--acpg_file", acpg_file
        ]
        
        # 2. 将自动决定的参数追加到命令中 [核心修改]
        for key, value in current_params.items():
            cmd.extend([f"--{key}", str(value)])

        if not os.path.exists(index_file):
            print(f"❌ Error: Index file not found -> {index_file}")
            print("Skipping this dataset and continuing...\n")
            continue

        print(f"Command: {' '.join(cmd)}")
        try:
            log_path = "output_train_auto.log" # 改个名区分一下
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n{'='*100}\n")
                log_file.write(f"[START] Dataset: {dataset} | Strategy: {current_params.get('alpha')} / {current_params.get('beta')} | Time: {datetime.datetime.now()}\n")
                log_file.write(f"Command: {' '.join(cmd)}\n")
                log_file.write("--- Real-time Output ---\n")

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in process.stdout:
                    print(line, end="")
                    log_file.write(line)
                    log_file.flush()

                returncode = process.wait()

            if returncode != 0:
                raise subprocess.CalledProcessError(returncode, cmd)
            else:
                print(f"✅ ACO_TEST completed successfully on {dataset} dataset!")

        except subprocess.CalledProcessError as e:
            print(f"⚠️ Error executing ACO_TEST on {dataset} dataset:")
            print(f"Return code: {e.returncode}")
            print("Skipping this dataset and continuing...\n")

        except FileNotFoundError:
            print(f"⚠️ Error: Executable not found -> {cmd[0]}")
            print("Hint: Recompile first with 'cd build && make bench_ACO_TEST'")
            break

        except Exception as e:
            print(f"⚠️ Unknown error on {dataset} dataset: {str(e)}")
            print("Skipping this dataset and continuing...\n")

    print("All datasets processed.")

if __name__ == "__main__":
    main()