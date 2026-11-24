"""Write the report, seal the artifacts, and independently verify the seal."""
import csv
from pathlib import Path
import sys

from drive import BATCHES, DATASETS, METHODS, NAMES, POINTS, ROOT, config, digest, read, verify, write

A = ROOT / "analysis"


def csv_rows(table):
    with (A / f"{table}.csv").open() as file:
        return list(csv.DictReader(file))


def target_text(point, key):
    prefix = key + "_"
    if point[prefix + "L"] is None:
        return "—"
    return f'L{point[prefix+"L"]} / {point[prefix+"recall_pct"]:.4f}% / {point[prefix+"qps"]:,.1f}'


def percent(number):
    return "—" if number is None else f"{number:+.2f}%"


def finish():
    points = csv_rows("points")
    rounds = csv_rows("rounds")
    parity = csv_rows("historical_parity")
    result = read(A / "outcome.json")
    provenance = read(ROOT / "configs/table_provenance.json")
    assert len(points) == POINTS and len(rounds) == BATCHES
    report = [
        "# E251 四集 B32、老 B64 与新 B64 复测", "",
        f"四集各 3,072 条真实公开查询、真 K1 和 K100、{POINTS} 点、{BATCHES} 个完整 CPU15 单线程批次，每点两遍。",
        "所有正式批次结束后按原 GT100 评分。下表使用各法在同一召回门槛内最快的实测点，QPS 取两遍均值。",
        "",
        "## 代表召回门槛", "",
        "| 数据集 | K | 门槛 | B32 的 L / 召回 / QPS | 老 B64 | 新 B64 | 新对 B32 | 新对老 B64 | 慢遍对老快遍 |",
        "|---|---:|---:|---|---|---|---:|---:|---:|",
    ]
    for ds in DATASETS:
        for k in (1, 100):
            x = result[ds][str(k)]["Mixed64/B32"]["primary"]
            y = result[ds][str(k)]["Mixed64/B64-old"]["primary"]
            assert x["target_pct"] == y["target_pct"]
            report.append(f'| {NAMES[ds]} | {k} | {x["target_pct"]:g}% | {target_text(x,"b")} | '
                          f'{target_text(y,"b")} | {target_text(x,"a")} | {percent(x["qps_delta_pct"])} | '
                          f'{percent(y["qps_delta_pct"])} | {percent(y["slow_vs_fast_pct"])} |')
    report += ["", "## 全网格", "",
               "固定门槛的速度胜点按双方均达标统计。折线描述只覆盖两法实际召回重叠，实测支配使用原始测量点。",
               "",
               "| 数据集 | K | 对照 | 新版同 L 召回提高 | 新版同 L 召回差（百分点） | 新版达标均值更快 | 新版慢遍仍更快 | 新版重叠折线更快 | 新版被对照实点支配 |",
               "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for ds in DATASETS:
        for k in (1, 100):
            for m in ("B32", "B64-old"):
                a = result[ds][str(k)][f"Mixed64/{m}"]
                lo, hi = a["same_L_recall_range_pp"]
                report.append(f'| {NAMES[ds]} | {k} | {m} | {a["same_L_wins"]}/{a["same_L_count"]} | '
                              f'{lo:+.4f} 到 {hi:+.4f} | {a["goals_faster"]}/{a["targets"]} | '
                              f'{a["goals_slow_faster"]}/{a["targets"]} | {a["interp_faster"]}/{a["interp_count"]} | {a["dominated"]} |')
    report += ["", "## 训练与资源", "",
               "| 数据集 | 新表来源 | 训练查询 / 追加 | 新表在线文件 KiB | 进程峰值 RSS GiB | K1 / K100 的 L 档数 |",
               "|---|---|---:|---:|---:|---:|"]
    for ds in DATASETS:
        entry = provenance[ds]
        pool = Path(entry["pool"])
        model_kib = sum((pool / name).stat().st_size for name in ("B64.ids.i32", "B64.counts.i8")) / 1024
        stats = read(ROOT / "data" / ds / "complete.json")
        c = read(config(ds))
        sizes = "/".join(str(len(c["grids"][k])) for k in ("1", "100"))
        report.append(f'| {NAMES[ds]} | {entry["origin"]} | {entry["scope"]["n"]:,} / {entry["scope"]["extra"]:,} | '
                      f'{model_kib:.1f} | {stats["peak_rss_kib"]/1024**2:.2f} | {sizes} |')
    report += ["", "Flickr30k 从固定 profile 角色取额外真查询并重算精确 raw-IP 标签，Yandex 从原 router_train 中按精确向量排重。",
               "复测的 COCO、Flickr30k、WebVid、Yandex 查询为 E229 历史公开窗。绝对 QPS 按本轮同期对照解读。",
               f"全部两遍包按字节相同。核验了 {len(parity)} 组历史同档四字段和 {POINTS*256:,} 条额外原生标量排序。",
               "",
               "![Recall@1 四集三方法](analysis/recall_qps_k1.png)", "",
               "![Recall@100 四集三方法](analysis/recall_qps_k100.png)", "",
               "[协议](protocol.md) · [逐点](analysis/points.csv) · [原始两遍](analysis/rounds.csv) · [固定目标](analysis/targets.csv) · "
               "[同 L 救损](analysis/same_L.csv) · [逐点匹配](analysis/matched.csv) · [表来源](configs/table_provenance.json) · [封存](seal.json)", ""]
    (ROOT / "report.md").write_text("\n".join(report))
    write(ROOT / "state.json", dict(status="COMPLETE_E251", datasets=DATASETS, methods=METHODS,
                                     points=POINTS, batches=BATCHES, historical_parity=len(parity)))
    files = {str(p.relative_to(ROOT)): dict(bytes=p.stat().st_size,sha256=digest(p))
             for p in sorted(ROOT.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
    write(ROOT / "seal.json", dict(status="SEALED_E251", files=files))


def audit():
    verify(ROOT / "inputs.json")
    record = read(ROOT / "seal.json")
    for rel, info in record["files"].items():
        p = ROOT / rel
        assert p.stat().st_size == info["bytes"] and digest(p) == info["sha256"], rel
    print(record["status"], len(record["files"]), "files verified")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        finish()
    audit()
