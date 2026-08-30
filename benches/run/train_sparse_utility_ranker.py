#!/usr/bin/env python3
"""Train a lightweight listwise reranker over the Fast top-r entry shortlist."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import struct
from pathlib import Path

import numpy as np
import torch


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_fvecs(path: Path, count: int) -> np.ndarray:
    with path.open("rb") as stream:
        dim = struct.unpack("i", stream.read(4))[0]
    raw = np.memmap(path, mode="r", dtype=np.float32).reshape(-1, dim + 1)
    return np.asarray(raw[:count, 1:], dtype=np.float32).copy()


def normalize(rows: np.ndarray) -> np.ndarray:
    return rows / np.maximum(np.linalg.norm(rows, axis=1, keepdims=True), 1e-12)


def load_utility(path: Path) -> dict[str, np.ndarray | dict]:
    document = json.loads(path.read_text())
    if document.get("status") != "complete" or len(document.get("results", [])) < 1:
        raise ValueError(f"incomplete sparse utility: {path}")
    rows = document["results"]
    n = document["num_queries"]
    shortlist = document["utility_shortlist"]
    candidates = np.asarray([q["candidate_entry_ids"] for q in rows[0]["queries"]], dtype=np.int32)
    recalls, ndcs, fast_recalls, fast_ndcs = [], [], [], []
    for row in rows:
        ids = np.asarray([q["candidate_entry_ids"] for q in row["queries"]], dtype=np.int32)
        if not np.array_equal(ids, candidates):
            raise ValueError("shortlists differ across operating points")
        recalls.append(np.asarray([q["candidate_recalls"] for q in row["queries"]], dtype=np.float32))
        ndcs.append(np.asarray([q["candidate_graph_ndcs"] for q in row["queries"]], dtype=np.float32))
        fast_recalls.append(np.asarray([q["fast_top3_recall"] for q in row["queries"]], dtype=np.float32))
        fast_ndcs.append(np.asarray([q["fast_top3_graph_ndc"] for q in row["queries"]], dtype=np.float32))
    if candidates.shape != (n, shortlist):
        raise ValueError("candidate shape mismatch")
    return {
        "document": document,
        "candidates": candidates,
        "recalls": np.stack(recalls),
        "ndcs": np.stack(ndcs),
        "fast_recalls": np.stack(fast_recalls),
        "fast_ndcs": np.stack(fast_ndcs),
    }


class DiagonalUtilityRanker(torch.nn.Module):
    def __init__(self, dim: int, hubs: int, shortlist: int) -> None:
        super().__init__()
        self.proto_weight = torch.nn.Parameter(torch.ones(dim))
        self.raw_weight = torch.nn.Parameter(torch.zeros(dim))
        self.entry_bias = torch.nn.Parameter(torch.zeros(hubs))
        self.rank_bias = torch.nn.Parameter(torch.zeros(shortlist))
        self.log_scale = torch.nn.Parameter(torch.tensor(math.log(10.0)))

    def forward(
        self, query: torch.Tensor, candidate_local: torch.Tensor,
        prototypes: torch.Tensor, raw_hubs: torch.Tensor,
    ) -> torch.Tensor:
        p = prototypes[candidate_local]
        r = raw_hubs[candidate_local]
        proto_score = torch.einsum("bd,bsd,d->bs", query, p, self.proto_weight)
        raw_score = torch.einsum("bd,bsd,d->bs", query, r, self.raw_weight)
        scale = torch.exp(self.log_scale).clamp(0.1, 100.0)
        return scale * (proto_score + raw_score) + self.entry_bias[candidate_local] + self.rank_bias


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-utility", type=Path, required=True)
    parser.add_argument("--validation-utility", type=Path, required=True)
    parser.add_argument("--train-queries", type=Path, required=True)
    parser.add_argument("--validation-queries", type=Path, required=True)
    parser.add_argument("--prototypes", type=Path, required=True)
    parser.add_argument("--raw-hubs", type=Path, required=True)
    parser.add_argument("--hub-ids", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seeds", default="20260828,20260829,20260830")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=0.02)
    parser.add_argument("--target-temperature", type=float, default=0.05)
    parser.add_argument("--cost-weight", type=float, default=0.05)
    parser.add_argument("--tail-weight", type=float, default=1.0)
    parser.add_argument("--threads", type=int, default=16)
    args = parser.parse_args()

    torch.set_num_threads(args.threads)
    train = load_utility(args.train_utility)
    validation = load_utility(args.validation_utility)
    train_doc = train["document"]
    val_doc = validation["document"]
    if train_doc["dataset"] != val_doc["dataset"] or train_doc["split"] != "drl_train" or val_doc["split"] != "validation":
        raise ValueError("dataset/split contract mismatch")
    if train_doc["utility_shortlist"] != val_doc["utility_shortlist"]:
        raise ValueError("shortlist mismatch")

    hub_ids = np.fromfile(args.hub_ids, dtype=np.int32)
    prototypes = normalize(np.fromfile(args.prototypes, dtype=np.float32).reshape(len(hub_ids), -1))
    raw_hubs = normalize(np.fromfile(args.raw_hubs, dtype=np.float32).reshape(len(hub_ids), -1))
    id_to_local = {int(value): index for index, value in enumerate(hub_ids)}

    def localize(candidates: np.ndarray) -> np.ndarray:
        out = np.empty_like(candidates)
        for rank in range(candidates.shape[1]):
            out[:, rank] = [id_to_local[int(value)] for value in candidates[:, rank]]
        return out

    train_local = localize(train["candidates"])
    val_local = localize(validation["candidates"])
    train_queries = normalize(read_fvecs(args.train_queries, train_doc["num_queries"]))
    val_queries = normalize(read_fvecs(args.validation_queries, val_doc["num_queries"]))

    def targets(data: dict) -> tuple[np.ndarray, np.ndarray]:
        mean_recall = np.mean(data["recalls"], axis=0)
        relative_ndc = np.mean(data["ndcs"] / np.maximum(data["fast_ndcs"][:, :, None], 1.0), axis=0)
        utility = mean_recall - args.cost_weight * relative_ndc
        hardness = 1.0 + args.tail_weight * (1.0 - np.mean(data["fast_recalls"], axis=0))
        return utility.astype(np.float32), hardness.astype(np.float32)

    train_utility, train_hardness = targets(train)
    val_utility, val_hardness = targets(validation)
    p_tensor = torch.from_numpy(prototypes)
    r_tensor = torch.from_numpy(raw_hubs)
    seeds = [int(value) for value in args.seeds.split(",")]
    args.output_dir.mkdir(parents=True, exist_ok=False)
    summaries = []

    train_n = len(train_queries)
    split = int(train_n * 0.8)
    fit_indices = np.arange(split)
    dev_indices = np.arange(split, train_n)

    for seed in seeds:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        model = DiagonalUtilityRanker(prototypes.shape[1], len(hub_ids), train_local.shape[1])
        optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
        best_loss = float("inf")
        best_state = None
        patience = 0
        epochs_run = 0

        for epoch in range(args.epochs):
            shuffled = np.random.permutation(fit_indices)
            model.train()
            for start in range(0, len(shuffled), args.batch_size):
                idx = shuffled[start:start + args.batch_size]
                q = torch.from_numpy(train_queries[idx])
                c = torch.from_numpy(train_local[idx].astype(np.int64))
                utility = torch.from_numpy(train_utility[idx])
                hardness = torch.from_numpy(train_hardness[idx])
                target = torch.softmax(utility / args.target_temperature, dim=1)
                logits = model(q, c, p_tensor, r_tensor)
                per_query = -(target * torch.log_softmax(logits, dim=1)).sum(dim=1)
                regularizer = 1e-4 * ((model.proto_weight - 1.0).square().mean() + model.raw_weight.square().mean())
                loss = (per_query * hardness).mean() + regularizer
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            model.eval()
            with torch.no_grad():
                q = torch.from_numpy(train_queries[dev_indices])
                c = torch.from_numpy(train_local[dev_indices].astype(np.int64))
                utility = torch.from_numpy(train_utility[dev_indices])
                hardness = torch.from_numpy(train_hardness[dev_indices])
                target = torch.softmax(utility / args.target_temperature, dim=1)
                logits = model(q, c, p_tensor, r_tensor)
                dev_loss = float((-(target * torch.log_softmax(logits, dim=1)).sum(dim=1) * hardness).mean())
            epochs_run = epoch + 1
            if dev_loss < best_loss - 1e-5:
                best_loss = dev_loss
                best_state = {key: value.detach().clone() for key, value in model.state_dict().items()}
                patience = 0
            else:
                patience += 1
                if patience >= 8:
                    break

        model.load_state_dict(best_state)
        model.eval()
        with torch.no_grad():
            logits = model(torch.from_numpy(val_queries), torch.from_numpy(val_local.astype(np.int64)), p_tensor, r_tensor)
            order = torch.argsort(logits, dim=1, descending=True).cpu().numpy()
        routes = np.take_along_axis(validation["candidates"], order[:, :3], axis=1).astype(np.int32)
        route_path = args.output_dir / f"routes_seed{seed}_top3.bin"
        routes.tofile(route_path)
        model_path = args.output_dir / f"model_seed{seed}.pt"
        torch.save(best_state, model_path)

        predicted_top1 = order[:, 0]
        base_top1 = np.zeros(len(val_queries), dtype=np.int64)
        oracle_top1 = np.argmax(val_utility, axis=1)
        q_idx = np.arange(len(val_queries))
        summary = {
            "seed": seed, "epochs_run": epochs_run, "best_internal_dev_loss": best_loss,
            "validation_mean_utility_fast_rank0": float(val_utility[q_idx, base_top1].mean()),
            "validation_mean_utility_predicted_top1": float(val_utility[q_idx, predicted_top1].mean()),
            "validation_mean_utility_shortlist_oracle": float(val_utility[q_idx, oracle_top1].mean()),
            "validation_top1_changed_fraction": float(np.mean(predicted_top1 != 0)),
            "routes": str(route_path), "routes_sha256": sha256(route_path),
            "model": str(model_path), "model_sha256": sha256(model_path),
        }
        summaries.append(summary)

    manifest = {
        "schema_version": 1,
        "method": "cost-aware listwise diagonal query-entry interaction reranker over Fast top-32",
        "dataset": train_doc["dataset"], "train_split": train_doc["split"],
        "validation_split": val_doc["split"], "train_queries": train_doc["num_queries"],
        "validation_queries": val_doc["num_queries"], "shortlist": train_doc["utility_shortlist"],
        "utility_search_Ls": train_doc["search_Ls"], "utility_top_ks": train_doc["top_ks"],
        "cost_weight": args.cost_weight, "tail_weight": args.tail_weight,
        "target_temperature": args.target_temperature, "learning_rate": args.learning_rate,
        "batch_size": args.batch_size, "max_epochs": args.epochs, "seeds": seeds,
        "sources": {
            "train_utility": str(args.train_utility), "train_utility_sha256": sha256(args.train_utility),
            "validation_utility": str(args.validation_utility), "validation_utility_sha256": sha256(args.validation_utility),
            "prototypes": str(args.prototypes), "prototypes_sha256": sha256(args.prototypes),
            "raw_hubs": str(args.raw_hubs), "raw_hubs_sha256": sha256(args.raw_hubs),
            "hub_ids": str(args.hub_ids), "hub_ids_sha256": sha256(args.hub_ids),
        },
        "runs": summaries,
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
