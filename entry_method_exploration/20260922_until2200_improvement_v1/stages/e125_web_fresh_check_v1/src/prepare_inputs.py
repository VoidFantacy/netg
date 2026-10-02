from pathlib import Path
import hashlib,json,struct,time,urllib.request,subprocess
import numpy as np
RUN=Path(__file__).resolve().parents[1];ROOT=Path("/data/netg/ACSG")
LOCK=json.loads((RUN/'config.locked.json').read_text())
def dump(p,v): p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''): h.update(b)
 return h.hexdigest()
def fvec(p,d):
 a=np.memmap(p,dtype='<f4',mode='r').reshape(-1,d+1)
 assert np.all(a[:,0].view('<i4')==d)
 return a[:,1:]
def key(a):return hashlib.sha256(a.tobytes()).digest()
def fetch(url,start,end,expected_total,path):
 req=urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'})
 with urllib.request.urlopen(req,timeout=60) as r:
  assert r.status==206 and r.headers['Content-Range']==f'bytes {start}-{end}/{expected_total}',dict(r.headers)
  data=r.read(end-start+2);assert len(data)==end-start+1
  meta=dict(url=url,range=[start,end],status=r.status,headers=dict(r.headers),sha256=hashlib.sha256(data).hexdigest())
 with path.open('xb') as f:f.write(data)
 return data,meta
refs=subprocess.run(['rg','-n','query.learn.50M|webvid.query.train.2.5M','benches/run','-g','*.py'],cwd=ROOT,capture_output=True,text=True)
(RUN/'reviews/source_code_references.txt').write_text(refs.stdout)
for ds,c in LOCK['datasets'].items():
 t=time.time();short='webvid' if ds.startswith('webvid') else 'yandex';d=c['dimension'];sel=LOCK['source_selection'][short]
 src=ROOT/'benches/datasets'/('WebVid2.5M_light_v1' if short=='webvid' else 'YandexT2I_official10M_ip_v1')
 out=RUN/'inputs'/ds;out.mkdir(exist_ok=False);manifest=json.loads((src/'manifest.json').read_text())
 seen=set();old_files=[]
 for name,identity in manifest['files'].items():
  if not(name.startswith('query.') and name.endswith('.fvecs')):continue
  p=src/name;assert sha(p)==identity['sha256'];a=fvec(p,d)
  seen.update(key(row) for row in a);old_files.append(dict(path=str(p),rows=len(a),sha256=identity['sha256']))
 for extra in [ROOT/'entry_method_exploration/20260920_wfree_frozen_replication_v1/inputs/webvid2_5m_light_v1/candidate_source.f32',ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1/inputs/webvid2_5m_light_v1/fit/queries.f32']:
  a=np.fromfile(extra,dtype='<f4').reshape(-1,d);seen.update(key(row) for row in a);old_files.append(dict(path=str(extra),rows=len(a),sha256=sha(extra)))
 if short=='webvid':
  source=src/'source/webvid.query.train.2.5M.fbin'
  with source.open('rb') as f:
   count,dim=struct.unpack('<II',f.read(8));assert (count,dim)==(2500000,d)
   f.seek(8+sel['start']*d*4);data=f.read(sel['candidate_count']*d*4)
  assert len(data)==sel['candidate_count']*d*4
  with (out/'candidate_source.f32').open('xb') as f:f.write(data)
  provenance=dict(source=str(source),source_rows=[sel['start'],sel['start']+sel['candidate_count']],source_stat=dict(bytes=source.stat().st_size,mtime_ns=source.stat().st_mtime_ns),slice_sha256=hashlib.sha256(data).hexdigest(),inherited_full_source_sha256=manifest['local_sources']['source/webvid.query.train.2.5M.fbin']['sha256'])
 else:
  total=40000000008;prefix,header_meta=fetch(sel['url'],0,8+16*d*4-1,total,out/'remote_prefix.bin')
  with (src/'source/query.learn.first45K.fbin').open('rb') as f:assert prefix==f.read(len(prefix))
  assert struct.unpack('<II',prefix[:8])==(50000000,d)
  first=8+sel['start']*d*4;last=first+sel['candidate_count']*d*4-1
  data,provenance=fetch(sel['url'],first,last,total,out/'candidate_source.f32')
  assert provenance['headers'].get('ETag')==header_meta['headers'].get('ETag')
  provenance.update(header_verification=header_meta,local_prefix_bytes_match=True,source_rows=[sel['start'],sel['start']+sel['candidate_count']])
 a=np.frombuffer(data,dtype='<f4').reshape(-1,d);rows=[];queries=[];duplicates=0;invalid=0
 for j,row in enumerate(a):
  if not np.all(np.isfinite(row)) or np.linalg.norm(row)==0:invalid+=1;continue
  k=key(row)
  if k in seen:duplicates+=1;continue
  seen.add(k);rows.append(sel['start']+j);queries.append(row)
  if len(rows)==LOCK['n']:break
 assert len(rows)==LOCK['n'],'insufficient unique queries'
 q=np.asarray(queries,dtype='<f4');q.tofile(out/'queries.f32');np.asarray(rows,dtype='<i8').tofile(out/'source_rows.i64')
 v=np.empty((len(q),d+1),dtype='<f4');v[:,0].view('<i4')[:]=d;v[:,1:]=q;v.tofile(out/'queries.fvecs')
 meta=dict(status='PASS_SOURCE_AND_DEDUP',dataset=ds,n=len(q),dimension=d,source=provenance,excluded_files=old_files,duplicates_skipped=duplicates,invalid_skipped=invalid,new_rows_unique=True,new_vs_all_known_formal_splits_byte_overlap=0,selection='source order, no labels or model outputs',created_unix=time.time(),seconds=time.time()-t,files={p.name:sha(p) for p in out.iterdir() if p.is_file()},scope='new source rows and no byte duplicates against all four registered splits; not a claim of semantic independence or exhaustive unregistered historical exposure')
 dump(out/'manifest.json',meta);print(ds,len(q),duplicates,'duplicates excluded',flush=True)
dump(RUN/'reviews/query_freeze.json',dict(status='FROZEN_BEFORE_GT_AND_SEARCH',created_unix=time.time(),datasets={ds:json.loads((RUN/'inputs'/ds/'manifest.json').read_text()) for ds in LOCK['datasets']}))
