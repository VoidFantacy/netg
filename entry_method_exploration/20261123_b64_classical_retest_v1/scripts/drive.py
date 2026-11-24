"""Build three L2 Mixed64 tables, then time the frozen matrix serially."""
from pathlib import Path
import subprocess
import sys
from time import monotonic

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
X = ROOT.parent
E183 = X / "20261017_gt10_residual_comprehensive_v1"
E197 = X / "20261101_residual_bottleneck_separation_v1"
E226 = X / "20261122_b32_b64_two_tower_v1"
E251 = X / "20261123_b64_four_dataset_retest_v1"
sys.path.extend((str(E226 / "scripts"), str(E251 / "scripts")))
from run import ENV, RAW, digest, lock, read, vectors, verify, write
from build_tables import LEVELS, events, keys

DEEP, SIFT, GIST = DATASETS = ("deep10m_l2_v1", "sift10m_bigann_l2_v1", "gist1m_l2_v1")
NAMES = dict(zip(DATASETS, ("Deep10M", "BIGANN-SIFT10M", "GIST1M")))
METHODS = ("B32", "Mixed64")
SMALL_K = (16, 20, 24, 28, 32, 40, 48, 56, 64, 80, 100, 128, 160, 200, 280, 400)
LARGE_K = (100, 112, 128, 144, 160, 176, 192, 208, 232, 256, 320, 400, 512, 640, 800)
GRIDS = {
    DEEP: {1: SMALL_K, 100: LARGE_K},
    SIFT: {1: SMALL_K, 100: LARGE_K},
    GIST: {1: (16, 24, 32, 40, 48, 56, 64, 80, 100, 128, 160, 200, 280, 400, 600, 800, 1200),
           100: (*LARGE_K, 1000, 1200)},
}
TARGETS = {
    DEEP: {1: (90, 94, 96, 97, 98, 99, 99.5), 100: (94, 95, 96, 97, 98, 99, 99.5)},
    SIFT: {1: (90, 95, 97, 98, 99, 99.5, 99.8), 100: (95, 96, 97, 98, 99, 99.5, 99.8)},
    GIST: {1: (75, 80, 85, 90, 94, 96, 98, 99), 100: (80, 85, 90, 92, 94, 96, 97, 98)},
}
POINTS = 2 * sum(len(v) for ds in DATASETS for v in GRIDS[ds].values())
BATCHES = 2 * POINTS


def config(ds):
    return ROOT / "configs" / f"{ds}.json"


def native(args, log_path):
    with log_path.open("x") as log:
        subprocess.run(["taskset", "-c", "15", *map(str, args)], stdout=log, stderr=subprocess.STDOUT,
                       env=ENV, check=True)


