from common import *
import itertools,math
allrows=[];cases=[]
for ds in ANCHORS:
 rr=list(csv.DictReader((R/f'analysis/{ds}.formal.csv').open()))
 for r in rr:
  for k in ['K','L','n','rescued','lost','net_members','improved_queries','damaged_queries']:r[k]=int(r[k])
  for k in list(r):
   if k not in ['dataset','method'] and not isinstance(r[k],int):r[k]=float(r[k])
 allrows+=rr
 for K in [1,100]:
  rows=[r for r in rr if r['K']==K];by={(r['method'],r['L']):r for r in rows};base=by['GT10',200];sq=by['REUSE-SQ',200];ideal=by['GATE-ORACLE',200];learn=by['GATE-LEARNED',200];off=by['GATE-OFF',200];ctrl=[r for r in rows if r['method']=='GT10'];b32=by['B32',200]
  for r in rows:
   cov=[g for g in ctrl if g['recall']>=r['recall']-1e-14 and g['qps']>=r['qps'] and (g['L']!=r['L'] or r['method']!='GT10')];rob=[g for g in cov if g['qps_min']>r['qps_max']];r['GT10_cover_L']=';'.join(str(g['L']) for g in cov);r['GT10_all3_cover_L']=';'.join(str(g['L']) for g in rob);r['B32_cover']=b32['recall']>=r['recall']-1e-14 and b32['qps']>=r['qps'] and r['method']!='B32'
  ci=[g for g in ctrl if g['recall']>=ideal['recall']-1e-14];cl=[g for g in ctrl if g['recall']>=learn['recall']-1e-14];gi=max(ci,key=lambda v:v['qps']) if ci else None;gl=max(cl,key=lambda v:v['qps']) if cl else None
  fit=[v for v in read(R/f'analysis/{ds}.fit.json') if v['K']==K][0]
  v=dict(dataset=ds,K=K,n=base['n'],main_recall=base['recall'],sq_recall=sq['recall'],sq_gain_pp=(sq['recall']-base['recall'])*100,sq_rescued=sq['rescued'],ideal_on_rate=ideal['on_rate'],learned_on_rate=learn['on_rate'],learned_gain_retained=learn['net_members']/sq['net_members'] if sq['net_members'] else None,ideal_qps=ideal['qps'],learned_qps=learn['qps'],sq_qps=sq['qps'],GT200_qps=base['qps'],ideal_speedup_vs_sq=ideal['qps']/sq['qps']-1,learned_speedup_vs_sq=learn['qps']/sq['qps']-1,off_minus_GT200_us=off['wall_us']-base['wall_us'],ideal_GT_cover=ideal['GT10_cover_L'],learned_GT_cover=learn['GT10_cover_L'],ideal_GT_all3_cover=ideal['GT10_all3_cover_L'],learned_GT_all3_cover=learn['GT10_all3_cover_L'],ideal_next_GT_L=gi['L'] if gi else None,ideal_next_GT_recall=gi['recall'] if gi else None,ideal_next_GT_qps=gi['qps'] if gi else None,learned_next_GT_L=gl['L'] if gl else None,learned_next_GT_recall=gl['recall'] if gl else None,learned_next_GT_qps=gl['qps'] if gl else None,selected_kind=fit['selected_kind'],selected_nf=fit['selected_nf'],cal_gain_retained=fit['cal_learned_net_gain']/fit['cal_net_gain'] if fit['cal_net_gain'] else None,cal_learned_on_rate=fit['cal_learned_on_rate'],cal_action_us=fit['cal_cost_us'],cal_oracle_action_us=fit['cal_oracle_action_us'],cal_learned_action_us=fit['cal_learned_action_us'])
  v.update(learned_B32_cover=learn['B32_cover'],ideal_B32_cover=ideal['B32_cover'],learned_combined_cover=bool(learn['GT10_cover_L']) or learn['B32_cover'],ideal_combined_cover=bool(ideal['GT10_cover_L']) or ideal['B32_cover'])
  cases.append(v)
csvwrite(R/'analysis/formal_points.csv',allrows);dump(R/'analysis/case_summary.json',cases);csvwrite(R/'analysis/case_summary.csv',cases)
# Development labels, timing distributions and native-vs-Python feature reconstruction.
costrows=[]
for ds in ANCHORS:
 c=read(R/f'configs/{ds}.dev.json');q=np.asarray(view(c['queries']),dtype=np.float64);n=len(q)
 for K in [1,100]:
  p=Path(c['output_dir'])/f'k{K}';bd=arr(p/'GT10_L200/raw/distances.f32','<f4').reshape(n,K);prof=arr(p/'GT10_L200/raw/profile_distances.f32','<f4').reshape(n,3);z=np.sort(prof.astype(float),axis=1);span=z[:,2]-z[:,0];gap=bd[:,-1].astype(float)-bd[:,0];X=np.c_[z[:,0],z[:,1]-z[:,0],span,(q*q).sum(1),span/(1+abs(z[:,0])),bd[:,0],bd[:,K//4],bd[:,K//2],bd[:,3*K//4],bd[:,-1],gap,gap/(1+abs(bd[:,0].astype(float)))];native=arr(p/'features.f64','<f8').reshape(n,12);assert np.allclose(X,native,rtol=2e-13,atol=1e-10);cs=arr(p/'completion_cost_us.f64','<f8').reshape(3,n);med=np.median(cs,axis=0);y=arr(p/'net_gain.f64','<f8')
  for name,s in [('fit',slice(0,2000)),('cal',slice(2000,4000))]:
   a=med[s];yy=y[s];costrows.append(dict(dataset=ds,K=K,role=name,n=len(a),mean_us=float(a.mean()),p10_us=float(np.quantile(a,.1)),p50_us=float(np.median(a)),p90_us=float(np.quantile(a,.9)),oracle_action_mean_us=float((a*(yy>0)).mean()),positive_gain_queries=int((yy>0).sum()),net_gain=int(yy.sum())))
csvwrite(R/'analysis/action_cost.csv',costrows);dump(R/'reviews/feature_audit.json',dict(status='PASS_NATIVE_FEATURES_VS_NUMPY_ALL_24000_DEV_QUERY_CASES',cases=24000))
print(json.dumps(cases,ensure_ascii=False,indent=2))
