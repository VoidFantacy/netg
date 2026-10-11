"""Bind existing TRAIN20K/public windows; create only new administrative jobs."""
from pathlib import Path
import hashlib,json,os,time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
PARENT=ROOT.parent/'20261010_m5_region_budget_curve_v1'
STORAGE=Path('/root/acsg-e172-storage-v2/campaign')
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def stat(p):
 s=Path(p).stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def put(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 os.sched_setaffinity(0,{14});started=time.monotonic()
 authorization=json.loads((ROOT/'authorization.json').read_text())
 assert authorization['user_answer']=='允许额外 15 分钟／数据集'
 old=json.loads((STORAGE/'config.locked.json').read_text())
 lock=json.loads((PARENT/'execution_lock.json').read_text())
 prior=json.loads((PARENT/'reviews/data_preflight.json').read_text())
 files={}
 for p,s in lock['input_stats'].items():
  assert stat(p)==s,'inherited source changed '+p
  rec=prior['registered_input_files'][p]
  files[p]={'path':p,'sha256':rec['sha256'],'bytes':s[2],'current_stat':s,
            'identity_scope':'E175 complete registered SHA plus unchanged current stat'}
 split_checks=[]
 for ds in DS:
  public=json.loads((PARENT/'jobs'/f'public_test.{ds}.json').read_text())
  src=old['datasets'][ds]['discovery'];assert src['n']==20000
  d=public['dimension'];job=dict(public)
  q,gt,rows=map(Path,[src['queries'],src['gt'],src['rows']])
  assert q.stat().st_size==20000*d*4 and gt.stat().st_size==20000*100*8 and rows.stat().st_size==20000*8
  original_manifest=json.loads((STORAGE/'m5/models'/ds/'compile_manifest.json').read_text())
  for p in [q,gt,rows]:
   before=stat(p);digest=sha(p);assert stat(p)==before
   if str(p) in original_manifest['input_sha256']:assert digest==original_manifest['input_sha256'][str(p)]
   files[str(p)]={'path':str(p),'sha256':digest,'bytes':before[2],'current_stat':before,'identity_scope':'fresh full existing TRAIN source SHA'}
  # Byte-level split check: neither public labels nor public responses enter FIT.
  train=np.memmap(q,dtype='u1',mode='r').reshape(20000,d*4)
  test=np.memmap(public['queries'],dtype='u1',mode='r').reshape(10000,d*4)
  train_hashes={hashlib.sha256(row).digest() for row in train}
  overlap=sum(hashlib.sha256(row).digest() in train_hashes for row in test)
  assert overlap==0,'TRAIN/public byte overlap'
  split_checks.append({'dataset':ds,'TRAIN_n':20000,'public_n':10000,'exact_query_byte_overlap':overlap,
       'TRAIN_alignment_source':str(STORAGE/'config.locked.json'),'public_is_previously_exposed':True})
  embedded=STORAGE/'reviews'/f'{ds}.embedded_base_domain.json'
  original=json.loads(embedded.read_text());domain=STORAGE/'reviews'/f'{ds}.data_domain.json'
  assert domain.exists() and original['status']=='FULL_EMBEDDED_BASE_WORDS_EQUAL_REGISTERED_BASE'
  clone=dict(original);clone['registered_domain_receipt']=str(domain)
  clone['E176_relocation']={'original_embedded_receipt':str(embedded),'original_sha256':sha(embedded),
    'registered_domain_relocated_path':str(domain),'registered_domain_sha256':sha(domain),
    'scope':'administrative existing receipt path relocation; original words/stat/SHA fields unchanged'}
  clone_path=ROOT/'reviews'/f'{ds}.embedded_base_domain.relocated.json';put(clone_path,clone)
  job.update(role='fit',n=20000,queries=str(q),query_format='raw',query_first=0,
   query_sha256=files[str(q)]['sha256'],GT=str(gt),GT_format='raw',GT_dtype='<i8',GT_width=100,
   GT_sha256=files[str(gt)]['sha256'],rows=str(rows),rows_sha256=files[str(rows)]['sha256'],
   original_m5_table=str(STORAGE/'m5/models'/ds/'residual_joint.bin'),embedded_domain=str(clone_path),
   out=str(ROOT/'fit_results'/ds),models_out=str(ROOT/'models'/ds),max_elapsed_seconds=900,
   historical_TRAIN_seconds=authorization['historical_TRAIN_seconds'][ds],
   additional_fit_budget_seconds=900,no_training=False)
  for k in ['methods','source_query_fvecs','source_query_sha256','source_GT_ivecs','source_GT_sha256',
   'source_window_first','source_window_n','source_rows_scope']:
   job.pop(k,None)
  put(ROOT/'fit_jobs'/f'{ds}.json',job)
  for p in [embedded,domain,clone_path,Path(job['original_m5_table'])]:
   s=stat(p);files[str(p)]={'path':str(p),'sha256':sha(p),'bytes':s[2],'current_stat':s,
                          'identity_scope':'fresh full receipt or frozen original model SHA'}
 put(ROOT/'reviews/fit_preflight.json',{'status':'PASS_TRAIN_IDENTITY_ALIGNMENT_AND_DISJOINT_PUBLIC_WINDOWS',
  'registered_input_files':files,'split_checks':split_checks,'no_new_exact_GT':True,
  'authorization_sha256':sha(ROOT/'authorization.json'),'protocol_sha256':sha(ROOT/'protocol.md'),
  'elapsed_seconds':time.monotonic()-started,'stage':'administrative identity and source preparation, before fitting'})
 put(ROOT/'fit_scope_lock.json',{'datasets':DS,'n':20000,'K_values':[1,100],
  'L':[200,400,800,1000,1200],'model_families':['pair','route'],'per_key_cap':4,'total_extra_cap':12,
  'min_distinct_query_support':2,'eligible_statuses':[2],'point_count_per_dataset':10,
  'additional_fit_cap_seconds_per_dataset':900,'protocol_sha256':sha(ROOT/'protocol.md'),
  'jobs':{str(p):sha(p) for p in sorted((ROOT/'fit_jobs').glob('*.json'))},'frozen_unix':time.time()})
 print(json.dumps({'status':'PASS_FIT_PREFLIGHT','seconds':time.monotonic()-started,'splits':split_checks}))
if __name__=='__main__':main()
