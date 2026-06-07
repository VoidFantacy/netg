import subprocess
import os
import time
import json

# ================= 配置区域 =================

# 1. 您的 settings.json 绝对路径
SETTINGS_JSON_PATH = "/path/to/ACSG/benches/datasets/settings.json"

# 2. 数据集根目录 (settings.json 里的相对路径是基于这里的)
# 数据都在 /path/to/ACSG/benches/datasets 下
DATASET_ROOT_DIR = "/path/to/ACSG/benches/datasets"

# 3. 维度映射表 (JSON里没有维度，我们需要手动指定标准维度)
DATASET_DIMS = {
    "deep10M": 96,
    "sift10M": 128,
    "sift10M_skewed": 128,
    "yandex_t2i": 200,
    "gist1M": 960
}

# 4. 指定要运行的数据集列表 (必须在 JSON 文件的 keys 里)
TARGETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]

# ===========================================

def run_command(cmd):
    """执行命令并实时输出"""
    print(f"\n[Batch] Executing: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing command: {cmd}")
        raise e

def main():
    # 0. 赋予 shell 脚本执行权限
    subprocess.run("chmod +x run_gate_generic.sh", shell=True)

    # 1. 读取 settings.json
    if not os.path.exists(SETTINGS_JSON_PATH):
        print(f"❌ Error: Cannot find settings.json at {SETTINGS_JSON_PATH}")
        return

    print(f"📖 Loading settings from {SETTINGS_JSON_PATH}...")
    with open(SETTINGS_JSON_PATH, 'r') as f:
        settings = json.load(f)

    # 2. 准备统计
    start_time_all = time.time()
    success_list = []
    fail_list = []

    # 3. 遍历目标数据集
    for name in TARGETS:
        if name not in settings['datasets']:
            print(f"⚠️  Skipping '{name}': Not found in settings.json")
            continue
        
        if name not in DATASET_DIMS:
            print(f"⚠️  Skipping '{name}': Dimension not defined in script.")
            continue

        # 获取配置信息
        ds_config = settings['datasets'][name]
        dim = DATASET_DIMS[name]
        
        # 提取子目录和文件名
        # 逻辑: ROOT / dataset_dir / base_path
        sub_dir = ds_config.get("dataset_dir", "")
        base_name = ds_config.get("base_path", "")
        query_name = ds_config.get("query_path", "")
        
        # 拼接绝对路径
        base_path = os.path.join(DATASET_ROOT_DIR, sub_dir, base_name)
        query_path = os.path.join(DATASET_ROOT_DIR, sub_dir, query_name)

        # 检查文件是否存在
        if not os.path.exists(base_path):
            print(f"❌ Error: Base file missing at {base_path}")
            fail_list.append(name)
            continue
        if not os.path.exists(query_path):
            print(f"❌ Error: Query file missing at {query_path}")
            fail_list.append(name)
            continue

        # 打印运行信息
        print(f"\n{'='*60}")
        print(f"🚀 Starting Experiment: {name}")
        print(f"   Dim  : {dim}")
        print(f"   Base : {base_path}")
        print(f"   Query: {query_path}")
        print(f"{'='*60}")

        try:
            # 调用 run_gate_generic.sh
            # ./run_gate_generic.sh <Name> <Dim> <Base> <Query>
            cmd = f"./run_gate_generic.sh {name} {dim} \"{base_path}\" \"{query_path}\""
            run_command(cmd)
            
            success_list.append(name)
            print(f"✅ Finished: {name}")

        except Exception as e:
            print(f"❌ Failed: {name}. Reason: {e}")
            fail_list.append(name)

    # 4. 汇总
    duration = (time.time() - start_time_all) / 60.0
    print(f"\n{'='*60}")
    print(f"📊 Batch Processing Summary")
    print(f"Total Time: {duration:.2f} mins")
    print(f"✅ Success ({len(success_list)}): {', '.join(success_list)}")
    print(f"❌ Failed  ({len(fail_list)}): {', '.join(fail_list)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()