import pathlib,json,subprocess,collections,statistics,csv,bisect
D=pathlib.Path(__file__).resolve().parent.parent; R=D.parent.parent; E=D.parent/'20260915_gate_l2_r1_r100_v1'
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
exe=D/'bin/diagnose.original'
nm=subprocess.check_output(['nm','-n','-S','--defined-only','-C',str(exe)],text=True)
symbols=[]
for line in nm.splitlines():
 parts=line.split(maxsplit=3)
 if len(parts)==4 and parts[2] in 'tTwW':
  try:symbols.append((int(parts[0],16),int(parts[1],16),parts[3]))
  except ValueError:pass
starts=[s[0] for s in symbols]
def sym(pc):
 i=bisect.bisect_right(starts,pc)-1
 if i>=0 and pc<symbols[i][0]+symbols[i][1]:return symbols[i][2]
 return '?'
profiles={}
for method in ['GT10-soft-t1','HNSW']:
 path=D/f'results/original/{method}.samples.json'
 if not path.exists():continue
 data=json.loads(path.read_text());pcs=[x['pc'] for x in data['histogram'] if 'diagnose.original' in x['file']]
 raw=subprocess.check_output(['addr2line','-a','-f','-C','-i','-e',str(exe)],input='\n'.join(hex(x) for x in pcs)+'\n',text=True)
 lines={};pc=None
 for line in raw.splitlines():
  if line.startswith('0x'):pc=int(line,16);lines[pc]=[]
  elif pc is not None:lines[pc].append(line)
 groups=collections.Counter();funcs=collections.Counter();sites=[]
 for h in data['histogram']:
  pc=h['pc'];stack=lines.get(pc,[]);fn=sym(pc) if stack else h['symbol'] or h['file'];s='\n'.join(stack)+'\n'+fn;off=pc-h['base'];category='other'
  if 'fvec_inner_product' in s or 'InnerProduct' in s and ('SIMD' in s or 'Distance' in s):category='distance_kernel_including_memory_stalls'
  elif 'insert_into_pool' in s or any(x in s for x in ['__adjust_heap','__push_heap','__pop_heap','stl_heap.h']):category='candidate_queue'
  elif 'libc.so' in h['file']:
   if 0x1a6880<=off<0x1a7100:category='libc_memcpy_memmove'
   else:category='other_libc'
  elif 'search_on_graph_new' in s or 'searchBaseLayerST' in s:category='graph_loop_visited_bounds_and_other'
  elif 'searchKnn' in s:category='hnsw_other'
  groups[category]+=h['count'];funcs[fn]+=h['count'];sites.append(dict(h,function=fn,inline_stack=stack,category=category,object_offset=off))
 profiles[method]={'samples':data['samples'],'sampled_seconds':data['wall_seconds'],'categories':[{'category':k,'count':v,'percent':100*v/data['samples']} for k,v in groups.most_common()],'functions':[{'function':k,'count':v,'percent':100*v/data['samples']} for k,v in funcs.most_common()],'sites':sorted(sites,key=lambda x:-x['count'])}
 save(D/f'results/{method}.symbolized.json',profiles[method])
rows=[]
for variant in ['original','prefetch','active_pool','combined','original_only']:
 p=D/f'results/{variant}/timing_progress.json'
 if p.exists():rows+=json.loads(p.read_text())
groups=collections.defaultdict(list)
for r in rows:groups[(r['variant'],r['method'],r['K'],r['L'])].append(r['seconds'])
metrics=[]
for (v,m,k,l),secs in groups.items():metrics.append({'variant':v,'method':m,'K':k,'L':l,'rounds':len(secs),'mean_seconds':statistics.mean(secs),'mean_qps':statistics.mean(10000/s for s in secs),'qps_min':min(10000/s for s in secs),'qps_max':max(10000/s for s in secs),'seconds':secs})
save(D/'results/summary.json',{'timing':metrics,'profile_categories':{k:v['categories'] for k,v in profiles.items()}})
if metrics:
 with (D/'results/timing_summary.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(metrics[0]));w.writeheader();w.writerows(metrics)
print(json.dumps({'timing':metrics,'profiles':{k:v['categories'] for k,v in profiles.items()}},ensure_ascii=False,indent=2))
