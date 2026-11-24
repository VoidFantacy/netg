"""Freeze the E213 inputs and run the dispatch checks and timing serially."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E212 = ROOT.parent / "20261120_gt10_nsg_b32_four_way_v1"
E200 = ROOT.parent / "20261110_multimodal_four_method_retest_v1"
sys.dont_write_bytecode = True
sys.path.append(str(E212 / "scripts"))
from run import DATASETS, E206, E211, MATRIX, N, REPO, identity, read, verify, write

ARMS = ("NSG-SPAN4", "GT10-B32-SPAN4", "GATE-SPAN4", "GATE-scalar")
WRAP = "_ZN5faiss26fvec_inner_product_batch_4EPKfS1_S1_S1_S1_mRfS2_S2_S2_"
SNAPSHOT = ("AGENTS.md", "LOCAL_CODEX_START.md", "summary.md", "spec.md", "s-target.md",
            "s-experiment.md", "experiment_history/README.md")
ENV = {**os.environ, **dict.fromkeys(
    ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
     "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"), "1"), "OMP_DYNAMIC": "FALSE"}


def freeze():
    prior = read(E212 / "input_freeze.json")["files"]
    gate_freeze = read(E200 / "formal_freeze.json")["files"]
    release_freeze = read(E211 / "release/freeze.json")["files"]
    locked = {}
    paths = [ROOT / file for file in ("src/benchmark.cpp", "scripts/run_experiment.py", "protocol.md")]
    paths.extend((E206 / "src/common.inc", E211 / "release/build.json",
                  E212 / "input_freeze.json", E212 / "scripts/run.py", E200 / "formal_freeze.json",
                  REPO / "ACSG/ACSG.cpp", REPO / "ACSG/ACSG.h"))
    for name in SNAPSHOT:
        dest = ROOT / "source_before" / name
        dest.parent.mkdir(exist_ok=True, parents=True)
        with dest.open("xb") as handle:
            handle.write((REPO / name).read_bytes())
    gt = read(E212 / "gt_eval.json")
    for ds in DATASETS:
        conf = read(E212 / "configs" / f"{ds}.json")
        hist = [E200 / "configs" / f"{ds}.formal_k{k}.json" for k in (1, 100)]
        gate_routers = []
        for file in hist:
            old = read(file)
            assert old["index"] == conf["index"]
            assert all(old["queries"][field] == conf["queries"][field] for field in ("path", "format", "d"))
            assert old["queries"].get("row_start", 0) == conf["queries"].get("row_start", 0) == 0
            gate_routers.append(next(r for r in old["routers"] if r.get("gate", False)))
        assert gate_routers[0] == gate_routers[1] and not gate_routers[0]["allow_build"]
        conf["gate_router"] = gate_routers[0]
        conf["output_dir"] = str(ROOT / "data" / ds)
        assert conf["queries"]["n"] == N and conf["threads"] == 1 and conf["cpu"] == 15
        for p in (conf["base"]["path"], conf["index"], conf["queries"]["path"], conf["table"],
                  gt[ds]["path"], *(conf["router"][key] for key in ("ids", "W", "graph"))):
            locked[p] = prior[p]
        for key in ("ids", "W", "graph"):
            p = conf["gate_router"][key]
            ident = identity(p, True)
            assert all(ident[key] == gate_freeze[p][key] for key in ("sha256", "bytes")), p
            locked[p] = ident
        config = ROOT / "configs" / f"{ds}.json"
        write(config, conf)
        paths.extend((config, *hist))
    score_path = ROOT / "gt_eval.json"
    write(score_path, gt)
    paths.append(score_path)
    link = read(E211 / "release/build.json")["argv"][-1]
    paths.extend(Path(p) for p in link if p.endswith(".a"))
    locked.update({str(path): identity(path, True) for path in paths})
    release = str(E211 / "release/libACSG.a")
    assert locked[release] == release_freeze[release]
    verify(locked)
    write(ROOT / "input_freeze.json", {"files": locked, "datasets": DATASETS, "matrix": MATRIX,
        "arms": ARMS, "GT": "identity only before formal timing completes"})
    commands = []
    for name in ("benchmark", "verify_dispatch"):
        binary = ROOT / "bin" / name
        cmd = [str(ROOT / "src/benchmark.cpp") if p.endswith("/src/benchmark.cpp")
               else str(binary) if p.endswith("/release/benchmark") else p for p in link]
        if name == "verify_dispatch":
            cmd[1:1] = ["-DVERIFY_DISPATCH", f"-Wl,--wrap={WRAP}"]
        with (ROOT / "logs" / f"build_{name}.log").open("x") as log:
            subprocess.run(cmd, cwd=REPO / "build", stdout=log, stderr=subprocess.STDOUT, check=True)
        commands.append(cmd)
    write(ROOT / "bin/build.json", {"argv": commands})
    write(ROOT / "bin/freeze.json", {"files": {str(p): identity(p, True)
          for p in (ROOT / "bin/benchmark", ROOT / "bin/verify_dispatch")}})


def launch(name, config, log):
    with log.open("x") as handle:
        subprocess.run(["taskset", "-c", "15", str(ROOT / "bin" / name), str(config)],
                       env=ENV, stdout=handle, stderr=subprocess.STDOUT, check=True)


def main():
    if "--resume" not in sys.argv:
        freeze()
    verify(read(ROOT / "input_freeze.json")["files"])
    verify(read(ROOT / "bin/freeze.json")["files"])
    for ds in DATASETS:
        config = ROOT / "configs" / f"{ds}.json"
        complete = ROOT / "data" / ds / "complete.json"
        if complete.exists():
            assert read(complete)["status"] == "PASS_E213_NATIVE"
            continue
        probe = ROOT / "reviews" / f"{ds}.dispatch.json"
        if not probe.exists():
            log = ROOT / "logs" / f"{ds}.dispatch.log"
            launch("verify_dispatch", config, log)
            result = json.loads(log.read_text().splitlines()[-1])
            assert result["status"] == "PASS_E213_DISPATCH" and result["dataset"] == ds
            write(probe, result)
        print(f"timing {ds}", flush=True)
        started = time.monotonic()
        launch("benchmark", config, ROOT / "logs" / f"{ds}.log")
        assert read(complete)["status"] == "PASS_E213_NATIVE"
        write(ROOT / "logs" / f"{ds}.receipt.json", {"seconds": time.monotonic() - started})
        print(f"completed {ds}", flush=True)
    verify(read(ROOT / "input_freeze.json")["files"])
    verify(read(ROOT / "bin/freeze.json")["files"])
    points = len(DATASETS) * len(MATRIX) * len(ARMS)
    write(ROOT / "timing_complete.json", {"status": "PASS_E213_TIMING_COMPLETE", "datasets": DATASETS,
          "points": points, "batches": 2 * points, "query_calls": 2 * points * N})


if __name__ == "__main__":
    main()
