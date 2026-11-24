"""Write the measured report and seal the result files after scoring."""
import csv
from pathlib import Path

import numpy as np

from drive import BATCHES, DATASETS, E197, METHODS, NAMES, POINTS, ROOT, config, digest, read, verify, write

ANALYSIS = ROOT / "analysis"


def csv_rows(name):
    with (ANALYSIS / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


def report(outcome, targets, wall):
    lines = [
        "# E252 新 B64 在三套经典平方 L2 数据上的复测",
        "",
        "Deep10M、BIGANN-SIFT10M 和 GIST1M 沿用冻结底库、图和 GT10。Mixed64 将",
        "原 B32 的有序前缀续填到每行至多 64 项。每集使用 24,192 条训练查询和 L176/192/208",
        "三档真 K100 主搜索漏点。Deep/SIFT 使用 soft 画像，GIST 用 hard 画像。",
        "",
        f"真 K1/K100 共 {POINTS} 点、{BATCHES} 个完整 CPU15 单线程批次，正式墙钟合计 {wall:.2f} 秒。"
        "每点两遍取算术平均。两遍结果包逐字节一致，"
        f"另核验首 256 条共 {POINTS*256:,} 条配置级查询的候选以及原距离合并排序。",
        "",
        "## 同 L 质量和成本",
        "",
        "| 数据集 | K | 查询 | 召回升 / 平 / 降 | 召回变化（百分点） | 额外精算数均值 | QPS 变化中位数 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for ds in DATASETS:
        n = outcome[ds]["n"]
        for k, result in outcome[ds]["scenes"].items():
            wins, ties, loss = (result[f"same_L_{key}"] for key in ("positive", "tied", "negative"))
            lo, hi = result["delta_pp"]
            lines.append(
                f'| {NAMES[ds]} | {k} | {n:,} | {wins} / {ties} / {loss} | {lo:+.4f} 到 {hi:+.4f} | '
                f'{result["mean_added_exact_256"]:.1f} | {result["same_L_qps_delta_median"]:+.2f}% |'
            )
    lines.extend([
        "",
        "额外精算数按各点首 256 条查询取平均，完整 QPS 使用全窗。低召回查询（真 K100",
        "命中少于 10 个）逐点失败率、救损和脱离失败的计数保存在逐点及同 L 表。",
        "",
        "## 固定召回目标达标比较",
        "",
        "两臂分别采用最快的同期实测达标点。慢遍胜出以新表慢遍 QPS 对原 B32 快遍 QPS 判断。",
        "",
        "| 数据集 | K | 新表均值更快 / 双边达标 | 新表慢遍更快 | QPS 变化范围 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for ds in DATASETS:
        for k, result in outcome[ds]["scenes"].items():
            speed_range = result["target_qps_delta_range"]
            span = f"{speed_range[0]:+.2f}% 到 {speed_range[1]:+.2f}%" if speed_range else "无双边达标"
            lines.append(f'| {NAMES[ds]} | {k} | {result["faster"]}/{result["common"]} | '
                         f'{result["slow_still_faster"]} | {span} |')
    lines.extend([
        "",
        "| 数据集 | K | 召回目标 | B32 的 L、召回与 QPS | Mixed64 的 L、召回与 QPS | QPS 变化 |",
        "| --- | ---: | ---: | --- | --- | ---: |",
    ])
    for row in targets:
        if not row["qps_delta_pct"]:
            continue
        arm_values = [f'L{row[f"{m}_L"]} / {float(row[f"{m}_recall_pct"]):.3f}% / {float(row[f"{m}_qps"]):,.1f}'
                      for m in METHODS]
        lines.append(f'| {NAMES[row["dataset"]]} | {row["K"]} | {row["target_pct"]}% | '
                     f'{" | ".join(arm_values)} | {float(row["qps_delta_pct"]):+.2f}% |')
    lines.extend([
        "",
        "## 表与离线成本",
        "",
        "| 数据集 | 训练阶段墙钟（秒） | 编译秒数 | 追加 ID 数 | 训练漏点 B32 / Mixed64 覆盖 | 在线新表 KiB | 峰值 RSS GiB |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for ds in DATASETS:
        folder = ROOT / "models" / ds
        source = read(folder / "roles.json")
        b = source["pool"]
        size = sum((folder / "mixed" / f).stat().st_size for f in ("B64.ids.i32", "B64.counts.i8")) / 1024
        rss = outcome[ds]["peak_rss_kib"] / 1024**2
        lines.append(
            f'| {NAMES[ds]} | {source["offline_seconds"]:.2f} | {b["seconds"]:.3f} | {b["appended_IDs"]:,} | '
            f'{b["covered_B32"]:,} / {b["covered_B64"]:,}（共 {b["tokens"]:,}） | {size:.1f} | {rss:.2f} |'
        )
    lines.extend([
        "",
        "训练阶段墙钟包括读取、实际三档主搜索、遗漏事件构造和新表编译，另有冻结输入验签。"
        "额外样本来自合法 fit 尾段和 QGT learn 角色，均与整套公开查询按向量字节互斥。"
        "实验在已公开的查询集、固定图和固定档位上完成。",
        "",
        "![Recall@1](analysis/recall_qps_k1.png)",
        "",
        "![Recall@100](analysis/recall_qps_k100.png)",
        "",
        "[协议](protocol.md) · [实测点](analysis/points.csv) · [两遍原始耗时](analysis/rounds.csv) · "
        "[同 L 救损](analysis/same_L.csv) · [固定目标](analysis/targets.csv) · [封存](seal.json)",
    ])
    with (ROOT / "report.md").open("x") as out:
        out.write("\n".join(lines) + "\n")


def audit_source():
    freeze = read(E197 / "formal_freeze.json")
    historical = {item["path"]: item["sha256"] for item in freeze["files"]}
    checked = {}
    for ds in DATASETS:
        c = read(config(ds))
        table_sha = digest(c["table"])
        assert table_sha == historical[c["table"]]
        query_path = Path(c["queries"]["path"])
        test_manifest = read(query_path.parent / "manifest.json")
        sources = {}
        for role in ("fit", "qgt", "test"):
            fvec = test_manifest["identities"][f"{role}_query"]
            path = Path(fvec["path"])
            assert digest(path) == fvec["sha256"]
            d = c["base"]["d"]
            raw = np.memmap(path.with_suffix(".f32"), "<i4", "r").reshape(-1, d)
            container = np.memmap(path, "<i4", "r").reshape(len(raw), d+1)
            assert (container[:, 0] == d).all() and np.array_equal(raw, container[:, 1:])
            sources[role] = dict(rows=len(raw), historical_fvecs_sha256=fvec["sha256"])
        checked[ds] = dict(B32_sha256=table_sha, words_equal=sources)
    write(ANALYSIS / "historical_identity.json", checked)


def finish():
    verify(ROOT / "inputs.json")
    rounds = csv_rows("rounds")
    points = csv_rows("points")
    assert len(rounds) == BATCHES and len(points) == POINTS
    wall = sum(float(row["seconds"]) for row in rounds)
    outcome = read(ANALYSIS / "outcome.json")
    audit_source()
    report(outcome, csv_rows("targets"), wall)
    write(ROOT / "state.json", dict(status="COMPLETE_E252", datasets=DATASETS, methods=METHODS,
                                      points=POINTS, batches=BATCHES, plot_methods=["Mixed64"], formal_wall_seconds=wall))
    files = {
        str(p.relative_to(ROOT)): dict(bytes=p.stat().st_size, sha256=digest(p))
        for p in sorted(ROOT.rglob("*")) if p.is_file() and "__pycache__" not in p.parts
    }
    write(ROOT / "seal.json", dict(status="SEALED_E252", files=files))
    for relative, item in files.items():
        file = ROOT / relative
        assert file.stat().st_size == item["bytes"] and digest(file) == item["sha256"], relative
    print(f"SEALED_E252 {len(files)} files verified")


if __name__ == "__main__":
    finish()
