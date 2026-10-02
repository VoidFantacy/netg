import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key]="8"
os.sched_setaffinity(0,set(range(8)))
import hashlib
import importlib.util
import json
import time
from pathlib import Path
import numpy as np

OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("directional_source",OUT.parent/"directional_error_v1/analyze.py")
old=importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
METHODS=["UniformReplacement","UnbiasedCorrection","ExactSubset","ShrinkOracle"]


def geometry(vhat, truth):
    norms=np.linalg.norm(truth,axis=1); p=truth/norms[:,None]
    norms_hat=np.linalg.norm(vhat,axis=1)
    assert norms_hat.min()>1e-12
    pp=vhat/norms_hat[:,None]
    e=vhat-truth; alpha=np.sum(e*p,axis=1)
    tangent=e-alpha[:,None]*p
    chord2=np.sum((pp-p)**2,axis=1)
    angle=np.degrees(np.arccos(np.clip(np.sum(pp*p,axis=1),-1,1)))
    return {"chord2_sum":float(chord2.sum()),"chord2_mean":float(chord2.mean()),
        "angle_degrees_quantiles":np.quantile(angle,[0,.5,.9,.99,1]).tolist(),
        "tangent_risk":float(np.sum(np.sum(tangent*tangent,axis=1)/norms**2)),
        "nonpositive_radial_hubs":int(np.sum(norms+alpha<=0)),
        "minimum_resultant_norm":float(norms_hat.min()),
        "minimum_radial_ratio":float(np.min((norms+alpha)/norms))},chord2,angle


def gt1_gaps(dataset,hub):
    c=old.CONFIG["datasets"][dataset]["original"]
    d=c["dimension"]
    raw=np.memmap(c["base"],"<f4",mode="r").reshape(-1,d+1)
    exact=np.fromfile(c["fit_source"]["gt_file"],"<i8").reshape(20000,100)
    target=old.unit(np.array(raw[exact[:,0],1:],dtype="f4"))
    gaps=[]
    for lo in range(0,20000,4096):
        scores=target[lo:lo+4096]@hub.astype("f4").T
        top=np.partition(scores,-2,axis=1)[:,-2:]
        gaps.extend((top.max(1)-top.min(1)).astype("f8"))
    return np.array(gaps)


