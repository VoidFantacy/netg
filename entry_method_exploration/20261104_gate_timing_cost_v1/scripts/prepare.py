from common import *
import shutil
E198=R.parent/'20261102_conditional_residual_policy_v1'
def modelpath(ds,K):
    root=E198 if ds in ['coco','webvid2_5m_light_v1'] else R
    return root/'storage/models'/ds/f'k{K}_L200'/'model.json'
roles=read(OLD/'role_freeze.json')
inputs=[]
for ds in DS:
    c=read(OLD/'configs'/f'{ds}.labels.json')
    for K,L in STATES:
        cc=dict(c,K=K,L=L,experiment_root=str(R),output_dir=str(R/'storage/labels'/ds/f'k{K}_L{L}'),
                model_files=[dict(K=k,L=l,path=str(modelpath(ds,k))) for k,l in STATES])
        dump(R/'configs'/f'{ds}.k{K}.labels.json',cc)
    for window in ['A','B']:
        cc=read(OLD/'configs'/f'{ds}.{window}.json');cc.update(experiment_root=str(R),output_dir=str(R/'storage/results'/ds/window),model_files=[dict(K=k,L=l,path=str(modelpath(ds,k))) for k,l in STATES])
        dump(R/'configs'/f'{ds}.{window}.json',cc)
    for p in [c['queries']['path'],c['test_gt']['path'],c['q8_table'],c['table'],c['router']['ids'],c['router']['W'],c['router']['graph']]:
        inputs.append(dict(path=p,sha256=sha(p),bytes=Path(p).stat().st_size))
dump(R/'role_freeze.json',dict(status='FROZEN_E199_ROLES',original_sha256=sha(OLD/'role_freeze.json'),roles=[x for x in roles['roles'] if x['dataset'] in DS],
    student_fit=[0,2048],student_development_and_gate_fit=[2048,2560],independent_cal=[2560,3072],public_windows='old exposed A/B each512',reused_E198_models=['coco','webvid2_5m_light_v1']))
dump(R/'assets_freeze.json',dict(status='FROZEN_BEFORE_NEW_LABELS_AND_TRAINING',protocol_sha256=sha(R/'protocol.md'),
    label_binary=dict(path=str(E198/'storage/labels_benchmark'),sha256=sha(E198/'storage/labels_benchmark')),
    inputs=inputs,train_sources=[dict(path=str(R/'scripts'/n),sha256=sha(R/'scripts'/n)) for n in ['train.py','model_io.py']],
    configs=[dict(path=str(p),sha256=sha(p)) for p in (R/'configs').glob('*.labels.json')]))
print('PREPARED_FOUR_MULTIMODAL_DATASETS',flush=True)
