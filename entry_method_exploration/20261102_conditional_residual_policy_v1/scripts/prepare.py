from common import *
roles=read(OLD/'role_freeze.json')
for ds in DS:
    src=read(OLD/'configs'/f'{ds}.labels.json')
    for K,L in STATES:
        c=dict(src,K=K,L=L,experiment_root=str(R),output_dir=str(R/'storage/labels'/ds/f'k{K}_L{L}'))
        dump(R/'configs'/f'{ds}.k{K}.L{L}.labels.json',c)
    for window in ['A','B']:
        c=read(OLD/'configs'/f'{ds}.{window}.json')
        c.update(experiment_root=str(R),output_dir=str(R/'storage/results'/ds/window))
        dump(R/'configs'/f'{ds}.{window}.json',c)
dump(R/'role_freeze.json',dict(status='FROZEN_E198_ROLES',original_e197_role_sha256=sha(OLD/'role_freeze.json'),
    roles=[x for x in roles['roles'] if x['dataset'] in DS],student_fit=[0,2048],student_development_and_gate_fit=[2048,2560],
    independent_policy_calibration=[2560,3072],bank='E197 Q8 first8K',formal='E195/E197 exposed A/B',state_specific=STATES))
inputs=[]
for ds in DS:
    c=read(OLD/'configs'/f'{ds}.labels.json')
    for p in [c['queries']['path'],c['test_gt']['path'],c['q8_table'],c['table'],c['router']['ids'],c['router']['W'],c['router']['graph']]:
        inputs.append(dict(path=p,sha256=sha(p),bytes=Path(p).stat().st_size))
dump(R/'labels_inputs.json',dict(inputs=inputs,protocol_sha256=sha(R/'protocol.md')))
print('PREPARED',DS,STATES)