def main():
    started=time.perf_counter()
    for part in ["results","reviews"]:(OUT/part).mkdir(exist_ok=True)
    assert not (OUT/"results/summary.json").exists()
    protected={str(p):old.identity(p) for p in [Path(__file__),OUT/"protocol.md",OUT/"theory.md",old.OUT/"results/summary.json"]}
    old.dump(OUT/"reviews/frozen.json",{"unix":time.time(),"files":protected,
        "upstream_freeze":str(old.OUT/"reviews/frozen.json"),"m":2048,"replications":16})
    reference=json.loads((old.OUT/"results/summary.json").read_text())
    records={}
    for ds_index,ds in enumerate(old.CONFIG["datasets"]):
        t0=time.perf_counter(); q,h,a,b=old.reconstruct(ds)
        n=len(q); m=2048; f=m/n
        v=h+a.T@q; vp=h+b.T@q; delta=a-b
        prior=np.load(old.OUT/"results"/(ds+".npz"))
        assert np.max(np.abs(v-prior["v"]))<1e-9 and np.max(np.abs(vp-prior["vp"]))<1e-9
        baseline,baseline_chord,_=geometry(vp,v)
        B=reference["datasets"][ds]["tangent_bias"]
        V=reference["datasets"][ds]["tangent_variance"]
        variance=n*(1-f)*V/f
        gamma=B/(B+variance)
        gaps=gt1_gaps(ds,h) if ds.startswith("web") else None
        if gaps is not None:
            full_temperature=max(float(np.median(gaps)),1e-4)
            saved_temp=json.loads((old.E125/"models"/ds/"profiles.json").read_text())["temperature"]
            assert full_temperature==saved_temp,(full_temperature,saved_temp)
        else:full_temperature=None
        all_rows=[]; all_records=[]; all_chord=[]; all_angle=[]
        for rep in range(16):
            seed=2026093002+ds_index+1000*rep
            selected=np.random.default_rng(seed).permutation(n)[:m]
            correction=delta[selected].T@q[selected]
            sums={"UniformReplacement":vp+correction,
                  "UnbiasedCorrection":vp+(n/m)*correction,
                  "ExactSubset":h+(n/m)*(a[selected].T@q[selected]),
                  "ShrinkOracle":vp+gamma*(n/m)*correction}
            record={"rep":rep,"seed":seed,"selected_sha256":hashlib.sha256(selected.astype('<i4').tobytes()).hexdigest(),
                    "correction_sum_sha256":hashlib.sha256(correction.tobytes()).hexdigest(),"methods":{}}
            cc=[]; angles=[]
            for name in METHODS:
                item,chord,angle=geometry(sums[name],v)
                item["chord_risk_ratio_to_approx"]=item["chord2_sum"]/baseline["chord2_sum"]
                item["tangent_risk_ratio_to_approx"]=item["tangent_risk"]/B
                item["hubs_chord_better_than_approx"]=int(np.sum(chord<baseline_chord))
                record["methods"][name]=item; cc.append(chord); angles.append(angle)
            if gaps is not None:
                record["pilot_temperature"]=max(float(np.median(gaps[selected])),1e-4)
                record["pilot_temperature_relative_error"]=record["pilot_temperature"]/full_temperature-1
            all_rows.append(selected); all_records.append(record); all_chord.append(cc); all_angle.append(angles)
        aggregates={}
        for name in METHODS:
            ratios=np.array([r["methods"][name]["chord_risk_ratio_to_approx"] for r in all_records])
            tangent=np.array([r["methods"][name]["tangent_risk_ratio_to_approx"] for r in all_records])
            aggregates[name]={"chord_ratio_mean":float(ratios.mean()),"chord_ratio_min":float(ratios.min()),
                "chord_ratio_max":float(ratios.max()),"seeds_improved":int(np.sum(ratios<1)),
                "tangent_ratio_mean":float(tangent.mean()),"seed0_chord_ratio":float(ratios[0]),
                "seeds_with_radial_flip":sum(r["methods"][name]["nonpositive_radial_hubs"]>0 for r in all_records)}
        record={"n":n,"m":m,"replications":16,"baseline":baseline,
            "theory":{"B":B,"V":V,"uniform_replacement_expected_tangent_ratio":((1-f)**2*B+n*f*(1-f)*V)/B,
                      "unbiased_expected_tangent_ratio":variance/B,"shrink_oracle_gamma":gamma,
                      "shrink_oracle_expected_tangent_ratio":((1-gamma)**2*B+gamma**2*variance)/B},
            "aggregates":aggregates,"all_replications":all_records,"full_temperature":full_temperature,
            "seconds":time.perf_counter()-t0}
        if gaps is not None:
            temps=np.array([r["pilot_temperature"] for r in all_records])
            record["pilot_temperature_range"]=[float(temps.min()),float(temps.max())]
        records[ds]=record
        np.savez_compressed(OUT/"results"/(ds+".npz"),selected_rows=np.array(all_rows,dtype='<i4'),
            chord2=np.array(all_chord),angle_degrees=np.array(all_angle),baseline_chord2=baseline_chord,
            gt1_gaps=gaps if gaps is not None else np.empty(0))
        print(ds,{"aggregates":aggregates,"theory":record["theory"],"full_temperature":full_temperature,
                  "pilot_temperature_range":record.get("pilot_temperature_range")},flush=True)
        assert time.perf_counter()-started<300
    for path,expected in protected.items():assert old.identity(path)==expected,path
    old.dump(OUT/"results/summary.json",{"status":"COMPUTED_PENDING_AUDIT","datasets":records,
        "seconds":time.perf_counter()-started,"methods":METHODS,"new_GT":0,"new_searches":0,
        "new_candidate_profiles_exported":0,"new_performance_points":0,
        "profile_vectors_in_memory_only":128,"selection":"fixed seed0 for any next candidate, never best seed"})
    print("COMPUTED",round(time.perf_counter()-started,3),flush=True)


if __name__=="__main__":main()
