#!/usr/bin/env python3
"""
run_ssg_all.py
NETG on SSG 全流程测试：
  - SSG Medoid Baseline（单入口点）
  - NETG on SSG（HNSW 路由 → 多 Hub 入口点）

search_L 对齐: {100, 128, 150, 200, 250, 300, 400, 512, 600, 800, 1024, 1200, 1500}
输出: L | QPS | Recall@100
"""

import subprocess
import os
import datetime

# ================= 配置区域 =================
DATASETS = ["sift10M"]   # 先测 sift10M，其他数据集建图后再加

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

LOG_PATH = "run_ssg_all.log"
NUM_RUNS = 3

# SSG 索引文件路径模板
SSG_INDEX_DIR = "ssg_index"

# NETG Router 文件路径模板（复用 ACPG 训练好的 Router）
DRL_DIR = "drl"
# ===========================================


def get_paths(dataset):
    """返回各文件路径"""
    ssg_file = f"{SSG_INDEX_DIR}/{dataset}.ssg"
    transformed_hubs = f"{DRL_DIR}/{dataset}_results/transformed_hubs.bin"
    transformed_ids  = f"{DRL_DIR}/{dataset}_results/transformed_hub_ids.bin"
    output_dir       = f"test/{dataset}_results"
    result_json      = f"{output_dir}/{dataset}_ssg_report.json"
    return ssg_file, transformed_hubs, transformed_ids, output_dir, result_json


def run_subprocess(cmd, dataset, log_file_path):
    display_cmd = " ".join(cmd)
    print(f"👉 执行命令: {display_cmd}")

    try:
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"\n{'='*100}\n")
            log_file.write(f"[SSG] Dataset: {dataset} | Time: {datetime.datetime.now()}\n")
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
    executable = "./build/bench_ssg"
    if not os.path.exists(executable):
        executable = "./build/benches/bench_ssg"
        if not os.path.exists(executable):
            print("❌ 找不到可执行文件: ./build/bench_ssg 或 ./build/benches/bench_ssg")
            print("请先编译: cd build && make -j$(nproc) bench_ssg")
            return

    # 初始化日志
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(f"SSG Benchmark Started: {datetime.datetime.now()}\n")
        f.write(f"Datasets: {DATASETS}\n")
        f.write(f"Metrics: QPS / Recall@100\n")
        f.write(f"search_L: 100,128,150,200,250,300,400,512,600,800,1024,1200,1500\n")
        f.write(f"Methods: SSG Medoid (Baseline) + NETG on SSG (HNSW Routing)\n")
        f.write(f"Num Runs: {NUM_RUNS}\n")

    print("🚀 开始 NETG on SSG 全流程测试")
    print("   方法 1: SSG Medoid (Baseline)")
    print("   方法 2: NETG on SSG (HNSW Routing)")
    print(f"   日志文件: {LOG_PATH}\n")

    for dataset in DATASETS:
        print(f"\n{'#'*60}")
        print(f"📦 数据集: {dataset}")
        print(f"{'#'*60}")

        ssg_file, trans_hubs, trans_ids, output_dir, result_json = get_paths(dataset)

        os.makedirs(output_dir, exist_ok=True)

        # 检查 SSG 索引
        if not os.path.exists(ssg_file):
            print(f"⚠️ 跳过 {dataset}: SSG 索引不存在 → {ssg_file}")
            print(f"   请先建图: SSG/build/tests/test_ssg_index ...")
            continue

        cmd = [
            executable,
            "--dataset",    dataset,
            "--ssg_file",   ssg_file,
            "--fn_result",  result_json,
            "--num_runs",   str(NUM_RUNS),
        ]

        # 挂载 NETG Router（如果存在）
        if os.path.exists(trans_hubs) and os.path.exists(trans_ids):
            cmd.extend([
                "--transformed_hubs", trans_hubs,
                "--transformed_ids",  trans_ids,
            ])
            print("🔗 已挂载 NETG Router → SSG Baseline + NETG on SSG 双路测试")
        else:
            print(f"⚠️ 未找到 Router 文件，仅跑 SSG Medoid Baseline")
            print(f"   缺少: {trans_hubs}")

        if run_subprocess(cmd, dataset, LOG_PATH):
            print(f"✅ {dataset} 完成! → {result_json}")

    print(f"\n🎉 全部测试结束。日志: {LOG_PATH}")


if __name__ == "__main__":
    main()
