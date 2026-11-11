"""Stdlib check of every pool count under all 32 prespecified mappings."""
import array,ast,collections,csv,gzip,hashlib,json,struct,sys,time,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];OLD=R.parent/'20261028_seven_dataset_scoring_v1'
sys.path.insert(0,str(OLD/'scripts'))
from packet_archive import read_bytes
def read(p):return json.loads(Path(p).read_text())
def a(p,k='i'):
 p=Path(p);v=array.array(k);v.frombytes(read_bytes(p) if not p.exists() else p.read_bytes());return v
def npz_array(path,name):
 with zipfile.ZipFile(path) as z:b=z.read(name+'.npy')
 assert b[:6]==b'\x93NUMPY';version=b[6];hsize=2 if version==1 else 4;hlen=int.from_bytes(b[8:8+hsize],'little');head=ast.literal_eval(b[8+hsize:8+hsize+hlen].decode());assert not head['fortran_order'] and head['descr']=='<i2',head
 v=array.array('h');v.frombytes(b[8+hsize+hlen:]);return v,head['shape']
def main():
 t=time.perf_counter();bounds={(x['dataset'],int(x['K'])):x for x in csv.DictReader((R/'analysis/support_bounds.csv').open())};perms={(x['dataset'],int(x['K']),int(x['permutation'])):x for x in csv.DictReader((R/'analysis/permutation_pool.csv').open())};datasets=list(dict.fromkeys(x[0] for x in bounds));checked=0
 for ds in datasets:
  c=read(OLD/f'configs/{ds}.json');model=read(Path(c['models'])/'model.json');ib=a(model['files']['id_block']);flat=a(model['files']['hub_blocks']);tab=[set(z for z in flat[i:i+8] if z>=0) for i in range(0,len(flat),8)];hubs=a(c['router']['ids']);slot={z:i for i,z in enumerate(hubs)};maps=[a(R/f'storage/models/{ds}/permutation{j:02d}.i32') for j in range(32)];source=set(a(Path(c['source_dir'])/'global_ids.i32'));d=c['test_gt'];g=a(d['path'],'q' if d['format']=='raw_i64' else 'i');stride=101 if d['format']=='ivecs' else 100;start=d.get('row_start',0);n=c['queries']['n']
  for mapping in maps:
   assert sorted(mapping)==list(range(len(tab)));assert all(len(tab[i])==len(tab[mapping[i]]) for i in range(len(tab)))
  for K in [1,100]:
   root=OLD/f'storage/results/{ds}/k{K}';mainids=a(root/'GT10_L200/raw/ids.i32');routes=a(root/'GT10_L200/raw/entry_ids.i32');trace=a(root/'REUSE-SQ_L200/trace.i32');b32=a(root/'B32_L200/raw/ids.i32');sums=[0]*32;missing_count=oldcovered=normal=maincover=scanned=0
   stored,shape=npz_array(R/f'analysis/{ds}.npz',f'k{K}_permuted_pool');assert shape==(32,n)
   for i in range(n):
    truth=set(g[(i+start)*stride+(stride==101):(i+start)*stride+(stride==101)+K]);main=set(mainids[i*K:(i+1)*K]);missing=truth-main;freq=collections.Counter(ib[v] for v in main);mainblocks=set(b for b,_ in sorted(freq.items(),key=lambda x:(-x[1],x[0]))[:8]);sl=[slot[x] for x in routes[3*i:3*i+3]];bf=collections.Counter(ib[z] for z in missing);pool=mainblocks.union(*(tab[x] for x in sl));native=set(trace[i*160:i*160+32])-{ -1 };assert pool==native
    missing_count+=len(missing);oldcovered+=len(missing&source);normal+=sum(bf[z] for z in pool);maincover+=sum(bf[z] for z in mainblocks);scanned+=sum(bf[z] for z in set(trace[i*160+32:i*160+64]) if z>=0)
    rescued=(truth&set(b32[i*K:(i+1)*K]))-main;assert rescued<=missing&source
    for j,mapping in enumerate(maps):
     pool=mainblocks.union(*(tab[mapping[x]] for x in sl));v=sum(bf[z] for z in pool);assert stored[j*n+i]==v,(ds,K,j,i);sums[j]+=v;checked+=1
   x=bounds[ds,K]
   for key,val in [('missing_members',missing_count),('old_source_covered',oldcovered),('normal_pool_covered',normal),('main_pool_covered',maincover),('normal_scanned_covered',scanned)]:assert int(x[key])==val,(ds,K,key)
   for j,val in enumerate(sums):assert int(perms[ds,K,j]['pool_missing_covered'])==val
   assert abs(float(x['fixed_ID_ceiling_pp'])-100*oldcovered/(n*K))<1e-12
  print(json.dumps(dict(dataset=ds,status='ALL_32_POOL_MAPPINGS_AUDITED')),flush=True)
 v=dict(status='PASS_E192_ALL_QUERY_STDLIB_SUPPORT_AND_PERMUTATION_AUDIT',query_mapping_cases=checked,support_rows=len(bounds),permutation_rows=len(perms),seconds=time.perf_counter()-t,scope='All pool counts and fixed-source bounds recomputed by stdlib sets; same operator, not independent personnel; no QPS inferred from diagnostics')
 (R/'reviews/diagnostic_audit.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True)
if __name__=='__main__':main()
