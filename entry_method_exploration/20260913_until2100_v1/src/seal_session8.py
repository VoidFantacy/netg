from pathlib import Path
import json,hashlib,time,shutil
C=Path(__file__).resolve().parents[1];B=C/'session8_closeout'
def identity(p):
 p=Path(p);s=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for z in iter(lambda:f.read(8<<20),b''):h.update(z)
 return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=h.hexdigest())
shutil.copy2('/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md',B/'supervisor_notes_observed.md')
files=[p for p in B.rglob('*') if p.is_file()]+[p for p in (C/'session8_report').rglob('*') if p.is_file()]+[C/x for x in ['handoff_session8.md','next_stage_design_session8.md','candidate_inventory_v9.json','session8_resource_protocol.json','reviews/inventory_v9_verification.json','src/inventory_session8.py','src/close_session8.py','src/resume_inspect_v8.py','src/seal_session8.py']]+[C/s/'reviews/final_artifact_freeze.json' for s in ['stage23_target_exact_utility_v1','stage24_sibling_links_v1','stage25_query_shortcuts_v1','stage26_query_gate_feasibility_v1']]
p=C/'reviews/session8_final_artifact_freeze.json';assert not p.exists();p.write_text(json.dumps(dict(epoch=time.time(),files=[identity(p) for p in sorted(set(files))],scope='Immutable snapshots of roots/state/handoff; E82-E85 numerical and payload proofs accepted independently by supervisor126-139, manifest anchors kept here. No mutable live-root path sealed.'),indent=2)+'\n');print('SESSION8_SEALED',len(set(files)),identity(p))
