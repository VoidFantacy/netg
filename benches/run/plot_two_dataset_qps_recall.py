#!/usr/bin/env python3
"""Plot repeated-test QPS/recall curves for the two fast-entry datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


DATASETS = {
    "webvid2_5m_light_v1": ("WebVid-2.5M / IP", "webvid_qps_recall"),
    "yandex_t2i_official10M_ip_v1": ("Yandex T2I-10M / IP", "yandex_qps_recall"),
}
METHODS = {
    "medoid": ("Medoid", "#777777", "o", "-"),
    "formal_raw": ("Formal Raw", "#4C78A8", "s", "-"),
    "formal_neural": ("Formal Neural", "#F58518", "^", "-"),
    "fast_raw": ("Fast QGT Raw", "#54A24B", "D", "--"),
    "fast_prototype": ("Fast Prototype", "#E45756", "*", "-"),
}


def plot_dataset(dataset: str, data: dict, output_dir: Path) -> None:
    title, stem = DATASETS[dataset]
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8))
    for ax, (metric, metric_title) in zip(
        axes, (("recall1", "Recall@1"), ("recall100", "Recall@100"))
    ):
        for key, (label, color, marker, linestyle) in METHODS.items():
            rows = data["search"][metric][key]
            points = [(int(search_l), row) for search_l, row in rows.items()]
            points.sort()
            recall = [row["recall"]["mean"] for _, row in points]
            recall_std = [row["recall"]["std"] for _, row in points]
            qps = [row["qps"]["mean"] for _, row in points]
            qps_std = [row["qps"]["std"] for _, row in points]
            ax.errorbar(
                recall,
                qps,
                xerr=recall_std,
                yerr=qps_std,
                label=label,
                color=color,
                marker=marker,
                linestyle=linestyle,
                linewidth=1.9,
                markersize=7.0 if key != "fast_prototype" else 9.0,
                capsize=2.5,
                alpha=0.96,
            )
            if key == "fast_prototype":
                for search_l, row in points:
                    ax.annotate(
                        f"L={search_l}",
                        (row["recall"]["mean"], row["qps"]["mean"]),
                        xytext=(5, 5),
                        textcoords="offset points",
                        fontsize=7.5,
                        color=color,
                    )
        ax.set_title(metric_title, fontsize=12, fontweight="semibold")
        ax.set_xlabel(metric_title)
        ax.set_ylabel("QPS")
        ax.grid(True, linestyle=":", linewidth=0.7, alpha=0.55)
        ax.ticklabel_format(axis="y", style="plain")
        ax.margins(x=0.06, y=0.10)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.955),
        ncol=5,
        frameon=False,
        fontsize=9,
    )
    fig.suptitle(f"{title}: QPS–Recall Trade-off", fontsize=14, fontweight="bold", y=1.02)
    fig.text(
        0.5,
        0.01,
        "Held-out 10K queries; QPS error bars combine repeated runs and Fast seeds. "
        "Labels mark Fast Prototype search_L.",
        ha="center",
        fontsize=8.5,
    )
    fig.tight_layout(rect=(0.0, 0.055, 1.0, 0.90))
    for suffix, dpi in (("png", 240), ("pdf", 300)):
        fig.savefig(output_dir / f"{stem}.{suffix}", dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("fast_entry_benchmark_results/benchmark_summary.json"),
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("fast_entry_benchmark_results/figures")
    )
    args = parser.parse_args()
    results = json.loads(args.summary.read_text())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for dataset in DATASETS:
        plot_dataset(dataset, results["datasets"][dataset], args.output_dir)
    print(args.output_dir.resolve())


if __name__ == "__main__":
    main()
