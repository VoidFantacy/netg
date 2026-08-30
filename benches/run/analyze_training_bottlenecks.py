#!/usr/bin/env python3
"""Quantify convergence and non-stationarity in ACSG training logs."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path


ACO_RE = re.compile(
    r"ACO_SANITY AvgError=(?P<avg>\S+) MinError=(?P<min>\S+) "
    r"MaxError=(?P<max>\S+) ZeroErrorRate=(?P<zero>\S+) "
    r"AvgHops=(?P<hops>\S+) InvalidLoss=(?P<invalid>\d+) "
    r"EmptyPath=(?P<empty>\d+)"
)
ROUTER_RE = re.compile(
    r"ROUTER_SANITY Epoch=(?P<epoch>\d+) Loss=(?P<loss>\S+) "
    r"OracleGTNeg=(?P<acc>\S+) Steps=(?P<steps>\d+)"
)
REFRESH_RE = re.compile(r"Epoch (?P<epoch>\d+): .*Hard Negatives")
ELAPSED_RE = re.compile(r"Elapsed \(wall clock\) time .*: (?P<value>\S+)")


def elapsed_seconds(value: str) -> float:
    fields = [float(part) for part in value.split(":" )]
    total = 0.0
    for field in fields:
        total = total * 60.0 + field
    return total


def parse_elapsed(path: Path | None) -> float | None:
    if path is None or not path.exists():
        return None
    match = ELAPSED_RE.search(path.read_text(errors="replace"))
    return elapsed_seconds(match.group("value")) if match else None


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def std(values: list[float]) -> float:
    if not values:
        return math.nan
    avg = mean(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / len(values))


def analyze_aco(path: Path, time_path: Path | None) -> dict:
    rows = []
    for match in ACO_RE.finditer(path.read_text(errors="replace")):
        rows.append({
            "avg_error": float(match.group("avg")),
            "min_error": float(match.group("min")),
            "max_error": float(match.group("max")),
            "zero_error_rate": float(match.group("zero")),
            "avg_hops": float(match.group("hops")),
            "invalid_loss": int(match.group("invalid")),
            "empty_path": int(match.group("empty")),
        })
    if not rows:
        raise ValueError(f"no ACO_SANITY records in {path}")

    errors = [row["avg_error"] for row in rows]
    best_idx = min(range(len(errors)), key=errors.__getitem__)
    split = min(5, len(errors))
    tail = errors[split:]
    wall = parse_elapsed(time_path)
    return {
        "log": str(path),
        "iterations": len(rows),
        "first_avg_error": errors[0],
        "iteration_5_avg_error": errors[split - 1],
        "final_avg_error": errors[-1],
        "best_avg_error": errors[best_idx],
        "best_iteration": best_idx + 1,
        "relative_improvement_iter1_to_5": (errors[0] - errors[split - 1]) / errors[0],
        "relative_improvement_iter5_to_final": (errors[split - 1] - errors[-1]) / errors[split - 1],
        "post_iter5_mean_error": mean(tail),
        "post_iter5_std_error": std(tail),
        "first_zero_error_rate": rows[0]["zero_error_rate"],
        "final_zero_error_rate": rows[-1]["zero_error_rate"],
        "first_avg_hops": rows[0]["avg_hops"],
        "final_avg_hops": rows[-1]["avg_hops"],
        "invalid_loss_total": sum(row["invalid_loss"] for row in rows),
        "empty_path_total": sum(row["empty_path"] for row in rows),
        "wall_seconds": wall,
        "estimated_seconds_per_iteration": wall / len(rows) if wall else None,
    }


def analyze_router(path: Path, time_path: Path | None) -> dict:
    text = path.read_text(errors="replace")
    rows = {}
    for match in ROUTER_RE.finditer(text):
        epoch = int(match.group("epoch"))
        rows[epoch] = {
            "loss": float(match.group("loss")),
            "oracle_gt_neg": float(match.group("acc")),
            "steps": int(match.group("steps")),
        }
    if not rows:
        raise ValueError(f"no ROUTER_SANITY records in {path}")

    refresh_epochs = sorted(int(match.group("epoch")) for match in REFRESH_RE.finditer(text))
    refresh_jumps = [rows[e]["loss"] - rows[e - 1]["loss"] for e in refresh_epochs if e in rows and e - 1 in rows]
    ordinary_deltas = [
        rows[e]["loss"] - rows[e - 1]["loss"]
        for e in sorted(rows)
        if e - 1 in rows and e not in refresh_epochs
    ]
    best_epoch = min(rows, key=lambda epoch: rows[epoch]["loss"])
    final_epoch = max(rows)
    wall = parse_elapsed(time_path)
    return {
        "log": str(path),
        "epochs": len(rows),
        "first_loss": rows[min(rows)]["loss"],
        "final_loss": rows[final_epoch]["loss"],
        "best_loss": rows[best_epoch]["loss"],
        "best_epoch": best_epoch,
        "final_epoch": final_epoch,
        "refresh_epochs": refresh_epochs,
        "refresh_jump_mean": mean(refresh_jumps),
        "refresh_jump_max": max(refresh_jumps) if refresh_jumps else None,
        "ordinary_epoch_delta_std": std(ordinary_deltas),
        "final_oracle_gt_negative": rows[final_epoch]["oracle_gt_neg"],
        "steps_per_epoch": rows[final_epoch]["steps"],
        "wall_seconds": wall,
        "estimated_seconds_per_epoch": wall / len(rows) if wall else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aco-log", type=Path, required=True)
    parser.add_argument("--aco-time", type=Path)
    parser.add_argument("--router-log", type=Path, required=True)
    parser.add_argument("--router-time", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = {
        "aco": analyze_aco(args.aco_log, args.aco_time),
        "router": analyze_router(args.router_log, args.router_time),
    }
    payload = json.dumps(report, indent=2, sort_keys=True)
    print(payload)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n")


if __name__ == "__main__":
    main()
