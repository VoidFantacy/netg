"""Freeze E251 inputs and run the three-method CPU15 matrix."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
X = ROOT.parent
E213 = X / "20261121_span4_gt10_b32_nsg_gate_v1"
E226 = X / "20261122_b32_b64_two_tower_v1"
E229 = X / "20261122_b64_formal_four_dataset_v1"
E243 = X / "20261123_b64_multibudget_training_v1"
E245 = X / "20261123_coco_b64_multibudget_training_v1"
sys.path.append(str(E226 / "scripts"))
from run import ENV, N, RAW, digest, lock, read, verify, write

COCO, FLICKR, WEBVID, YANDEX = DATASETS = (
    "coco", "flickr30k", "webvid2_5m_light_v1", "yandex_t2i_official10M_ip_v1"
)
NAMES = dict(zip(DATASETS, ("COCO", "Flickr30k", "WebVid 2.5M", "Yandex first10M")))
METHODS = ("B32", "B64-old", "Mixed64")
EXTRAS = {
    (COCO, 1): (144, 176, 192, 208),
    (FLICKR, 1): (40, 48, 56, 144, 176),
    (WEBVID, 1): (144, 156, 166, 168, 176, 180, 192, 216),
    (YANDEX, 1): (144, 176, 192, 240),
    (COCO, 100): (188, 196, 204, 212, 232),
    (FLICKR, 100): (144, 160, 196, 204, 240),
    (WEBVID, 100): (188, 196, 204, 212, 232, 288, 440, 560, 800, 960),
    (YANDEX, 100): (144, 160, 196, 204, 240),
}
EXTRA_TARGETS = {(WEBVID, 1): (84,), (WEBVID, 100): (84, 86, 88, 90)}
PRIMARY = {
    (COCO, 1): 99, (COCO, 100): 97, (FLICKR, 1): 99.5, (FLICKR, 100): 97.5,
    (WEBVID, 1): 84, (WEBVID, 100): 75.5, (YANDEX, 1): 92, (YANDEX, 100): 90,
}
TABLE_FILES = ("B64.ids.i32", "B64.counts.i8", "complete.json")
POINTS = 465
BATCHES = 2 * POINTS


def config(ds):
    return ROOT / "configs" / f"{ds}.json"


def sealed(path, experiment, archive):
    assert digest(path) == archive[str(path.relative_to(experiment))]["sha256"], path
    return path


def seal_files(experiment):
    return read(experiment / "seal.json")["files"]


def native(config_path, log_path):
    with log_path.open("x") as log:
        subprocess.run(["taskset", "-c", "15", str(ROOT / "bin/benchmark"), str(config_path)],
                       stdout=log, stderr=subprocess.STDOUT, env=ENV, check=True)


def prepare():
    from build_tables import build_mixed

    e229 = seal_files(E229)
    e226 = seal_files(E226)
    truth = sealed(E213 / "gt_eval.json", E213, read(E213 / "seal.json")["experiment_files"])
    compiler = sealed(E226 / "bin/benchmark", E226, e226)
    build = sealed(E229 / "bin/build.json", E229, e229)
    argv = [a.replace(str(E229), str(ROOT)) if a.startswith(str(E229)) else a for a in read(build)["argv"]]
    write(ROOT / "bin/build.json", {"argv": argv})
    start_files = [ROOT / "protocol.md", ROOT / "src/benchmark.cpp", Path(__file__).resolve(),
                   ROOT / "scripts/build_tables.py", truth, compiler, build,
                   E229 / "seal.json", E226 / "seal.json"]
    start_files += [Path(x) for x in argv if x.endswith(".a")]
    start_files += [X / "20261120_residual_budget_matched_table_v1/src/common.inc",
                    X / "20261121_neighbor_residual_online_v1/src/residual.hpp"]
    with (ROOT / "logs/build.log").open("x") as log:
        subprocess.run(argv, check=True, stdout=log, stderr=subprocess.STDOUT)
    start_files.extend((ROOT / "bin/benchmark", ROOT / "bin/build.json"))
    combos = 0
    provenance = {}
    timings = read(truth)
    for ds in DATASETS:
        old = sealed(E229 / "configs" / f"{ds}.json", E229, e229)
        evidence = sealed(E229 / "configs" / f"{ds}.roles.json", E229, e229)
        old_targets = sealed(E229 / "configs" / f"{ds}.targets.json", E229, e229)
        c = read(old)
        rows_path = sealed(Path(c["rows"]), E229, e229)
        c["output_dir"] = str(ROOT / "data" / ds)
        c["grids"] = {str(k): sorted(set(c["grids"][str(k)]) | set(EXTRAS[ds, k])) for k in (1, 100)}
        combos += sum(map(len, c["grids"].values()))
        targets = {str(k): sorted(set(read(old_targets)[str(k)]) | set(EXTRA_TARGETS.get((ds, k), ()))) for k in (1, 100)}
        assert all(PRIMARY[ds, k] in targets[str(k)] for k in (1, 100))
        target_file = ROOT / "configs" / f"{ds}.targets.json"
        write(target_file, targets)
        prior = Path(c["pool_dir"])
        prior_root, prior_cert = (E229, e229) if prior.is_relative_to(E229) else (E226, e226)
        sources = [old, evidence, old_targets, rows_path, target_file, c["queries"]["path"],
                   c["base"]["path"], c["index"], c["table"], timings[ds]["path"],
                   *(c["router"][k] for k in ("ids", "W", "graph"))]
        sources = [Path(item) for item in sources]
        sources += [sealed(prior / f, prior_root, prior_cert) for f in TABLE_FILES]
        if ds in (COCO, WEBVID):
            origin = E245 if ds == COCO else E243
            scope = seal_files(origin)
            pool = origin / "models/mixed"
            roles = sealed(origin / "models/train/roles.json", origin, scope)
            sources += [origin / "seal.json", roles, *[sealed(pool / f, origin, scope) for f in TABLE_FILES]]
            provenance[ds] = dict(origin=origin.name, scope=read(roles), pool=str(pool), original_eval=read(evidence))
        else:
            pool, roles, training_files = build_mixed(ds, c, ROOT, compiler, native)
            sources.extend(training_files)
            provenance[ds] = dict(origin="E251", scope=read(roles), pool=str(pool), original_eval=read(evidence))
        stats = read(pool / "complete.json")
        assert stats["status"] == "PASS_E226_B64" and stats["appended_IDs"] > 0
        c["mixed_pool"] = str(pool)
        write(config(ds), c)
        start_files.extend(sources + [config(ds)])
        print(ds, "new table frozen", provenance[ds]["scope"], flush=True)
    assert combos * len(METHODS) == POINTS
    p = ROOT / "configs" / "table_provenance.json"
    write(p, provenance)
    lock(ROOT / "inputs.json", start_files + [p])


def formal():
    verify(ROOT / "inputs.json")
    for ds in DATASETS:
        cfg = read(config(ds))
        receipt = Path(cfg["output_dir"]) / "complete.json"
        if not receipt.is_file():
            native(config(ds), ROOT / "logs" / f"{ds}.formal.log")
        info = read(receipt)
        p = len(METHODS) * sum(map(len, cfg["grids"].values()))
        assert (info["status"], info["points"], info["batches"], info["qualified_queries"]) == (
            "PASS_E251_FORMAL", p, p * 2, p * 256
        )
        print(ds, {k: v for k, v in info.items() if k != "binding"}, flush=True)
    verify(ROOT / "inputs.json")
    write(ROOT / "timing_complete.json", dict(status="PASS_E251_TIMING", datasets=DATASETS, points=POINTS, batches=BATCHES))


if __name__ == "__main__":
    {"prepare": prepare, "formal": formal}[sys.argv[1]]()
