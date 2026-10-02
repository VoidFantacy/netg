"""Seal the already checked research deliverables after the requested deadline."""
import datetime,hashlib,json
from pathlib import Path

R=Path(__file__).resolve().parents[1];repo=R.parent.parent
now=datetime.datetime.now(datetime.timezone.utc)
state=json.loads((R/'state.json').read_text())
assert now>=datetime.datetime.fromisoformat(state['deadline']),'Requested research interval is not over.'
assert state['status']=='FINAL_REVIEW'
assert not (R/'manifest.json').exists()
audit=json.loads((R/'reviews/completion_audit.json').read_text())
assert audit['status']=='PASS'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,identity in audit['root_checks'].items():
    assert sha(repo/name)==identity['after_sha256'],name
pdf=json.loads((R/'reviews/pdf_verification.json').read_text())
assert sha(R/'GT10现状与改进方向.pdf')==pdf['pdf_sha256']
for name,identity in pdf['sources'].items():assert sha(R/name)==identity,name
state.update(status='COMPLETED_NO_DEFAULT_CHANGE',completed_at_utc=now.isoformat(),
             completed_at_local=now.astimezone(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
             pending_experiments=0,implementation_candidates=0,
             final_identity='manifest.json',all_required_work_complete=True)
(R/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
files={str(p.relative_to(R)):{'size':p.stat().st_size,'sha256':sha(p)}
       for p in sorted(R.rglob('*')) if p.is_file()}
manifest={'sealed_at_utc':now.isoformat(),'status':state['status'],
          'manifest_excludes_itself':True,'artifact_files':files,
          'root_documents':{name:sha(repo/name) for name in audit['root_checks']},
          'history_record':{'path':'experiment_history/127_gt10_strength_review.md',
                            'sha256':sha(repo/'experiment_history/127_gt10_strength_review.md')},
          'history_index_sha256':sha(repo/'experiment_history/README.md')}
(R/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':state['status'],'completed_at_local':state['completed_at_local'],
                  'artifact_files':len(files),'default_changed':False},ensure_ascii=False))
