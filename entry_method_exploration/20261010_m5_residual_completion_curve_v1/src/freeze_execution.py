"""Close real preflight/build/smoke reviews; freeze finite formal execution."""
from pathlib import Path
import hashlib,json,time
ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT.parent/'20261010_m5_region_budget_curve_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def stat(p):
 s=Path(p).stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def main():
 params=load(ROOT/'parameter_lock.json');assert params['points']==160 and params['timed_batches']==480
 assert sha(ROOT/'protocol.md')==params['protocol_sha256']
 fit=load(ROOT/'fit_state.json');assert fit['status']=='FIT_COMPLETE_ALL_MODELS_FROZEN' and fit['active'] is None
 checks=['data_preflight.json','build.json','benchmark_source_review.json','analysis_source_review.json','qualification_source_independent_review.json','native_qualification.json','scope_review.json']
 for name in checks:assert load(ROOT/'reviews'/name)['status'].startswith('PASS'),name
 qual=load(ROOT/'reviews/native_qualification.json')
 assert qual['status']=='PASS_E176_N16_ORACLES_AND_FROZEN_ORIGINAL_WORD_REGRESSION'
 assert qual['word_file_comparisons']==340 and len(qual['jobs'])==2
 assert all(x['exit_code']==0 and x['max_threads_observed']==1 for x in qual['jobs'])
 for p,h in qual['source_identity'].items():assert sha(p)==h
 for name in ['benchmark_source_review.json','analysis_source_review.json']:
  for p,h in load(ROOT/'reviews'/name)['source_sha256_at_review'].items():assert sha(p)==h
 for p,h in params['jobs'].items():assert sha(p)==h
 pre=load(ROOT/'reviews/data_preflight.json')
 inputs={p:rec['current_stat'] for p,rec in pre['registered_input_files'].items()}
 for p,s in inputs.items():assert stat(p)==s
 originals=load(ROOT/'source_before/manifest.json')
 for name,h in originals['parent_sources'].items():assert sha(PARENT/'src'/name)==h,'original E175 source changed'
 sources={str(p):sha(p) for p in sorted((ROOT/'src').iterdir()) if p.is_file()}
 sources.update({str(p):sha(p) for p in sorted((ROOT/'bin').iterdir()) if p.is_file()})
 lock={'status':'FROZEN_E176_ALL_SCIENTIFIC_SOURCES_MODELS_AND_ORIGINAL_BINDINGS','source_and_binary_sha256':sources,
  'input_stats':inputs,'protocol_sha256':params['protocol_sha256'],'parameter_lock_sha256':sha(ROOT/'parameter_lock.json'),
  'reviews_sha256':{str(ROOT/'reviews'/n):sha(ROOT/'reviews'/n) for n in checks},'created_unix':time.time(),
  'new_TRAIN_per_dataset':{x['dataset']:x['elapsed_seconds'] for x in fit['completed']},
  'finite_scope':{'points':160,'timed_batches':480,'comparisons':800,'mechanisms':60}}
 put(ROOT/'execution_lock.json',lock)
 put(ROOT/'reviews/preexecution_acceptance.json',{'status':'PASS_E176_ACTUAL_PREFLIGHT_BUILD_REVIEW_SMOKE_AND_FROZEN_MATRIX',
  'execution_lock_sha256':sha(ROOT/'execution_lock.json'),'protocol_sha256':params['protocol_sha256'],
  'parameter_lock_sha256':sha(ROOT/'parameter_lock.json'),'reviews_sha256':lock['reviews_sha256'],
  'full_plain_oracle_scope':'single full independent scalar/linear and main/cached-R word qualification per formal method, before each KL timing',
  'public_test_already_exposed':True,'default_replacement':False,'no_adaptive_selection':True})
 print(json.dumps({'status':'PASS_PREEXECUTION_CLOSURE','sources':len(sources),'inputs':len(inputs)}))
if __name__=='__main__':main()
