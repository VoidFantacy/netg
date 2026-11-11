from common import *
while not (R/'reviews/assets_complete.json').exists() or not (R/'reviews/build.json').exists():time.sleep(2)
assert read(R/'reviews/build.json')['returncode']==0
cfgs=[]
for ds in DS:
    c=read(R/'configs'/f'{ds}.k1.labels.json');c.update(output_dir=str(R/'storage/gate_labels'/ds))
    dest=R/'configs'/f'{ds}.gate_labels.json';dump(dest,c);cfgs.append(dict(path=str(dest),sha256=sha(dest)))
sources=[R/'storage/benchmark',R/'protocol.md',R/'scripts/train_gates.py',R/'scripts/model_io.py']+list((R/'src').glob('*'))
for ds in DS:
    for p in read(R/'configs'/f'{ds}.gate_labels.json')['model_files']:
        mf=Path(p['path']);j=read(mf);sources.extend([mf,Path(j['node_ids']),Path(j['node_embeddings'])])
dump(R/'gate_training_freeze.json',dict(status='FROZEN_BEFORE_GATE_LABELS',configs=cfgs,sources=[dict(path=str(p),sha256=sha(p)) for p in sources]))
records=[]
for ds in DS:
    r=run(['taskset','-c','15',str(R/'storage/benchmark'),'gate_labels',str(R/'configs'/f'{ds}.gate_labels.json')],R/'reviews'/f'{ds}.gate_labels.log');records.append(r);print('GATE_LABELS',ds,r['seconds'],flush=True)
    r=run([sys.executable,str(R/'scripts/train_gates.py'),ds],R/'reviews'/f'{ds}.gate_fit.log');records.append(r)
dump(R/'reviews/gates_complete.json',dict(status='PASS_FOUR_DATASET_EIGHT_STATE_GATES',records=records))
