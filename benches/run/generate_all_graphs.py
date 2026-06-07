import subprocess
import os
import shutil
import json

# 配置部分
DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
BUILD_DIR = "./build/benches"
GRAPH_PROCESSOR = f"{BUILD_DIR}/graph_processor"

def run_cmd(cmd):
    print(f"👉 执行: {' '.join(cmd)}")
    ret = subprocess.call(cmd)
    if ret != 0:
        print("❌ 失败！")
        return False
    return True

def find_valid_cluster_source(base_dir, dataset):
    """寻找任何可用的聚类源文件"""
    candidates = [
        f"{base_dir}/entry_points.json",
        f"{base_dir}/entry_points_pca.json",
        f"{base_dir}/neural_entry_points.json",
        f"dpc/{dataset}_results/dpc_hierarchical_results.json" # DPC 原始结果
    ]
    
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def main():
    if not os.path.exists(GRAPH_PROCESSOR):
        print("❌ 找不到 graph_processor，请先编译: cd build && make graph_processor -j")
        return

    print("🚀 开始生成 3 种不同配置的图文件 (自动修复缺失文件模式)...\n")

    for dataset in DATASETS:
        print(f"\n{'='*60}")
        print(f"📦 处理数据集: {dataset}")
        print(f"{'='*60}")

        base_dir = f"graph_processing/{dataset}_results"
        os.makedirs(base_dir, exist_ok=True)
        acpg_file = f"acpg/{dataset}_index/acpg_nsg.json"
        
        # 1. 寻找最佳输入源
        source_file = find_valid_cluster_source(base_dir, dataset)
        if not source_file:
             print(f"⚠️ {dataset} 彻底丢失聚类源文件 (entry_points/dpc)，无法恢复！跳过。")
             continue
        
        print(f"✅ 使用源文件: {source_file}")
        
        # 2. 创建一个临时底板，防止被后续步骤误删/改名
        # 我们统一把源文件复制成 'base_input.json'，所有步骤都读它
        base_input = f"{base_dir}/base_input_temp.json"
        shutil.copy(source_file, base_input)

        model_onnx = f"drl/{dataset}_results/ae_encoder.onnx"
        
        # PCA 模型路径 (通常由 build_neural_graph 生成，或者复用之前的)
        # 如果找不到专门的 PCA 文件，有些流程可能会生成到 base_dir
        pca_model = f"{base_dir}/pca_transform.bin"
        
        # 神经图结构文件
        neural_graph_txt = f"drl/{dataset}_results/neural_graph.txt"
        if not os.path.exists(neural_graph_txt):
             neural_graph_txt = f"{base_dir}/neural_graph.txt"

        # C++ 程序固定输出的文件名
        raw_output = f"{base_dir}/entry_points.json"

        # -------------------------------------------------
        # 🟢 任务 1: 生成 [PCA + 几何图] -> entry_points_pca.json
        # -------------------------------------------------
        print(f"\n[1/3] 生成 PCA + 几何图...")
        if os.path.exists(pca_model):
            if run_cmd([
                GRAPH_PROCESSOR,
                "--acpg", acpg_file,
                "--cluster", base_input, # 读临时底板
                "--out", base_dir,
                "--model", pca_model, 
                "--use_pca" 
            ]):
                target = f"{base_dir}/entry_points_pca.json"
                # graph_processor 输出了 entry_points.json，我们把它重命名
                if os.path.exists(raw_output):
                    shutil.move(raw_output, target)
                    print(f"✅ 成功生成: {target}")
                else:
                    print("❌ 输出文件未生成")
        else:
            print(f"⚠️ 跳过 PCA: 未找到 PCA 模型 {pca_model}")

        # -------------------------------------------------
        # 🟢 任务 2: 生成 [Neural + 几何图] -> entry_points_neural_euclidean.json
        # -------------------------------------------------
        if os.path.exists(model_onnx):
            print(f"\n[2/3] 生成 Neural + 几何图...")
            if run_cmd([
                GRAPH_PROCESSOR,
                "--acpg", acpg_file,
                "--cluster", base_input, # 读临时底板
                "--out", base_dir,
                "--model", model_onnx
            ]):
                target = f"{base_dir}/entry_points_neural_euclidean.json"
                if os.path.exists(raw_output):
                    shutil.move(raw_output, target)
                    print(f"✅ 成功生成: {target}")
        else:
            print(f"⚠️ 跳过 Neural: 未找到 ONNX 模型 {model_onnx}")

        # -------------------------------------------------
        # 🟢 任务 3: 生成 [Neural + 神经图] -> entry_points_neural_topology.json
        # -------------------------------------------------
        if os.path.exists(model_onnx) and os.path.exists(neural_graph_txt):
            print(f"\n[3/3] 生成 Neural + 神经图 (Golden Edges)...")
            if run_cmd([
                GRAPH_PROCESSOR,
                "--acpg", acpg_file,
                "--cluster", base_input, # 读临时底板
                "--out", base_dir,
                "--model", model_onnx,
                "--neural_graph", neural_graph_txt
            ]):
                target = f"{base_dir}/entry_points_neural_topology.json"
                if os.path.exists(raw_output):
                    shutil.move(raw_output, target)
                    print(f"✅ 成功生成: {target}")
        else:
            print(f"⚠️ 跳过 Neural Graph: 缺少模型或图文件 ({neural_graph_txt})")
            
        # 清理临时底板
        if os.path.exists(base_input):
            os.remove(base_input)

    print("\n🎉 所有图文件生成修复完毕！")

if __name__ == "__main__":
    main()