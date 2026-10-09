"""Root-only independent incremental replay of all frozen TRAIN greedy choices.

Uses token-to-edge gain decrements, rather than the compiler's lazy incidence
recount. It does not choose a replacement table or read SELECT/CAL/confirmation.
"""
from pathlib import Path
import hashlib, heapq, json, sys, time
import numpy as np

R=Path(__file__).resolve().parents[1]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def replay(routes,gt,lo1,lo100,labels,log):
 slots={int(label):slot for slot,label in enumerate(labels)}
 assert len(slots)==len(labels)
 token_weights=[];token_edges=[];edges={};gains={}
 for i in range(len(gt)):
  actual_slots=sorted({slots[int(label)] for label in routes[i]})
  r1=set(map(int,lo1[i]));r100=set(map(int,lo100[i]));first=int(gt[i,0])
  for target in map(int,gt[i]):
   weight=int(target not in r100)+100*int(target==first and target not in r1)
   if not weight:continue
   token=len(token_weights);pairs=[(slot,target) for slot in actual_slots]
   token_weights.append(weight);token_edges.append(pairs)
   for pair in pairs:
    edges.setdefault(pair,[]).append(token);gains[pair]=gains.get(pair,0)+weight
 heap=[(-gain,*pair) for pair,gain in gains.items()];heapq.heapify(heap)
 covered=bytearray(len(token_weights));selected=set();counts=[0]*len(labels);rows=[[] for _ in labels];objective=0
 def next_choice():
  while heap:
   negative,slot,target=heapq.heappop(heap);pair=(slot,target)
   if pair in selected or counts[slot]>=8 or -negative!=gains[pair]:continue
   if negative>=0:return None
   return slot,target,-negative
  return None
 for position,item in enumerate(log):
  expected=(item['slot'],item['target'],item['gain'])
  assert all(type(x) is int for x in expected),'integer log'
  actual=next_choice();assert actual==expected,('global integer greedy/tie differs',position,actual,expected)
  slot,target,gain=actual;pair=(slot,target);selected.add(pair);counts[slot]+=1;rows[slot].append(target);new_gain=0
  for token in edges[pair]:
   if covered[token]:continue
   covered[token]=1;weight=token_weights[token];new_gain+=weight;objective+=weight
   for affected in token_edges[token]:
    gains[affected]-=weight;assert gains[affected]>=0
    s,t=affected
    if affected not in selected and counts[s]<8 and gains[affected]>0:heapq.heappush(heap,(-gains[affected],s,t))
  assert new_gain==gain,'incremental new token weight differs from selected gain'
 assert next_choice() is None,'frozen log stopped with a positive legal choice'
 return dict(rows=rows,objective=objective,incidences=len(token_weights),universe_pairs=len(edges),selected_pairs=len(selected))

