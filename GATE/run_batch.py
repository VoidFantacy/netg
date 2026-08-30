import subprocess
import os
import time
import json

# ================= 配置区域 =================
SETTINGS_JSON_PATH = os.environ.get(
    "GATE_SETTINGS_JSON",
    "/mnt/new/New/ACSG/benches/datasets/settings.json"
)
DATASET_ROOT_DIR = os.environ.get(
    "GATE_DATASET_ROOT",
    "/mnt/new/New/ACSG/benches/datasets"
)

# 维度映射表
DATASET_DIMS = {
    "deep10M": 96,
    "sift10M": 128,
    "sift10M_skewed": 128,
    "yandex_t2i": 200,
    "gist1M": 960
}

# 全部数据集重跑（修复样本生成 + 训练保存策略后全量重跑）
TARGETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]

# 是否强制重新生成样本和重新训练（删除旧的 hub_embeddings.bin / pos_sample.txt / *.pth）
FORCE_REGEN = True
# ===========================================

def run_command(cmd):
    print(f"\n[Batch] Executing: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def main():
    # 赋予权限
    subprocess.run("chmod +x run_gate_generic.sh", shell=True)

    if not os.path.exists(SETTINGS_JSON_PATH):
        print(f"❌ Error: Cannot find settings.json at {SETTINGS_JSON_PATH}")
        return

    print(f"📖 Loading settings from {SETTINGS_JSON_PATH}...")
    with open(SETTINGS_JSON_PATH, 'r') as f:
        settings = json.load(f)

    start_time_all = time.time()
    success_list = []
    fail_list = []

    for name in TARGETS:
        if name not in settings['datasets']:
            print(f"⚠️  Skipping '{name}': Not found in settings.json")
            continue
        
        ds_config = settings['datasets'][name]
        dim = DATASET_DIMS.get(name)
        if not dim:
            print(f"⚠️  Skipping '{name}': Dimension not defined.")
            continue
        
        # 提取路径 (ROOT / dataset_dir / filename)
        sub_dir = ds_config.get("dataset_dir", "")
        base_name = ds_config.get("base_path", "")
        query_name = ds_config.get("query_path", "")
        gt_name = ds_config.get("gt_path", "")  # 【新增】读取 GT 文件名
        
        base_path = os.path.join(DATASET_ROOT_DIR, sub_dir, base_name)
        query_path = os.path.join(DATASET_ROOT_DIR, sub_dir, query_name)
        gt_path = os.path.join(DATASET_ROOT_DIR, sub_dir, gt_name) if gt_name else ""

        # 检查文件
        if not os.path.exists(base_path):
            print(f"❌ Error: Base file missing at {base_path}")
            fail_list.append(name)
            continue
        
        # 打印信息
        print(f"\n{'='*60}")
        print(f"🚀 Starting Experiment: {name}")
        print(f"   Dim  : {dim}")
        print(f"   Base : {base_path}")
        print(f"   Query: {query_path}")
        if gt_path and os.path.exists(gt_path):
            print(f"   GT   : {gt_path}")
        else:
            print(f"   GT   : Not found (Recall will be 0)")
            gt_path = "" # 确保传给 shell 的是空字符串，或者不传
        print(f"{'='*60}")

        try:
            # 强制重跑：删除旧的 hub_embeddings、样本文件、模型，触发重新生成
            if FORCE_REGEN:
                out_dir = f"/mnt/new/New/ACSG/GATE/output_{name}"
                import glob
                for f_del in [
                    f"{out_dir}/hub_embeddings.bin",
                    f"{out_dir}/train_samples_dir/pos_sample.txt",
                    f"{out_dir}/train_samples_dir/neg_sample.txt",
                ] + glob.glob(f"{out_dir}/models/*.pth"):
                    if os.path.exists(f_del):
                        os.remove(f_del)
                        print(f"  🗑  Removed: {f_del}")

            cmd = f"./run_gate_generic.sh {name} {dim} \"{base_path}\" \"{query_path}\" \"{gt_path}\""
            run_command(cmd)
            success_list.append(name)
            print(f"✅ Finished: {name}")
        except Exception as e:
            print(f"❌ Failed: {name}. Reason: {e}")
            fail_list.append(name)

    duration = (time.time() - start_time_all) / 60.0
    print(f"\n{'='*60}")
    print(f"📊 Batch Summary | Total Time: {duration:.2f} mins")
    print(f"✅ Success: {', '.join(success_list)}")
    print(f"❌ Failed:  {', '.join(fail_list)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()