"""Build the fit-only PCA and omission/cache banks used by the native benchmark."""
from collections import defaultdict
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
E215=ROOT.parent/"20261121_b32_cross_budget_tails_v1"
E214=ROOT.parent/"20261121_b32_batch4_scoring_v1"
E212=ROOT.parent/"20261120_gt10_nsg_b32_four_way_v1"
sys.dont_write_bytecode=True
sys.path.append(str(E214/"scripts"))
from run import identity, read, verify, write
import numpy as np

DATASETS=("coco","webvid2_5m_light_v1")
DIM=64
N, PUBLIC_N=16000, 3072
LS=(160,176,184,192,200,256,320,400)
METHODS=("GT10","B32","B32-fit","VOTE","CACHE")


def save_lists(path, lists):
    offsets=np.cumsum([0,*map(len,lists)],dtype=np.uint64)
    np.asarray(offsets,"<u8").tofile(path+".offsets.u64")
    np.fromiter((p for row in lists for p in row),dtype="<i4",count=int(offsets[-1])).tofile(path+".ids.i32")
    return int(offsets[-1])


def model(conf, dest):
    start=time.monotonic()
    roles=np.fromfile(conf["roles"],"i1")
    groups=np.fromfile(conf["identity_groups"],"<i4")
    fit=np.flatnonzero(roles==0)
    held=np.flatnonzero(roles>0)
    assert len(roles)==N==len(groups)
    assert not set(groups[fit]).intersection(groups[held])
    q=conf["train_queries"]
    train=np.memmap(q["path"],"<f4","r").reshape(-1,q["d"])[fit]
    norm=np.linalg.norm(train,axis=1)
    assert np.all(np.isfinite(norm)&(norm>0))
    unit=np.ascontiguousarray(train/norm[:,None],dtype="<f4")
    basis=np.linalg.eigh(unit.astype(np.float64).T@unit.astype(np.float64))[1][:,-DIM:][:,::-1]
    axes=np.ascontiguousarray(basis.T,dtype="<f4")
    projected=unit@axes.T
    projected=projected/np.linalg.norm(projected,axis=1)[:,None]
    unit.tofile(dest/"unit.f32")
    axes.tofile(dest/"axes.f32")
    projected.astype("<f4").tofile(dest/"projected.f32")
    np.asarray(fit,"<i4").tofile(dest/"fit_rows.i32")
    np.asarray(held,"<i4").tofile(dest/"held_rows.i32")
    p=Path(conf["packets"]["100"]["low"])/"ids.i32"
    actual=np.memmap(p,"<i4","r").reshape(N,100)[fit]
    truth=np.memmap(conf["train_gt"]["path"],"<i8","r").reshape(-1,100)[fit]
    omissions=[sorted(set(map(int,g))-set(r)) for g,r in zip(truth,actual)]
    count=save_lists(str(dest/"omissions"),omissions)
    cache=[]
    for start_row in range(0,len(fit),128):
        stop=min(start_row+128,len(fit))
        score=unit[start_row:stop]@unit.T
        score[np.arange(stop-start_row),np.arange(start_row,stop)]=np.inf
        nearby=np.argsort(-score,kind="stable",axis=1)[:,:16]
        for ns in nearby:
            votes=defaultdict(float)
            for rank,i in enumerate(ns,1):
                for cid in omissions[i]:
                    votes[cid]+=1/rank
            cache.append(sorted(votes,key=lambda p:(-votes[p],p))[:96])
    cached_count=save_lists(str(dest/"cache"),cache)
    return {"dimension":q["d"],"projection_dim":DIM,"fit_queries":len(fit),"held_queries":len(held),
        "omission_IDs":count,"cached_IDs":cached_count,"prep_wall_seconds":time.monotonic()-start}


def main():
    old=read(E215/"input_freeze.json")["files"]
    verify(old)
    public=read(E212/"input_freeze.json")["files"]
    gt=read(E212/"gt_eval.json")
    involved={}
    for name in ("AGENTS.md","LOCAL_CODEX_START.md","summary.md","spec.md","s-target.md",
                 "s-experiment.md","experiment_history/README.md"):
        dest=ROOT/"source_before"/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        assert not dest.exists(),dest
        shutil.copyfile(REPO/name,dest)
    for ds in DATASETS:
        train_cfg=read(E215/"configs"/(ds+".json"))
        pub_cfg=read(E212/"configs"/(ds+".json"))
        assert all(pub_cfg[name]==train_cfg[name] for name in ("index","base","metric_id","dataset"))
        assert pub_cfg["threads"]==1 and pub_cfg["cpu"]==15 and pub_cfg["queries"]["n"]==PUBLIC_N
        for p in [pub_cfg["queries"]["path"],pub_cfg["table"],gt[ds]["path"]]+list(
                 pub_cfg["router"][x] for x in ("ids","W","graph")):
            involved[p]=public[p]
        dest=ROOT/"models"/ds
        dest.mkdir()
        receipt=model(train_cfg,dest)
        print(ds,receipt,flush=True)
        write(dest/"prepare.json",receipt)
        train_cfg.update(model_dir=str(dest),output_dir=str(ROOT/"data"/ds/"heldout"))
        pub_cfg.update(model_dir=str(dest),fit_table=train_cfg["anchor_table"],output_dir=str(ROOT/"data"/ds/"formal"))
        write(ROOT/"configs"/f"{ds}.heldout.json",train_cfg)
        write(ROOT/"configs"/f"{ds}.formal.json",pub_cfg)
    verify(involved)
    write(ROOT/"gt_eval.json",{d:gt[d] for d in DATASETS})
    write(ROOT/"prepare_freeze.json",{"files":{**involved,**{str(p):identity(p,True)
            for p in (*sorted((ROOT/"models").glob("*/*")),*sorted((ROOT/"configs").glob("*.json")),
                      ROOT/"gt_eval.json",ROOT/"protocol.md",ROOT/"scripts/prepare.py")}},
            "inherited_train_manifest":str(E215/"input_freeze.json"),"public_GT_for_model":False})


if __name__=="__main__":
    main()
