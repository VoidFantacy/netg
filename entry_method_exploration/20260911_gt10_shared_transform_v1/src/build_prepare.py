from setup import *
import numpy as np
def policy(ds,name,W=None):
 prep=json.loads((E24/'inputs'/ds/'prepared.json').read_text());ids=str(E24/'inputs'/ds/'hub_ids.i32')
 return dict(name=name,family='profile',model_name=name,W=str(W or E24/'models'/ds/name/'W.f32'),mapping=ids,tie_ids=ids,hub_count=prep['H'],dim=prep['dim'],k=3,seed=20260828,hnsw_seed=20260828,slot_labels=False,canonical_entry_order=True)
if __name__=='__main__':
 assert json.loads((O/'reviews/preflight.json').read_text())['status']=='PASS'
 base=json.loads((E27/'bin/evaluate.build.json').read_text())['argv']
 for name in ['evaluate','propose','label']:
  argv=base.copy();argv[argv.index(str(E27/'src/evaluate.cpp'))]=str(O/'src'/f'{name}.cpp');argv[-1]=str(O/'bin'/name)
  start=time.time();r=subprocess.run(argv,capture_output=True,text=True);(O/'logs'/f'{name}.build.log').write_text(r.stdout+r.stderr)
  dump(O/'bin'/f'{name}.build.json',dict(argv=argv,seconds=time.time()-start,exit_code=r.returncode,sources=[identity(O/'src'/f'{s}.cpp') for s in ['legacy_reference','benchmark_with_nsg',name]]))
  assert r.returncode==0,(name,r.stderr[-2000:]);print('built',name,flush=True)
 for ds in DS:
  c=json.loads((O/'inputs'/ds/'fit/config.json').read_text());c['anchor']=str(E24/'models'/ds/'gt10_hard/W.f32');c['policies']=[policy(ds,s) for s in ['gt1_hard','gt10_hard']]
  # Same seed and real-ID/canonical-order contract as E24 deployment.
  dump(O/'inputs'/ds/'propose.json',c)
  c.update(threads=16,triples_file=str(O/'inputs'/ds/'proposals/triples.i32'),logical_call_cap=1120000,old_triples=str(E23/'inputs'/ds/'fit/triples.i32'),old_ids=str(E23/'labels'/ds/'ids.i32'),old_ndc=str(E23/'labels'/ds/'graph_ndc.u32'))
  dump(O/'inputs'/ds/'label.json',c)
