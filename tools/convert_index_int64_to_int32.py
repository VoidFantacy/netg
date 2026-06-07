#!/usr/bin/env python3
"""
convert_index_int64_to_int32.py
将旧版 acpg_nsg.bin（图邻居用 int64 存储）转换为新版（int32 存储）。

格式说明（VERSION=2）：
  [4]  VERSION (int32)
  [8]  ntotal (int64)
  [4]  d (int32)
  [4]  metric (int32)
  [1]  is_trained (bool)
  [1]  is_built (bool)
  [1]  build_type (char)
  [4]  alpha (float)
  [4]  beta (float)
  [4]  rho (float)
  [4]  lambda (float)
  [4]  iterations (int32)
  [4]  thresholdrej (int32)
  [4]  search_L (int32)
  [4]  nsg_R (int32)
  [4]  enterpoint (int32)
  [8]  ant_nums (int64)
  [8]  pheromone_size (uint64)
  [4*pheromone_size] pheromone data (float)
  [8]  weight_size (uint64)
  [4*weight_size]  weight data (float)
  [4]  graph_K (int32)
  [8]  neighbor_count (uint64)
  [OLD: 8*neighbor_count] neighbor data (int64)  ← 旧格式
  [NEW: 4*neighbor_count] neighbor data (int32)  ← 新格式
  [8]  vec_count (uint64)
  [4*vec_count]  vector data (float)
  [8]  top_enterpoints_size (uint64)
  per entry: [4] id (int32) + [8] weight (double)
"""

import struct
import sys
import os
import shutil

def read_fmt(f, fmt):
    size = struct.calcsize(fmt)
    return struct.unpack(fmt, f.read(size))

def write_fmt(f, fmt, *vals):
    f.write(struct.pack(fmt, *vals))

