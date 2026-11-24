"""Summarize exact measurements and seal the new run."""
import csv

from drive import BATCHES, DATASETS, METHODS, NAMES, POINTS, ROOT, digest, read, verify, write
from score import PAIRS

ANALYSIS = ROOT / "analysis"
LABELS = {"GT10": "GT10", "B32": "GT10+B32", "Mixed64": "GT10+新 B64"}


def csv_rows(name):
    with (ANALYSIS / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


def report(outcome, targets, wall):
    lines = [
        "# E253 三套经典 L2 数据的三方法同期比较",
        "",
        "纯 GT10、GT10+B32、GT10+Mixed64 冻结 E252 相同底库、主图、GT10 画像、补点表、"
        "公开查询窗和 L 网格。纯 GT10 直接返回主搜索结果。",
        "",
        f"真 K1/K100 共 {POINTS} 点、{BATCHES} 个完整 CPU15 单线程批次，正式墙钟合计 {wall:.2f} 秒。"
        "每点两遍取 QPS 算术平均。两遍结果包逐字节相同，原 B32 和 Mixed64 的 192 组返回与 E252 四字段逐字一致。"
        f"每点另核首 256 条查询，共 {POINTS*256:,} 条配置级核验。",
        "",
        "## 相同 L 的取舍",
        "",
        "| 数据集 | K | 比较 | 召回升 / 平 / 降 | 召回变化（百分点） | 额外精算数 | QPS 变化中位数 |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for ds in DATASETS:
        for k, scene in outcome[ds]["scenes"].items():
            for control, method in PAIRS:
                p = scene["pairs"][f"{method}_vs_{control}"]
                wins = " / ".join(str(p[f"same_L_{v}"]) for v in ("positive", "tied", "negative"))
                lo, hi = p["delta_pp"]
                lines.append(f'| {NAMES[ds]} | {k} | {LABELS[method]} 对 {LABELS[control]} | {wins} | '
                             f'{lo:+.4f} 到 {hi:+.4f} | {p["mean_added_exact_256"]:.1f} | '
                             f'{p["same_L_qps_delta_median"]:+.2f}% |')
    lines.extend([
        "",
        "额外精算数是每点前 256 条资格查询的均值。逐点和同 L 表记录 K100 的低召回查询"
        "（命中 0–9 个）、故障改善和脱离计数。",
        "",
        "## 固定召回目标",
        "",
        "各方法使用最快的同期实测达标点。比较在共同达标的目标上进行，"
        "同一门槛允许三种方法的实际召回不同。慢遍胜出表示较新方法的慢遍仍高于对照快遍。",
        "",
        "| 数据集 | K | GT10 / B32 / Mixed64 各自最快次数 | B32 对 GT10 更快 | 新 B64 对 GT10 更快 | 新 B64 对 B32 更快 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    for ds in DATASETS:
        for k, scene in outcome[ds]["scenes"].items():
            best = " / ".join(str(scene["fastest"][m]) for m in METHODS)
            pace = []
            for control, method in PAIRS:
                p = scene["pairs"][f"{method}_vs_{control}"]
                pace.append(f'{p["faster"]}/{p["common"]}（慢遍 {p["slow_still_faster"]}）')
            lines.append(f'| {NAMES[ds]} | {k} | {best} | {" | ".join(pace)} |')
    lines.extend([
        "",
        "| 数据集 | K | 召回目标 | GT10 的 L、召回和 QPS | GT10+B32 的 L、召回和 QPS | 新 B64 的 L、召回和 QPS |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ])
    for row in targets:
        values = []
        for m in METHODS:
            if row[f"{m}_L"]:
                values.append(f'L{row[f"{m}_L"]} / {float(row[f"{m}_recall_pct"]):.3f}% / {float(row[f"{m}_qps"]):,.1f}')
            else:
                values.append("未达标")
        lines.append(f'| {NAMES[row["dataset"]]} | {row["K"]} | {row["target_pct"]}% | {" | ".join(values)} |')
    lines.extend([
        "",
        "![Recall@1](analysis/recall_qps_k1.png)",
        "",
        "![Recall@100](analysis/recall_qps_k100.png)",
        "",
        "[协议](protocol.md) · [逐点](analysis/points.csv) · [两遍计时](analysis/rounds.csv) · "
        "[同 L 救损](analysis/same_L.csv) · [固定目标](analysis/targets.csv) · [原生返回校验](analysis/historical_parity.csv) · [封存](seal.json)",
    ])
    with (ROOT / "report.md").open("x") as out:
        out.write("\n".join(lines) + "\n")


def finish():
    verify(ROOT / "inputs.json")
    repeats = csv_rows("rounds")
    assert len(repeats) == BATCHES and len(csv_rows("points")) == POINTS
    assert len(csv_rows("historical_parity")) == 192
    wall = sum(float(row["seconds"]) for row in repeats)
    report(read(ANALYSIS / "outcome.json"), csv_rows("targets"), wall)
    write(ROOT / "state.json", dict(status="COMPLETE_E253", datasets=DATASETS, methods=METHODS, points=POINTS,
                                      batches=BATCHES, historical_payload_matches=192, formal_wall_seconds=wall))
    files = {str(p.relative_to(ROOT)): dict(bytes=p.stat().st_size, sha256=digest(p))
             for p in sorted(ROOT.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
    write(ROOT / "seal.json", dict(status="SEALED_E253", files=files))
    for relative, item in files.items():
        p = ROOT / relative
        assert p.stat().st_size == item["bytes"] and digest(p) == item["sha256"], relative
    print(f"SEALED_E253 {len(files)} files verified")


if __name__ == "__main__":
    finish()
