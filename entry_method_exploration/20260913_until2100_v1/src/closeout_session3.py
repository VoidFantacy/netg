"""One-shot session3 closeout. No ANN/training or final-query input."""
from pathlib import Path
import json,time,shutil,hashlib,datetime,os,re
C=Path(__file__).resolve().parents[1];R=C.parents[1]
def read(p):return json.loads(p.read_text())
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ident(p):
    st=p.stat();return dict(path=str(p),bytes=st.st_size,mtime_ns=st.st_mtime_ns,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
active=[]
for p in Path('/proc').glob('[0-9]*/cmdline'):
    try:
        args=p.read_bytes().split(b'\0');pid=int(p.parent.name)
        if pid==os.getpid() or not args or Path(args[0].decode(errors='replace')).name in ['bash','sh','timeout']:continue
        cmd=' '.join(x.decode(errors='replace') for x in args)
        if 'entry_method_exploration/' in cmd and ('/bin/evaluate' in cmd or re.search(r'/src/(run|run_v2|train|deploy|build|build_modes|prepare|analyze|verify_modes|verify_queries|review_report)\.py(?:\s|$)',cmd)):active.append(dict(pid=pid,command=cmd))
    except (OSError,ProcessLookupError):pass
assert not active,active
now=time.time();assert now<1789272798
local=datetime.datetime.fromtimestamp(now,datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S +0800')
E66=C/'stage7_multimode_index_v1';E67=C/'stage8_multimode_wall_v1';E68=C/'stage9_profile_ranking_diagnosis_v1'
jobs=read(E66/'logs/jobs.json')+read(E67/'logs/jobs.json')
assert len(jobs)==8 and all(j['status']=='COMPLETE' and j['returncode']==0 and j['peak_threads']==1 and j['affinity']==[15] for j in jobs)
assert sum(j['actual_NSG'] for j in jobs)==1126608
state=read(C/'state.json');state.update(status='SESSION3_PHASE_COMPLETE_SAFE_HANDOFF',stage='E68_COMPLETE_SAFE_HANDOFF',writer='authorized independent serial session 3, safe handoff prepared',native_pids=[],session_safe_boundary_epoch=now,session_safe_boundary_local_time=local,day_goal_complete=False,next_action='Read handoff and run src/resume_inspect_v3.py. New stage10 exact-profile triple NSG diagnosis, prospective cache identity/budget first. Do not rerun stage1..9. E34 final still pending.',formal_QPS_scope='E65/E67 historical development, previously used auxiliary selection feedback',session3_status='COMPLETE_SAFE_HANDOFF',session3_native_job_seconds=sum(j['seconds'] for j in jobs),session3_final_feedback_used=False)
dump(C/'state.json',state)
p=C/'handoff_session3.md';s=p.read_text().replace('约243MiB','约245MiB').replace('本会话读至11:58','本会话读至12:01最终验收');p.write_text(s)
shutil.copy2(p,C/'handoff.md')
snap=C/'reviews/session3_closeout_snapshot';assert not snap.exists();snap.mkdir()
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:shutil.copy2(R/name,snap/name)
shutil.copy2(R/'experiment_history/README.md',snap/'history_README.md')
for name in ['state.json','handoff.md']:shutil.copy2(C/name,snap/name)
previous=read(C/'reviews/session2_closeout.json');size=sum(p.stat().st_size for p in C.rglob('*') if p.is_file())
close=C/'reviews/session3_closeout.json';assert not close.exists()
dump(close,dict(status='PASS_SESSION3_SAFE_BOUNDARY',epoch=now,local_time=local,session_safe_exit_deadline=1789272798,day_deadline=1789304400,day_goal_complete=False,native_pids=[],active_native_or_training=active,all_native_and_analysis_tools_terminal=True,native_jobs_complete=8,session3_NSG_calls=1126608,session3_HNSW_calls=982080,session3_new_builds=4,synthetic_extra_builds=1,synthetic_extra_HNSW=15,synthetic_extra_NSG=0,day_NSG_calls=2069814,day_HNSW_calls=2810656,day_new_builds=346,session3_native_job_seconds=sum(j['seconds'] for j in jobs),offline_profile_construction_seconds=sum(d['seconds'] for d in read(E66/'results/build.json')['datasets']),E68_full_score_seconds=read(E68/'reviews/verification.json')['seconds'],E68_independent_review_seconds=read(E68/'reviews/independent_review.json')['seconds'],E68_full_score_reference_queries=111808,E68_duplicate_alias_queries=55904,E66_baseline_graph_loads=2,E66_subsequent_graph_loads=12,E66_count_loads=18,E67_source_graph_loads_copies=45,E67_plain_count_loads=90,session3_development_QPS_points=55,session3_wall_batches=275,day_development_QPS_points=100,day_wall_batches=500,final_validation_QPS_points=0,E67_unique_failure_queries=93,E67_failure_L_events=182,new_GT=0,gradient_updates=0,free_GiB=shutil.disk_usage('/data').free/(1<<30),campaign_bytes_before_final_seal=size,new_bytes_since_session2_precloseout=size-previous['campaign_bytes_before_closeout_snapshots'],checked_file_identities_precloseout=read(C/'reviews/session3_precloseout_resume_check.json')['checked_files'],supervisor_review_through='2026-09-13 12:01, E66/E67/E68 all seals and figures passed',scope='fit/cal/audit/aux historical exposure; auxiliary choice counts training; E68 full profile score not utility; exact NSG cache coverage read from supervisor only; no E34 final or held-out used today',next_command='env PYTHONDONTWRITEBYTECODE=1 .venv_cpu/bin/python entry_method_exploration/20260913_until2100_v1/src/resume_inspect_v3.py'))
# Stage seals point to immutable root_after, not the mutable current root docs.
seal=C/'reviews/session3_final_artifact_freeze.json';assert not seal.exists()
files=list(snap.glob('*'))+[close,C/'handoff_session2.md',C/'handoff_session3.md',C/'candidate_inventory_v3.json',C/'next_stage_design_session3.md',C/'next_stage_design_session3_v2.md',C/'src/resume_inspect_v3.py',C/'src/inventory_session3.py',Path(__file__).resolve(),C/'reviews/supervisor_cache_coverage_readonly.json',C/'reviews/session3_precloseout_resume_check.json']
files += [stage/'reviews/final_artifact_freeze.json' for stage in [E66,E67,E68]]
dump(seal,dict(epoch=time.time(),status='SEALED_SESSION3_SAFE_HANDOFF_DAY_CONTINUES',files=[ident(p) for p in sorted(files)],day_goal_complete=False))
print(json.dumps(dict(status='SESSION3_CLOSEOUT_WRITTEN',local_time=local,files=len(files),free_GiB=shutil.disk_usage('/data').free/(1<<30),next='Run final read-only resume verification and return safely.'),ensure_ascii=False))