def train(ds, c, source, compiler, base_sha):
    begin = monotonic()
    folder = ROOT / "models" / ds
    folder.mkdir()
    fit = source["train_queries"]
    p = Path(fit["path"]).parent
    train_gt = source["train_gt"]
    assert Path(train_gt["path"]) == p / "fit.gt.i32"
    assert fit["n"] == train_gt["n"] == 16000
    assert fit["total_n"] == train_gt["total_n"] == 20000
    assert fit.get("row_start", 0) == train_gt.get("row_start", 0) == 0
    qgt = p / "qgt.f32"
    q_fit = vectors(dict(fit, n=20000))
    q_hubs = vectors(dict(fit, path=str(qgt), n=5000))
    role_rows = [p / f"{role}.source_rows.i64" for role in ("fit", "qgt")]
    fit_rows, hub_rows = (np.fromfile(file, "<i8") for file in role_rows)
    assert len(set(fit_rows)) == 20000 and len(set(hub_rows)) == 5000
    assert not (set(fit_rows) & set(hub_rows))
    q = np.concatenate((q_fit, q_hubs[:4192])).astype("<f4")
    assert len(q) == len(keys(q)) == 24192 and np.isfinite(q).all()
    assert not (keys(q) & keys(vectors(source["test_queries"])))

    deps = [Path(fit["path"]), qgt, *role_rows, Path(source["source_manifest"])]
    blocks = []
    for role, count in (("fit", 20000), ("qgt", 5000)):
        receipt = p / f"{role}.gt" / "complete.json"
        item = read(receipt)
        assert (item["status"], item["n"], item["k"], item["metric"], item["base_sha256"]) == (
            "PASS", count, 100, "squared_L2", base_sha
        )
        labels = p / f"{role}.gt.i32"
        packed_path = p / f"{role}.gt.ivecs"
        assert digest(packed_path) == item["gt_sha256"]
        packed = np.fromfile(packed_path, "<i4").reshape(count, 101)
        dense = np.fromfile(labels, "<i4").reshape(count, 100)
        assert (packed[:, 0] == 100).all() and np.array_equal(packed[:, 1:], dense)
        blocks.append(dense)
        deps.extend((receipt, labels, packed_path))
    gt = np.concatenate((blocks[0], blocks[1][:4192])).astype("<i4")
    assert gt.shape == (len(q), 100) and gt.min() >= 0 and gt.max() < c["base"]["n"]
    assert (np.diff(np.sort(gt, axis=1), axis=1) > 0).all()
    query_file = folder / "train.f32"
    q.tofile(query_file)
    gt.tofile(folder / "train.gt.i32")
    np.concatenate((fit_rows, hub_rows[:4192])).astype("<i8").tofile(folder / "learn_rows.i64")
    teacher_dir = folder / "teacher"
    teacher_cfg = ROOT / "configs" / f"{ds}.teacher.json"
    write(teacher_cfg, dict(c, train_n=len(q), train_queries=str(query_file), build_teacher=True,
                            grid=LEVELS, output_dir=str(teacher_dir)))
    native((ROOT / "bin/benchmark", teacher_cfg), ROOT / "logs" / f"{ds}.teacher.log")
    outcome = read(teacher_dir / "complete.json")
    assert (outcome["status"], outcome["n"], outcome["points"], outcome["threads"], outcome["GT_read"]) == (
        "PASS_E252_TRAIN_MAIN", len(q), len(LEVELS), 1, False
    )
    raw = Path(c["table"]).read_bytes()
    assert raw[:8] == b"M5POST1\0"
    _, h, width = map(int, np.frombuffer(raw, "<u4", 3, 8))
    assert width == 32
    ids = np.frombuffer(raw, "<i4", h, 40)
    counts = np.frombuffer(raw, "u1", h, 40 + h * 4)
    values = np.frombuffer(raw, "<i4", 32 * h, 40 + h * 5).reshape(h, 32)
    prefix = {row: set(items[:count]) for row, items, count in zip(ids, values, counts)}
    token_dir = folder / "tokens"
    covered, levels = events(teacher_dir, gt, prefix, token_dir)
    pool = folder / "mixed"
    compile_cfg = ROOT / "configs" / f"{ds}.compile.json"
    write(compile_cfg, dict(base_n=c["base"]["n"], table=c["table"], teacher_root=str(token_dir),
                            token_source=str(token_dir), old_covered=covered, output_dir=str(pool)))
    native((compiler, "compile64", compile_cfg), ROOT / "logs" / f"{ds}.compile.log")
    result = read(pool / "complete.json")
    assert result["status"] == "PASS_E226_B64"
    assert result["teacher"] == len(LEVELS) * len(q) and result["covered_B32"] == covered
    assert result["appended_IDs"] > 0
    role_file = folder / "roles.json"
    write(role_file, dict(original_fit=16000, extra_fit=4000, extra_qgt=4192, total=len(q),
                          source_rows_disjoint=True, full_public_vector_overlap=0,
                          levels=levels, offline_seconds=monotonic() - begin, pool=result))
    c["mixed_pool"] = str(pool)
    return deps + [teacher_cfg, compile_cfg, *sorted(p for p in folder.rglob("*") if p.is_file())]


