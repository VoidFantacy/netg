"""Complete training and frozen full comparisons after stage1 has terminated."""
from common import *
from execute import Executor
from synthetic import synthetic
from cluster import cluster,feature_specs,audit_features
from train import train_dataset
from audit import audit_inputs,audit_directions,audit_labels,audit_predictions,audit_fit_replay,audit_acceptance

def frozen_python():
    paths=[p for p in (RUN/'src').glob('*.py')]+[RUN/'reviews/implementation_scope.md',RUN/'reviews/analysis_contract.md',RUN/'reviews/analysis_contract.initial.md',RUN/'reviews/execute.stage1_initial.py',RUN/'reviews/oracle_domain_correction.md',RUN/'method.md']
    out=RUN/'reviews/python_frozen.json'
    if out.exists():
        for f in read(out)['files']:assert ident(f['path'])==f
    else:dump(out,dict(created_unix=time.time(),files=[ident(p) for p in paths]))

def model_identity():
    paths=[p for p in (RUN/'models').rglob('*') if p.is_file()]
    return [ident(p) for p in paths]

def forward(ex,ds,role):
    cfg=base_config(ds,role);cfg.update(mode='features',features=feature_specs(ds))
    ex.execute(cfg,RUN/'results'/ds/f'{role}_features',f'{role}_features');audit_features(ds,role)
    cfg.update(mode='predict',models=[m for m in read(RUN/'models'/ds/'methods.json') if m['type']=='learned'],save_all_scores=False)
    ex.execute(cfg,RUN/'results'/ds/f'{role}_predictions',f'{role}_predictions');audit_predictions(ds,role)

def main():
    os.sched_setaffinity(0,{15});ex=Executor('stage2');assert (RUN/'reviews/stage1_complete.json').exists()
    assert all(j.get('exit_code')==0 for j in ex.jobs),'diagnose previous job errors before proceeding'
    frozen_python();synthetic(ex)
    dump(RUN/'state.json',dict(status='AUDITING_LABELS_AND_TRAINING',runner_pid=os.getpid(),pending=['label/model audits','frozen acceptance','complete curve','final report']))
    for ds in LOCK['datasets']:
        audit_inputs(ds);audit_directions(ds);audit_labels(ds)
        if not(RUN/'reviews'/f'clustering_{ds}.json').exists():cluster(ds)
        cfg=base_config(ds,'fit');cfg.update(mode='features',features=feature_specs(ds))
        ex.execute(cfg,RUN/'results'/ds/'fit_features','fit_features');audit_features(ds,'fit')
        if not(RUN/'models'/ds/'training_report.json').exists():train_dataset(ds)
        forward(ex,ds,'fit')
        cfg=base_config(ds,'fit');cfg.update(mode='evaluate',methods=read(RUN/'models'/ds/'methods.json'),points=[dict(K=K,L=128) for K in (1,100)],repeats=1)
        ex.execute(cfg,RUN/'results'/ds/'fit_replay','fit_replay');audit_fit_replay(ds)
    # Freeze every dictionary, weight, alpha, fixed action and model before acceptance materialization.
    frozen=RUN/'reviews/models_frozen.json'
    if frozen.exists():
        for f in read(frozen)['files']:assert ident(f['path'])==f
    else:dump(frozen,dict(status='PASS',created_unix=time.time(),files=model_identity(),
                          training_seconds=sum(read(RUN/'models'/ds/'training_report.json')['seconds'] for ds in LOCK['datasets'])))
    prepare('accept')
    for ds in LOCK['datasets']:audit_inputs(ds);forward(ex,ds,'accept')
    dump(RUN/'state.json',dict(status='RUNNING_FROZEN_ACCEPTANCE',runner_pid=os.getpid(),pending=['complete 11-method L128','complete six-method five-budget curves','independent audit/report']))
    for ordinal,ds in enumerate(LOCK['datasets']):
        cfg=base_config(ds,'accept');cfg.update(mode='evaluate',methods=read(RUN/'models'/ds/'methods.json'),points=[dict(K=K,L=128) for K in (1,100)],repeats=3,dataset_order=ordinal)
        ex.execute(cfg,RUN/'results'/ds/'accept','accept')
    dump(RUN/'state.json',dict(status='RUNNING_FROZEN_BUDGET_CURVES',runner_pid=os.getpid(),pending=['complete six-method curves','independent audit/report']))
    for ordinal,ds in enumerate(LOCK['datasets']):
        cfg=base_config(ds,'accept');methods=read(RUN/'models'/ds/'methods.json')
        cfg.update(mode='evaluate',methods=[m for m in methods if m['name'] in ('GT10','Single1','BestFixed','GraphCost','GraphRecall','RandomCost')],
                   points=[dict(K=K,L=L) for K in (1,100) for L in ((64,256,400,800) if K==1 else (100,256,400,800))],repeats=3,dataset_order=ordinal)
        ex.execute(cfg,RUN/'results'/ds/'curve','curve')
    for ds in LOCK['datasets']:audit_acceptance(ds)
    for f in read(frozen)['files']:assert ident(f['path'])==f
    ex.check()
    dump(RUN/'reviews/stage2_complete.json',dict(status='PASS',seconds=time.time()-ex.start,models_frozen_unix=read(frozen)['created_unix']))
    dump(RUN/'state.json',dict(status='MEASUREMENTS_COMPLETE',pending=['independent cost and result audit','analysis figures/report','synchronized documentation'],active_processes=[]))

if __name__=='__main__':
    try:main()
    except BaseException as err:
        dump(RUN/'state.json',dict(status='EXECUTION_ERROR_REQUIRES_DIAGNOSIS',stage='stage2',error=repr(err),method_conclusion=None));raise
