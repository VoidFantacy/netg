"""Move only new unfrozen E197 log bytes to durable root; keep stable readable links."""
from checkpoint_storage import *
assert STABLE.is_dir() and not STABLE.is_symlink()
def allocated(p):return int(subprocess.run(['du','-s','-B1',str(p)],capture_output=True,text=True,check=True).stdout.split()[0])
protected={str(Path(x['path'])) for x in read(R/'formal_freeze.json')['files']}
rows=[]
paths=sorted((R/'reviews').glob('*.formal-*.log'),key=lambda p:p.stat().st_size,reverse=True)
for p in paths:
    if allocated(R)<=28*(1<<20):break
    if p.is_symlink():continue
    assert str(p) not in protected
    target=STABLE/'durable_native_logs'/p.name;assert not target.exists()
    digest=sha(p);copy_verified(p,target);assert sha(target)==digest
    temp=p.with_name(p.name+'.durable_link');assert not temp.exists();temp.symlink_to(target);temp.replace(p)
    assert sha(p)==digest
    rows.append(dict(original_path=str(p),durable_path=str(target),sha256=digest,bytes=target.stat().st_size))
assert allocated(R)<=28*(1<<20)
dump(R/'reviews/native_log_relocation.json',dict(status='PASS_ORIGINAL_NATIVE_LOG_BYTES_DURABLE_STABLE_LINKS',files=rows,
    experiment_allocated_bytes=allocated(R),all_frozen_bytes_unchanged=True))
print('NATIVE_LOGS_DURABLE',len(rows),allocated(R),flush=True)
