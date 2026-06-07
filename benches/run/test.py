import subprocess
import os
import datetime
import sys

# ================= 配置区域 =================
# 你想要测试的数据集
DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]

# 线程数设置 (影响 CPU 利用率监测，防止底层数学库抢占线程)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"  
os.environ["OPENBLAS_NUM_THREADS"] = "1"

# 日志文件
LOG_PATH = "test_results_final.log"
# ===========================================

def run_subprocess(cmd, dataset, log_file_path):
    display_cmd = " ".join(cmd)
    print(f"👉 执行命令: {display_cmd}")
    
    try:
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"\n{'='*100}\n")
            log_file.write(f"[TEST RUN] Dataset: {dataset} | Time: {datetime.datetime.now()}\n")
            log_file.write(f"Command: {display_cmd}\n")
            log_file.write("--- C++ Output ---\n")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # 实时打印 C++ 的输出 (包括表格和 CPU %)
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
    # 1. 检查可执行文件 (智能兼容两种常见的 CMake 输出路径)
    executable = "./build/test"
    if not os.path.exists(executable):
        executable = "./build/benches/test"
        if not os.path.exists(executable):
            print(f"❌ 找不到可执行文件: ./build/test 或 ./build/benches/test")
            print("请确认 C++ 代码是否已编译成功。")
            return

    # 2. 初始化日志
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(f"Benchmark Started: {datetime.datetime.now()}\n")

    print(f"🚀 开始全量对比测试 (非对称 HNSW 路由模式)...")
    print(f"日志文件: {LOG_PATH}\n")

    for dataset in DATASETS:
        print(f"\n{'#'*60}")
        print(f"📦 测试数据集: {dataset}")
        print(f"{'#'*60}")

        # 路径定义
        base_dir = f"graph_processing/{dataset}_results"
        output_dir = f"test/{dataset}_results"
        os.makedirs(output_dir, exist_ok=True)
        
        acpg_file = f"acpg/{dataset}_index/acpg_nsg.json"
        result_json = f"{output_dir}/{dataset}_final_report.json"
        
        # ==========================================
        # 【核心参数】读取离线转换好的 Hubs 以及原始 Hubs
        # ==========================================
        transformed_hubs = f"drl/{dataset}_results/transformed_hubs.bin"
        transformed_ids = f"drl/{dataset}_results/transformed_hub_ids.bin"
        raw_hubs = f"drl/{dataset}_results/raw_hubs.bin"  # <--- 新增
        
        # 图文件 (由 generate_all_graphs.py 生成) 
        f_pca = f"{base_dir}/entry_points_pca.json"
        f_geo = f"{base_dir}/entry_points_neural_euclidean.json"
        f_topo = f"{base_dir}/entry_points_neural_topology.json"

        # 检查底层索引是否存在
        if not os.path.exists(acpg_file):
            print(f"⚠️ 跳过 {dataset}: 缺少索引文件 {acpg_file}")
            continue

        # --- 组装基础命令 ---
        cmd = [
            executable,
            "--dataset", dataset,
            "--acpg_file", acpg_file,
            "--fn_result", result_json,
            "--test_scope", "all",  # 让 C++ 跑所有已加载的任务
            "--num_runs", "10",      # 测试 10 次取平均
            "--R", "32"
        ]

        # 动态添加存在的旧方案图文件参数 (Task 0, Task 1 等)
        if os.path.exists(f_pca):
            cmd.extend(["--cluster_pca", f_pca])
        else:
            print(f"⚠️ [提示] 未找到 PCA 图: {f_pca}")

        if os.path.exists(f_geo):
            cmd.extend(["--cluster_neural_geo", f_geo])
        else:
            print(f"⚠️ [提示] 未找到 Neural(Geo) 图: {f_geo}")

        if os.path.exists(f_topo):
            cmd.extend(["--cluster_neural_topo", f_topo])
        else:
            print(f"⚠️ [提示] 未找到 Neural(Topo) 图: {f_topo}")

        # ==========================================
        # 【挂载非对称路由参数】(Task 5)
        # ==========================================
        if os.path.exists(transformed_hubs) and os.path.exists(transformed_ids):
            cmd.extend([
                "--transformed_hubs", transformed_hubs,
                "--transformed_ids", transformed_ids
            ])
            print("🚀 [Task 5] 已挂载 transformed_hubs，将进行 0ms HNSW 非对称路由测试！")
        else:
            print(f"⚠️ [提示] 未找到 transformed_hubs.bin，Task 5 将被跳过！")
        
        # ==========================================
        # 【挂载消融实验对照组参数】(Task 2)
        # ==========================================
        if os.path.exists(raw_hubs):
            cmd.extend([
                "--raw_hubs", raw_hubs
            ])
            print("📊 [Task 2] 已挂载 raw_hubs，将运行 Raw HNSW 基线进行严格消融对比！")
        else:
            print(f"⚠️ [提示] 未找到 raw_hubs.bin，Task 2 将被跳过！")
        
        # --- 执行 ---
        if run_subprocess(cmd, dataset, LOG_PATH):
            print(f"✅ {dataset} 完成! 结果 -> {result_json}")

    print("\n🎉 所有测试结束。请查看终端输出的表格或日志文件。")

if __name__ == "__main__":
    main()