from pathlib import Path
import sys,struct,time,json,shutil
import numpy as np
O=Path(__file__).resolve().parents[1];C=O.parent;R=C.parents[1]
sys.path.insert(0,str(C/'stage32_final_tooling_v1/src'))
from common import read,dump,identity,freeze,sha,threads
threads();E73=C/'stage14_compact_modes_v1';E84=C/'stage25_query_shortcuts_v1';E90=C/'stage31_cross_source_restore_v1'
inv=read(C/'candidate_inventory_v11.json')['candidates'];ds='webvid2_5m_light_v1'
def candidate(ds,name):return next(x for x in inv if x['dataset']==ds and x['name']==name)
c=read(E73/'inputs'/ds/'aux.json');compact=next(m for m in c['methods'] if m['model_name']=='compact10')
edge=candidate(ds,'E84_shortcut10')['configuration'];restore=candidate(ds,'E90_supported10')['configuration']
base=Path(compact['graph_file']).read_bytes();before=Path(edge['graph_file']).read_bytes();restored=Path(restore['graph_file']).read_bytes()
assert len(base)==len(before)==len(restored)
head=struct.unpack_from('<6QiI3QdQ',base);n,size,label,coord=head[2:6]
w0=np.fromfile(compact['W'],np.float32).reshape(n,c['dim']);wr=np.fromfile(restore['W'],np.float32).reshape(n,c['dim'])
data=bytearray(before);back=bytearray(restored);changed=[]
for j in range(n):
 at=96+j*size+coord;z=c['dim']*4
 assert base[at:at+z]==before[at:at+z]==w0[j].tobytes()
 assert restored[at:at+z]==wr[j].tobytes()
 data[at:at+z]=wr[j].tobytes();back[at:at+z]=w0[j].tobytes()
 if w0[j].tobytes()!=wr[j].tobytes():changed.append(j)
assert bytes(back)==base and len(changed)==10
graph=O/'models/composed.hnsw';assert not graph.exists();graph.write_bytes(data)
undo=bytearray(data)
for j in range(n):
 at=96+j*size+coord;undo[at:at+c['dim']*4]=w0[j].tobytes()
assert bytes(undo)==before
new=dict(restore,graph_file=str(graph),model_name='composed10',name='composed10_L128')
dump(O/'models/model.json',new)
models=[dict(next(m for m in c['methods'] if m['model_name']=='baseline10')),dict(compact),dict(edge),dict(restore),new]
assert len({m['model_name'] for m in models})==5
paths=[O/'protocol.md',O/'config.locked.json',C/'session11_resource_protocol.json',C/'candidate_inventory_v11.json',E73/'bin/evaluate',O/'models/model.json',graph]
for split,count in [('preflight',128),('aux',7952)]:
 cfg=dict(c,methods=models,num_queries=count,input_total_rows=7952,timing_repeats=0,split='E92_historical_aux_'+split,real_call_cap=5*(2*count+16),dataset_order=0)
 dump(O/'inputs'/(split+'.json'),cfg);paths.append(O/'inputs'/(split+'.json'))
for m in models:paths += [Path(m[k]) for k in ['W','mapping','tie_ids','graph_file']]
paths += [Path(c[k]) for k in ['queries_file','gt_file','row_ids']]
yd='yandex_t2i_official10M_ip_v1';yc=candidate(yd,'E73_compact10')['configuration'];yr=candidate(yd,'E90_supported10')['configuration'];ye=candidate(yd,'E84_shortcut10')['configuration']
assert sha(yc['W'])==sha(yr['W']) and sha(yc['graph_file'])==sha(yr['graph_file'])
for m in [yc,yr,ye]:paths += [Path(m[k]) for k in ['W','mapping','tie_ids','graph_file']]
dump(O/'reviews/installation.json',dict(status='PASS',changed_vector_rows=changed,nonvector_bytes='exactly E84',reverse_restore='exactly E84 and E73',yandex_composition_alias='E84_shortcut10',yandex_new_query_count=0,draft_arithmetic_repair='Before prequery freeze: 5*(272+15920)=80960 NSG, 5*(256+15904)=80800 HNSW; original prose draft archived.'))
paths += list((O/'src').glob('*.py'))+[O/'reviews/installation.json']
freeze(O/'reviews/prequery_freeze.json',paths)
dump(O/'state.json',dict(status='READY_PREFLIGHT',day_goal_complete=False,prepared_at=time.time()))
print('E92_PREPARED',len(changed),flush=True)
