from pathlib import Path
import json,hashlib,time,shutil,re,subprocess
C=Path(__file__).resolve().parents[1];R=C.parents[1];B=C/'session9_closeout'
def ident(p):
 p=Path(p);s=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for z in iter(lambda:f.read(8<<20),b''):h.update(z)
 return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=h.hexdigest())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
md=[C/'session9_report/report.md',C/'handoff_session9.md',C/'next_stage_design_session9.md',C/'session9_final_preparation/readme.md',C/'stage29_proposal_rank_diagnosis_v1/report_v2.md']+[R/'experiment_history'/x for x in ['75_edge_utility.md','76_utility_proposals.md','77_proposal_rank_diagnosis.md']]
links=0
for p in md:
 for ref in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if ref.startswith(('http:','https:','#')):continue
  ref=ref.split('#')[0];target=Path(ref) if ref.startswith('/') else p.parent/ref;assert target.exists(),(str(p),ref);links+=1
r=subprocess.run(['git','diff','--check','--','AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'],cwd=R,text=True,capture_output=True);assert r.returncode==0,r.stdout+r.stderr
# Read commands only, omit command arguments/environment from process output.
p=subprocess.run(['ps','-eo','pid,ppid,comm'],text=True,capture_output=True);(B/'local_namespace_process_sample.txt').write_text(p.stdout)
assert not any(line.split()[-1] in ['evaluate','train','g++','cc1plus'] for line in p.stdout.splitlines()[1:])
shutil.copy2('/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md',B/'supervisor_notes_final_observed.md')
dump(B/'final_checks.json',dict(status='PASS',local_links=links,git_diff_check=0,process_sample_scope='Local isolated namespace only; native and verifier tool terminals separately checked.',pending_tool_sessions=[],final_E34_access=False,day_goal_complete=False))
folders=[C/x for x in ['stage27_edge_utility_v1','stage28_utility_proposals_v1','stage29_proposal_rank_diagnosis_v1','session9_report','session9_final_preparation','session9_closeout']]
files=set(p for o in folders for p in o.rglob('*') if p.is_file() and not p.is_symlink());files|={p for p in C.rglob('*') if p.is_file() and not p.is_symlink() and p.stat().st_mtime>=1789290509.9};files|={R/f for f in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']};files|={R/'experiment_history'/f for f in ['README.md','75_edge_utility.md','76_utility_proposals.md','77_proposal_rank_diagnosis.md']};used=sum(p.stat().st_size for p in files);free=shutil.disk_usage('/data').free;remaining=192*2**20-used;assert remaining>0 and free-remaining-72*2**20>6.55*2**30
old=json.loads((B/'resource_accounting.json').read_text());dump(B/'resource_accounting_final.json',dict(status='PASS',accounted_bytes=used,accounted_MiB=used/2**20,additional_since_first_bytes=used-old['accounted_bytes'],free_GiB=free/2**30,after_remaining_cap_and_72MiB_GiB=(free-remaining-72*2**20)/2**30,final_seal_metadata_reserved_MiB=1,scope=old['scope']))
# Seal snapshots rather than mutable root/state/handoff aliases.
sealpaths=[p for o in [B,C/'session9_report',C/'session9_final_preparation'] for p in o.rglob('*') if p.is_file()]+[C/x for x in ['handoff_session9.md','next_stage_design_session9.md','candidate_inventory_v10.json','session9_resource_protocol.json','reviews/inventory_v10_verification.json','src/prepare_e88.py','src/inventory_session9.py','src/report_session9.py','src/closeout_session9.py','src/resume_inspect_v9.py','src/seal_session9.py','src/prepare_final_metadata_session9.py']]+[C/st/'reviews/final_artifact_freeze.json' for st in ['stage27_edge_utility_v1','stage28_utility_proposals_v1','stage29_proposal_rank_diagnosis_v1']]+[C/'stage29_proposal_rank_diagnosis_v1/reviews/supplement_freeze.json']
p=C/'reviews/session9_final_artifact_freeze.json';assert not p.exists();dump(p,dict(epoch=time.time(),files=[ident(p) for p in sorted(set(sealpaths))],scope='Immutable root/state/handoff and complete closeout snapshots, three completed stage seal anchors; no mutable live root paths. E86-E88 full proofs independently reviewed.'))
print('SESSION9_FINAL_SEAL_PASS',len(set(sealpaths)),used/2**20,free/2**30)
