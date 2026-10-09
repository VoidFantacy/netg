"""Exact integer joint residual-coverage greedy; no calibration/confirmation inputs."""
from array import array
from pathlib import Path
import hashlib,heapq,json,struct,sys,time
import numpy as np
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,value):
 with Path(p).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')

def incidences(routes,g1,g100,r1,r100,label_slots,all_gt=False):
 edges={};weights=array('I');covered_tokens=[];token=0
 for i,labels in enumerate(routes):
  slots=sorted({label_slots[int(j)] for j in labels})
  members={}
  missing1={int(g1[i])} if all_gt else {int(g1[i])}-set(map(int,r1[i]))
  missing100=set(map(int,g100[i])) if all_gt else set(map(int,g100[i]))-set(map(int,r100[i]))
  for t in missing1:members[t]=100
  for t in missing100:members[t]=members.get(t,0)+1
  for target,w in sorted(members.items()):
   weights.append(w);covered_tokens.append((i,target,w))
   for slot in slots:edges.setdefault((slot,target),array('I')).append(token)
   token+=1
 return edges,weights,covered_tokens

def greedy(edges,weights,H,b=8):
 heap=[(-sum(weights[int(i)] for i in incid),slot,target) for (slot,target),incid in edges.items()]
 heapq.heapify(heap);covered=bytearray(len(weights));counts=[0]*H;rows=[[] for _ in range(H)];log=[]
 while heap and len(log)<b*H:
  upper,slot,target=heapq.heappop(heap)
  if counts[slot]>=b:continue
  tokens=edges[(slot,target)];gain=sum(weights[int(i)] for i in tokens if not covered[int(i)])
  if gain<=0:continue
  if gain!=-upper:
   heapq.heappush(heap,(-gain,slot,target));continue
  rows[slot].append(target);counts[slot]+=1;log.append(dict(slot=slot,target=target,gain=gain))
  for i in tokens:covered[int(i)]=1
 return rows,log,sum(weights[i] for i in range(len(weights)) if covered[i])

def frequency(edges,weights,H,b=8):
 grouped=[[] for _ in range(H)]
 for (slot,target),incidence in edges.items():
  grouped[slot].append((-sum(weights[int(i)] for i in incidence),target))
 return [[t for _,t in heapq.nsmallest(b,candidates)] for candidates in grouped]

def export(path,labels,rows,base_n):
 H=len(labels);b=8;assert len(rows)==H and len(set(labels))==H
 size=1
 while size<2*H:size*=2
 keys=np.full(size,-1,dtype='<i4');slots=np.full(size,-1,dtype='<i4')
 for slot,key in enumerate(labels):
  pos=(int(key)*2654435761)&(size-1)
  while keys[pos]!=-1:pos=(pos+1)&(size-1)
  keys[pos]=key;slots[pos]=slot
 postings=np.full((H,b),-1,dtype='<i4');counts=np.zeros(H,dtype='u1')
 for slot,row in enumerate(rows):
  assert len(row)<=b and len(set(row))==len(row) and all(0<=t<base_n for t in row)
  postings[slot,:len(row)]=row;counts[slot]=len(row)
 order=np.argsort(np.array(labels,dtype='i4'),kind='stable');sorted_labels=np.array(labels,dtype='<i4')[order];sorted_slots=order.astype('<i4')
 header=struct.pack('<8s8I',b'M5POST1\0',1,H,b,size,int(counts.sum()),base_n,0,0)
 payload=header+np.array(labels,dtype='<i4').tobytes()+counts.tobytes()+postings.tobytes()+keys.tobytes()+slots.tobytes()+sorted_labels.tobytes()+sorted_slots.tobytes()
 runtime_scratch=4096;assert len(payload)+runtime_scratch<=128*1024
 with path.open('xb') as f:f.write(payload)
 return dict(bytes=len(payload),runtime_scratch_reserved=runtime_scratch,total_incremental_reserved=len(payload)+runtime_scratch,sha256=sha(path),pairs=int(counts.sum()),unique_targets=len({t for row in rows for t in row}),rows=sum(bool(row) for row in rows))

