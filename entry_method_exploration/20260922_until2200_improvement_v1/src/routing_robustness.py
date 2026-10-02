from pathlib import Path
import numpy as np,json,hashlib,time
P=Path(__file__).resolve().parents[1];records={};files={};t=time.perf_counter()
for label,ds,out,L in [('Web old','webvid2_5m_light_v1',P/'stages/e125_approximate_target_profiles_v1/results/webvid2_5m_light_v1/evaluation',1000),('Y old','yandex_t2i_official10M_ip_v1',P/'stages/e125_approximate_target_profiles_v1/results/yandex_t2i_official10M_ip_v1/evaluation',128),('Web fresh','webvid2_5m_light_v1',P/'stages/e125_web_fresh_check_v1/results/evaluation',1000)]:
 name='GT10-soft-t1' if ds.startswith('web') else 'GT10-hard';A=out/'k1'/f'{name}_L{L}';B=out/'k1'/f'ApproxTarget10_L{L}'
 for D in [A,B]:
  for f in ['entry_ids.i32','ids.i32']:
   p=D/f;files[str(p.relative_to(P))]=hashlib.sha256(p.read_bytes()).hexdigest()
 a=np.fromfile(A/'entry_ids.i32','<i4').reshape(-1,3);b=np.fromfile(B/'entry_ids.i32','<i4').reshape(-1,3);ia=np.fromfile(A/'ids.i32','<i4');ib=np.fromfile(B/'ids.i32','<i4');same=np.all(a==b,axis=1);assert np.all(ia[same]==ib[same]);common=(a[:,:,None]==b[:,None,:]).any(2).sum(1)
 # Independent Python set/list check of every row, no refit or search.
 independent=[len(set(x.tolist())&set(y.tolist())) for x,y in zip(a,b)];assert independent==common.tolist();assert sum(x==y for x,y in zip(a.tolist(),b.tolist()))==int(same.sum())
 records[label]={'n':len(a),'L':L,'same_ordered_three_entries':int(same.sum()),'entry_set_changed':int((~same).sum()),'same_return_ID':int((ia==ib).sum()),'different_return_ID':int((ia!=ib).sum()),'entry_intersection_0_1_2_3':[int((common==j).sum()) for j in range(4)],'same_entries_same_result':True}
result={'status':'PASS_DESCRIPTIVE_POSTHOC','records':records,'inputs_sha256':files,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'seconds':time.perf_counter()-t,'new_searches':0,'new_candidate_training':0,'new_performance_points':0,'scope':'existing frozen output/entry arrays only; descriptive, not a subgroup selection rule or path trace'};p=P/'reviews/routing_robustness_summary.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(records,indent=2))
