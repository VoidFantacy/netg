"""Run the frozen classical L2 matrix with all three arms in the same session."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
X = ROOT.parent
E252 = X / "20261123_b64_classical_retest_v1"
sys.path.append(str(X / "20261122_b32_b64_two_tower_v1" / "scripts"))
from run import ENV, RAW, digest, lock, read, verify, write

DEEP, SIFT, GIST = DATASETS = ("deep10m_l2_v1", "sift10m_bigann_l2_v1", "gist1m_l2_v1")
NAMES = dict(zip(DATASETS, ("Deep10M", "BIGANN-SIFT10M", "GIST1M")))
METHODS = ("GT10", "B32", "Mixed64")
POINTS, BATCHES = 288, 576


def config(ds):
    return ROOT / "configs" / f"{ds}.json"


def prepare():
    seal = read(E252 / "seal.json")["files"]

    def frozen(path):
        ref = seal[str(path.relative_to(E252))]
        assert path.stat().st_size == ref["bytes"] and digest(path) == ref["sha256"], path
        return path

    verify(frozen(E252 / "inputs.json"))
    build = frozen(E252 / "bin/build.json")
    argv = [s.replace(str(E252), str(ROOT)) for s in read(build)["argv"]]
    build_path = ROOT / "bin/build.json"
    write(build_path, dict(argv=argv))
    with (ROOT / "logs/build.log").open("x") as log:
        subprocess.run(argv, env=ENV, stdout=log, stderr=subprocess.STDOUT, check=True)
    files = [E252 / "seal.json", E252 / "inputs.json", frozen(E252 / "src/benchmark.cpp"), build,
             ROOT / "src/benchmark.cpp", ROOT / "bin/benchmark", build_path, Path(__file__).resolve(),
             ROOT / "protocol.md", frozen(E252 / "configs/score.json"),
             *[Path(s) for s in argv if s.endswith(".a")]]
    points = 0
    for ds in DATASETS:
        prev = frozen(E252 / "configs" / f"{ds}.json")
        c = read(prev)
        frozen(Path(c["rows"]))
        for name in ("B64.ids.i32", "B64.counts.i8"):
            files.append(frozen(Path(c["mixed_pool"]) / name))
        c["output_dir"] = str(ROOT / "data" / ds)
        write(config(ds), c)
        files.extend((config(ds), prev, Path(c["rows"]), Path(c["table"])))
        points += len(METHODS) * sum(map(len, c["grids"].values()))
    assert points == POINTS
    lock(ROOT / "inputs.json", files)


def formal():
    verify(ROOT / "inputs.json")
    for ds in DATASETS:
        c = read(config(ds))
        receipt = Path(c["output_dir"]) / "complete.json"
        if not receipt.is_file():
            with (ROOT / "logs" / f"{ds}.formal.log").open("x") as log:
                subprocess.run(["taskset", "-c", "15", str(ROOT / "bin/benchmark"), str(config(ds))],
                               env=ENV, stdout=log, stderr=subprocess.STDOUT, check=True)
        result = read(receipt)
        n = 3 * sum(map(len, c["grids"].values()))
        assert (result["status"], result["points"], result["batches"], result["qualified_queries"],
                result["public_GT_read"]) == ("PASS_E253_FORMAL", n, n*2, n*256, False)
        print(ds, result["points"], "points,", result["batches"], "batches verified", flush=True)
    verify(ROOT / "inputs.json")
    verify(E252 / "inputs.json")
    write(ROOT / "timing_complete.json", dict(status="PASS_E253_TIMING", datasets=DATASETS, points=POINTS, batches=BATCHES))


if __name__ == "__main__":
    {"prepare": prepare, "formal": formal}[sys.argv[1]]()
