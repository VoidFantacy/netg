"""Seal verified E216 runs and input identities."""
import csv

from prepare import DATASETS,E212,E215,ROOT,read,verify,write
from run import digest


def main():
    q=read(ROOT/"formal_complete.json")
    assert q["status"]=="PASS_E216_FORMAL"
    dense=read(ROOT/"confirm_complete.json")
    assert dense=={"status":"PASS_E216_DENSE","points":59,"batches":118}
    assert read(ROOT/"analysis/dense_decision.json")["exact_primary_packets"]==23
    assert read(ROOT/"reviews/independent_audit.json")["status"]=="PASS_E216_STDLIB_AUDIT"
    for root,name in ((ROOT,"prepare_freeze.json"),(ROOT,"native_freeze.json"),
                      (ROOT,"confirm_freeze.json"),(E215,"input_freeze.json")):
        verify(read(root/name)["files"])
    with (ROOT/"analysis/rounds.csv").open() as f:
        rounds=list(csv.DictReader(f))
    assert len(rounds)==320 and all(int(r["cpu"])==15 and int(r["threads"])==1 for r in rounds)
    with (ROOT/"analysis/dense_rounds.csv").open() as f:
        extra=list(csv.DictReader(f))
    assert len(extra)==118 and all(int(r["cpu"])==15 and int(r["threads"])==1 for r in extra)
    state={"status":"SEALED_E216_NEIGHBOR_RESIDUAL_ONLINE","datasets":DATASETS,
           "points":q["points"],"batches":q["batches"],"query_calls":q["query_calls"],
           "timed_wall_seconds":sum(float(r["seconds"]) for r in rounds),
           "dense_confirmation":dense,"dense_wall_seconds":sum(float(r["seconds"]) for r in extra),
           "pending_experiment_queue":False,"report":"report.md"}
    write(ROOT/"state.json",state)
    files={str(p.relative_to(ROOT)):{"bytes":p.stat().st_size,"sha256":digest(p)}
           for p in sorted(ROOT.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
    shared=(E212/"scripts/analyze.py",E212/"scripts/audit.py",E215/"analysis/neighbor_source.csv")
    write(ROOT/"seal.json",{"status":"SEALED_E216","experiment_files":files,
                            "external_analysis":{str(p):digest(p) for p in shared}})
    print("sealed",len(files),"experiment files")


if __name__=="__main__":
    main()
