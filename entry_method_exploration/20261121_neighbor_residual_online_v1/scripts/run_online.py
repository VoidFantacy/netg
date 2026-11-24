"""Launch each frozen E216 phase serially on CPU15."""
from pathlib import Path
import os
import subprocess
import sys
import time

from prepare import DATASETS, E214, E215, LS, METHODS, PUBLIC_N, REPO, ROOT, identity, read, verify, write
from run import E211

ENV={**os.environ,**dict.fromkeys(("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS",
      "BLIS_NUM_THREADS","NUMEXPR_NUM_THREADS"),"1"),"OMP_DYNAMIC":"FALSE"}
BINARY=ROOT/"bin/benchmark"


def check_originals():
    verify(read(ROOT/"prepare_freeze.json")["files"])
    verify(read(E215/"input_freeze.json")["files"])


def launch(stage,config,dataset):
    begin=time.monotonic()
    with (ROOT/"logs"/f"{dataset}.{stage}.log").open("x") as log:
        subprocess.run(("taskset","-c","15",str(BINARY),stage,str(config)),env=ENV,
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    write(ROOT/"logs"/f"{dataset}.{stage}.receipt.json",{"wall_seconds":time.monotonic()-begin})


def prepare():
    base=read(E211/"release/build.json")["argv"][-1]
    argv=[str(ROOT/"src/benchmark.cpp") if p.endswith("/src/benchmark.cpp")
          else str(BINARY) if p.endswith("/release/benchmark") else p for p in base]
    bound={str(p):identity(p,True) for p in (
        ROOT/"src/benchmark.cpp",ROOT/"src/residual.hpp",ROOT/"scripts/run_online.py",
        ROOT.parent/"20261120_residual_budget_matched_table_v1/src/common.inc",
        E211/"release/build.json",*[Path(x) for x in argv if x.endswith(".a")])}
    lib=str(E211/"release/libACSG.a")
    assert bound[lib] == read(E211/"release/freeze.json")["files"][lib]
    with (ROOT/"logs/compile.log").open("x") as log:
        subprocess.run(argv,cwd=REPO/"build",env=ENV,stdout=log,stderr=subprocess.STDOUT,check=True)
    write(ROOT/"bin/build.json",{"argv":argv})
    for dataset in DATASETS:
        launch("build",ROOT/"configs"/f"{dataset}.heldout.json",dataset)
        for name in ("fit.hnsw","graph_build.json"):
            p=ROOT/"models"/dataset/name
            bound[str(p)]=identity(p,True)
    bound[str(BINARY)]=identity(BINARY,True)
    write(ROOT/"native_freeze.json",{"files":bound})


def main():
    mode=sys.argv[1]
    assert mode in ("heldout","formal")
    check_originals()
    if mode=="heldout" and not (ROOT/"native_freeze.json").exists():
        prepare()
    verify(read(ROOT/"native_freeze.json")["files"])
    if mode=="formal":
        receipt=read(ROOT/"analysis/heldout_decision.json")
        assert receipt["decision"]=="RUN_FORMAL"
        assert receipt["qualified"]
    for dataset in DATASETS:
        complete=ROOT/"data"/dataset/mode/"complete.json"
        if not complete.exists():
            print(f"{mode} {dataset}",flush=True)
            launch(mode,ROOT/"configs"/f"{dataset}.{mode}.json",dataset)
        assert read(complete)["status"]=="PASS_E216_"+mode.upper()
        print(f"completed {mode} {dataset}",flush=True)
    check_originals()
    verify(read(ROOT/"native_freeze.json")["files"])
    result={"status":"PASS_E216_"+mode.upper(),"datasets":DATASETS}
    if mode=="formal":
        points=len(DATASETS)*2*len(LS)*len(METHODS)
        result.update(points=points,batches=2*points,query_calls=2*points*PUBLIC_N)
    write(ROOT/(mode+"_complete.json"), result)


if __name__=="__main__":
    main()
