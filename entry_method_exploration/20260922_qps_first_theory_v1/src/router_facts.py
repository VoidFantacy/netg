"""Read historical topology metadata and manifests, without loading a graph."""

import csv
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
TOPOLOGY = ROOT / "entry_method_exploration/20260920_until1900_theory_v1/stages/e115_score_topology_factorial/results/topology_description.json"
INPUTS = ROOT / "entry_method_exploration/20260922_knn_three_point_timing_v1/reviews/inputs.json"
COUNTS = ROOT / "entry_method_exploration/20260920_until1900_theory_v1/research/router_work_identity_v1/results/queries.csv"
SOURCE = ROOT / "benches/hnswlib/hnswalg.h"


def main():
    manifest = {row["path"]: row for row in json.loads(INPUTS.read_text())["files"]}
    facts = []
    for row in json.loads(TOPOLOGY.read_text())["datasets"]:
        original = row["graphs"]["GP_original"]
        identity = original["source"]
        assert identity == manifest[identity["path"]]
        assert original["header"][6] >= 1
        first = next(layer for layer in original["layers"] if layer["layer"] == 1)
        facts.append({"dataset": row["dataset"], "historical_graph_identity": identity,
                      "level1_nodes": first["nodes"],
                      "upper_exit_possible_states_upper_bound": first["nodes"],
                      "direct_uint8_action_table_bytes": original["header"][2],
                      "conditional_occupancy": "Unknown: node count is not observed query support or action value"})
    with COUNTS.open(newline="") as stream:
        fields = csv.DictReader(stream).fieldnames
    assert "upper_expansions" in fields and "upper_exit_id" not in fields
    source = SOURCE.read_text()
    assert "currObj, query_data, std::max(ef_, k), isIdAllowed" in source
    result = {"status": "PASS", "facts": facts,
              "source_inference": "For these level>=1 HNSW graphs, descent stays in level1 nodes before base search; at most 52 exit IDs. No claim all are reachable or occupied.",
              "old_router_work_csv_fields": fields,
              "cache_scope": "Inspected work-count cache has no upper exit ID; no claim all historical files were exhaustively searched",
              "identity_scope": "Old topology and record125 manifests agree; no graph/base/query/GT payload opened",
              "inputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in [TOPOLOGY, INPUTS, COUNTS, SOURCE]},
              "new_searches": 0, "new_training": 0}
    with (HERE / "reviews/router_state_facts.json").open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "PASS", "upper_exit_state_bounds": [r["level1_nodes"] for r in facts]}))


if __name__ == "__main__":
    main()
