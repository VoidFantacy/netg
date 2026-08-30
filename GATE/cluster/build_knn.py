
import argparse

import faiss

import numpy as np

import struct

import os

import sys



def read_fvecs(filename):

    print(f"Loading data from {filename}...")

    with open(filename, 'rb') as f:

        d = struct.unpack('i', f.read(4))[0]

        f.seek(0, 2)

        n = f.tell() // (4 + 4 * d)

        f.seek(0)

        x = np.zeros((n, d), dtype=np.float32)

        for i in range(n):

            f.read(4)

            x[i] = np.frombuffer(f.read(d * 4), dtype=np.float32)

    print(f"Data shape: {x.shape}")

    return x



def save_graph(filename, I):

    print(f"Saving graph to {filename}...")

    (n, k) = I.shape

    

    # 强制使用小端序 (<) 4字节整数 (i)

    # 这样可以保证在任何机器上生成的二进制都与 C++ 的 fread 兼容

    header_struct = struct.Struct('<i')

    

    with open(filename, 'wb') as f:

        for i in range(n):

            # 过滤无效邻居 (-1)

            valid_neighbors = [int(idx) for idx in I[i] if idx >= 0]

            real_k = len(valid_neighbors)

            

            # 1. 写入 K (4字节)

            f.write(header_struct.pack(real_k))

            

            # 2. 写入邻居 ID (real_k * 4字节)

            if real_k > 0:

                # astype('<i4') 强制转换为 小端序 32位整数

                arr = np.array(valid_neighbors, dtype=np.int32).astype('<i4')

                f.write(arr.tobytes())



def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('--base_path', required=True)

    parser.add_argument('--output_path', required=True)

    parser.add_argument('--k', type=int, default=200)

    args = parser.parse_args()



    xb = read_fvecs(args.base_path)

    d = xb.shape[1]



    print(f"Building KNN graph (K={args.k})...")

    # 使用 HNSW 加速构建

    index = faiss.IndexHNSWFlat(d, 32)

    index.hnsw.efConstruction = 128 

    index.add(xb)

    

    print("Searching for neighbors...")

    index.hnsw.efSearch = 128

    D, I = index.search(xb, args.k)



    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)

    save_graph(args.output_path, I)

    print("✅ KNN Graph built successfully (Aligned Mode).")



if __name__ == '__main__':

    main()

