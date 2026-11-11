"""Second implementation: no NumPy, sklearn, common.py, or main analyzer import."""
import array,bisect,collections,csv,gzip,hashlib,json,math,statistics,struct,subprocess,tarfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
DS=['coco','flickr30k','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1',
    'deep10m_l2_v1','sift10m_bigann_l2_v1','gist1m_l2_v1']
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def arrays(root):
 m=read(root/'packet_archive.json');assert sha(m['archive'])==m['archive_sha256'];data={}
 p=subprocess.Popen(['zstd','-q','-d','-c',m['archive']],stdout=subprocess.PIPE)
 with tarfile.open(fileobj=p.stdout,mode='r|') as tar:
  for member in tar:data[member.name]=tar.extractfile(member).read()
 assert p.wait()==0
 result={}
 for ref in m['files']:
  b=data[ref['member']];assert hashlib.sha256(b).hexdigest()==ref['payload_sha256']
  if ref['transform']=='identity':assert hashlib.sha256(b).hexdigest()==ref['original_sha256']
  result[ref['path']]=b
 return result
def intarray(b):
 a=array.array('i');a.frombytes(b);assert a.itemsize==4;return a
started=time.perf_counter();source_checked=0
freeze=read(R/'formal_freeze.json')
for item in freeze['files']:
 assert sha(item['path'])==item['sha256'],item['path'];source_checked+=1
for item in freeze['large_inherited_inputs']:
 stat=Path(item['path']).stat()
 assert stat.st_size==item['bytes'] and stat.st_mtime_ns==item['mtime_ns'],item['path']
rows=list(csv.DictReader((R/'analysis/points.csv').open()))
bykey={(r['dataset'],r['window'],int(r['K']),int(r['L']),r['method']):r for r in rows}
comparison=list(csv.DictReader((R/'analysis/comparisons.csv').open()))
cb={(r['dataset'],r['window'],int(r['K']),int(r['L']),r['method']):r for r in comparison}
checked=batches=0;formal_wall=0.;label_rows=0
for ds in DS:
 role=next(x for x in read(R/'role_freeze.json')['roles'] if x['dataset']==ds)
 original_GT=role['original_GT'];original_q=role['original_queries']
 selected=intarray((R/'storage/inputs'/ds/'source_rows.i32').read_bytes())
 prepared_gt=(R/'storage/inputs'/ds/'gt.i32').read_bytes()
 prepared_q=(R/'storage/inputs'/ds/'queries.f32').read_bytes()
 width=8 if original_GT['format']=='raw_i64' else 4
 header=4 if original_GT['format']=='ivecs' else 0
 gtstride=100*width+header
 qdim=int(original_q['d']);qheader=4 if original_q['format']=='fvecs' else 0
 qstart=8 if original_q['format']=='fbin' else 0;qstride=qdim*4+qheader
 with Path(original_GT['path']).open('rb') as original,Path(original_q['path']).open('rb') as vectors:
  for i,source_row in enumerate(selected):
   original.seek((original_GT.get('row_start',0)+source_row)*gtstride+header)
   expected=struct.unpack('<100'+('q' if width==8 else 'i'),original.read(100*width))
   assert expected==struct.unpack_from('<100i',prepared_gt,i*400)
   vectors.seek(qstart+(original_q.get('row_start',0)+source_row)*qstride+qheader)
   assert vectors.read(qdim*4)==prepared_q[i*qdim*4:(i+1)*qdim*4]
 info=read(R/'storage/labels'/ds/'complete.json');count=0;old_key=None;rank=-1
 with gzip.open(R/'storage/labels'/ds/'labels.i32.gz','rb') as stream:
  while True:
   block=stream.read(44*8192)
   if not block:break
   assert len(block)%44==0
   for qi,K,seed,position,bh,gain,loss,net,extra,slots,expanded in struct.iter_unpack('<11i',block):
    assert K in [1,100] and 0<=qi<3072 and 0<=position<96
    assert 0<=gain<=K-bh and 0<=loss<=bh<=K and net==gain-loss
    assert 0<=extra<=384 and 0<=slots<=64*384
    key=(K,qi)
    if key!=old_key:assert position==0;old_key=key;rank=0
    else:rank+=1;assert position==rank
    count+=1
 assert count==info['rows'];label_rows+=count
 model=read(R/'storage/models'/ds/'selected.json')
 assert model['label_metadata_sha256']==sha(R/'storage/labels'/ds/'labels.i32.gz')
 for window in ['A','B']:
  c=read(R/'configs'/f'{ds}.{window}.json');root=Path(c['output_dir']);native=read(root/'complete.json');raw=arrays(root);n=c['queries']['n']
  gt=intarray(Path(c['test_gt']['path']).read_bytes());assert len(gt)==n*100
  gtsets={K:[set(gt[i*100:i*100+K]) for i in range(n)] for K in [1,100]}
  local=[]
  for p in native['results']:
   K,L,m=int(p['K']),int(p['L']),p['method'];key=ds,window,K,L,m;row=bykey[key];prefix=f'k{K}/{m}_L{L}/raw/'
   ids=intarray(raw[prefix+'ids.i32']);assert len(ids)==n*K
   hits=[len(set(ids[i*K:(i+1)*K])&gtsets[K][i]) for i in range(n)]
   assert sum(hits)==int(row['hits']) and abs(sum(hits)*100/(n*K)-float(row['recall_pct']))<1e-10
   if K==100:assert sum(h<10 for h in hits)==int(row['failed_lt10'])
   wall=[r['wall_seconds'] for r in p['rounds']];qps=n/statistics.median(wall)
   assert abs(qps-float(row['qps']))<1e-8*max(qps,1)
   h=hashlib.sha256(struct.pack('<QQ',n,K))
   for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update(raw[prefix+name])
   h.update(b'\0'*(16*n))
   for rep in p['rounds']:assert rep['threads']==1 and rep['packet_sha256']==h.hexdigest()
   local.append(dict(K=K,L=L,method=m,hits=sum(hits),qps=qps,qps_min=min(n/t for t in wall),qps_max=max(n/t for t in wall)))
   checked+=1;batches+=3;formal_wall+=sum(wall)
  for p in local:
   key=ds,window,p['K'],p['L'],p['method']
   if key not in cb:continue
   row=cb[key]
   controls=[x for x in local if x['K']==p['K'] and x['method'] in ['GT10','OPT-B32','REUSE-SQ']]
   covers=[x for x in controls if (x['hits']>=p['hits'] and x['qps']>=p['qps'] and
            (x['hits']>p['hits'] or x['qps']>p['qps']))]
   assert (row['covered']=='True')==bool(covers)
   assert (row['range_covered']=='True')==any(x['qps_min']>=p['qps_max'] for x in covers)
   eligible=[x for x in controls if x['qps']>=p['qps']]
   if eligible:
    best=max(eligible,key=lambda x:(x['hits'],x['qps']))
    assert row['no_slower_control']==f"{best['method']}/L{best['L']}"
    assert abs(float(row['gain_vs_no_slower_pp'])-(p['hits']-best['hits'])*100/(n*p['K']))<1e-10
  print('STDLIB_VERIFIED',ds,window,len(local),flush=True)
