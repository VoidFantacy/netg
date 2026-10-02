import pathlib,json,subprocess,collections,statistics,csv,bisect,hashlib,ctypes,datetime
D=pathlib.Path(__file__).resolve().parent.parent;E=D.parent/'20260916_nsg_search_optimization_v1'
read=lambda p:json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert read(D/'state.json')['status']=='DIAGNOSIS_COMPLETE'
# Resolve the active glibc IFUNC implementation before classifying copy samples.
class DI(ctypes.Structure):_fields_=[('fname',ctypes.c_char_p),('base',ctypes.c_void_p),('sname',ctypes.c_char_p),('saddr',ctypes.c_void_p)]
lib=ctypes.CDLL(None);lib.dladdr.argtypes=[ctypes.c_void_p,ctypes.POINTER(DI)];lib.dladdr.restype=ctypes.c_int
libc={}
for name in ['memmove','memcpy']:
 addr=ctypes.cast(getattr(lib,name),ctypes.c_void_p).value;di=DI();assert lib.dladdr(addr,ctypes.byref(di));libc[name]={'offset':addr-di.base,'file':di.fname.decode()}
assert libc['memmove']['offset']==0x1a6880 and libc['memcpy']['offset']==0x1a6880,libc
save(D/'reviews/libc_copy_resolution.json',libc)
exe=D/'bin/profile';symbols=[]
for line in subprocess.check_output(['nm','-n','-S','--defined-only','-C',str(exe)],text=True).splitlines():
 p=line.split(maxsplit=3)
 if len(p)==4 and p[2] in 'tTwW':
  try:symbols.append((int(p[0],16),int(p[1],16),p[3]))
  except ValueError:pass
starts=[x[0] for x in symbols]
def sym(pc):
 i=bisect.bisect_right(starts,pc)-1
 return symbols[i][2] if i>=0 and pc<symbols[i][0]+symbols[i][1] else '?'
profiles={}
for method in ['GT10-soft-t1','HNSW']:
 data=read(D/f'results/profile/{method}.samples.json');pcs=[h['pc'] for h in data['histogram'] if h['file']==str(exe)]
 output=subprocess.check_output(['addr2line','-a','-f','-C','-i','-e',str(exe)],input='\n'.join(hex(x) for x in pcs)+'\n',text=True)
 stacks={};pc=None
 for line in output.splitlines():
  if line.startswith('0x'):pc=int(line,16);stacks[pc]=[]
  elif pc is not None:stacks[pc].append(line)
 groups=collections.Counter();funcs=collections.Counter();sites=[]
 for h in data['histogram']:
  pc=h['pc'];stack=stacks.get(pc,[]);fn=sym(pc) if stack else h['symbol'] or h['file'];s='\n'.join(stack)+'\n'+fn;offset=pc-h['base'];cat='other'
  if 'fvec_inner_product' in s or 'InnerProduct' in s and ('SIMD' in s or 'Distance' in s):cat='distance_kernel_including_memory_stalls'
  elif 'insert_into_pool' in s or any(v in s for v in ['__adjust_heap','__push_heap','__pop_heap','stl_heap.h']):cat='candidate_queue'
  elif 'libc.so' in h['file']:cat='libc_memcpy_memmove' if 0x1a6880<=offset<0x1a7100 else 'other_libc'
  elif 'search_on_graph_new' in s or 'searchBaseLayerST' in s:cat='graph_loop_visited_bounds_and_other'
  elif 'searchKnn' in s:cat='hnsw_other'
  groups[cat]+=h['count'];funcs[fn]+=h['count'];sites.append(dict(h,function=fn,inline_stack=stack,category=cat,object_offset=offset))
 assert sum(groups.values())==data['samples']
 profiles[method]={'samples':data['samples'],'sampled_seconds':data['wall_seconds'],'categories':{k:100*v/data['samples'] for k,v in groups.items()},'functions':[{'function':k,'count':v,'percent':100*v/data['samples']} for k,v in funcs.most_common()],'sites':sorted(sites,key=lambda x:-x['count'])}
 save(D/f'results/{method}.symbolized.json',profiles[method])
work={}
for method in ['GT10-soft-t1','HNSW']:
 rows=list(csv.DictReader((D/f'results/probe/{method}.work.csv').open()));assert len(rows)==10000
 work[method]={k:statistics.mean(int(x[k]) for x in rows) for k in rows[0] if k!='query'}
 if method=='GT10-soft-t1':
  for x in rows:
   assert int(x['neighbor_slots'])==int(x['invalid_slots'])+int(x['visited_skips'])+int(x['evaluated_neighbors'])
   assert int(x['graph_ndc'])==int(x['evaluated_neighbors'])+3
   assert int(x['pool_calls'])==int(x['accepted'])
   assert int(x['evaluated_neighbors'])==int(x['pool_bound_rejects'])+int(x['accepted'])
 for kind in ['route','graph']:
  import array
  expected=array.array('Q');ref=E/'results/webvid2_5m_light_v1'/f'{method}__{"reference" if method=="HNSW" else "optimized"}_K100_L1250'/f'{kind}_ndc.u64'
  with ref.open('rb') as f:expected.fromfile(f,10000)
  assert [int(x[kind+'_ndc']) for x in rows]==list(expected)
formal=[]
for r in csv.DictReader((E/'results/metrics.csv').open()):
 if r['dataset'].startswith('webvid') and r['method'] in ['GT10-soft-t1','HNSW'] and r['kernel']!='legacy':
  ndc=float(r['route_ndc_mean'])+float(r['graph_ndc_mean']);wall=1000/float(r['qps_from_mean_wall'])
  formal.append({'K':int(r['K']),'L':int(r['L']),'method':r['method'],'recall':float(r['recall']),'qps':float(r['qps_mean']),'mean_ms':wall,'total_ndc':ndc,'amortized_ns_per_ndc':wall*1e6/ndc})
stages={m:read(D/f'results/profile/{m}.stages.json') for m in work}
layout=read(D/'results/probe/layout.json');batch=read(D/'results/profile/batch4_numeric.json')
summary={'formal_e99':formal,'profile_categories':{k:{'samples':v['samples'],'seconds':v['sampled_seconds'],'percent':v['categories']} for k,v in profiles.items()},'stages':stages,'work_mean_per_query':work,'layout':layout,'batch4_numeric':batch}
save(D/'results/summary.json',summary)
for name,rows in [('formal_cost',formal),('work_mean',[dict(method=k,**v) for k,v in work.items()])]:
 with (D/f'results/{name}.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for manifest in ['frozen.json','protected.json']:
 for p,h in read(D/'reviews'/manifest).items():assert hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==h,p
save(D/'reviews/diagnostic_audit.json',{'status':'PASS','reviewed_at':datetime.datetime.now().isoformat(),'search_calls':80000,'real_distance_calls_and_return_parity':'PASS','work_accounting':'PASS','original_assets_unchanged':'PASS','no_new_formal_qps':True})
print(json.dumps(summary,ensure_ascii=False,indent=2))
