from common import *
E198=R.parent/'20261102_conditional_residual_policy_v1'
assert read(R/'assets_freeze.json')['status']=='FROZEN_BEFORE_NEW_LABELS_AND_TRAINING'
records=[]
for ds in ['flickr30k','yandex_t2i_official10M_ip_v1']:
    for K,L in STATES:
        r=run(['taskset','-c','15',str(E198/'storage/labels_benchmark'),'labels',str(R/'configs'/f'{ds}.k{K}.labels.json')],R/'reviews'/f'{ds}.k{K}.labels.log')
        records.append(r);print('NEW_LABELS',ds,K,r['seconds'],flush=True)
for ds in ['flickr30k','yandex_t2i_official10M_ip_v1']:
    for K,L in STATES:
        r=run([sys.executable,str(R/'scripts/train.py'),ds,str(K),str(L)],R/'reviews'/f'{ds}.k{K}.train.log')
        records.append(r);print('NEW_MODEL',ds,K,r['seconds'],flush=True)
dump(R/'reviews/assets_complete.json',dict(status='PASS_FROZEN_E198_REUSE_PLUS_NEW_FLICKR_YANDEX_MODELS',records=records))