def prepare():
    native_bin = ROOT / "bin/benchmark"
    compiler = E226 / "bin/benchmark"
    compiler_seal = E226 / "seal.json"
    assert digest(compiler) == read(compiler_seal)["files"]["bin/benchmark"]["sha256"]
    catalogue = E183 / "reviews/dataset_catalogue.json"
    freeze = E183 / "reviews/input_freeze.json"
    sources = read(catalogue)["datasets"]
    original = read(freeze)["files"]
    files = [native_bin, compiler, compiler_seal, catalogue, freeze, ROOT / "protocol.md",
             ROOT / "bin/build.json", ROOT / "src/benchmark.cpp", Path(__file__).resolve(),
             E251 / "scripts/build_tables.py", E226 / "scripts/run.py",
             X / "20261120_residual_budget_matched_table_v1/src/common.inc",
             E183 / "src/benchmark.cpp", E183 / "src/residual_tools.cpp",
             X / "20261121_neighbor_residual_online_v1/src/residual.hpp"]
    files += [Path(p) for p in read(ROOT / "bin/build.json")["argv"] if p.endswith(".a")]
    truth = {}
    for ds in DATASETS:
        source = sources[ds]
        match = E197 / "configs" / f"{ds}.A.json"
        previous = read(match)
        assert source["base"] == previous["base"]
        assert source["index"] == previous["index"] and source["metric_id"] == previous["metric_id"] == 1
        assert previous["router"] in source["routers"]
        c = {k: source[k] for k in ("base", "index", "metric_id", "dataset")}
        c.update(threads=1, cpu=15, router=previous["router"], table=previous["table"],
                 queries=source["test_queries"], output_dir=str(ROOT / "data" / ds),
                 grids={str(k): grid for k, grid in GRIDS[ds].items()})
        assert Path(c["table"]).name == "JOINT32.bin"
        total = c["queries"]["n"]
        eval_n = min(3072, total)
        rows = np.sort(np.random.default_rng(252).choice(total, eval_n, replace=False)).astype("<i4")
        rows_file = ROOT / "configs" / f"{ds}.rows.i32"
        rows.tofile(rows_file)
        c.update(eval_n=eval_n, rows=str(rows_file))
        deps = [c["base"]["path"], c["index"], c["queries"]["path"], *[c["router"][k] for k in ("ids", "W", "graph")]]
        for path in deps:
            assert digest(path) == original[path]["sha256"], path
        expected = source["test_gt"]
        receipt_file = Path(expected["path"]).with_name("test.gt") / "complete.json"
        cert = read(receipt_file)
        sha = original[expected["path"]]["sha256"]
        assert (cert["status"], cert["base_sha256"], cert["n"], cert["metric"], cert["k"]) == (
            "PASS", original[c["base"]["path"]]["sha256"], total, "squared_L2", 100
        )
        packed_public = Path(expected["path"]).with_suffix(".ivecs")
        truth[ds] = dict(expected, expected_sha256=sha, ivecs=str(packed_public), ivecs_sha256=cert["gt_sha256"])
        files += [*map(Path, deps), Path(c["table"]), match, rows_file, receipt_file]
        print(ds, "inputs verified, starting teacher", flush=True)
        files.extend(train(ds, c, source, compiler, original[c["base"]["path"]]["sha256"]))
        write(config(ds), c)
        files.append(config(ds))
        print(ds, "table frozen", read(Path(c["mixed_pool"]) / "complete.json"), flush=True)
    score_config = ROOT / "configs/score.json"
    write(score_config, dict(truth=truth, targets=TARGETS))
    # The public GT identity is inherited above. Its payload is opened only in scoring.
    lock(ROOT / "inputs.json", files + [score_config])


def formal():
    verify(ROOT / "inputs.json")
    for ds in DATASETS:
        cfg = read(config(ds))
        receipt = Path(cfg["output_dir"]) / "complete.json"
        if not receipt.is_file():
            native((ROOT / "bin/benchmark", config(ds)), ROOT / "logs" / f"{ds}.formal.log")
        got = read(receipt)
        p = len(METHODS) * sum(map(len, cfg["grids"].values()))
        assert (got["status"], got["points"], got["batches"], got["qualified_queries"], got["public_GT_read"]) == (
            "PASS_E252_FORMAL", p, p * 2, p * 256, False
        )
        print(ds, {k: v for k, v in got.items() if k != "binding"}, flush=True)
    verify(ROOT / "inputs.json")
    write(ROOT / "timing_complete.json", dict(status="PASS_E252_TIMING", datasets=DATASETS, points=POINTS, batches=BATCHES))


if __name__ == "__main__":
    {"prepare": prepare, "formal": formal}[sys.argv[1]]()
