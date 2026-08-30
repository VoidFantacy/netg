#!/usr/bin/env python3
"""Compare the historical leaked/L2 run with the official held-out/IP run.

The output deliberately labels these as different protocols.  Numeric deltas
measure the end-to-end consequence of rebuilding the data contract; they are
not an isolated attribution to query leakage, metric, or base identity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


METHOD_NAMES = {
    "0. Medoid (Baseline)": "NSG_Medoid",
    "5. Asym-Neural HNSW Routing (0ms inference)": "NETG_AsymHNSW",
}


def curves(report: dict) -> dict[str, dict[int, dict]]:
    result = {}
    for method in report["results"]:
        name = METHOD_NAMES.get(method["method_name"], method["method_name"])
        result[name] = {row["search_L"]: row for row in method["performance"]}
    return result


def tail_curves(report: dict) -> dict[str, dict[int, dict]]:
    return {
        method["method"]: {row["search_L"]: row for row in method["search_results"]}
        for method in report["methods"]
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-main", type=Path, required=True)
    parser.add_argument("--old-tail", type=Path, required=True)
    parser.add_argument("--new-r1", type=Path, required=True)
    parser.add_argument("--new-r100", type=Path, required=True)
    parser.add_argument("--new-tail", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    loaded = {key: json.loads(getattr(args, key).read_text()) for key in
              ("old_main", "old_tail", "new_r1", "new_r100", "new_tail")}
    old_main, new_r1, new_r100 = map(curves, (loaded["old_main"], loaded["new_r1"], loaded["new_r100"]))
    old_tail, new_tail = map(tail_curves, (loaded["old_tail"], loaded["new_tail"]))

    rows = []
    for method in ("NSG_Medoid", "NETG_AsymHNSW"):
        for search_l in (64, 128, 200, 512, 1024):
            if search_l not in old_main.get(method, {}) or search_l not in new_r1.get(method, {}):
                continue
            row = {
                "method": method,
                "search_L": search_l,
                "old_custom_l2_recall_at_1": old_main[method][search_l]["recall"],
                "new_official_ip_recall_at_1": new_r1[method][search_l]["recall"],
            }
            if search_l in new_r100.get(method, {}):
                row["new_official_ip_recall_at_100"] = new_r100[method][search_l]["recall"]
            if search_l in old_tail.get(method, {}) and search_l in new_tail.get(method, {}):
                old = old_tail[method][search_l]
                new = new_tail[method][search_l]
                row.update({
                    "old_custom_l2_mean_recall_at_10": old["mean_recall"],
                    "new_official_ip_mean_recall_at_10": new["mean_recall"],
                    "old_custom_l2_tail_rate_recall_lt_0_1": sum(x < 0.1 for x in old["per_query_recalls"]) / len(old["per_query_recalls"]),
                    "new_official_ip_tail_rate_recall_lt_0_1": sum(x < 0.1 for x in new["per_query_recalls_aligned"]) / len(new["per_query_recalls_aligned"]),
                })
            rows.append(row)

    new_tail_pairing = []
    nsg_new = new_tail.get("NSG_Medoid", {})
    netg_new = new_tail.get("NETG_AsymHNSW", {})
    for search_l in sorted(set(nsg_new) & set(netg_new)):
        nsg_values = nsg_new[search_l]["per_query_recalls_aligned"]
        netg_values = netg_new[search_l]["per_query_recalls_aligned"]
        if len(nsg_values) != len(netg_values):
            raise ValueError(f"aligned query count mismatch at L={search_l}")
        for threshold in (0.1, 0.2):
            nsg_failed = [value < threshold for value in nsg_values]
            netg_failed = [value < threshold for value in netg_values]
            nq = len(nsg_failed)
            rescued = sum(left and not right for left, right in zip(nsg_failed, netg_failed))
            still_failed = sum(left and right for left, right in zip(nsg_failed, netg_failed))
            newly_harmed = sum(not left and right for left, right in zip(nsg_failed, netg_failed))
            nsg_count = sum(nsg_failed)
            netg_count = sum(netg_failed)
            new_tail_pairing.append({
                "search_L": search_l,
                "threshold_recall_lt": threshold,
                "num_queries": nq,
                "nsg_failed": nsg_count,
                "netg_failed": netg_count,
                "nsg_failure_rate": nsg_count / nq,
                "netg_failure_rate": netg_count / nq,
                "failure_rate_change_percentage_points": (netg_count - nsg_count) / nq * 100.0,
                "rescued": rescued,
                "still_failed": still_failed,
                "newly_harmed": newly_harmed,
                "net_rescued": rescued - newly_harmed,
            })

    comparison = {
        "warning": "Protocols differ in base identity, metric, GT, and query split; deltas are not a leakage-only causal estimate.",
        "before": {"artifact": "Yandex-T2I-derived-10M/custom-L2", "split": "public-query reused by ACO/Router/test", "provenance": "historical-unverified"},
        "after": {"artifact": loaded["new_r1"].get("artifact_version"), "metric": loaded["new_r1"].get("metric"), "split": loaded["new_r1"].get("split"), "num_queries": loaded["new_r1"].get("num_queries")},
        "rows": rows,
        "new_protocol_paired_tail_analysis": new_tail_pairing,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(comparison, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
