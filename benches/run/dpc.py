import subprocess
import os
import datetime

def main():
    DATASETS = [ "deep10M","sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
    os.environ["OMP_NUM_THREADS"] = "8"
    
    print("Prepare to run KPH-DPC hierarchical clustering...\n")

    for dataset in DATASETS:
        print(f"\n{'='*50}")
        print(f"Running KPH-DPC clustering on {dataset} dataset...")
        print(f"{'='*50}")

        # DPC聚类输出目录
        OUTPUT_DIR = f"dpc/{dataset}_results"
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 假设ACPG索引文件已经存在（由之前的ACO流程生成）
        acpg_file = f"acpg/{dataset}_index/acpg_nsg.json"
        dpc_output_file = f"{OUTPUT_DIR}/dpc_hierarchical_results.json"

        cmd = [
            "./build/benches/kph_dpc_clustering",
            "--acpg_file", acpg_file,
            "--output_file", dpc_output_file,
            "--num_threads", "8"
        ]

        if not os.path.exists(acpg_file):
            print(f"❌ Error: ACPG index file not found -> {acpg_file}")
            print("Please run ACO_TEST first to generate ACPG index files")
            print("Skipping this dataset and continuing...\n")
            continue

        print(f"Command: {' '.join(cmd)}")
        try:
            # 实时读取输出
            log_path = "dpc_output.log"
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n{'='*100}\n")
                log_file.write(f"[START DPC] Dataset: {dataset} | Time: {datetime.datetime.now()}\n")
                log_file.write(f"Command: {' '.join(cmd)}\n")
                log_file.write("--- Real-time DPC Output ---\n")

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
                print(f"✅ KPH-DPC clustering completed successfully on {dataset} dataset!")
                
                # 检查输出文件是否生成
                if os.path.exists(dpc_output_file):
                    file_size = os.path.getsize(dpc_output_file)
                    print(f"✅ DPC results saved to: {dpc_output_file} ({file_size} bytes)")
                else:
                    print(f"⚠️ Warning: Output file not found at {dpc_output_file}")

        except subprocess.CalledProcessError as e:
            print(f"⚠️ Error executing KPH-DPC clustering on {dataset} dataset:")
            print(f"Return code: {e.returncode} (Note: -11=segmentation fault, likely C++ memory error)")
            print("Skipping this dataset and continuing...\n")

            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n--- DPC Error Detected ---\n")
                log_file.write(f"Return code: {e.returncode}\n")
                log_file.write(f"{'='*100}\n")

        except FileNotFoundError:
            print(f"⚠️ Error: DPC executable not found -> {cmd[0]}")
            print("Hint: Recompile first with 'cd build && make kph_dpc_clustering'")
            print("Skipping all datasets and exiting...\n")
            break

        except Exception as e:
            print(f"⚠️ Unknown error on {dataset} dataset: {str(e)}")
            print("Skipping this dataset and continuing...\n")

    print("\nAll datasets processed for KPH-DPC clustering.")

def check_dpc_executable():
    """检查DPC可执行文件是否存在"""
    dpc_executable = "./build/benches/kph_dpc_clustering"
    if not os.path.exists(dpc_executable):
        print(f"❌ DPC executable not found: {dpc_executable}")
        print("Please compile the DPC clustering code first.")
        return False
    return True

if __name__ == "__main__":
    if check_dpc_executable():
        main()