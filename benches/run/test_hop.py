import subprocess
import os
import datetime

# ================= 配置区域 =================
DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

LOG_PATH = "run_from_step3_full_recall100_hop.log"
NUM_RUNS = 3
# ===========================================

def run_subprocess(cmd, dataset, log_file_path):
    display_cmd = " ".join(cmd)
    print(f"👉 执行命令: {display_cmd}")

    try:
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"\n{'='*100}\n")
            log_file.write(f"[TEST_HOP] Dataset: {dataset} | Time: {datetime.datetime.now()}\n")
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
            print(f"❌ {dataset} 测试异常退出 (Code: {returncode})")
            return False
        return True

    except Exception as e:
        print(f"⚠️ 脚本错误: {str(e)}")
        return False


def main():
    # 查找可执行文件
    executable = "./build/test_hop"
    if not os.path.exists(executable):
        executable = "./build/benches/test_hop"
        if not os.path.exists(executable):
            print("❌ 找不到可执行文件: ./build/test_hop 或 ./build/benches/test_hop")
            print("请先编译: cd build && make -j$(nproc) test_hop")
            return

    # 初始化日志
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(f"test_hop Benchmark Started: {datetime.datetime.now()}\n")
        f.write(f"Datasets: {DATASETS}\n")
        f.write(f"Metrics: Recall@1 / Avg Hops / Memory (MB)\n")
        f.write(f"search_L: aligned with HNSW ef_params\n")

    print(f"🚀 开始 NETG Hop 统计测试 (Recall@1 / Hops / Memory)")
    print(f"日志文件: {LOG_PATH}\n")

    for dataset in DATASETS:
        print(f"\n{'#'*60}")
        print(f"📦 测试数据集: {dataset}")
        print(f"{'#'*60}")

        # 路径定义（与 test.py 保持一致）
        output_dir = f"test/{dataset}_results"
        os.makedirs(output_dir, exist_ok=True)

        acpg_file        = f"acpg/{dataset}_index/acpg_nsg.json"
        transformed_hubs = f"drl/{dataset}_results/transformed_hubs.bin"
        transformed_ids  = f"drl/{dataset}_results/transformed_hub_ids.bin"
        result_json      = f"{output_dir}/{dataset}_hop_report.json"

        # 检查索引
        if not os.path.exists(acpg_file):
            print(f"⚠️ 跳过 {dataset}: 缺少索引文件 {acpg_file}")
            continue

        cmd = [
            executable,
            "--dataset",    dataset,
            "--acpg_file",  acpg_file,
            "--fn_result",  result_json,
            "--num_runs",   str(NUM_RUNS),
        ]

        if os.path.exists(transformed_hubs) and os.path.exists(transformed_ids):
            cmd.extend([
                "--transformed_hubs", transformed_hubs,
                "--transformed_ids",  transformed_ids,
            ])
            print("🚀 已挂载 transformed_hubs → NETG (HNSW Routing) 任务已启用")
        else:
            print(f"⚠️ 未找到 transformed_hubs.bin，只跑 Medoid Baseline")

        if run_subprocess(cmd, dataset, LOG_PATH):
            print(f"✅ {dataset} 完成! 结果 -> {result_json}")

    print(f"\n🎉 全部测试结束。日志: {LOG_PATH}")


if __name__ == "__main__":
    main()
