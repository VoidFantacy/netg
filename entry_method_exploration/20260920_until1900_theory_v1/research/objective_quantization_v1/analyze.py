import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
os.sched_setaffinity(0,{15})
from pathlib import Path
import json,csv,time,hashlib,shutil
import numpy as np
TB=Path(__file__).resolve().parents[1];E104=TB.parent/'20260920_query_representation_pilot_v1'
R=TB/'research/objective_quantization_v1';started=time.time()
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def write(p,rows):
    with Path(p).open('x') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
assert not R.exists();R.mkdir();shutil.copy2(__file__,R/'analyze.py');shutil.copy2(TB/'research/objective_quantization_protocol.md',R/'protocol.md')
cells=[];sources=[E104/'src/analyze_labels.py']
for ds in read(E104/'config.locked.json')['datasets']:
    for split,n in [('fit',2048),('cal',512)]:
        p=E104/'labels'/ds/(split+'_labels');paths={s:str(p/s) for s in ['k1.hits.u8','k100.hits.u8','teacher_mask.u8','baseline_slots.i32']}
        for path in paths.values():assert Path(path).exists();sources.append(Path(path))
        sources.append(E104/'results'/f'{split}_label_analysis.json');cells.append(dict(dataset=ds,split=split,n=n,paths=paths))
source_ids=[ident(p) for p in dict.fromkeys(sources)]
dump(R/'config.locked.json',dict(created_unix=time.time(),cells=cells,source_files=source_ids,
    analysis_source=ident(R/'analyze.py'),protocol=ident(R/'protocol.md'),threads=1,cpu=15,NSG_calls=0,new_training=0,
    historical_payload_exposed=True,new_statistics_frozen_before_calculation=True))
summary=[];all_rows=[];verified=0
for c in cells:
    n=c['n'];p=c['paths'];h1=np.fromfile(p['k1.hits.u8'],'u1').reshape(n,56).astype('i4');h100=np.fromfile(p['k100.hits.u8'],'u1').reshape(n,56).astype('i4')
    teacher=np.fromfile(p['teacher_mask.u8'],'u1').reshape(n,56).astype(bool);anchor=np.fromfile(p['baseline_slots.i32'],'<i4').reshape(n,2)[:,0]
    assert np.all((h1==0)|(h1==1)) and np.all((0<=h100)&(h100<=100)) and np.all(h100>=h1)
    score=100*h1+h100;assert np.array_equal(teacher,score==score.max(axis=1,keepdims=True))
    max1=h1.max(axis=1);max100=h100.max(axis=1);compatible=(h1==max1[:,None])&(h100==max100[:,None])
    joint100=np.where(h1==max1[:,None],h100,-1).max(axis=1)
    lex=(h1==max1[:,None])&(h100==joint100[:,None]);assert np.array_equal(teacher,lex)
    a1=h1[np.arange(n),anchor];a100=h100[np.arange(n),anchor]
    regret=max100-joint100;assert np.all(regret>=0)
    assert np.array_equal(regret>0,~compatible.any(axis=1))
    assert np.all((joint100>=a100)|(max1>a1))
    for i in range(n):
        target=max(zip(h1[i].tolist(),h100[i].tolist()))
        direct=[j for j in range(56) if (int(h1[i,j]),int(h100[i,j]))==target]
        assert direct==np.flatnonzero(teacher[i]).tolist();verified+=1
        all_rows.append(dict(dataset=c['dataset'],split=c['split'],query=i,anchor_hit1=int(a1[i]),anchor_hit100=int(a100[i]),
            max_hit1=int(max1[i]),max_hit100=int(max100[i]),joint_teacher_hit100=int(joint100[i]),
            conflict=int(regret[i]>0),K100_regret_hits=int(regret[i]),common_optimal_set_count=int(compatible[i].sum()),
            joint_teacher_set_count=int(teacher[i].sum())))
    s=dict(dataset=c['dataset'],split=c['split'],n=n,conflicting_queries=int((regret>0).sum()),
        conflict_pct=100*float((regret>0).mean()),K100_oracle_over_joint_teacher_pp=float(regret.mean()),
        K100_oracle_over_joint_teacher_max_pp=int(regret.max()),K1_oracle_over_joint_teacher_pp=0,
        anchor_R1_pct=100*float(a1.mean()),anchor_R100_pct=float(a100.mean()),
        joint_teacher_R1_pct=100*float(max1.mean()),joint_teacher_R100_pct=float(joint100.mean()),
        individual_K100_oracle_R100_pct=float(max100.mean()),
        joint_teacher_K1_harms_anchor=int((max1<a1).sum()),joint_teacher_K100_harms_anchor=int((joint100<a100).sum()),
        all_actions_same_K1_queries=int((h1.min(axis=1)==max1).sum()),all_actions_same_K100_queries=int((h100.min(axis=1)==max100).sum()))
    old=[x for x in read(E104/'results'/f'{c["split"]}_label_analysis.json')['datasets'] if x['dataset']==c['dataset']][0]
    for item in old['metrics']:
        value=s['joint_teacher_R1_pct'] if item['K']==1 else s['individual_K100_oracle_R100_pct']
        assert abs(item['finite_pool_oracle_recall']*100-value)<1e-9
    assert abs(old['selected_mean_utility_teacher_K100_harm_fraction']*n-s['joint_teacher_K100_harms_anchor'])<1e-9
    assert old['selected_mean_utility_teacher_K1_harm_fraction']==0
    summary.append(s)
write(R/'summary.csv',summary);write(R/'queries.csv',all_rows)
for x in source_ids:assert ident(x['path'])==x
assert time.time()-started<30
dump(R/'complete.json',dict(status='PASS',seconds=time.time()-started,query_rows=verified,teacher_masks_lexicographic_equal=True,
    original_oracle_and_harm_metrics_restored=True,source_files_checked=len(source_ids),NSG_calls=0,ANN_calls=0,new_GT=0,new_graphs=0,new_training=0,
    outputs=[ident(R/p) for p in ['summary.csv','queries.csv']],source=ident(R/'analyze.py'),default_changed=False))
print(json.dumps(dict(summary=summary,complete=read(R/'complete.json')),indent=2))
