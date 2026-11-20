"""Build the elected default from production sources without replacing historical binaries."""
import os
import shlex
import subprocess

from run import ROOT, REPO, build, identity, read, write


def main():
    assert read(ROOT/"analysis/decision.json")["passes_production_performance_gate"]
    assert read(ROOT/"reviews/candidate_dispatch.json")["status"]=="PASS_E211_DISPATCH"
    source=REPO/"ACSG/ACSG.h"
    assert "bool flat_ip_batch4_enabled_ = true;" in source.read_text()
    out=ROOT/"release"
    out.mkdir()
    build(out,ROOT/"src/benchmark.cpp",ROOT/"logs/release_build.log")

    ninja=subprocess.check_output(["ninja","-C","build","-t","commands","benches/test"],
                                  text=True,cwd=REPO)
    obj=out/"test.cpp.o"
    compile_bench=next(shlex.split(line) for line in ninja.splitlines()
                       if line.endswith("/benches/test.cpp"))
    for flag,path in (("-o",obj),("-MT",obj),("-MF",obj.with_suffix(".d"))):
        compile_bench[compile_bench.index(flag)+1]=str(path)
    link=next(shlex.split(line.split("&&")[1]) for line in ninja.splitlines()
              if " -o benches/test " in line)
    link=[str(obj) if s=="benches/CMakeFiles/test.dir/test.cpp.o"
          else str(out/"test") if s=="benches/test"
          else str(out/"libACSG.a") if s=="ACSG/libACSG.a" else s for s in link]
    with (ROOT/"logs/release_build_test.log").open("x") as log:
        for cmd in (compile_bench,link):
            subprocess.run(cmd,check=True,cwd=REPO/"build",stdout=log,stderr=subprocess.STDOUT)
    write(out/"bench_build.json",{"argv":[compile_bench,link],
                                   "binary":identity(out/"test",True)})
    with (ROOT/"logs/release_test_help.log").open("x") as log:
        subprocess.run([out/"test","--help"],check=True,env=dict(os.environ,OMP_NUM_THREADS="1",
                       OPENBLAS_NUM_THREADS="1"),stdout=log,stderr=subprocess.STDOUT)
    sources=(REPO/"ACSG/ACSG.cpp",source,REPO/"ACSG/IndexACSG.cpp",REPO/"benches/test.cpp")
    write(out/"sources.json",{"files":{str(p):identity(p,True) for p in sources}})


if __name__=="__main__":
    main()
