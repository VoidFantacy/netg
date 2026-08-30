"""Export exact dense-cosine GATE routes for the shared ACSG evaluator."""

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from cluster.model.train.dataset import load_graph_features, read_fvecs
from cluster.model.train.model import Model


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_fvecs(path, vectors):
    with open(path, "wb") as handle:
        dim = np.asarray([vectors.shape[1]], dtype=np.int32).tobytes()
        for vector in vectors:
            handle.write(dim)
            handle.write(np.asarray(vector, dtype=np.float32).tobytes())


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--query", required=True)
    parser.add_argument("--hub-ids", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--top-m", type=int, default=3)
    parser.add_argument("--max-queries", type=int, default=10000)
    parser.add_argument("--batch-size", type=int, default=2048)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    with args.config.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    model_params = config["model"]
    dataset_params = config["dataset"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    loaded = torch.load(args.model, map_location=device, weights_only=False)
    if isinstance(loaded, Model):
        model = loaded.to(device)
    else:
        model = Model(
            model_params["input_dim"], model_params["hidden_dim"],
            model_params["output_dim"], model_params["dropout"],
        ).to(device)
        model.load_state_dict(loaded)
    model.eval()

    hubs = read_fvecs(dataset_params["HUB_PATH"])
    graph_features = load_graph_features(
        dataset_params["SUBGRAPH_DIR"], len(hubs), hubs,
        dataset_params.get("GRAPH2VEC_CSV"),
    )
    hub_ids = np.fromfile(args.hub_ids, dtype=np.int32)
    if len(hub_ids) != len(hubs) or len(set(map(int, hub_ids))) != len(hub_ids):
        raise ValueError("hub IDs must be unique and match the hub count")
    queries = read_fvecs(args.query)[:args.max_queries]
    if queries.shape[1] != model_params["output_dim"]:
        raise ValueError("query dimension does not match model output dimension")
    if not 0 < args.top_m <= len(hubs):
        raise ValueError("invalid top-m")

    with torch.no_grad():
        hub_embeddings = model(
            torch.from_numpy(hubs).to(device),
            torch.from_numpy(graph_features).to(device),
        )
        hub_embeddings = F.normalize(hub_embeddings, dim=1)
        route_indices = []
        for begin in range(0, len(queries), args.batch_size):
            query = torch.from_numpy(queries[begin:begin + args.batch_size]).to(device)
            similarity = F.normalize(query, dim=1) @ hub_embeddings.T
            route_indices.append(torch.topk(similarity, args.top_m, dim=1).indices.cpu().numpy())
    route_indices = np.concatenate(route_indices).astype(np.int32, copy=False)
    routes = hub_ids[route_indices]
    if routes.shape != (len(queries), args.top_m):
        raise RuntimeError(f"unexpected route shape: {routes.shape}")

    routes_path = args.output_dir / f"routes_top{args.top_m}.int32"
    indices_path = args.output_dir / f"hub_indices_top{args.top_m}.int32"
    embeddings_path = args.output_dir / "hub_embeddings.fvecs"
    routes.tofile(routes_path)
    route_indices.tofile(indices_path)
    write_fvecs(embeddings_path, hub_embeddings.cpu().numpy())

    manifest = {
        "schema_version": 1,
        "purpose": "exact dense-cosine GATE routes for frozen-graph evaluation",
        "config": str(args.config),
        "model": str(args.model),
        "model_sha256": sha256_file(args.model),
        "query": args.query,
        "query_count": len(queries),
        "hub_ids": args.hub_ids,
        "hub_count": len(hubs),
        "top_m": args.top_m,
        "routing": "exact dense cosine; no approximate routing-index error",
        "routes": str(routes_path),
        "routes_sha256": sha256_file(routes_path),
        "route_shape": list(routes.shape),
        "hub_indices": str(indices_path),
        "hub_indices_sha256": sha256_file(indices_path),
        "hub_embeddings": str(embeddings_path),
        "hub_embeddings_sha256": sha256_file(embeddings_path),
        "finite_embeddings": bool(torch.isfinite(hub_embeddings).all().item()),
    }
    with (args.output_dir / "manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
