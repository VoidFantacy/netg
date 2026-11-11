from common import *
build=read(R/'reviews/build_labels.json');assert build['returncode']==0
freeze=dict(status='FROZEN_LABELS_BEFORE_RESPONSES',protocol_sha256=sha(R/'protocol.md'),binary_sha256=sha(R/'storage/labels_benchmark'),
    inputs=read(R/'labels_inputs.json'),roles_sha256=sha(R/'role_freeze.json'),configs=[dict(path=str(p),sha256=sha(p)) for p in sorted((R/'configs').glob('*.labels.json'))])
assert not (R/'labels_freeze.json').exists();dump(R/'labels_freeze.json',freeze)
records=[]
for ds in DS:
    for K,L in STATES:
        cfg=R/'configs'/f'{ds}.k{K}.L{L}.labels.json'
        rec=run(['taskset','-c','15',str(R/'storage/labels_benchmark'),'labels',str(cfg)],R/'reviews'/f'{ds}.k{K}.L{L}.labels.log')
        records.append(rec);dump(R/'reviews/labels_progress.json',records)
        print('LABELS_DONE',ds,K,L,round(rec['seconds'],2),flush=True)
dump(R/'reviews/labels_complete.json',dict(status='PASS_ALL_EIGHT_STATE_LABELS',records=records))
