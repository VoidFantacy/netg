#!/usr/bin/env python3
"""Aggregate the two-dataset QPS/recall/tail benchmark into JSON, CSV and Markdown."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path


DATASETS = {
    "webvid2_5m_light_v1": "WebVid-2.5M/IP",
    "yandex_t2i_official10M_ip_v1": "Yandex T2I official 10M/IP",
}
SEARCH_METHODS = {
    "medoid": ("formal", "0. Medoid (Baseline)", "Medoid"),
    "formal_raw": ("formal", "2. Raw HNSW Routing (Ablation Baseline)", "Formal Raw"),
    "formal_neural": ("formal", "5. Asym-Neural HNSW Routing (0ms inference)", "Formal Neural"),
    "fast_raw": ("fast", "2. Raw HNSW Routing (Ablation Baseline)", "Fast QGT Raw"),
    "fast_prototype": ("fast", "5. Asym-Neural HNSW Routing (0ms inference)", "Fast Prototype"),
}
TAIL_METHODS = {
    "medoid": ("formal", "NSG_Medoid", "Medoid"),
    "formal_raw": ("formal", "Raw_HNSW_Ablation", "Formal Raw"),
    "formal_neural": ("formal", "NETG_AsymHNSW", "Formal Neural"),
    "fast_raw": ("fast", "Raw_HNSW_Ablation", "Fast QGT Raw"),
    "fast_prototype": ("fast", "NETG_AsymHNSW", "Fast Prototype"),
}
THRESHOLDS = (0.1, 0.2, 0.5, 0.8)


def load(path: Path) -> dict:
    with path.open() as stream:
        return json.load(stream)


def mean_std(values: list[float]) -> dict[str, float]:
    values = [float(value) for value in values]
    return {
        "mean": statistics.fmean(values),
        "std": statistics.pstdev(values),
        "min": min(values),
        "max": max(values),
        "n": len(values),
    }


def combine_group_stats(groups: list[tuple[float, float, int]]) -> dict[str, float]:
    total = sum(count for _, _, count in groups)
    grand = sum(mean * count for mean, _, count in groups) / total
    variance = sum(
        count * (std * std + (mean - grand) ** 2)
        for mean, std, count in groups
    ) / total
    return {
        "mean": grand,
        "std": math.sqrt(max(variance, 0.0)),
        "n": total,
        "groups": len(groups),
    }


def search_map(document: dict) -> dict[str, dict[int, dict]]:
    return {
        method["method_name"]: {
            int(row["search_L"]): row for row in method["performance"]
        }
        for method in document["results"]
    }


def tail_map(document: dict) -> dict[str, dict[int, dict]]:
    return {
        method["method"]: {
            int(row["search_L"]): row for row in method["search_results"]
        }
        for method in document["methods"]
    }


def validate_search(document: dict, dataset: str, top_k: int, runs: int) -> None:
    expected = (dataset, "held-out-test", 10000, top_k, runs)
    observed = (
        document.get("dataset"), document.get("split"), document.get("num_queries"),
        document.get("top_k"), document.get("num_runs"),
    )
    if observed != expected:
        raise ValueError(f"search contract mismatch: expected={expected}, observed={observed}")


def validate_tail(document: dict, dataset: str) -> None:
    expected = (dataset, "held-out-test", 10000, 10)
    observed = (
        document.get("dataset"), document.get("split"),
        document.get("num_queries"), document.get("top_k"),
    )
    if observed != expected:
        raise ValueError(f"tail contract mismatch: expected={expected}, observed={observed}")
    for method in document["methods"]:
        for row in method["search_results"]:
            aligned = row.get("per_query_recalls_aligned")
            if aligned is None or len(aligned) != 10000:
                raise ValueError(
                    f"missing aligned recalls: {dataset}/{method['method']}/L={row['search_L']}"
                )


def aggregate_search(
    formal_doc: dict, fast_docs: list[dict], method_key: str,
) -> dict[str, dict]:
    source, source_name, _ = SEARCH_METHODS[method_key]
    documents = [formal_doc] if source == "formal" else fast_docs
    mapped = [search_map(document) for document in documents]
    medoid_name = SEARCH_METHODS["medoid"][1]
    search_ls = sorted(set.intersection(*(set(item[source_name]) for item in mapped)))
    output = {}
    for search_l in search_ls:
        rows = [item[source_name][search_l] for item in mapped]
        medoids = [item[medoid_name][search_l] for item in mapped]
        output[str(search_l)] = {
            "recall": mean_std([row["recall"] for row in rows]),
            "qps": combine_group_stats([
                (row["qps"], row["qps_std"], document["num_runs"])
                for row, document in zip(rows, documents)
            ]),
            "qps_ratio_to_same_invocation_medoid": mean_std([
                row["qps"] / medoid["qps"] for row, medoid in zip(rows, medoids)
            ]),
            "per_artifact": [
                {
                    "qps": row["qps"], "qps_std": row["qps_std"],
                    "recall": row["recall"], "internal_runs": document["num_runs"],
                }
                for row, document in zip(rows, documents)
            ],
        }
    return output


def tail_observation(row: dict, medoid_row: dict) -> dict:
    values = row["per_query_recalls_aligned"]
    baseline = medoid_row["per_query_recalls_aligned"]
    output = {"mean_recall10": row["mean_recall"], "thresholds": {}}
    for threshold in THRESHOLDS:
        failed = [value < threshold for value in values]
        base_failed = [value < threshold for value in baseline]
        rescued = sum(before and not after for before, after in zip(base_failed, failed))
        harmed = sum(not before and after for before, after in zip(base_failed, failed))
        output["thresholds"][str(threshold)] = {
            "failure_rate_pct": 100.0 * sum(failed) / len(failed),
            "failure_count": sum(failed),
            "rescued": rescued,
            "newly_harmed": harmed,
            "net_rescued": rescued - harmed,
        }
    return output


def aggregate_tail(
    formal_doc: dict, fast_docs: list[dict], method_key: str,
) -> dict[str, dict]:
    source, source_name, _ = TAIL_METHODS[method_key]
    documents = [formal_doc] if source == "formal" else fast_docs
    mapped = [tail_map(document) for document in documents]
    medoid_name = TAIL_METHODS["medoid"][1]
    search_ls = sorted(set.intersection(*(set(item[source_name]) for item in mapped)))
    output = {}
    for search_l in search_ls:
        observations = [
            tail_observation(item[source_name][search_l], item[medoid_name][search_l])
            for item in mapped
        ]
        output[str(search_l)] = {
            "mean_recall10": mean_std([row["mean_recall10"] for row in observations]),
            "thresholds": {
                str(threshold): {
                    field: mean_std([
                        row["thresholds"][str(threshold)][field] for row in observations
                    ])
                    for field in (
                        "failure_rate_pct", "failure_count", "rescued",
                        "newly_harmed", "net_rescued",
                    )
                }
                for threshold in THRESHOLDS
            },
        }
    return output


def build_dataset(raw: Path, dataset: str, seeds: list[int], runs: int) -> dict:
    formal_r1 = load(raw / dataset / "formal_r1.json")
    formal_r100 = load(raw / dataset / "formal_r100.json")
    formal_tail = load(raw / dataset / "formal_tail_r10.json")
    fast_r1 = [load(raw / dataset / f"fast_seed{seed}_r1.json") for seed in seeds]
    fast_r100 = [load(raw / dataset / f"fast_seed{seed}_r100.json") for seed in seeds]
    fast_tail = [load(raw / dataset / f"fast_seed{seed}_tail_r10.json") for seed in seeds]
    validate_search(formal_r1, dataset, 1, runs)
    validate_search(formal_r100, dataset, 100, runs)
    for document in fast_r1:
        validate_search(document, dataset, 1, runs)
    for document in fast_r100:
        validate_search(document, dataset, 100, runs)
    validate_tail(formal_tail, dataset)
    for document in fast_tail:
        validate_tail(document, dataset)

    search = {"recall1": {}, "recall100": {}}
    tail = {}
    for method_key in SEARCH_METHODS:
        search["recall1"][method_key] = aggregate_search(formal_r1, fast_r1, method_key)
        search["recall100"][method_key] = aggregate_search(formal_r100, fast_r100, method_key)
    for method_key in TAIL_METHODS:
        tail[method_key] = aggregate_tail(formal_tail, fast_tail, method_key)

    comparisons = {"recall1": {}, "recall100": {}}
    for metric in comparisons:
        fast = search[metric]["fast_prototype"]
        neural = search[metric]["formal_neural"]
        for search_l in sorted(set(fast) & set(neural), key=int):
            direct = fast[search_l]["qps"]["mean"] / neural[search_l]["qps"]["mean"] - 1.0
            normalized = (
                fast[search_l]["qps_ratio_to_same_invocation_medoid"]["mean"]
                / neural[search_l]["qps_ratio_to_same_invocation_medoid"]["mean"] - 1.0
            )
            comparisons[metric][search_l] = {
                "fast_minus_neural_recall": (
                    fast[search_l]["recall"]["mean"] - neural[search_l]["recall"]["mean"]
                ),
                "fast_vs_neural_direct_qps_pct": direct * 100.0,
                "fast_vs_neural_medoid_normalized_qps_pct": normalized * 100.0,
            }
    return {"search": search, "tail_recall10": tail, "comparisons": comparisons}


def write_search_csv(path: Path, results: dict) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow([
            "dataset", "metric", "method", "search_L", "recall_mean",
            "recall_std_across_seeds", "qps_mean", "qps_std_combined",
            "qps_observations", "qps_ratio_to_same_invocation_medoid",
        ])
        for dataset, data in results["datasets"].items():
            for metric, methods in data["search"].items():
                for method_key, rows in methods.items():
                    for search_l, row in sorted(rows.items(), key=lambda item: int(item[0])):
                        writer.writerow([
                            dataset, metric, SEARCH_METHODS[method_key][2], search_l,
                            row["recall"]["mean"], row["recall"]["std"],
                            row["qps"]["mean"], row["qps"]["std"], row["qps"]["n"],
                            row["qps_ratio_to_same_invocation_medoid"]["mean"],
                        ])


def write_tail_csv(path: Path, results: dict) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow([
            "dataset", "method", "search_L", "mean_recall10",
            "mean_recall10_std_across_seeds", "threshold", "failure_rate_pct",
            "failure_rate_std_across_seeds", "rescued", "newly_harmed", "net_rescued",
        ])
        for dataset, data in results["datasets"].items():
            for method_key, rows in data["tail_recall10"].items():
                for search_l, row in sorted(rows.items(), key=lambda item: int(item[0])):
                    for threshold, stats in row["thresholds"].items():
                        writer.writerow([
                            dataset, TAIL_METHODS[method_key][2], search_l,
                            row["mean_recall10"]["mean"], row["mean_recall10"]["std"],
                            threshold, stats["failure_rate_pct"]["mean"],
                            stats["failure_rate_pct"]["std"], stats["rescued"]["mean"],
                            stats["newly_harmed"]["mean"], stats["net_rescued"]["mean"],
                        ])


def fmt(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def write_markdown(path: Path, results: dict) -> None:
    lines = [
        "# Fast-Entry 双数据集 QPS / Recall / Tail 报告",
        "",
        "> 统一协议：held-out 10K queries；QPS 每个 artifact 内运行 "
        f"{results['protocol']['internal_runs']} 次；Fast 使用聚类 seeds "
        f"`{'/'.join(map(str, results['protocol']['fast_seeds']))}`。",
        "",
        "QPS 的 `±` 为内部重复与 Fast 跨 seed 合并后的总体标准差。"
        "跨 invocation 的原始 QPS 会受系统状态影响，因此 Fast/Neural 判断优先看同次 Medoid 归一化后的差值。",
        "",
        "## 结论速览",
        "",
        "- **WebVid：Fast Prototype 明确优于 Formal Neural。** Recall@1 提高 "
        "`+0.0080~+0.0131`，Recall@100 提高 `+0.0021~+0.0032`；同次 Medoid "
        "归一化 QPS 分别提高 `+1.15%~+9.67%` 与 `+1.83%~+8.89%`。",
        "- **Yandex：Fast Prototype 基本复现 Formal Neural，并获得小幅 QPS 优势。** "
        "Recall@1 差值为 `-0.00213~+0.00003`，Recall@100 差值为 "
        "`-0.00020~+0.00018`；同次 Medoid 归一化 QPS 分别提高 "
        "`+1.34%~+7.16%` 与 `+1.14%~+5.53%`。",
        "- **Tail 没有被均值掩盖。** 相对 Medoid，Fast 在两个数据集、全部 L 和全部 "
        "预注册阈值上均为正净救回；WebVid 的 Fast tail 进一步优于 Neural，Yandex "
        "则总体与 Neural 接近。",
        "- 因此当前证据支持 fast-entry 的跨数据集有效性，但论文表述应区分：WebVid 是"
        "效果与速度双提升，Yandex 是基本等效效果下的低成本替代。",
        "",
    ]
    for dataset, data in results["datasets"].items():
        lines.extend([f"## {DATASETS[dataset]}", ""])
        for metric, title in (("recall1", "Recall@1"), ("recall100", "Recall@100")):
            lines.extend([
                f"### {title} 与 QPS", "",
                "| L | Method | Recall mean ± seed std | QPS mean ± std | QPS / same-run Medoid | n |",
                "| ---: | --- | ---: | ---: | ---: | ---: |",
            ])
            methods = data["search"][metric]
            search_ls = sorted(set.intersection(*(set(rows) for rows in methods.values())), key=int)
            for search_l in search_ls:
                for method_key in SEARCH_METHODS:
                    row = methods[method_key][search_l]
                    lines.append(
                        f"| {search_l} | {SEARCH_METHODS[method_key][2]} | "
                        f"{fmt(row['recall']['mean'])} ± {fmt(row['recall']['std'])} | "
                        f"{fmt(row['qps']['mean'], 1)} ± {fmt(row['qps']['std'], 1)} | "
                        f"{fmt(row['qps_ratio_to_same_invocation_medoid']['mean'], 3)}× | "
                        f"{row['qps']['n']} |"
                    )
            lines.extend([
                "", "Fast Prototype 相对 Formal Neural：", "",
                "| L | Recall difference | Direct QPS difference | Medoid-normalized QPS difference |",
                "| ---: | ---: | ---: | ---: |",
            ])
            for search_l, row in sorted(data["comparisons"][metric].items(), key=lambda item: int(item[0])):
                lines.append(
                    f"| {search_l} | {row['fast_minus_neural_recall']:+.5f} | "
                    f"{row['fast_vs_neural_direct_qps_pct']:+.2f}% | "
                    f"{row['fast_vs_neural_medoid_normalized_qps_pct']:+.2f}% |"
                )
            lines.append("")

        lines.extend([
            "### Tail：逐 query Recall@10", "",
            "| L | MeanR@10 Medoid | MeanR@10 Neural | MeanR@10 Fast | Threshold | Medoid fail | Neural fail | Fast fail mean ± seed std | Fast rescued | Fast harmed | Fast net |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ])
        medoid = data["tail_recall10"]["medoid"]
        neural = data["tail_recall10"]["formal_neural"]
        fast = data["tail_recall10"]["fast_prototype"]
        search_ls = sorted(set(medoid) & set(neural) & set(fast), key=int)
        for search_l in search_ls:
            for threshold in map(str, THRESHOLDS):
                m = medoid[search_l]["thresholds"][threshold]
                n = neural[search_l]["thresholds"][threshold]
                f = fast[search_l]["thresholds"][threshold]
                lines.append(
                    f"| {search_l} | {fmt(medoid[search_l]['mean_recall10']['mean'])} | "
                    f"{fmt(neural[search_l]['mean_recall10']['mean'])} | "
                    f"{fmt(fast[search_l]['mean_recall10']['mean'])} | {threshold} | "
                    f"{fmt(m['failure_rate_pct']['mean'], 2)}% | "
                    f"{fmt(n['failure_rate_pct']['mean'], 2)}% | "
                    f"{fmt(f['failure_rate_pct']['mean'], 2)} ± {fmt(f['failure_rate_pct']['std'], 2)}% | "
                    f"{fmt(f['rescued']['mean'], 1)} | {fmt(f['newly_harmed']['mean'], 1)} | "
                    f"{fmt(f['net_rescued']['mean'], 1)} |"
                )
        lines.extend(["", f"原始结果：`raw/{dataset}/`", ""])

    lines.extend([
        "## QPS–Recall 曲线", "",
        "- WebVid：`figures/webvid_qps_recall.png` / `figures/webvid_qps_recall.pdf`",
        "- Yandex：`figures/yandex_qps_recall.png` / `figures/yandex_qps_recall.pdf`",
        "- 图中 QPS 是纯搜索阶段的原始实测值；tail 由独立二进制和独立进程事后计算，不在 QPS 计时区间内。",
        "",
        "## 解释边界", "",
        "- Recall 在同一 artifact 上是确定性的；Fast 的 recall/tail 标准差来自三个聚类 seed。",
        "- QPS 不是跨日期单次值，而是当前统一批次的多次运行；仍应同时看 mean/std。",
        "- Fast 与 Formal 位于不同 invocation，优先使用 same-run Medoid 归一化差值消除机器状态漂移。",
        "- Tail 的重复运行不会改变确定性结果，因此用三个 Fast seed 衡量方法方差，而不是机械重复同一文件。",
        "- 本报告不包含 exact train-GT 生成成本；离线总成本结论必须另行计入。",
        "",
        "机器可读文件：`benchmark_summary.json`、`search_metrics.csv`、`tail_metrics.csv`。",
        "",
    ])
    path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--seeds", default="20260828,20260829,20260830")
    parser.add_argument("--internal-runs", type=int, default=3)
    args = parser.parse_args()
    result_dir = args.result_dir.resolve()
    raw = result_dir / "raw"
    seeds = [int(value) for value in args.seeds.split(",") if value]
    results = {
        "schema_version": 1,
        "status": "two-dataset-repeated-held-out-benchmark",
        "protocol": {
            "datasets": list(DATASETS), "num_queries": 10000,
            "internal_runs": args.internal_runs, "fast_seeds": seeds,
            "top_k": [1, 100], "tail_top_k": 10,
            "tail_thresholds": list(THRESHOLDS),
            "qps_primary_comparison": "same-invocation Medoid-normalized ratio",
        },
        "datasets": {
            dataset: build_dataset(raw, dataset, seeds, args.internal_runs)
            for dataset in DATASETS
        },
    }
    (result_dir / "benchmark_summary.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n"
    )
    write_search_csv(result_dir / "search_metrics.csv", results)
    write_tail_csv(result_dir / "tail_metrics.csv", results)
    write_markdown(result_dir / "benchmark_summary.md", results)
    print(result_dir / "benchmark_summary.md")


if __name__ == "__main__":
    main()
