from common import *
from archive import archive
while not (R/'reviews/gates_complete.json').exists():time.sleep(2)
run([sys.executable,str(R/'scripts/prepare_matrix.py')],R/'reviews/prepare_matrix.log')
records=[]
for ds in ['flickr30k','yandex_t2i_official10M_ip_v1']:
    for K,L in STATES:
        cfg=R/'configs'/f'{ds}.k{K}.inference.json';dump(cfg,dict(model_file=str(R/'storage/models'/ds/f'k{K}_L200/model.json'),labels_dir=str(R/'storage/labels'/ds/f'k{K}_L200')))
        run(['taskset','-c','15',str(R.parent/'20261102_conditional_residual_policy_v1/storage/formal_benchmark'),'inference',str(cfg)],R/'reviews'/f'{ds}.k{K}.inference.log')
for ds in DS:
    p=R/'configs'/f'{ds}.qualification.json';rec=run(['taskset','-c','15',str(R/'storage/benchmark'),'matrix',str(p)],R/'reviews'/f'{ds}.qualification.log');records.append(rec)
    archive(R/'storage/qualification'/ds);print('QUALIFIED',ds,rec['seconds'],flush=True)
dump(R/'reviews/qualification_complete.json',dict(status='PASS_FOUR_DATASET_BRANCH_PROFILE_OLD_ACTION_AND_PLACEMENT_QUALIFICATION',records=records))
