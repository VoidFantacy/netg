import gzip,hashlib,json,sys,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
ds=sys.argv[1];root=R/'storage/dense_controls'/ds;t=time.perf_counter();items=[]
assert json.loads((R/f'reviews/dense_results_audit_{ds}.json').read_text())['status'].startswith('PASS')
for p in root.rglob('trace.i32'):
 original=sha(p);size=p.stat().st_size;z=Path(str(p)+'.gz');assert not z.exists()
 with p.open('rb') as src,gzip.open(z,'wb',compresslevel=1) as out:shutil.copyfileobj(src,out,8<<20)
 h=hashlib.sha256()
 with gzip.open(z,'rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 assert h.hexdigest()==original
 items.append(dict(original_path=str(p),uncompressed_bytes=size,uncompressed_sha256=original,gzip_path=str(z),gzip_bytes=z.stat().st_size,gzip_sha256=sha(z)));p.unlink()
(root/'trace_archive.json').write_text(json.dumps(dict(status='PASS_LOSSLESS_TRACE_ARCHIVE',files=items,seconds=time.perf_counter()-t,actual_timed_packets_unchanged=True),indent=2)+'\n');print(json.dumps(dict(dataset=ds,trace_files=len(items),saved_MiB=sum(x['uncompressed_bytes']-x['gzip_bytes'] for x in items)/2**20)),flush=True)
