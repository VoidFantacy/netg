import os
import json
import subprocess
import sys
import datetime
from pathlib import Path

# ==================== 配置 ====================

TARGET_DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
PROJECT_ROOT = Path("/path/to/ACSG")
SETTINGS_PATH = PROJECT_ROOT / "benches/datasets/settings.json"
LGO_EXEC_DIR = PROJECT_ROOT / "LSH-APG/cppCode/LSH-APG"

# 新增：日志文件路径 (你指定的路径)
LOG_FILE_PATH = Path("/path/to/ACSG/lsh_batch_log.txt")

# ==================== 逻辑 ====================

def load_settings():
    if not SETTINGS_PATH.exists():
        print(f"❌ Error: Settings file not found at {SETTINGS_PATH}")
        sys.exit(1)
    with open(SETTINGS_PATH, 'r') as f:
        return json.load(f)

def get_absolute_path(root_config, dataset_cfg, file_key):
    if file_key not in dataset_cfg:
        return None
    rel_root = root_config
    ds_dir = dataset_cfg.get("dataset_dir", "")
    file_name = dataset_cfg[file_key]
    full_path = PROJECT_ROOT / rel_root / ds_dir / file_name
    return full_path.resolve()

def log_print(message, log_file):
    """辅助函数：同时打印到控制台和写入文件"""
    print(message)
    if log_file:
        log_file.write(message + "\n")
        log_file.flush()

def run_benchmark(dataset_name, base_path, query_path, gt_path, log_file):
    header = f"\n🚀 [Running] {dataset_name}"
    log_print(header, log_file)
    log_print(f"   Base : {base_path}", log_file)
    log_print(f"   Query: {query_path}", log_file)
    log_print(f"   GT   : {gt_path}", log_file)
    
    # 直接传4个参数: ./lgo <name> <base> <query> <gt>
    cmd = [
        "./lgo",
        dataset_name,
        str(base_path),
        str(query_path),
        str(gt_path)
    ]
    
    try:
        # 使用 Popen 来实时获取输出并写入日志，而不是等运行完才写入
        process = subprocess.Popen(
            cmd,
            cwd=LGO_EXEC_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # 将错误输出也合并到标准输出
            text=True,                # 以文本形式处理
            bufsize=1                 # 行缓冲
        )

        # 逐行读取输出
        for line in process.stdout:
            line = line.rstrip() # 去除末尾换行符
            print(line)          # 打印到屏幕
            if log_file:
                log_file.write(line + "\n") # 写入文件
                log_file.flush()            # 确保实时写入

        process.wait()

        if process.returncode != 0:
            log_print(f"❌ Execution failed for {dataset_name} (Return Code: {process.returncode})", log_file)
        
    except KeyboardInterrupt:
        log_print("\n🛑 Interrupted by User.", log_file)
        sys.exit(1)
    except Exception as e:
        log_print(f"❌ System Error: {e}", log_file)

def main():
    # 确保日志文件的父目录存在
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"📂 Loading settings from: {SETTINGS_PATH}")
    print(f"📝 Logging output to: {LOG_FILE_PATH}")

    settings = load_settings()
    root_dir = settings.get("root_dir", ".")
    datasets_map = settings.get("datasets", {})

    # 以追加模式打开日志文件 ('a')，如果希望每次覆盖可以用 'w'
    with open(LOG_FILE_PATH, 'a', encoding='utf-8') as log_f:
        
        # 写入本次运行的头部信息
        start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_f.write(f"\n{'='*20} Batch Start: {start_time} {'='*20}\n")
        
        for ds_name in TARGET_DATASETS:
            if ds_name not in datasets_map:
                msg = f"⚠️  Skipping {ds_name}: Not found in settings"
                log_print(msg, log_f)
                continue
                
            cfg = datasets_map[ds_name]
            
            # 获取真实绝对路径
            base_path = get_absolute_path(root_dir, cfg, "base_path")
            query_path = get_absolute_path(root_dir, cfg, "query_path")
            gt_path = get_absolute_path(root_dir, cfg, "gt_path")

            if not base_path or not base_path.exists():
                msg = f"❌ Base file missing: {base_path}"
                log_print(msg, log_f)
                continue

            # 运行并传入日志文件句柄
            run_benchmark(ds_name, base_path, query_path, gt_path, log_f)

        end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_f.write(f"\n{'='*20} Batch Finished: {end_time} {'='*20}\n")

    print("\n✅ All Batch Jobs Finished.")

if __name__ == "__main__":
    main()