assert checked==freeze['points']==len(rows) and batches==freeze['batches']
proposals=list(csv.DictReader((R/'analysis/cost_control_proposals.csv').open()))
proposed_checks=0
for ds in DS:
 native=read(R/'storage/calibration_v2'/ds/'complete.json')['results']
 for p in proposals:
  if p['dataset']!=ds:continue
  K=int(p['K']);control=p['control'];target=float(p['cal_target_us'])
  curve=sorted((1e6/float(x['qps']),int(x['L'])) for x in native if int(x['K'])==K and x['method']==control)
  times=[x[0] for x in curve];j=bisect.bisect_right(times,target)
  if j==0:estimate=curve[0][1]
  elif j==len(curve):estimate=curve[-1][1]
  else:
   t0,l0=curve[j-1];t1,l1=curve[j];estimate=l0+(l1-l0)*(target-t0)/(t1-t0)
  assert int(round(estimate))==int(p['estimated_L'])
  expected=sorted(set(max(100,L) for L in [int(round(estimate))-2,int(round(estimate)),int(round(estimate))+2,int(p['base_L'])+1]))
  assert p['proposed_L']==';'.join(map(str,expected));proposed_checks+=1
result=dict(status='PASS_STDLIB_ACTUAL_INTEGER_HASH_WALL_AND_CONTROL_AUDIT',
 source_files_checked=source_checked,formal_points=checked,formal_batches=batches,
 formal_batch_wall_seconds=formal_wall,all_training_label_structural_rows=label_rows,
 independent_cost_proposal_checks=proposed_checks,
 diagnostic_GT_mask_audit='Main analyzer checks every 72-byte record; this second implementation does not rerun graph search or all labels',
 bootstrap_resampling_independently_repeated=False,seconds=time.perf_counter()-started,
 same_executor_different_implementation=True,default_changed=False)
dump(R/'analysis/stdlib_audit.json',result);print(json.dumps(result),flush=True)
