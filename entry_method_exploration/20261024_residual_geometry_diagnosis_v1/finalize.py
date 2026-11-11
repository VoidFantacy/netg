#!/usr/bin/env python3
"""Check delivery identities, cross-dataset ranks, and conditional effect arithmetic."""
from pathlib import Path
import ast
import csv
import hashlib
import json
import math
import re
import time

R=Path(__file__).resolve().parent
REPO=R.parents[1]
def rows(n):return list(csv.DictReader((R/f'analysis/{n}.csv').open()))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ranks(x):
    order=sorted(range(len(x)),key=lambda i:x[i]);out=[0.]*len(x);i=0
    while i<len(x):
        j=i+1
        while j<len(x) and x[order[j]]==x[order[i]]:j+=1
        for k in range(i,j):out[order[k]]=(i+j+1)/2
        i=j
    return out
def rho(x,y):
    a,b=ranks(x),ranks(y);am=sum(a)/len(a);bm=sum(b)/len(b)
    return sum((u-am)*(v-bm) for u,v in zip(a,b))/math.sqrt(sum((u-am)**2 for u in a)*sum((v-bm)**2 for v in b))

def main():
    t=time.time();ss=rows('dataset_summary');qm=rows('query_metrics');adjusted=rows('baseline_stratified_associations')
    checked=[]
    for c in rows('cross_dataset_associations'):
        actual=rho([float(s[c['feature']]) for s in ss],[float(s['K100_member_repair_pct']) for s in ss])
        assert abs(actual-float(c['spearman']))<1e-12
        checked.append(c['feature'])
    cond=0
    for s in ss:
        qq=[q for q in qm if q['dataset']==s['dataset']];n=len(qq)
        for feature in ['background_separation_z','GT100_mean_residual_frequency']:
            rk=ranks([float(q[feature]) for q in qq]);weighted=weight=0
            for lo,hi in [(1,4),(5,9),(10,49),(50,100)]:
                left=[];right=[]
                for r,q in zip(rk,qq):
                    miss=100-int(q['GT_K100_hits'])
                    if lo<=miss<=hi:(right if r>(n+1)/2 else left).append(int(q['K100_net_delta'])>0)
                if len(left)>=10 and len(right)>=10:
                    w=len(left)+len(right);weight+=w;weighted+=w*(sum(right)/len(right)-sum(left)/len(left))
            ref=next(v for v in adjusted if v['dataset']==s['dataset'] and v['feature']==feature)
            assert abs(100*weighted/weight-float(ref['standardized_delta_pp']))<1e-10
            assert weight==int(ref['included_incomplete_queries']);cond+=1
    docs={}
    for fn in ['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','AGENTS.md']:
        p=REPO/fn;before=R/'source_before'/fn
        assert p.read_bytes().endswith(before.read_bytes())
        docs[fn]={'before_sha256':digest(before),'current_sha256':digest(p),'old_entire_bytes_preserved':True}
    links=0
    for f in [R/'report_zh.md',R/'README.md',R/'protocol.md',REPO/'experiment_history/184_residual_geometry_diagnosis_v1.md']:
        for p in re.findall(r'\]\(([^)]+)\)',f.read_text()):
            if '://' in p or p.startswith('#'):continue
            assert (f.parent/p.split('#')[0]).resolve().exists(),(f,p);links+=1
    for f in R.glob('*.py'):ast.parse(f.read_text())
    rec=json.loads((R/'analysis/receipt.json').read_text());aud=json.loads((R/'analysis/integer_audit.json').read_text())
    assert rec['n_queries']==len(qm)==56000 and len(ss)==7 and len(aud['datasets'])==7
    assert rec['protocol_sha256']==digest(R/'protocol.md') and rec['analyzer_sha256']==digest(R/'analyze.py')
    assert aud['script_sha256']==digest(R/'audit_integers.py')
    assert sum(int(v['damaged_members']) for v in rows('all_L_and_router_sensitivity'))==5
    state={'status':'COMPLETED_OFFLINE_DIAGNOSIS_NO_DEFAULT_CHANGE','experiment':'E184','new_formal_performance_experiment':False,
        'latest_performance_evidence':'E183','n_queries':56000,'datasets':7,'new_ANN_calls':0,'new_GT_generation':0,'new_training':0,
        'default_changed':False,'automatic_next_experiments':False,'report':'report_zh.md',
        'costs_seconds':{'successful_diagnosis':rec['elapsed_seconds'],'integer_second_implementation':aud['elapsed_seconds'],
                        'failed_first_attempt':None,'failed_first_attempt_note':'not recorded; log preserved; not zero',
                        'rendering_and_documentation':None},
        'review_scope':'same executor, distinct integer and rank implementations; no independent reviewer',
        'finished_time_utc8':time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(time.time()+8*3600))}
    (R/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    validation={'status':'PASS','old_root_document_identity':docs,'local_report_links_checked':links,
        'cross_dataset_Spearman_separate_manual_rank_checks':checked,'separate_conditional_effect_checks':cond,
        'all_B32_sensitivity_damage_events_preserved':5,'visual_review':'both PNG figures viewed, labels legible; final coverage legend moved outside data',
        'elapsed_seconds':time.time()-t,'validation_scope':'integers, rank/conditioning arithmetic, source identities and delivery; not causal inference or new GT'}
    (R/'delivery_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
    manifest={str(p.relative_to(R)):{'bytes':p.stat().st_size,'sha256':digest(p)}
        for p in R.rglob('*') if p.is_file() and p.name!='delivery_manifest.json'}
    (R/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'PASS','queries':len(qm),'cross_rank_checks':len(checked),'conditional_checks':cond,
        'manifest_files':len(manifest)},ensure_ascii=False))

if __name__=='__main__':main()
