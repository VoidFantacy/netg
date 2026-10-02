from pathlib import Path
import json,time,datetime,hashlib,os
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def identity(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}
assert json.loads((R/'reviews/final_delivery_audit.json').read_text())['status']=='PASS'
assert json.loads((R/'reviews/artifact_seals_verification_final.json').read_text())['status']=='PASS'
assert json.loads((R/'reviews/pdf_verification.json').read_text())['status']=='PASS'
for q in Path('/proc').iterdir():
 if not q.name.isdigit():continue
 try:args=(q/'cmdline').read_bytes().split(b'\0');exe=args[0].decode(errors='replace')
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 assert not(exe.startswith(str(R)) and '/bin/' in exe),'native job remains'
now=datetime.datetime.now(datetime.timezone.utc);state=json.loads((R/'state.json').read_text());state.update(status='COMPLETED_RESEARCH_NO_DEFAULT_CHANGE',completed_at_utc=now.isoformat(),current_stage='All authorized research, one frozen fresh Web comparison, policy revision and delivery complete',default_changed=False,current_complete_online_frontier_improvement=False,low_cost_candidate_status='RETAIN_LOW_COST_CANDIDATE',remaining_jobs=[],new_NSG_calls=1201492,new_ANN_calls=649376,new_exact_GT_queries=54096,early_stop_triggered=False);(R/'state.json').write_text(json.dumps(state,indent=2)+'\n')
h={'updated_unix':time.time(),'status':state['status'],'active_goal_deadline':'2026-09-22T22:00:00+08:00','live_sessions':[],'default_changed':False,'online_frontier_improvement':False,'candidate_status':'RETAIN_LOW_COST_CANDIDATE','user_policy_revision':'No one-point CI veto of exploration; AGENTS and research_decision_policy.md authoritative; historical E125 gate preserved','latest_complete_performance':'stages/e125_web_fresh_check_v1/report.md','latest_theory_diagnostic':'research/approximate_residual_variance_v1/report.md','latest_readonly_output_alignment':'reviews/routing_robustness_summary.json','report':'report.md','PDF':'GT10理论与性能改进研究.pdf','directions':'directions.md','next':'No queued experiment; future bounded work follows revised policy and data roles','memory_updated':False,'no_subagents':True};(R/'reviews/current_handoff.json').write_text(json.dumps(h,indent=2)+'\n')
p=R/'reviews/visual_and_figure_review.json';v=json.loads(p.read_text());v.update(final_pdf_sha256=identity(R/'GT10理论与性能改进研究.pdf')['sha256'],final_changes_inspected=['page13 theory pagination','page8 routing robustness note']);p.write_text(json.dumps(v,indent=2)+'\n')
roots={str(p.relative_to(ROOT)):identity(p) for p in [ROOT/f for f in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']]+[p for n in range(128,141) for p in (ROOT/'experiment_history').glob(f'{n}_*.md')]}
artifacts={str(p.relative_to(R)):identity(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='manifest.json'}
# Include nested manifests too; only the root output manifest excludes itself.
for p in sorted(R.rglob('manifest.json')):
 if p!=R/'manifest.json':artifacts[str(p.relative_to(R))]=identity(p)
seal={'status':state['status'],'at_utc':now.isoformat(),'manifest_excludes_itself':True,'artifact_files':artifacts,'root_documents_and_history':roots,'default_changed':False,'latest_candidate':'RETAIN_LOW_COST_CANDIDATE','no_live_native_jobs':True}
p=R/'manifest.json';assert not p.exists();p.write_text(json.dumps(seal,indent=2)+'\n');print(json.dumps({'status':seal['status'],'artifacts':len(artifacts),'root_documents_and_history':len(roots),'artifact_bytes':sum(x['bytes'] for x in artifacts.values()),'manifest_sha256':identity(p)['sha256'],'at_utc':now.isoformat()},indent=2))
