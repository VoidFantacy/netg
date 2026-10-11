"""Freeze all fitted models and fresh matched curves before native evaluation."""
from pathlib import Path
import hashlib,json,os,time
ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT.parent/'20261010_m5_region_budget_curve_v1'
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
NAMES=['NSG','GT','M5','M5OPT','M5REG96','REGOPT96','WIDE12','M5RES12']
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def stat(p):
 s=Path(p).stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def put(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def main():
 os.sched_setaffinity(0,{14});t=time.monotonic()
 fit=json.loads((ROOT/'fit_state.json').read_text())
 assert fit['status']=='FIT_COMPLETE_ALL_MODELS_FROZEN' and fit['active'] is None
 assert len(fit['completed'])==2 and all(x['elapsed_seconds']<=900 and x['model_eligible'] for x in fit['completed'])
 assert {x['dataset'] for x in fit['completed']}==set(DS)
 fitted={x['dataset']:x for x in fit['completed']}
 expected_keys={f'k{k}_L{l}' for k in [1,100] for l in [200,400,800,1000,1200]}
 pre=json.loads((ROOT/'reviews/fit_preflight.json').read_text());files=dict(pre['registered_input_files'])
 for p,entry in files.items():assert stat(p)==entry['current_stat'],'registered source changed '+p
 inventory={'status':'PASS_FROZEN_ORIGINAL_M5_AND_TRAIN_RESIDUAL_COMPLETION_INVENTORY','datasets':{},
            'FIT_increment_per_dataset':{x['dataset']:x['elapsed_seconds'] for x in fit['completed']}}
 old_inv=json.loads((PARENT/'reviews/inventory.json').read_text())
 for ds in DS:
  mpath=ROOT/'models'/ds/'compile_manifest.json';manifest=json.loads(mpath.read_text())
  actual_manifest_sha=sha(mpath)
  assert Path(fitted[ds]['model_manifest']).resolve()==mpath.resolve()
  assert actual_manifest_sha==fitted[ds]['model_manifest_sha256'],'manifest differs from successful <=900s FIT receipt'
  fit_job=json.loads((ROOT/'fit_jobs'/f'{ds}.json').read_text())
  assert manifest['dataset']==ds and manifest['role']=='fit'
  assert manifest['status']=='FROZEN_TRAIN_ONLY_POST_M5_RESIDUAL_COMPLETION_ALL_10_POINTS'
  assert manifest['eligible_query_statuses']==[2] and not manifest['public_test_read']
  assert manifest['n']==20000 and manifest['point_count']==10
  assert set(manifest['models'])==expected_keys,'missing or extra fitted K/L model'
  models={}
  for key,items in manifest['models'].items():
   k,l=map(int,key[1:].split('_L'))
   assert set(items)=={'pair','route'}
   models[key]={}
   for family in ['pair','route']:
    rec=items[family];p=Path(rec['path']);digest=sha(p);assert digest==rec['sha256']
    assert rec['K']==k and rec['L']==l and rec['base_n']==fit_job['base_n']
    assert p.resolve()==(ROOT/'models'/ds/f'{family}.{key}.i32').resolve()
    assert rec['dtype']=='<i4' and len(rec['shape'])==2 and rec['shape'][1]==7
    assert p.stat().st_size==rec['bytes']==rec['shape'][0]*7*4
    s=stat(p);files[str(p)]={'path':str(p),'sha256':digest,'bytes':s[2],'current_stat':s,'identity_scope':'fresh complete fitted model SHA'}
    models[key][family]=str(p)
  s=stat(mpath);files[str(mpath)]={'path':str(mpath),'sha256':actual_manifest_sha,'bytes':s[2],'current_stat':s,'identity_scope':'full frozen compiler manifest bound to successful FIT receipt'}
  job=json.loads((PARENT/'jobs'/f'public_test.{ds}.json').read_text())
  table=next(x['table'] for x in job['methods'] if x['name']=='M5')
  methods=[]
  for name in NAMES:
   m={'name':name,'table':None if name in ['NSG','GT'] else table,
      'table_sha256':None if name in ['NSG','GT'] else sha(table),
      'extra_cap':96 if name in ['M5REG96','REGOPT96'] else 12 if name in ['WIDE12','M5RES12'] else 0,
      'first_seed':False,'optimized':name in ['M5OPT','REGOPT96','WIDE12','M5RES12'],
      'family':{'NSG':'base','GT':'base','M5':'post','M5OPT':'opt','M5REG96':'reg',
                'REGOPT96':'opt_reg','WIDE12':'route_bank','M5RES12':'bank'}[name],
      'completion_family':'pair' if name=='M5RES12' else 'route' if name=='WIDE12' else ''}
   methods.append(m)
  job.update(methods=methods,completion_models=models,completion_manifest=str(mpath),
    embedded_domain=str(ROOT/'reviews'/f'{ds}.embedded_base_domain.relocated.json'),
    out=str(ROOT/'results/public_test'/ds),no_training=True,
    FIT_increment_seconds=next(x['elapsed_seconds'] for x in fit['completed'] if x['dataset']==ds),
    original_protocol_sha256=sha(PARENT/'protocol.md'),protocol_sha256=sha(ROOT/'protocol.md'))
  put(ROOT/'jobs'/f'public_test.{ds}.json',job)
  inventory['datasets'][ds]={**old_inv['datasets'][ds],'completion_manifest':str(mpath),'models':manifest['models']}
  for key in ['queries','GT','rows']:
   p=Path(job[key]);s=stat(p);digest=sha(p)
   expected=job[{'queries':'query_sha256','GT':'GT_sha256','rows':'rows_sha256'}[key]]
   assert digest==expected and stat(p)==s,'public window source identity changed'
   files[str(p)]={'path':str(p),'sha256':digest,'bytes':s[2],'current_stat':s,'identity_scope':'fresh complete existing exposed window SHA after model freeze'}
 put(ROOT/'reviews/inventory.json',inventory)
 put(ROOT/'reviews/data_preflight.json',{'status':'PASS_E176_ALL_MODELS_FROZEN_AND_PUBLIC_SOURCE_IDENTITY',
  'registered_input_files':files,'FIT_split_preflight':str(ROOT/'reviews/fit_preflight.json'),
  'FIT_completed':fit['completed'],'public_test_training':False,
  'protocol_sha256':sha(ROOT/'protocol.md'),'elapsed_seconds':time.monotonic()-t})
 put(ROOT/'parameter_lock.json',{'status':'FROZEN_E176_160_POINT_480_BATCH_MATCHED_MATRIX',
  'datasets':DS,'methods':NAMES,'K_values':[1,100],'L':[200,400,800,1000,1200],'n':10000,
  'timing_repeats':3,'points':160,'timed_batches':480,'comparisons':800,'mechanisms':60,
  'primary_method':'M5RES12','protocol_sha256':sha(ROOT/'protocol.md'),
  'jobs':{str(p):sha(p) for p in sorted((ROOT/'jobs').glob('*.json'))},'parameters_freeze_unix':time.time(),
  'no_adaptive_public_test_selection':True,'no_adaptive_cancel_or_selection':True,'new_TRAIN_per_dataset':inventory['FIT_increment_per_dataset']})
 print(json.dumps({'status':'PASS_FORMAL_INPUTS_FROZEN','points':160,'seconds':time.monotonic()-t}))
if __name__=='__main__':main()
