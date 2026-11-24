"""Rerun two frozen CACHE anchors with dense nearby budget controls."""
from pathlib import Path
import subprocess

from prepare import DATASETS,ROOT,REPO,identity,read,verify,write
from run_online import ENV, check_originals

STUDY=((DATASETS[0],100,200,(192,200,208,216,224,232,240,248,256)),
       (DATASETS[1],1,192,(184,192,200,208,216,224,232,240,248,256)))


def main():
    assert read(ROOT/"reviews/independent_audit.json")["status"]=="PASS_E216_STDLIB_AUDIT"
    check_originals()
    verify(read(ROOT/"native_freeze.json")["files"])
    old=ROOT/"src/benchmark.cpp"
    new=ROOT/"src/confirm.cpp"
    code=old.read_text()
    start=code.index("void formal(")
    a,s=code[:start],code[start:]
    a=a.replace("constexpr std::array<int,8> budgets{{160,176,184,192,200,256,320,400}};\n","")
    s=s.replace("    for (const int k:{1,100}) for (const int l:budgets) {","""    const int k=c.at("K"), focus=c.at("focus_L");
    const auto budgets=c.at("dense_L").get<std::vector<int>>();
    for (const int l:budgets) {
        std::vector<Arm> active{arms[0],arms[1],arms[2]};
        if (l==focus) active.push_back(arms[4]);""",1)
    s=s.replace("offset<arms.size()","offset<active.size()").replace("(rep?arms.size()-1-offset:offset))%arms.size()",
                "(rep?active.size()-1-offset:offset))%active.size()").replace("const auto& arm=arms[i];","const auto& arm=active[i];")
    s=s.replace("2*budgets.size()*arms.size()","3*budgets.size()+1").replace("4*budgets.size()*arms.size()","2*(3*budgets.size()+1)")
    s=s.replace('"PASS_E216_FORMAL"','"PASS_E216_DENSE"')
    assert "3*budgets.size()+1" in s and "const auto& arm=active[i];" in s
    with new.open("x") as handle: handle.write(a+s)
    binary=ROOT/"bin/confirm"
    argv=[str(new) if p.endswith("/src/benchmark.cpp") else str(binary) if p.endswith("/bin/benchmark") else p
          for p in read(ROOT/"bin/build.json")["argv"]]
    with (ROOT/"logs/confirm.compile.log").open("x") as log:
        subprocess.run(argv,cwd=REPO/"build",env=ENV,stdout=log,stderr=subprocess.STDOUT,check=True)
    files=[new,binary,ROOT/"confirmation.md",ROOT/"scripts/confirm.py",old]
    configs=[]
    for dataset,k,focus,ls in STUDY:
        c=read(ROOT/"configs"/f"{dataset}.formal.json")
        c.update(K=k,focus_L=focus,dense_L=ls,output_dir=str(ROOT/"data"/dataset/"confirm"))
        path=ROOT/"configs"/f"{dataset}.confirm.json"
        write(path,c)
        configs.append((path,c))
        files.append(path)
    freeze={str(p):identity(p,True) for p in files}
    write(ROOT/"confirm_freeze.json",{"files":freeze,"argv":argv})
    for path,c in configs:
        print("dense confirmation",c["dataset"],flush=True)
        with (ROOT/"logs"/f"{c['dataset']}.confirm.log").open("x") as log:
            subprocess.run(("taskset","-c","15",str(binary),"formal",str(path)),
                           env=ENV,stdout=log,stderr=subprocess.STDOUT,check=True)
        done=read(Path(c["output_dir"])/"complete.json")
        assert done["status"]=="PASS_E216_DENSE" and done["points"]==3*len(c["dense_L"])+1
    check_originals()
    verify(read(ROOT/"native_freeze.json")["files"])
    verify(freeze)
    points=sum(3*len(ls)+1 for _,_,_,ls in STUDY)
    write(ROOT/"confirm_complete.json",{"status":"PASS_E216_DENSE","points":points,"batches":2*points})


if __name__=="__main__":
    main()
