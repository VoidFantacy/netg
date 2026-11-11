from common import *
assert read(R/'reviews/labels_complete.json')['status']=='PASS_ALL_EIGHT_STATE_LABELS'
dump(R/'training_freeze.json',dict(status='FROZEN_BEFORE_MODEL_FIT',protocol_sha256=sha(R/'protocol.md'),
    sources=[dict(path=str(p),sha256=sha(p)) for p in [R/'scripts/train.py',R/'scripts/model_io.py']]))
records=[]
for ds in DS:
    for K,L in STATES:
        rec=run([sys.executable,str(R/'scripts/train.py'),ds,str(K),str(L)],R/'reviews'/f'{ds}.k{K}.L{L}.train.log')
        records.append(rec);dump(R/'reviews/training_progress.json',records)
        print('TRAINING_DONE',ds,K,L,rec['seconds'],flush=True)
dump(R/'reviews/training_complete.json',dict(status='PASS_EIGHT_MODELS',records=records))
