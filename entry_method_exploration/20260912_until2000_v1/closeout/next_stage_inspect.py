"""Read existing IDs and provenance only; no query vectors, GT labels or ANN."""
from pathlib import Path
import json,hashlib,os,sys,argparse
import numpy as np
R=Path('/data/netg/ACSG');D=R/'entry_method_exploration'
E24=D/'20260910_gt_topk_profiles_v1';E37=D/'20260912_offline_profile_rl_v1';E57=D/'20260912_expanded_final_comparison_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inspect():
 assert os.sched_getaffinity(0)=={8}
 assert all(os.environ[k]=='1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'])
 assert next(int(x.split(':')[1]) for x in Path('/proc/self/status').read_text().splitlines() if x.startswith('Threads:'))==1
 records=[];sources=[]
 provenance=read(E57/'reviews/split_isolation.json')
 for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
  selected=read(E37/'inputs'/ds/'selection.json');p=Path(selected['source']['row_ids']);ids=np.fromfile(p,np.int64);localpath=E37/'inputs'/ds/'source_local.i32';local=np.fromfile(localpath,np.int32);samplepath=E37/'inputs'/ds/'row_ids.i64';sample=np.fromfile(samplepath,np.int64)
  assert len(ids)==20000 and len(local)==len(sample)==5120 and np.array_equal(ids[local],sample)
  calpath=E57/'inputs'/ds/'cal/row_ids.i64';auditpath=E37/'inputs'/ds/'audit/row_ids.i64'
  groups={'profile_fit':ids,'RL_train':sample[:4096],'monitor':sample[4096:],'cal':np.fromfile(calpath,np.int64),'audit':np.fromfile(auditpath,np.int64)}
  assert all(len(np.unique(a))==len(a) for a in groups.values())
  intersections=[dict(left=a,right=b,count=len(set(groups[a].tolist())&set(groups[b].tolist()))) for i,a in enumerate(groups) for b in list(groups)[i+1:]]
  assert next(x['count'] for x in intersections if x['left']=='profile_fit' and x['right']=='monitor')==1024
  assert next(x['count'] for x in intersections if x['left']=='RL_train' and x['right']=='monitor')==0
  assert len(set(ids.tolist())&set(groups['cal'].tolist()))==0
  records.append(dict(dataset=ds,groups={name:dict(count=len(a),minimum_id=int(a.min()),maximum_id=int(a.max())) for name,a in groups.items()},same_source_ID_intersections=intersections,
   meaning='Monitor is gradient-disjoint but fully included in initial supervised profile fit; cal is outside profile fit but already used for selection; no group is claimed project-blind',
   fresh_development_rows_identified=False,unreconciled_project_wide_exposure=True))
  sources.extend(dict(path=str(q),sha256=sha(q)) for q in [p,localpath,samplepath,calpath,auditpath,E37/'inputs'/ds/'selection.json'])
 return dict(status='PASS_EXISTING_SCOPE_VERIFIED',datasets=records,provenance_status=provenance['status'],new_vectors_read=0,new_GT_labels_read=0,new_ANN=0,new_training=0,training_plan_ready=False,sources=sources)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args();result=inspect()
 if args.output:
  assert not args.output.exists(),'choose a new output path; do not overwrite history';args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='sources'},ensure_ascii=False,indent=2))