def main(ds):
 C=json.loads((R/'config.locked.json').read_text());dc=C['datasets'][ds];src=dc['discovery'];H=dc['H'];n=src['n']
 outputs=R/'results/native'/ds/'discovery';assert json.loads((outputs/'complete.json').read_text())['status']=='PASS_NATIVE_COLLECTION'
 out=R/'m5/models'/ds;out.mkdir(parents=True,exist_ok=False);started=time.perf_counter()
 labels=np.fromfile(dc['anchor']['ids'],'<i4');assert len(labels)==H;label_slots={int(t):i for i,t in enumerate(labels)}
 gt=np.fromfile(src['gt'],src['gt_dtype']).reshape(n,100);assert (gt>=0).all() and (gt<dc['base_n']).all()
 p1,p100=dc['points'];low1=outputs/f"k1_L{p1['Lminus']}";low100=outputs/f"k100_L{p100['Lminus']}"
 routes=np.fromfile(low1/'entry_ids.i32','<i4').reshape(n,3);other=np.fromfile(low100/'entry_ids.i32','<i4').reshape(n,3);assert np.array_equal(routes,other)
 r1=np.fromfile(low1/'ids.i32','<i4').reshape(n,1);r100=np.fromfile(low100/'ids.i32','<i4').reshape(n,100)
 before={str(p):sha(p) for p in [Path(src['gt']),Path(dc['anchor']['ids']),low1/'entry_ids.i32',low1/'ids.i32',low100/'entry_ids.i32',low100/'ids.i32']}
 edges,weights,tokens=incidences(routes,gt[:,0],gt,r1,r100,label_slots)
 rows,log,value=greedy(edges,weights,H)
 meta=export(out/'residual_joint.bin',list(labels),rows,dc['base_n']);put(out/'selection_log.json',log)
 put(out/'residual_joint.rows.json',rows)
 meta['training_integer_objective']=value;meta['incidences']=len(weights);meta['universe_pairs']=len(edges)
 controls={}
 indep=frequency(edges,weights,H);controls['missing_frequency']=export(out/'missing_frequency.bin',list(labels),indep,dc['base_n'])
 global_freq={}
 for _,target,w in tokens:global_freq[target]=global_freq.get(target,0)+w
 missing_global=[t for t,_ in sorted(global_freq.items(),key=lambda v:(-v[1],v[0]))[:24]]
 np.array(missing_global,dtype='<i4').tofile(out/'missing_global.i32');controls['missing_global']=dict(targets=missing_global,bytes=4*len(missing_global),sha256=sha(out/'missing_global.i32'))
 del edges,weights,tokens
 alle,w_all,all_tokens=incidences(routes,gt[:,0],gt,r1,r100,label_slots,all_gt=True)
 allrows,alllog,allvalue=greedy(alle,w_all,H);controls['allgt_joint']=export(out/'allgt_joint.bin',list(labels),allrows,dc['base_n']);put(out/'allgt_joint.selection_log.json',alllog)
 controls['allgt_frequency']=export(out/'allgt_frequency.bin',list(labels),frequency(alle,w_all,H),dc['base_n'])
 all_freq={}
 for _,target,w in all_tokens:all_freq[target]=all_freq.get(target,0)+w
 global_all=[t for t,_ in sorted(all_freq.items(),key=lambda v:(-v[1],v[0]))[:24]]
 np.array(global_all,dtype='<i4').tofile(out/'allgt_global.i32');controls['allgt_global']=dict(targets=global_all,bytes=4*len(global_all),sha256=sha(out/'allgt_global.i32'))
 controls['empty']=export(out/'empty.bin',list(labels),[[] for _ in range(H)],dc['base_n'])
 assert all(sha(p)==v for p,v in before.items()),'read-only input identity'
 put(out/'compile_manifest.json',dict(status='FROZEN_TRAIN_ONLY_POSTING_BYTES',dataset=ds,shared_K_table=True,b=8,max_candidates=24,rows_arrival_order='global exact integer greedy log',lookup_order='actual heap-pop labels',primary=meta,controls=controls,
  input_sha256=before,seconds=time.perf_counter()-started,cal_read=False,confirm_read=False,remaining_controls=['full-base geometry','same-universe geometry','same-U tiny-HNSW','128KiB tiny-HNSW'],actual_merge_audit_pending=True))
 print('M5_TABLES_FROZEN',ds,meta,flush=True)
if __name__=='__main__':
 assert len(sys.argv)==2;main(sys.argv[1])
