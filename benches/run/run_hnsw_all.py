import subprocess
import os
import datetime

# ================= 配置区域 =================
DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]

# yandex_t2i 使用 Inner Product 距离，其他使用 L2
IP_DATASETS = {"yandex_t2i"}

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

LOG_PATH = "run_hnsw_qps_recall.log"
NUM_RUNS = 3
TOP_K_LIST = [1, 100]   # 先测 Recall@1，再测 Recall@100
# ===========================================


def run_subprocess(cmd, dataset, top_k, log_file_path):
    display_cmd = " ".join(cmd)
    print(f"👉 执行命令: {display_cmd}")

    try:
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"\n{'='*100}\n")
            log_file.write(f"[HNSW] Dataset: {dataset} | top_k: {top_k} | Time: {datetime.datetime.now()}\n")
            log_file.write(f"Command: {display_cmd}\n")
            log_file.write("--- C++ Output ---\n")

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

            returncode = process.wait()

        if returncode != 0:
            print(f"❌ {dataset} top_k={top_k} 测试异常退出 (Code: {returncode})")
            return False
        return True

    except Exception as e:
        print(f"⚠️ 脚本错误: {str(e)}")
        return False


def main():
    # 查找可执行文件
    executable = "./build/bench_hnsw"
    if not os.path.exists(executable):
        executable = "./build/benches/bench_hnsw"
        if not os.path.exists(executable):
            print("❌ 找不到可执行文件: ./build/bench_hnsw 或 ./build/benches/bench_hnsw")
            print("请先编译: cd build && make -j$(nproc) bench_hnsw")
            return

    # 初始化日志
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(f"HNSW QPS+Recall Benchmark Started: {datetime.datetime.now()}\n")
        f.write(f"Datasets: {DATASETS}\n")
        f.write(f"Top-K: {TOP_K_LIST}\n")
        f.write(f"Metrics: QPS / Recall@K\n")
        f.write(f"Num Runs: {NUM_RUNS}\n")

    print(f"🚀 开始 HNSW QPS + Recall 基准测试")
    print(f"   测试顺序: Recall@1 → Recall@100")
    print(f"   日志文件: {LOG_PATH}\n")

    for dataset in DATASETS:
        print(f"\n{'#'*60}")
        print(f"📦 数据集: {dataset}")
        print(f"{'#'*60}")

        output_dir = f"test/{dataset}_results"
        os.makedirs(output_dir, exist_ok=True)

        for top_k in TOP_K_LIST:
            print(f"\n--- Recall@{top_k} ---")

            result_json = f"{output_dir}/{dataset}_hnsw_recall{top_k}.json"

            cmd = [
                executable,
                "--dataset",    dataset,
                "--fn_result",  result_json,
                "--top_k",      str(top_k),
                "--num_runs",   str(NUM_RUNS),
            ]

            # yandex_t2i 使用 Inner Product 距离
            if dataset in IP_DATASETS:
                cmd.append("--use_ip")

            if run_subprocess(cmd, dataset, top_k, LOG_PATH):
                print(f"✅ {dataset} Recall@{top_k} 完成 → {result_json}")
            else:
                print(f"❌ {dataset} Recall@{top_k} 失败，继续下一个...")

    print(f"\n🎉 全部测试结束。日志: {LOG_PATH}")


if __name__ == "__main__":
    main()