def convert(src_path: str, dst_path: str):
    print(f"  读取: {src_path}")
    print(f"  写入: {dst_path}")

    with open(src_path, 'rb') as fin, open(dst_path, 'wb') as fout:

        # ── 1. VERSION ──────────────────────────────────────────────
        (VERSION,) = read_fmt(fin, '<i')
        if VERSION not in (1, 2):
            raise ValueError(f"不支持的 VERSION={VERSION}，仅支持 1 或 2")
        write_fmt(fout, '<i', VERSION)
        print(f"  VERSION = {VERSION}")

        # ── 2. 核心元数据 ────────────────────────────────────────────
        (ntotal,)       = read_fmt(fin, '<q')   # int64
        (d,)            = read_fmt(fin, '<i')   # int32
        (metric,)       = read_fmt(fin, '<i')   # int32
        (is_trained,)   = read_fmt(fin, '<B')   # bool(uint8)
        (is_built,)     = read_fmt(fin, '<B')
        (build_type,)   = read_fmt(fin, '<c')   # char
        write_fmt(fout, '<q', ntotal)
        write_fmt(fout, '<i', d)
        write_fmt(fout, '<i', metric)
        write_fmt(fout, '<B', is_trained)
        write_fmt(fout, '<B', is_built)
        fout.write(build_type)
        print(f"  ntotal={ntotal}, d={d}")

        # ── 3. ACSG 参数 ─────────────────────────────────────────────
        (alpha,)        = read_fmt(fin, '<f')
        (beta,)         = read_fmt(fin, '<f')
        (rho,)          = read_fmt(fin, '<f')
        (lam,)          = read_fmt(fin, '<f')
        (iterations,)   = read_fmt(fin, '<i')
        (thresholdrej,) = read_fmt(fin, '<i')
        (search_L,)     = read_fmt(fin, '<i')
        (nsg_R,)        = read_fmt(fin, '<i')
        (enterpoint,)   = read_fmt(fin, '<i')
        (ant_nums,)     = read_fmt(fin, '<q')   # int64
        for v, fmt in [(alpha,'<f'),(beta,'<f'),(rho,'<f'),(lam,'<f'),
                       (iterations,'<i'),(thresholdrej,'<i'),(search_L,'<i'),
                       (nsg_R,'<i'),(enterpoint,'<i'),(ant_nums,'<q')]:
            write_fmt(fout, fmt, v)

        # ── 4. pheromone ─────────────────────────────────────────────
        (ph_size,) = read_fmt(fin, '<Q')   # uint64
        write_fmt(fout, '<Q', ph_size)
        fout.write(fin.read(ph_size * 4))  # float32 array, 直接拷贝

        # ── 5. weight ────────────────────────────────────────────────
        (wt_size,) = read_fmt(fin, '<Q')
        write_fmt(fout, '<Q', wt_size)
        fout.write(fin.read(wt_size * 4))

        # ── 6. 图结构（核心转换）────────────────────────────────────
        (graph_K,)        = read_fmt(fin, '<i')
        (neighbor_count,) = read_fmt(fin, '<Q')
        write_fmt(fout, '<i', graph_K)
        write_fmt(fout, '<Q', neighbor_count)
        print(f"  graph_K={graph_K}, neighbor_count={neighbor_count}")

        if graph_K > 0 and neighbor_count > 0:
            CHUNK = 1_000_000   # 每批处理 100 万个，避免一次性占太多内存
            converted = 0
            while converted < neighbor_count:
                batch = min(CHUNK, neighbor_count - converted)
                raw = fin.read(batch * 8)          # 旧：int64 × batch
                if len(raw) != batch * 8:
                    raise IOError(f"文件截断：期望 {batch*8} 字节，实际读到 {len(raw)}")
                vals = struct.unpack(f'<{batch}q', raw)    # int64

                # 转成 int32（-1 表示无效，其余是节点 ID，不超过 int32 范围）
                out_raw = struct.pack(f'<{batch}i', *vals)  # int32
                fout.write(out_raw)

                converted += batch
                if converted % 50_000_000 == 0:
                    pct = converted / neighbor_count * 100
                    print(f"    图转换进度: {pct:.1f}%  ({converted}/{neighbor_count})")

            print(f"  ✅ 图邻居转换完成: {neighbor_count} 条 int64 → int32")
            saved_mb = neighbor_count * 4 / 1024 / 1024
            print(f"  💾 节省内存: {saved_mb:.0f} MB")

        # ── 7. 向量数据（直接拷贝）──────────────────────────────────
        (vec_count,) = read_fmt(fin, '<Q')
        write_fmt(fout, '<Q', vec_count)
        print(f"  向量数据: {vec_count} floats ({vec_count*4/1024/1024:.0f} MB)，直接拷贝...")
        # 分块拷贝，避免大内存峰值
        remaining = vec_count * 4
        COPY_CHUNK = 256 * 1024 * 1024  # 256 MB per chunk
        while remaining > 0:
            chunk = min(COPY_CHUNK, remaining)
            fout.write(fin.read(chunk))
            remaining -= chunk

        # ── 8. top_enterpoints（VERSION=2 才有）─────────────────────
        if VERSION == 2:
            (ep_size,) = read_fmt(fin, '<Q')
            write_fmt(fout, '<Q', ep_size)
            # 每个 EnterPoint: id(int32) + weight(double=8字节)
            fout.write(fin.read(ep_size * (4 + 8)))
            print(f"  top_enterpoints: {ep_size} 个")

        # ── 检查是否读完 ─────────────────────────────────────────────
        tail = fin.read(16)
        if tail:
            print(f"  ⚠️  文件末尾还有 {len(tail)} 字节未读，请核查格式")
        else:
            print(f"  ✅ 文件读取完整")

        # 强制落盘，确保 .new 文件完整写入
        fout.flush()
        os.fsync(fout.fileno())

    print(f"  转换完成 ✅")


def main():
    DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
    BASE_DIR  = "/mnt/new/New/ACSG"

    targets = []
    for ds in DATASETS:
        path = os.path.join(BASE_DIR, f"acpg/{ds}_index/acpg_nsg.json")
        if os.path.exists(path):
            targets.append((ds, path))
        else:
            print(f"⚠️  跳过 {ds}：找不到 {path}")

    if not targets:
        print("没有找到任何索引文件，退出。")
        return

    print(f"共找到 {len(targets)} 个索引文件待转换\n")

    for ds, src in targets:
        print(f"\n{'='*60}")
        print(f"📦 数据集: {ds}")
        backup = src + ".int64.bak"
        dst    = src + ".new"

        # 备份原文件
        if not os.path.exists(backup):
            print(f"  备份原文件 → {os.path.basename(backup)}")
            shutil.copy2(src, backup)
        else:
            print(f"  备份已存在，跳过备份")

        # 转换到临时文件
        try:
            convert(backup, dst)
        except Exception as e:
            print(f"  ❌ 转换失败: {e}")
            if os.path.exists(dst):
                os.remove(dst)
            continue

        # 替换原文件
        if not os.path.exists(dst):
            print(f"  ❌ .new 文件不存在，跳过替换（可能已在上次运行中完成）")
            continue
        os.replace(dst, src)
        print(f"  ✅ 已替换原索引文件")

    print(f"\n🎉 全部转换完成！备份保留为 *.int64.bak")


if __name__ == "__main__":
    main()
