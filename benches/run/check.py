import os
import struct
import numpy as np

# 1. 锁定目标：使用和 C++ 日志里一模一样的相对路径
# C++ Log: Loading GT from: "./benches/datasets/SIFT10M/sift_groundtruth.ivecs"
REL_PATH = "benches/datasets/SIFT10M/sift_groundtruth.ivecs"
ABS_PATH = os.path.abspath(REL_PATH)

def fix_gt():
    print(f"🎯 Target File: {ABS_PATH}")
    
    if not os.path.exists(ABS_PATH):
        print("❌ Error: File not found! Are you in the 'code' directory?")
        return

    # 2. 验尸：先看看它现在到底是几
    file_size = os.path.getsize(ABS_PATH)
    with open(ABS_PATH, 'rb') as f:
        current_k = struct.unpack('i', f.read(4))[0]
    
    print(f"🧐 Current Header K: {current_k}")
    
    if current_k == 100:
        print("✅ It is already 100. (If C++ says 5000, check if C++ uses a different file copy!)")
        # 即使是 100，为了保险我们也可以强制重写一遍，但通常没必要
        # return 

    # 3. 手术：读取数据，裁剪，重写
    print("🔪 Performing surgery... (Resizing K to 100)")
    
    # 计算向量数量 N
    # 文件大小 = N * (4 + K * 4)
    # 反推 N
    vec_size_bytes = 4 + current_k * 4
    n = file_size // vec_size_bytes
    print(f"   Found {n} vectors with K={current_k}")

    # 使用 memmap 读取 (只读模式)
    data = np.memmap(ABS_PATH, dtype='int32', mode='r', shape=(n, current_k + 1))
    
    # 提取 ID (去掉第一列的维度信息)
    ids = data[:, 1:].copy()
    
    # 截取前 100 个邻居
    new_k = 100
    ids_100 = ids[:, :new_k]
    
    # 4. 缝合：写入新文件
    # 构造新的 buffer
    # 格式: [100, id0, id1, ... id99] (全是 int32)
    print(f"💾 Saving to {ABS_PATH}...")
    
    with open(ABS_PATH, 'wb') as f:
        for i in range(n):
            f.write(struct.pack('i', new_k)) # 写入新的 K=100
            f.write(ids_100[i].tobytes())    # 写入前 100 个 ID

    print("🎉 Surgery successful. The file is now K=100.")

if __name__ == "__main__":
    fix_gt()