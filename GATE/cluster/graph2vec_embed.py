"""Deterministic topology-only Graph2Vec adapter for the GATE baseline.

GATE's public instructions leave graph embedding as an external step.  This
adapter implements the standard Weisfeiler-Lehman + Doc2Vec formulation and
writes both a pandas-compatible CSV and a provenance manifest.
"""

import argparse
import hashlib
import json
import os
import platform
from pathlib import Path

import gensim
import numpy as np
from gensim.models.doc2vec import Doc2Vec, TaggedDocument


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_digest(paths) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def wl_document(path: Path, iterations: int) -> TaggedDocument:
    with path.open("r", encoding="utf-8") as handle:
        graph = json.load(handle)
    if set(graph) != {"nodes", "edges"}:
        raise ValueError(f"{path}: expected topology-only nodes+edges JSON")

    nodes = [int(node) for node in graph["nodes"]]
    if len(nodes) != len(set(nodes)) or not nodes:
        raise ValueError(f"{path}: nodes must be non-empty and unique")
    node_to_local = {node: index for index, node in enumerate(nodes)}
    adjacency = [set() for _ in nodes]
    for edge in graph["edges"]:
        if len(edge) != 2:
            raise ValueError(f"{path}: malformed edge {edge}")
        source, target = map(int, edge)
        if source not in node_to_local or target not in node_to_local:
            raise ValueError(f"{path}: edge endpoint outside node set")
        source = node_to_local[source]
        target = node_to_local[target]
        adjacency[source].add(target)
        adjacency[target].add(source)

    labels = [str(len(neighbors)) for neighbors in adjacency]
    words = [f"0:{label}" for label in labels]
    for depth in range(1, iterations + 1):
        next_labels = []
        for node, neighbors in enumerate(adjacency):
            signature = labels[node] + "|" + "|".join(
                sorted(labels[neighbor] for neighbor in neighbors)
            )
            next_labels.append(hashlib.md5(signature.encode("utf-8")).hexdigest())
        labels = next_labels
        words.extend(f"{depth}:{label}" for label in labels)

    return TaggedDocument(words=words, tags=[int(path.stem)])


def write_csv(path: Path, embeddings: np.ndarray) -> None:
    # Match pandas.DataFrame(...).to_csv(): blank index header, integer columns.
    with path.open("w", encoding="utf-8") as handle:
        handle.write("," + ",".join(map(str, range(embeddings.shape[1]))) + "\n")
        for index, row in enumerate(embeddings):
            values = ",".join(format(float(value), ".9g") for value in row)
            handle.write(f"{index},{values}\n")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("subgraph_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--num-graphs", type=int, default=512)
    parser.add_argument("--dimensions", type=int, default=512)
    parser.add_argument("--wl-iterations", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--min-count", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite non-empty output directory: {args.output_dir}"
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)

    paths = [args.subgraph_dir / f"{index}.json" for index in range(args.num_graphs)]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing {len(missing)} graph JSON files; first={missing[0]}")

    print(f"Loading {len(paths)} topology graphs and extracting WL labels...", flush=True)
    documents = [wl_document(path, args.wl_iterations) for path in paths]
    if [document.tags[0] for document in documents] != list(range(args.num_graphs)):
        raise RuntimeError("document tags are not contiguous graph IDs")

    print("Training deterministic single-worker Doc2Vec...", flush=True)
    model = Doc2Vec(
        documents=documents,
        vector_size=args.dimensions,
        window=0,
        min_count=args.min_count,
        dm=0,
        sample=0.0001,
        workers=1,
        epochs=args.epochs,
        alpha=0.025,
        min_alpha=0.0001,
        seed=args.seed,
    )
    embeddings = np.stack(
        [np.asarray(model.dv[index], dtype=np.float32) for index in range(args.num_graphs)]
    )
    if embeddings.shape != (args.num_graphs, args.dimensions):
        raise RuntimeError(f"unexpected embedding shape: {embeddings.shape}")
    if not np.isfinite(embeddings).all():
        raise RuntimeError("non-finite graph embeddings")

    npy_path = args.output_dir / "graph2vec_embedding.npy"
    csv_path = args.output_dir / "graph2vec_embedding.csv"
    np.save(npy_path, embeddings, allow_pickle=False)
    write_csv(csv_path, embeddings)

    manifest = {
        "schema_version": 1,
        "purpose": "standalone GATE topology embedding adapter",
        "fidelity_note": (
            "GATE upstream leaves graph embedding external; this is a standard "
            "topology-only WL+Doc2Vec Graph2Vec reproduction, not an upstream artifact"
        ),
        "algorithm": {
            "graph_direction": "directed NSG edges converted to undirected simple adjacency",
            "initial_node_label": "undirected degree",
            "wl_iterations": args.wl_iterations,
            "doc2vec": "PV-DBOW (dm=0)",
            "dimensions": args.dimensions,
            "epochs": args.epochs,
            "min_count": args.min_count,
            "sample": 0.0001,
            "workers": 1,
            "seed": args.seed,
        },
        "input": {
            "subgraph_dir": str(args.subgraph_dir),
            "num_graphs": args.num_graphs,
            "combined_sha256": source_digest(paths),
        },
        "output": {
            "shape": list(embeddings.shape),
            "dtype": str(embeddings.dtype),
            "npy": str(npy_path),
            "npy_sha256": sha256_file(npy_path),
            "csv": str(csv_path),
            "csv_sha256": sha256_file(csv_path),
            "finite": bool(np.isfinite(embeddings).all()),
            "row_norm_min": float(np.linalg.norm(embeddings, axis=1).min()),
            "row_norm_max": float(np.linalg.norm(embeddings, axis=1).max()),
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "gensim": gensim.__version__,
        },
    }
    manifest_path = args.output_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(manifest, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
