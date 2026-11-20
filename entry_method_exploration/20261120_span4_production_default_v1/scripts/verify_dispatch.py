"""Validate link-observed batch dispatch outside the performance runs."""
import os
import subprocess
import sys

from run import ROOT, DATASETS, read, write, identity


L2_DATASETS=("deep10m_l2_v1","sift10m_bigann_l2_v1","gist1m_l2_v1")
SYMBOLS=(
    "_ZN5faiss26fvec_inner_product_batch_4EPKfS1_S1_S1_S1_mRfS2_S2_S2_",
    "_ZN5faiss18fvec_L2sqr_batch_4EPKfS1_S1_S1_S1_mRfS2_S2_S2_",
)


def main():
    assert sys.argv[1:] in (["--candidate"],["--release"])
    release=sys.argv[1]=="--release"
    dest=ROOT/("release" if release else "bin")
    binary=dest/"verify_dispatch"
    compile_argv=read(ROOT/"bin/build.json")["argv"][-1]
    compile_argv=[str(ROOT/"src/verify_dispatch.cpp") if s.endswith("/src/benchmark.cpp")
                  else str(binary) if s.endswith("/bin/benchmark")
                  else str(dest/"libACSG.a") if s.endswith("/bin/libACSG.a")
                  else s for s in compile_argv]
    compile_argv.extend(f"-Wl,--wrap={symbol}" for symbol in SYMBOLS)
    log_dir=ROOT/"logs"
    tag="release" if release else "candidate"
    with (log_dir/f"{tag}_verify_build.log").open("x") as log:
        subprocess.run(compile_argv,check=True,stdout=log,stderr=subprocess.STDOUT)
    env=dict(os.environ,OMP_DYNAMIC="FALSE")
    for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS",
                "BLIS_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
        env[key]="1"
    fixture_cpus="0-3" if release else "0"
    cases=[("fixture",["taskset","-c",fixture_cpus,str(binary),"--default" if release else "--candidate"])]
    if release:
        paths=[(ds,ROOT/"configs"/f"{ds}.json") for ds in DATASETS]
        paths.extend((ds,ROOT/"configs"/f"{ds}.fallback.json") for ds in L2_DATASETS)
        cases.extend((ds,["taskset","-c","15",str(binary),str(p)]) for ds,p in paths)
    outcomes=[]
    for ds,cmd in cases:
        log=log_dir/f"{tag}_verify_{ds}.log"
        with log.open("x") as handle:
            subprocess.run(cmd,check=True,env=env,stdout=handle,stderr=subprocess.STDOUT)
        outcomes.append({"case":ds,"receipt":str(log),"sha256":identity(log,True)["sha256"]})
        print(f"{tag} {ds} passed",flush=True)
    write(ROOT/"reviews"/f"{tag}_dispatch.json",{"status":"PASS_E211_DISPATCH",
        "release_default_untouched":release,"outcomes":outcomes,
        "build_argv":compile_argv,"binary":identity(binary,True)})


if __name__=="__main__":
    main()
