from train import *
import itertools

assert read(E31/'state.json')['status']=='COMPLETE'
assert read(E31/'reviews/final_audit.json')['status']=='PASS'
assert not (O/'reviews/protected_before.json').exists()
checks={}
for item in read(E31/'reviews/protected_before.json'):
    assert identity(item['path'])==item,item['path'];checks[item['path']]=item
for p in E31.rglob('*'):
    if p.is_file():checks[str(p)]=identity(p)
dump(O/'reviews/protected_before.json',list(checks.values()))
assert (O/'src/teacher_core.py').read_text()==(E31/'src/train.py').read_text().split('\ndef learning_rate')[0]
freeze(O/'reviews/frozen_protocol_before_scale.json',[O/'protocol.md']+list((O/'src').glob('*.py')))
scales={};files=[O/'protocol.md']+list((O/'src').glob('*.py'))
for ds in DS:
    data=load_fit(ds);q,p,ts,g,hits,ndc=data;n=len(q)
    candidates=np.fromfile(E28/'inputs'/ds/'proposals/candidates.i32',np.int32).reshape(n,8)
    expected=candidates[:,np.array(list(itertools.combinations(range(8),3)))];assert np.array_equal(expected,ts.numpy())
    best=hits.max(1).values;cost=ndc.masked_fill(hits!=best[:,None],torch.inf).min(1).values
    assert torch.equal(g,(hits==best[:,None])&(ndc==cost[:,None]))
    model=Transform(p);a=compute(model,data,'teacher',with_anchor=False);teacher_grad=model.fn.weight.grad.detach().clone()
    b=compute(model,data,'reward',with_anchor=False);reward_grad=model.fn.weight.grad.detach().clone()
    assert b['gradient_norm']>1e-12
    beta=a['gradient_norm']/b['gradient_norm'];c=compute(model,data,'reward',beta,with_anchor=False)
    assert abs(c['gradient_norm']/a['gradient_norm']-1)<1e-10
    scales[ds]=dict(beta=beta,teacher_data_gradient_norm=a['gradient_norm'],unscaled_reward_gradient_norm=b['gradient_norm'],
        scaled_reward_gradient_norm=c['gradient_norm'],gradient_cosine=float((teacher_grad*reward_grad).sum()/(teacher_grad.norm()*reward_grad.norm())),
        initial_teacher=a,initial_reward=b,fit_queries=n,selection='fixed once at A0 before any optimizer update')
    for path in (O/'inputs'/ds).rglob('*'):
        if path.is_file():assert sha(path)==sha(E31/'inputs'/ds/path.relative_to(O/'inputs'/ds));files.append(path)
    cfg=read(O/'inputs'/ds/'fit/config.json')
    files.extend(Path(cfg[x]) for x in ['queries_file','gt_file','row_ids','hub_ids'])
    files.extend([E24/'models'/ds/'gt10_hard/W.f32',E28/'inputs'/ds/'proposals/triples.i32',E28/'inputs'/ds/'proposals/candidates.i32',E28/'labels'/ds/'hits.u8',E28/'labels'/ds/'graph_ndc.u32'])
dump(O/'reviews/reward_scales.json',scales)
files += [O/'reviews/reward_scales.json',O/'reviews/objective_tests.json']
freeze(O/'reviews/frozen_before_training.json',files)
dump(O/'reviews/preflight.json',dict(status='PASS',protected_files=len(checks),teacher_core_identical=True,complete_action_enumeration=True,teacher_definition_reconstructed=True,new_labels=0,NSG_calls=0,heldout_access=False))
dump(O/'state.json',dict(status='PREFLIGHT_COMPLETE_TRAINING_PENDING',training_runs=0,real_search_calls=0,heldout_access=False))
print('PREFLIGHT_PASS',len(checks),scales,flush=True)
