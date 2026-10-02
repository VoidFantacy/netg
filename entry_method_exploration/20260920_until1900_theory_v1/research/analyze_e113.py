import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
os.sched_setaffinity(0,{15})
from pathlib import Path
import json,time,hashlib,struct,csv
import numpy as np
R=Path(__file__).resolve().parents[1];started=time.time()
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def write(p,rows):
 with Path(p).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def vectors_in_nsg(path,n,d):
 with Path(path).open('rb') as f:
  def rd(fmt):return struct.unpack('<'+fmt,f.read(struct.calcsize('<'+fmt)))
  version,nn,dd,metric,trained,built,build=rd('iqii??c');assert version in (1,2) and nn==n and dd==d and metric==0 and trained and built
  rd('ffffiiiiiq')
  for _ in range(2):count,=rd('Q');assert count==n;f.seek(count*4,1)
  width,count=rd('iQ');assert count==n*width;f.seek(count*4,1)
  count,=rd('Q');assert count==n*d;offset=f.tell()
 return np.memmap(path,mode='r',dtype='<f4',offset=offset,shape=(n,d))
cfg=read(R/'config.locked.json');assert read(R/'reviews/trace_complete.json')['status']=='PASS';assert not (R/'reviews/numeric_verification.json').exists();assert sha(__file__)==read(R/'reviews/analysis_lock.json')['source']['sha256'];gate_cfg=cfg['feature_gate'];summaries=[];decisions=[];raw=[];verified_rows=0
for ds,c in cfg['datasets'].items():
 p=R/'results'/ds;n=c['n'];off=np.fromfile(p/'pair_offsets.u64','<u8');keys=np.fromfile(p/'pair_keys.u64','<u8');codes=np.fromfile(p/'pair_codes.u8','u1');total=np.fromfile(p/'total_comparisons.u64','<u8');valid=np.fromfile(p/'valid_comparisons.u64','<u8');gt=np.fromfile(c['GT1'],'<i4');assert gt.shape==(n,)
 assert off.shape==(n*2+1,) and off[0]==0 and off[-1]==len(keys)==len(codes);assert np.all(off[1:]>=off[:-1]);assert total.shape==valid.shape==(n*2,) and np.all(total>=valid) and np.all(valid>=np.diff(off));assert np.all((codes&7)>0) and np.all((codes>>3)>0)
 low=keys>>32;high=keys&np.uint64(0xffffffff);assert np.all(low<high) and np.all(high<c['base_n']);del low,high
 for row in range(n*2):
  x=keys[int(off[row]):int(off[row+1])];assert np.all(x[1:]>x[:-1]);verified_rows+=1
 for K in [1,100]:
  for suffix,field in [('ids.i32','ids'),('distances.f32','distances'),('ndc.u64','ndc')]:assert sha(p/f'k{K}.{suffix}')==sha(c['expected'][str(K)][field])
 for f in p.iterdir():
  if f.is_file():raw.append(ident(f))
 qid=np.repeat(np.arange(n*2,dtype='u2')//2,np.diff(off).astype('i8'));order=np.argsort(keys,kind='stable');sk=keys[order];sq=qid[order];sc=codes[order]&7;del keys,codes,qid,order
 boundary=np.empty(len(sk),dtype=bool);boundary[0]=True;boundary[1:]=(sk[1:]!=sk[:-1])|(sq[1:]!=sq[:-1]);qstarts=np.flatnonzero(boundary);del boundary
 pk=sk[qstarts];pq=sq[qstarts];pb=np.bitwise_or.reduceat(sc,qstarts);del sk,sq,sc,qstarts
 boundary=np.empty(len(pk),dtype=bool);boundary[0]=True;boundary[1:]=pk[1:]!=pk[:-1];starts=np.flatnonzero(boundary);del boundary
 pair_keys=pk[starts];ends=np.r_[starts[1:],len(pk)];counts=ends-starts;pos=np.add.reduceat((pb==1).astype('u8'),starts);neg=np.add.reduceat((pb==2).astype('u8'),starts)
 assert np.all(pos+neg<=counts) and np.all(counts<=n);eligible_index=np.flatnonzero((counts>=gate_cfg['min_query_support'])&(pos>=gate_cfg['min_positive_distinct_GT1'])&(neg>=gate_cfg['min_negative_distinct_GT1']))
 base=vectors_in_nsg(c['index'],c['base_n'],c['dimension']);eligible=[];zero_vectors=0
 for index in eligible_index:
  sl=slice(int(starts[index]),int(ends[index]));qq=pq[sl];bb=pb[sl];gpos=len(np.unique(gt[qq[bb==1]]));gneg=len(np.unique(gt[qq[bb==2]]))
  if gpos<gate_cfg['min_positive_distinct_GT1'] or gneg<gate_cfg['min_negative_distinct_GT1']:continue
  key=int(pair_keys[index]);a=key>>32;b=key&0xffffffff;diff=base[a].astype('f8')-base[b].astype('f8');norm=float(np.linalg.norm(diff));assert np.isfinite(norm)
  if norm==0:zero_vectors+=1;continue
  eligible.append(dict(pair_index=int(index),key=key,low_id=a,high_id=b,query_support=int(counts[index]),positive_query_support=int(pos[index]),negative_query_support=int(neg[index]),positive_distinct_GT1=gpos,negative_distinct_GT1=gneg,difference_norm=norm))
 eligible.sort(key=lambda x:(-min(x['positive_distinct_GT1'],x['negative_distinct_GT1']),-x['query_support'],x['key']));selected=eligible[:gate_cfg['dictionary_size']];seen=np.zeros(n,dtype=bool);vectors=[];selected_rows=[];disagreements=0;observed_strict=0;support_rows=[];q=np.fromfile(c['queries'],'<f4').reshape(n,c['dimension']).astype('f8')
 for rank,item in enumerate(selected):
  j=item['pair_index'];sl=slice(int(starts[j]),int(ends[j]));qq=pq[sl];bb=pb[sl];seen[qq]=True;v=base[item['low_id']].astype('f8')-base[item['high_id']].astype('f8');vectors.append((v/item['difference_norm']).astype('<f4'));score=q[qq]@v;symbol=np.where(score>0,1,np.where(score<0,2,4));strict=(bb==1)|(bb==2);bad=(symbol!=bb)&strict;disagreements+=int(bad.sum());observed_strict+=int(strict.sum());selected_rows.append(dict(rank=rank,**{k:v for k,v in item.items() if k!='pair_index'},float64_feature_sign_disagreements=int(bad.sum()),recorded_strict_queries=int(strict.sum())))
  support_rows.extend(dict(rank=rank,query=int(qqi),GT1=int(gt[qqi]),actual_comparison_sign_bits=int(bit),float64_difference_score=float(value)) for qqi,bit,value in zip(qq,bb,score))
 out=p/'support_analysis';out.mkdir();np.asarray(vectors,dtype='<f4').reshape(len(selected),c['dimension']).tofile(out/'selected_difference_directions.f32')
 dump(out/'eligible_pairs.json',eligible);dump(out/'selected_pairs.json',selected_rows)
 if support_rows:write(out/'selected_pair_query_support.csv',support_rows)
 histogram=[dict(query_support=int(value),number_of_pairs=int(freq)) for value,freq in zip(*np.unique(counts,return_counts=True))];write(out/'pair_support_histogram.csv',histogram)
 summary=dict(dataset=ds,fit_queries=n,total_comparison_calls=int(total.sum()),valid_comparison_calls=int(valid.sum()),unique_query_action_pair_records=int(off[-1]),unique_query_pair_records=len(pk),distinct_graph_node_pairs=len(pair_keys),single_query_pairs=int((counts==1).sum()),single_query_pair_fraction=float((counts==1).mean()),query_support_median=float(np.median(counts)),query_support_p99=float(np.quantile(counts,.99)),query_support_max=int(counts.max()),pairs_with_support_at_least_32=int((counts>=32).sum()),pairs_preeligible_by_query_sign_counts=len(eligible_index),zero_difference_preeligible_pairs=zero_vectors,eligible_pairs=len(eligible),selected_pairs=len(selected),selected_recorded_query_coverage_pct=100*float(seen.mean()),mixed_or_zero_sign_query_pairs=int(((pb!=1)&(pb!=2)).sum()),opposite_sign_same_query_pairs=int(((pb&1>0)&(pb&2>0)).sum()),selected_float64_feature_sign_disagreements=disagreements,selected_recorded_strict_queries=observed_strict)
 clauses=dict(at_least_32_eligible=len(eligible)>=gate_cfg['dictionary_size'],selected_query_coverage_at_least_half=bool(seen.mean()>=gate_cfg['min_query_coverage']));decisions.append(dict(dataset=ds,clauses=clauses,pass_all=all(clauses.values())));summaries.append(summary);dump(out/'summary.json',summary)
 del pk,pq,pb,pair_keys,starts,ends,counts,pos,neg,base,q
 assert time.time()-started<900
status='PASS_SHARED_COMPARISONS_NEEDS_PREDICTIVITY_GATE' if all(x['pass_all'] for x in decisions) else 'STOP_EXACT_PAIR_FEATURE_DICTIONARY'
gate=dict(status=status,datasets=decisions,heuristic_support_gate=True,predictive_utility_gain_proven=False,new_training=0,new_ANN=0,new_GT=0,new_graphs=0,default_changed=False)
write(R/'results/shared_support.csv',summaries);dump(R/'results/gate.json',gate);dump(R/'reviews/numeric_verification.json',dict(status='PASS',raw_files=raw,all_8192_query_action_rows_sorted_unique=verified_rows==8192,historical_selected_output_SHA_parity=True,all_queries_retained=True,analysis_source=ident(__file__),seconds=time.time()-started));dump(R/'state.json',dict(status='SUPPORT_ANALYSIS_COMPLETE',decision=status,pending=['interpretation','stage closeout']));dump(R/'reviews/analysis_complete.json',dict(status='PASS',seconds=time.time()-started,gate=gate,source=ident(__file__)));print(json.dumps(dict(gate=gate,summaries=summaries,seconds=time.time()-started),ensure_ascii=False,indent=2))
