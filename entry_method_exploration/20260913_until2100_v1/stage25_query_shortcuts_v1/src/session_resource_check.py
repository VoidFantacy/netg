from common import *
folders=[C/'stage23_target_exact_utility_v1',C/'stage24_sibling_links_v1',O]
counts={p.name:sum(f.stat().st_size for f in p.rglob('*') if f.is_file() and not f.is_symlink()) for p in folders}
assert sum(counts.values())<192*2**20
resources()
record=dict(status='PASS',epoch=time.time(),stage_bytes=counts,total_bytes=sum(counts.values()),session_cap_bytes=192*2**20,free_bytes=shutil.disk_usage('/data').free,note='Supplement includes E83 omitted by frozen common.resources; frozen source remains unchanged. All three stage caps total 160 MiB, below session 192 MiB.')
dump(O/'reviews'/('session_resource_'+str(time.time_ns())+'.json'),record)
print(json.dumps(record))