def main(ds):
 started=time.monotonic();inputs={}
 def read(path,expected=None):
  path=Path(path);raw=path.read_bytes();h=hashlib.sha256(raw).hexdigest()
  assert expected is None or h==expected,'input differs before decode'
  inputs[str(path)]=h;return raw
 def document(path):return json.loads(read(path))
 C=document(R/'config.locked.json');initial=document(R/'reviews/frozen_inputs_and_theory.json');dc=C['datasets'][ds];src=dc['discovery'];n=src['n'];H=dc['H']
 folder=R/'m5/models'/ds;locked=document(folder/'control_inputs.frozen.json');manifest=document(folder/'compile_manifest.json')
 assert locked['status']=='ROOT_FROZEN_TRAIN_CONTROL_INPUTS_BEFORE_ANY_GATE_FEEDBACK' and locked['dataset']==ds
 assert manifest['status']=='FROZEN_TRAIN_ONLY_POSTING_BYTES' and manifest['dataset']==ds and manifest['shared_K_table'] and manifest['b']==8
 for path,digest in locked['input_sha256'].items():read(path,digest)
 for path,digest in manifest['input_sha256'].items():read(path,digest)
 for path in [src['gt'],dc['anchor']['ids']]:assert inputs[path]==initial[path]['sha256'],'initial campaign source freeze'
 native=R/'results/native'/ds/'discovery';job=document(native/'job.json');complete=document(native/'complete.json')
 assert complete['status']=='PASS_NATIVE_COLLECTION' and complete['n']==n and complete['threads']==1
 assert all(job[k]==dc[k] for k in ['dimension','base_n','index','anchor']) and job['queries']==src['queries'] and job['n']==n
 assert {(p['K'],p['L']) for p in job['points']}=={(p['K'],L) for p in dc['points'] for L in (p['Lminus'],p['L0'])}
 points={p['K']:p for p in dc['points']};lower={K:native/f"k{K}_L{points[K]['Lminus']}" for K in [1,100]}
 for K,path in lower.items():
  meta=document(path/'complete.json');assert meta['status']=='PASS_NATIVE_PLAIN_COUNT' and meta['actual_scalar'] and meta['n']==n and meta['K']==K and meta['L']==points[K]['Lminus']
 labels=np.frombuffer(read(dc['anchor']['ids'],initial[dc['anchor']['ids']]['sha256']),'<i4');assert len(labels)==H
 gt=np.frombuffer(read(src['gt'],initial[src['gt']]['sha256']),src['gt_dtype']).reshape(n,100)
 assert ((gt>=0)&(gt<dc['base_n'])).all() and (np.diff(np.sort(gt,axis=1),axis=1)>0).all()
 packets={}
 for K,path in lower.items():
  packets[K]=np.frombuffer(read(path/'ids.i32',manifest['input_sha256'][str(path/'ids.i32')]),'<i4').reshape(n,K)
  assert (((packets[K]>=0)&(packets[K]<dc['base_n']))|(packets[K]==-1)).all()
 routes=np.frombuffer(read(lower[1]/'entry_ids.i32',manifest['input_sha256'][str(lower[1]/'entry_ids.i32')]),'<i4').reshape(n,3)
 other=np.frombuffer(read(lower[100]/'entry_ids.i32',manifest['input_sha256'][str(lower[100]/'entry_ids.i32')]),'<i4').reshape(n,3);assert np.array_equal(routes,other)
 log=json.loads(read(folder/'selection_log.json',locked['selection_log_sha256']))
 value=replay(routes,gt,packets[1],packets[100],labels,log)
 expected_rows=json.loads(read(folder/'residual_joint.rows.json',locked['input_sha256'][str(folder/'residual_joint.rows.json')]))
 assert value['rows']==expected_rows
 for key in ['objective','incidences','universe_pairs','selected_pairs']:
  original={'objective':'training_integer_objective','incidences':'incidences','universe_pairs':'universe_pairs','selected_pairs':'pairs'}[key]
  assert value[key]==manifest['primary'][original],('existing compiler summary differs',key)
 assert all(sha(path)==h for path,h in inputs.items()),'read-only sources changed'
 receipt=dict(status='PASS_ALL_TRAIN_INTEGER_GREEDY_INDEPENDENT_INCREMENTAL_REPLAY',dataset=ds,n=n,H=H,
  **{k:v for k,v in value.items() if k!='rows'},input_sha256=inputs,source_sha256=sha(Path(__file__)),
  all_choices_and_global_ties_verified=True,selection_log_sha256=locked['selection_log_sha256'],
  integer_objective_weights={'K1':100,'K100':1},seconds=time.monotonic()-started,
  select_read=False,cal_read=False,confirm_read=False,table_changed=False,
  scope='All existing TRAIN choices and gains audited. No native output/GTK ordering theorem, performance, or population claim.')
 with (folder/'train_integer_greedy.audit.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
 print(json.dumps(receipt),flush=True)

if __name__=='__main__':assert len(sys.argv)==2;main(sys.argv[1])
