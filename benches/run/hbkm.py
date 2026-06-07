"""
HBKM hub miner — own implementation for the §5.4 ablation against
ACO+W-DPC topology-aware mining.

Algorithm (lazy split-largest, top-down):
  Start with one cluster containing all N points. Repeatedly take the
  largest current leaf that still has >= 2*k_branch members and split
  it with plain k-means into k_branch sub-clusters. Stop when we have
  >= target_k leaves, then trim to target_k by keeping the largest.

Key differences vs GATE's `cluster/kmeans.py` (which we are benchmarking
against):
  * No soft balance penalty. The penalty term `lambda * (|C| - target)^2`
    becomes scale-mismatched on L2-normalised data (Gist1M, Deep10M,
    Yandex T2I) where d^2 ~ O(1) but the penalty grows as O(N^2 / k^2),
    causing oscillation. Plain k-means converges reliably.
  * Lazy expansion (greedy bisect-largest) instead of GATE's eager
    "split every leaf at every level" recursion. Produces exactly the
    requested hub count without 8x or 16x overshoot, so the trim step
    keeps the largest, statistically representative leaves.

Hubs are medoids of leaf clusters (Definition 3 in GATE), i.e. the real
base point closest to each cluster centroid — interchangeable with
ACO+W-DPC hubs at the C++ search interface.

Outputs (per dataset):
  drl/{ds}_results/raw_hubs_hbkm.bin             hub vectors (float32)
  drl/{ds}_results/transformed_hub_ids_hbkm.bin  hub ids     (int32)
  dpc_hbkm/{ds}_results/dpc_hierarchical_results.json  (combined_centers)

Pure numpy, no sklearn / faiss / tqdm.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import os
import struct
import sys
import time

import numpy as np


# -----------------------------------------------------------------------------
# I/O helpers
# -----------------------------------------------------------------------------

def read_fvecs(path: str, max_rows: int | None = None) -> np.ndarray:
    """Read .fvecs (int32 dim header + dim*float32 per vector)."""
    file_size = os.path.getsize(path)
    with open(path, "rb") as f:
        dim = struct.unpack("i", f.read(4))[0]
        rec = 4 + 4 * dim
        n = file_size // rec
        if max_rows is not None and max_rows < n:
            n = max_rows
        f.seek(0)
        flat = np.fromfile(f, dtype=np.float32, count=n * (dim + 1))
    return flat.reshape(n, dim + 1)[:, 1:].copy()


def load_target_k(dpc_json: str) -> int:
    with open(dpc_json) as f:
        d = json.load(f)
    top = set(d.get("top_centers", []))
    bot = set(d.get("bottom_centers", []))
    return len(top | bot)


# -----------------------------------------------------------------------------
# Plain k-means primitives
# -----------------------------------------------------------------------------

def _kmeanspp_init(X: np.ndarray, k: int, rng: np.random.Generator,
                   sample_cap: int = 60_000) -> np.ndarray:
    """K-means++ seeding on a random subsample (fast for large clusters)."""
    n = X.shape[0]
    if n <= k:
        return X.copy()
    if n > sample_cap:
        sub = X[rng.choice(n, sample_cap, replace=False)]
    else:
        sub = X
    m = sub.shape[0]
    centers = np.empty((k, X.shape[1]), dtype=np.float32)
    centers[0] = sub[rng.integers(0, m)]
    closest_sq = np.full(m, np.inf, dtype=np.float64)
    for i in range(1, k):
        diff = sub - centers[i - 1]
        d2 = np.einsum("ij,ij->i", diff, diff).astype(np.float64)
        np.minimum(closest_sq, d2, out=closest_sq)
        s = closest_sq.sum()
        if s <= 0:
            centers[i] = sub[rng.integers(0, m)]
        else:
            centers[i] = sub[rng.choice(m, p=closest_sq / s)]
    return centers


def _assign_argmin(X: np.ndarray, centers: np.ndarray,
                   batch: int = 200_000) -> tuple[np.ndarray, float]:
    """Plain (no penalty) batched argmin assignment. Returns (labels, mean d^2)."""
    n = X.shape[0]
    cc = np.einsum("kd,kd->k", centers, centers)
    out = np.empty(n, dtype=np.int32)
    sum_d2 = 0.0
    for s in range(0, n, batch):
        e = min(n, s + batch)
        Xb = X[s:e]
        xx = np.einsum("bd,bd->b", Xb, Xb)[:, None]
        d2 = xx + cc - 2.0 * (Xb @ centers.T)
        np.maximum(d2, 0.0, out=d2)
        lab = np.argmin(d2, axis=1)
        out[s:e] = lab
        sum_d2 += float(d2[np.arange(e - s), lab].sum())
    return out, sum_d2 / max(1, n)


def kmeans_plain(X: np.ndarray, k: int, *,
                 n_iter: int = 20,
                 rng: np.random.Generator,
                 verbose: bool = False) -> np.ndarray:
    """
    Plain Lloyd's k-means with k-means++ init. No balance constraint —
    hierarchical splitting handles size variance instead.
    """
    n, d = X.shape
    if n <= k:
        return np.arange(n, dtype=np.int32)

    centers = _kmeanspp_init(X, k, rng)
    labels = np.full(n, -1, dtype=np.int32)
    prev_d2 = float("inf")

    for it in range(n_iter):
        new_labels, mean_d2 = _assign_argmin(X, centers)

        # Update centroids: with small k (k_branch ~ 8) per-cluster
        # boolean masks are the fastest path on numpy.
        new_centers = np.empty_like(centers)
        counts = np.bincount(new_labels, minlength=k).astype(np.int64)
        cc_old = np.einsum("kd,kd->k", centers, centers)
        for j in range(k):
            if counts[j] > 0:
                new_centers[j] = X[new_labels == j].mean(axis=0)
            else:
                # Respawn empty cluster on a high-d^2 point (random sample)
                samp = rng.choice(n, min(2048, n), replace=False)
                Xs = X[samp]
                xx = np.einsum("bd,bd->b", Xs, Xs)[:, None]
                d2_s = xx + cc_old - 2.0 * (Xs @ centers.T)
                np.maximum(d2_s, 0.0, out=d2_s)
                far = samp[int(np.argmax(d2_s.min(axis=1)))]
                new_centers[j] = X[far]

        moved = int((new_labels != labels).sum())
        if verbose:
            print(f"      iter {it+1:02d}/{n_iter}  moved={moved}  "
                  f"min={int(counts.min()):>6d} max={int(counts.max()):>6d}  "
                  f"mean_d2={mean_d2:.3g}")
        if moved == 0 and it > 0:
            labels = new_labels
            break
        # Convergence on objective
        if it > 1 and abs(prev_d2 - mean_d2) / max(prev_d2, 1e-12) < 1e-4:
            labels = new_labels
            break
        labels = new_labels
        prev_d2 = mean_d2
        centers = new_centers
    return labels


# -----------------------------------------------------------------------------
# Top-down lazy HBKM
# -----------------------------------------------------------------------------

def hbkm_topdown(X: np.ndarray, target_k: int, *,
                 k_branch: int = 8,
                 n_iter: int = 20,
                 seed: int = 42,
                 verbose: bool = True) -> list[np.ndarray]:
    """
    Lazy top-down HBKM. Always splits the largest current leaf next.
    Returns exactly `target_k` leaves (or fewer if data runs out).
    """
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    min_to_split = 2 * k_branch  # don't split tiny leaves

    if verbose:
        print(f"  [HBKM] N={n:,}  D={X.shape[1]}  target_k={target_k}  "
              f"k_branch={k_branch}  iter={n_iter}")

    # Heap of (-size, tag, indices) so largest pops first; tag breaks ties
    leaves: list[np.ndarray] = []
    pending: list[tuple[int, int, np.ndarray]] = []
    next_tag = 0
    heapq.heappush(pending, (-n, next_tag, np.arange(n, dtype=np.int64)))
    next_tag += 1

    splits = 0
    while len(leaves) + len(pending) < target_k and pending:
        neg_size, _, idx = heapq.heappop(pending)
        size = -neg_size
        if size < min_to_split:
            leaves.append(idx)
            continue

        sub_X = X[idx]
        labels = kmeans_plain(sub_X, k_branch, n_iter=n_iter, rng=rng,
                              verbose=False)

        # Collect non-empty children
        children: list[np.ndarray] = []
        for j in range(k_branch):
            m = labels == j
            if m.any():
                children.append(idx[m])

        # Guard: if k-means couldn't actually split (1 or 0 children),
        # mark as final leaf to avoid infinite loop.
        if len(children) <= 1:
            leaves.append(idx)
            continue

        # Push children to pending heap
        sub_sizes: list[int] = []
        for child in children:
            heapq.heappush(pending, (-len(child), next_tag, child))
            next_tag += 1
            sub_sizes.append(len(child))
        produced = len(children)

        splits += 1
        if verbose and (splits <= 5 or splits % 20 == 0):
            tot = len(leaves) + len(pending)
            print(f"  [HBKM] split #{splits:>3d}: parent={size:>8,d} -> "
                  f"{produced} children (sizes "
                  f"{min(sub_sizes) if sub_sizes else 0:,}.."
                  f"{max(sub_sizes) if sub_sizes else 0:,})  "
                  f"leaves+pending={tot}", flush=True)

    # Drain pending into leaves
    while pending:
        leaves.append(heapq.heappop(pending)[2])

    if verbose:
        print(f"  [HBKM] split count={splits}  total leaves={len(leaves)}")

    # Trim to target_k by keeping the largest (most representative)
    if len(leaves) > target_k:
        leaves.sort(key=len, reverse=True)
        leaves = leaves[:target_k]
        if verbose:
            print(f"  [HBKM] trimmed to {target_k} largest leaves")

    if verbose:
        sizes = np.array([len(l) for l in leaves])
        print(f"  [HBKM] leaf sizes: min={sizes.min()}  max={sizes.max()}  "
              f"mean={sizes.mean():.0f}  std={sizes.std():.0f}")
    return leaves


def extract_medoid_hubs(X: np.ndarray, leaves: list[np.ndarray]) -> np.ndarray:
    """For each leaf return the global index of the point closest to centroid."""
    hub_ids = np.empty(len(leaves), dtype=np.int64)
    for i, idx in enumerate(leaves):
        sub = X[idx]
        c = sub.mean(axis=0)
        diff = sub - c
        d2 = np.einsum("id,id->i", diff, diff)
        hub_ids[i] = idx[int(np.argmin(d2))]
    return hub_ids


# -----------------------------------------------------------------------------
# Pipeline driver
# -----------------------------------------------------------------------------

DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]


def settings_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.abspath(os.path.join(here, "../datasets/settings.json"))
    if os.path.exists(p):
        return p
    raise FileNotFoundError("settings.json not found")


def project_root(settings_file: str) -> str:
    return os.path.abspath(os.path.join(os.path.dirname(settings_file), "../.."))


def base_path_for(dataset: str, settings: dict, root: str) -> str:
    ds_conf = settings["datasets"][dataset]
    raw_root = settings.get("root_dir", "./benches/datasets")
    if raw_root.startswith("./"):
        data_root = os.path.join(root, raw_root[2:])
    else:
        data_root = raw_root
    return os.path.join(data_root, ds_conf["dataset_dir"], ds_conf["base_path"])


def run_one(dataset: str, *, k_branch: int, n_iter: int, seed: int,
            override_k: int | None) -> None:
    print(f"\n{'='*70}\n[HBKM] Dataset: {dataset}\n{'='*70}", flush=True)

    sp = settings_path()
    with open(sp) as f:
        settings = json.load(f)
    root = project_root(sp)

    base_file = base_path_for(dataset, settings, root)
    if not os.path.exists(base_file):
        print(f"  [skip] base not found: {base_file}", flush=True)
        return

    dpc_json = os.path.join(root, f"dpc/{dataset}_results/dpc_hierarchical_results.json")
    if override_k is None:
        if not os.path.exists(dpc_json):
            print(f"  [skip] cannot pick target_k: missing {dpc_json}", flush=True)
            return
        target_k = load_target_k(dpc_json)
    else:
        target_k = int(override_k)
    src = "override" if override_k else "W-DPC union"
    print(f"  [HBKM] target hub count = {target_k}  (from {src})", flush=True)

    out_drl = os.path.join(root, f"drl/{dataset}_results")
    out_dpc = os.path.join(root, f"dpc_hbkm/{dataset}_results")
    os.makedirs(out_drl, exist_ok=True)
    os.makedirs(out_dpc, exist_ok=True)

    print(f"  [HBKM] reading base from {base_file}", flush=True)
    t0 = time.time()
    X = read_fvecs(base_file)
    print(f"  [HBKM] base shape = {X.shape}  load_time={time.time()-t0:.1f}s",
          flush=True)

    t0 = time.time()
    leaves = hbkm_topdown(X, target_k, k_branch=k_branch, n_iter=n_iter,
                          seed=seed)
    print(f"  [HBKM] clustering done in {time.time()-t0:.1f}s", flush=True)

    hub_ids = extract_medoid_hubs(X, leaves)
    if len(np.unique(hub_ids)) != len(hub_ids):
        before = len(hub_ids)
        hub_ids = np.unique(hub_ids)
        print(f"  [HBKM] de-duplicated hubs: {before} -> {len(hub_ids)}",
              flush=True)
    hub_ids = np.sort(hub_ids).astype(np.int32)
    hub_vecs = X[hub_ids].astype(np.float32)
    print(f"  [HBKM] {len(hub_ids)} medoid hubs ready", flush=True)

    raw_hubs_path = os.path.join(out_drl, "raw_hubs_hbkm.bin")
    ids_path      = os.path.join(out_drl, "transformed_hub_ids_hbkm.bin")
    json_path     = os.path.join(out_dpc, "dpc_hierarchical_results.json")

    hub_vecs.tofile(raw_hubs_path)
    hub_ids.astype(np.int32).tofile(ids_path)
    with open(json_path, "w") as f:
        json.dump({
            "combined_centers": hub_ids.tolist(),
            "method":           "HBKM-topdown-lazy",
            "target_k":         target_k,
            "k_branch":         k_branch,
            "n_iter":           n_iter,
            "seed":             seed,
        }, f)

    print(f"  [HBKM] wrote {raw_hubs_path}  "
          f"({hub_vecs.nbytes/1024:.1f} KB)", flush=True)
    print(f"  [HBKM] wrote {ids_path}  "
          f"({len(hub_ids)*4/1024:.1f} KB)", flush=True)
    print(f"  [HBKM] wrote {json_path}", flush=True)


def main():
    ap = argparse.ArgumentParser(description="HBKM hub mining for §5.4 ablation")
    ap.add_argument("--datasets", nargs="*", default=DATASETS,
                    help=f"datasets to process (default: {DATASETS})")
    ap.add_argument("--k_branch", type=int, default=8,
                    help="branching factor for k-means at each split (default 8, "
                         "matching GATE's hbkm() default)")
    ap.add_argument("--n_iter", type=int, default=20,
                    help="max k-means iterations per split")
    ap.add_argument("--seed", type=int, default=42,
                    help="random seed")
    ap.add_argument("--k", type=int, default=None,
                    help="override hub count (default: match W-DPC union)")
    args = ap.parse_args()

    for ds in args.datasets:
        try:
            run_one(ds, k_branch=args.k_branch, n_iter=args.n_iter,
                    seed=args.seed, override_k=args.k)
        except Exception as e:
            print(f"[error] {ds}: {e}", flush=True)
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    sys.exit(main())
