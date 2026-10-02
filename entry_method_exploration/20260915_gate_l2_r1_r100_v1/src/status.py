from pathlib import Path
import json,time,shutil
r=Path(__file__).resolve().parents[1];s=json.loads((r/'state.json').read_text())
p=Path(s.get('log','/nonexistent'))
last=[]
if p.is_file():
 with p.open('rb') as f:
  f.seek(max(0,p.stat().st_size-8192));last=f.read().decode('utf-8',errors='replace').splitlines()[-1:]
info=dict(status=s['status'],stage=s.get('stage'),pid=s.get('pid'),elapsed_seconds=round(time.time()-s.get('started_unix',time.time()),1),stages_passed=len(list((r/'reviews').glob('stage_*.json'))),free_gib=round(shutil.disk_usage(r).free/1024**3,2),latest=last)
if s.get('pid') and Path(f"/proc/{s['pid']}/status").exists():
 fields={a.split(':',1)[0]:a.split(':',1)[1].strip() for a in Path(f"/proc/{s['pid']}/status").read_text().splitlines() if ':' in a}
 info.update(process_threads=fields.get('Threads'),rss=fields.get('VmRSS'),peak_rss=fields.get('VmHWM'))
print(json.dumps(info,ensure_ascii=False,indent=2))
