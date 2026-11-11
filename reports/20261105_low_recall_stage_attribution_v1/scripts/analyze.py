"""Post-hoc stage accounting from sealed per-query GT100 hit counts; no ANN."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import csv,json,hashlib
import numpy as np

W=Path(__file__).resolve().parents[3];R=Path(__file__).resolve().parents[1]
OLD=W/'reports/20261024_failure_rescue_residual_lt10_v2'
DATA=[('coco','COCO'),('flickr30k','Flickr30k'),('webvid2_5m_light_v1','WebVid'),('yandex_t2i_official10M_ip_v1','Yandex'),('deep10m_l2_v1','Deep10M'),('sift10m_bigann_l2_v1','SIFT10M'),('gist1m_l2_v1','GIST1M')]
LS=[100,128,200,400,800,1000,1200]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return list(csv.DictReader(p.open()))
def write(name,rows):
    with (R/'analysis'/name).open('w',newline='') as f:
        out=csv.DictWriter(f,list(rows[0]));out.writeheader();out.writerows(rows)
def dump(name,obj):(R/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def pct(a,b):return 100*a/b if b else None
points=read(OLD/'failure_by_L.csv');previous=read(OLD/'paired_rescue_by_L.csv')
pm={(x['dataset'],int(x['L']),x['method']):x for x in points}
cm={(x['dataset'],int(x['L']),x['comparison']):x for x in previous}
source=np.load(OLD/'per_query_hits.npz')
summary=[];paths=[];events=[];stages=[];original=[]
for ds,label in DATA:
    for L in LS:
        h={m:source[f'{ds}__{m}__L{L}'].astype(np.int16) for m in ['NSG','GT10','B32']}
        n=len(h['NSG']);lo={m:v<10 for m,v in h.items()};ns,gt,br=[lo[m] for m in ['NSG','GT10','B32']]
        code=ns.astype(int)*4+gt.astype(int)*2+br.astype(int)
        counts=np.bincount(code,minlength=8);assert sum(counts)==n
        for m in ['NSG','GT10','B32']:
            p=pm[ds,L,m];assert len(h[m])==int(p['n'])
            assert int(lo[m].sum())==int(p['low_count'])
            assert abs(float(h[m].mean())-float(p['recall_pct']))<1e-10
            original.append(dict(dataset=ds,label=label,L=L,method=m,n=n,low_count=int(lo[m].sum()),low_pct=pct(lo[m].sum(),n),recall_pct=p['recall_pct'],complete_qps=p['qps'],qps_min=p['qps_min'],qps_max=p['qps_max'],complete_us=1e6/float(p['qps'])))
        for i,count in enumerate(counts):paths.append(dict(dataset=ds,label=label,L=L,n=n,path=format(i,'03b'),low_NSG=int(bool(i&4)),low_GT10=int(bool(i&2)),low_B32=int(bool(i&1)),count=int(count)))
        for q in np.flatnonzero(ns|gt|br):events.append(dict(dataset=ds,label=label,L=L,query_row=int(q),NSG_hits=int(h['NSG'][q]),GT10_hits=int(h['GT10'][q]),B32_hits=int(h['B32'][q]),path=format(int(code[q]),'03b')))
        gfix=int((ns&~gt).sum());gnew=int((~ns&gt).sum());bfix=int((gt&~br).sum());bnew=int((~gt&br).sum())
        remaining=int((ns&br).sum());final_new=int((~ns&br).sum());total_net=int(ns.sum()-br.sum())
        summary.append(dict(dataset=ds,label=label,L=L,n=n,NSG_low=int(ns.sum()),GT10_low=int(gt.sum()),B32_low=int(br.sum()),NSG_low_pct=pct(ns.sum(),n),GT10_low_pct=pct(gt.sum(),n),B32_low_pct=pct(br.sum(),n),GT10_rescued=gfix,GT10_new_low=gnew,GT10_net_reduction=gfix-gnew,GT10_rescue_rate_pct=pct(gfix,ns.sum()),B32_rescued=bfix,B32_new_low=bnew,B32_net_reduction=bfix-bnew,B32_rescue_rate_pct=pct(bfix,gt.sum()),B32_rescued_NSG_legacy=int(counts[6]),B32_rescued_GT10_induced=int(counts[2]),GT10_rescue_relapsed_under_B32=int(counts[5]),NSG_original_final_rescued=int((ns&~br).sum()),NSG_original_final_unresolved=remaining,GT10_induced_final_unresolved=int(counts[3]),final_new_vs_NSG=final_new,combined_net_reduction=total_net,combined_net_reduction_pct_of_NSG_low=pct(total_net,ns.sum()),GT10_share_of_combined_net_reduction_pct=pct(gfix-gnew,total_net) if total_net>0 else None,B32_share_of_combined_net_reduction_pct=pct(bfix-bnew,total_net) if total_net>0 else None))
        assert int(ns.sum())-gfix+gnew==int(gt.sum())
        assert int(gt.sum())-bfix+bnew==int(br.sum())
        assert bfix==int(counts[6]+counts[2])
        assert int(br.sum())==remaining+final_new
        for name,a,b in [('GT10_vs_NSG','NSG','GT10'),('B32_vs_GT10','GT10','B32')]:
            af,bf=lo[a],lo[b];delta=h[b]-h[a];resc=int((af&~bf).sum());new=int((~af&bf).sum())
            prior=cm[ds,L,name]
            for key,v in [('reference_low_count',int(af.sum())),('result_low_count',int(bf.sum())),('exit_low_count',resc),('enter_low_count',new),('low_net_improved_count',int((af&(delta>0)).sum()))]:assert int(prior[key])==v,(ds,L,name,key)
            avg_delta=float(delta.mean());tail_net_pp=float(delta[af].sum())/n
            qa,qb=float(pm[ds,L,a]['qps']),float(pm[ds,L,b]['qps'])
            stages.append(dict(dataset=ds,label=label,L=L,n=n,stage=name,reference_low=int(af.sum()),result_low=int(bf.sum()),rescued=resc,new_low=new,net_reduction=resc-new,rescue_rate_pct=pct(resc,af.sum()),net_failure_rate_drop_pp=pct(resc-new,n),low_improved_count=int((af&(delta>0)).sum()),low_improved_still_low=int((af&bf&(delta>0)).sum()),mean_recall_gain_pp=avg_delta,net_recall_gain_from_reference_low_pp=tail_net_pp,net_recall_gain_from_other_queries_pp=avg_delta-tail_net_pp,reference_low_gross_rescued_members=prior['low_rescued_members'],all_gross_rescued_members=prior['total_rescued_members'],share_gross_rescued_members_from_low_pct=prior['share_rescued_members_from_low_pct'],reference_complete_qps=qa,result_complete_qps=qb,complete_qps_change_pct=(qb/qa-1)*100,complete_extra_us=1e6/qb-1e6/qa))

write('stage_attribution_all_datasets.csv',summary)
write('stage_attribution_four_multimodal.csv',[x for x in summary if x['dataset'] in dict(DATA[:4])])
write('three_stage_paths.csv',paths);write('low_query_transitions.csv',events)
write('stage_effects_and_costs.csv',stages);write('original_point_metrics.csv',original)
dump('analysis/analysis_receipt.json',dict(status='PASS_STAGE_ACCOUNTING_FROM_SEALED_HITS',datasets=7,primary_multimodal_datasets=4,L=LS,K=100,definition='GT100 hit count 0..9; exactly10 excluded',source_points=len(points),three_stage_groups=len(summary),paths=len(paths),paired_stage_rows=len(stages),query_L_groups=sum(x['n'] for x in summary),unique_queries=sum(len(source[f'{ds}__NSG__L100']) for ds,_ in DATA),per_query_transition_rows=len(events),all_count_conservation_checks=True,all_original_147_points_and_98_pairs_aligned=True,new_ANN=0,new_GT=0,new_timing=0,new_models=0,PDF=False))
print('PASS: 49 stage groups, 392 paths, 147 points and 98 comparisons aligned; no new experiments.')
