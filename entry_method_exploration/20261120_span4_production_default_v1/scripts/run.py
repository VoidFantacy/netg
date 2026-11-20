"""Qualify the ACSG production branch on the same frozen inputs as E210."""
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
E210=ROOT.parent/"20261120_span4_four_dataset_retest_v1"
E209=ROOT.parent/"20261120_webvid_b32_span_confirmation_v1"
E206=ROOT.parent/"20261120_residual_budget_matched_table_v1"
DATASETS=("coco","flickr30k","webvid2_5m_light_v1","yandex_t2i_official10M_ip_v1")
N=3072
LS={1:(64,100,160,200,320,400,800),100:(100,160,200,320,400,640,960)}
MATRIX=tuple((k,l) for k in LS for l in LS[k])


def read(path):
    return json.loads(Path(path).read_text())


def write(path,value):
    with Path(path).open("x") as f:
        json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False)
        f.write("\n")


def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        while block:=f.read(16*1024*1024):
            h.update(block)
    return h.hexdigest()


def identity(path,hashed):
    p=Path(path)
    st=p.stat()
    value={"resolved":str(p.resolve()),"bytes":st.st_size,"mtime_ns":st.st_mtime_ns}
    if hashed:
        value["sha256"]=digest(p)
    return value


def verify(files):
    for p,v in files.items():
        assert identity(p,"sha256" in v)==v,p


def freeze():
    earlier=read(E210/"input_freeze.json")["files"]
    gt=read(E210/"gt_eval.json")
    confs=[]
    inherited={}
    for ds in DATASETS:
        conf=read(E210/"configs"/f"{ds}.json")
        assert conf["queries"]["n"]==N and "test_gt" not in conf
        refs=[conf["base"]["path"],conf["index"],conf["queries"]["path"],conf["table"],
              *(conf["router"][k] for k in ("W","ids","graph")),gt[ds]["path"]]
        inherited.update({p:earlier[p] for p in refs})
        conf["output_dir"]=str(ROOT/"data"/ds)
        path=ROOT/"configs"/f"{ds}.json"
        write(path,conf)
        confs.append(path)
    verify(inherited)
    gt_path=ROOT/"gt_eval.json"
    write(gt_path,gt)
    paths=(*confs,gt_path,ROOT/"scripts/run.py",ROOT/"src/benchmark.cpp",ROOT/"protocol.md",
           E206/"src/common.inc",REPO/"ACSG/ACSG.cpp",REPO/"ACSG/ACSG.h",REPO/"ACSG/IndexACSG.cpp",
           REPO/"ACSG/IndexACSG.h",REPO/"ACSG/detail/CandidatePool.h",
           REPO/"build/build.ninja",E210/"input_freeze.json",E209/"bin/build.json",
           REPO/"build/MRNN_Descent/libmrnndescent.a",REPO/"build/faiss/faiss/libfaiss.a")
    frozen={**inherited,**{str(p):identity(p,True) for p in paths}}
    write(ROOT/"input_freeze.json",{"files":frozen,"source":"E210 frozen assets + live ACSG source",
         "public_GT":"stat only until every timed dataset finishes","K_L":LS})
    build(ROOT/"bin",ROOT/"src/benchmark.cpp",ROOT/"logs/build.log")


def build(directory, source, log_path):
    ninja=subprocess.check_output(["ninja","-C","build","-t","commands","ACSG/libACSG.a"],
                                  text=True,cwd=REPO)
    binary=directory/source.stem
    archive=directory/"libACSG.a"
    original=read(E209/"bin/build.json")["argv"]
    argv=[str(source) if s.endswith("/src/benchmark.cpp")
          else str(binary) if s.endswith("/bin/benchmark")
          else str(archive) if s.endswith("/ACSG/libACSG.a") else s for s in original
          if not s.endswith("/acsg_current.o")]
    cmd_list=[]
    objects=[]
    for filename in ("IndexACSG.cpp","ACSG.cpp"):
        cmd=next(shlex.split(line) for line in ninja.splitlines() if line.endswith("/ACSG/"+filename))
        output=directory/(filename+".o")
        for flag,path in (("-o",output),("-MT",output),("-MF",output.with_suffix(".d"))):
            cmd[cmd.index(flag)+1]=str(path)
        cmd_list.append(cmd)
        objects.append(str(output))
    cmd_list.extend((["ar","rcs",str(archive),*objects],argv))
    start=time.monotonic()
    with log_path.open("x") as log:
        for cmd in cmd_list:
            subprocess.run(cmd,cwd=REPO/"build",stdout=log,stderr=subprocess.STDOUT,check=True)
    write(directory/"build.json",{"argv":cmd_list,"seconds":time.monotonic()-start})
    write(directory/"freeze.json",{"files":{str(p):identity(p,True) for p in (archive,binary)}})


def main():
    if sys.argv[1:]==["--resume"]:
        verify(read(ROOT/"input_freeze.json")["files"])
        verify(read(ROOT/"bin/freeze.json")["files"])
    else:
        freeze()
    env={**os.environ,**{k:"1" for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS",
        "BLIS_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS")},"OMP_DYNAMIC":"FALSE"}
    for ds in DATASETS:
        config=ROOT/"configs"/f"{ds}.json"
        finished=ROOT/"data"/ds/"complete.json"
        if finished.exists():
            assert read(finished)["status"]=="PASS_E211_NATIVE"
            continue
        print(f"running {ds}",flush=True)
        start=time.monotonic()
        with (ROOT/"logs"/f"{ds}.log").open("x") as log:
            result=subprocess.run(["taskset","-c","15",str(ROOT/"bin/benchmark"),str(config)],
                           env=env,stdout=log,stderr=subprocess.STDOUT)
        write(ROOT/"logs"/f"{ds}.receipt.json",{"returncode":result.returncode,
               "seconds":time.monotonic()-start})
        result.check_returncode()
        print(f"completed {ds}",flush=True)
    verify(read(ROOT/"input_freeze.json")["files"])
    verify(read(ROOT/"bin/freeze.json")["files"])
    write(ROOT/"timing_complete.json",{"status":"PASS_E211_TIMING_COMPLETE","datasets":list(DATASETS),
        "points":224,"batches":448,"query_calls":1376256})


if __name__=="__main__":
    main()
