#!/usr/bin/env python3
"""Fixed joint-search preference objective. Only fit arrays are read here."""
import argparse
import math
import time
import numpy as np
import torch
import torch.nn.functional as F
from common import RUN, dump, identity, read, sha


class Objective:
    def __init__(self, q, p, tau, qi, winner, loser, weight):
        self.q, self.p, self.tau = q, p, tau
        self.n, self.d = q.shape; self.h = p.shape[0]
        self.qi, self.winner, self.loser, self.weight = qi, winner, loser, weight
        self.offset = (q @ p.T) / tau

    def parts(self, delta, lam):
        scores = self.offset + self.q @ delta.T
        margin = scores[self.qi, self.winner] - scores[self.qi, self.loser]
        data = (self.weight * F.softplus(-margin)).sum() / self.n
        penalty = lam * delta.square().sum() / (2 * self.h)
        return data, penalty

    def value(self, delta, lam):
        a, b = self.parts(delta, lam)
        return a + b


def full_gradient(obj, delta, lam):
    x = delta.detach().clone().requires_grad_(True)
    loss = obj.value(x, lam)
    return torch.autograd.grad(loss, x)[0].detach()


def fit(obj, family, lam, v0, settings, dest=None):
    if family == 'full':
        parameter = torch.zeros((obj.h, obj.d), dtype=torch.float64, requires_grad=True)
        parameters = [parameter]
        def matrix(): return parameter
    else:
        v = v0.clone().requires_grad_(True)
        z = torch.zeros((v.shape[1], obj.h), dtype=torch.float64, requires_grad=True)
        parameters = [v, z]
        def matrix(): return (v @ z).T
    optim = torch.optim.LBFGS(parameters, lr=1.0, **settings)
    evaluations, trace = 0, []
    started = time.monotonic()
    def closure():
        nonlocal evaluations
        optim.zero_grad(set_to_none=True)
        data, penalty = obj.parts(matrix(), lam)
        loss = data + penalty
        assert torch.isfinite(loss), 'nonfinite objective'
        loss.backward()
        evaluations += 1
        if evaluations == 1 or evaluations % 10 == 0:
            item = {'function_evaluation': evaluations, 'data_loss': float(data.detach()),
                    'penalty': float(penalty.detach()), 'objective': float(loss.detach()),
                    'gradient_l2': math.sqrt(sum(float(x.grad.square().sum()) for x in parameters)),
                    'seconds': time.monotonic()-started}
            trace.append(item)
            if dest:
                with (dest/'trace.jsonl').open('a') as f:
                    f.write(__import__('json').dumps(item)+'\n')
                print(__import__('json').dumps({'family':family,'lambda':lam,**item}), flush=True)
        return loss
    initial = float(obj.value(matrix(), lam).detach())
    optim.step(closure)
    optim.zero_grad(set_to_none=True)
    data, penalty = obj.parts(matrix(), lam)
    (data+penalty).backward()
    delta = matrix().detach().clone()
    full_g = full_gradient(obj, delta, lam)
    norm_g = float(torch.linalg.vector_norm(full_g))
    # Strong convexity of the free-D objective gives f(D)-f* <= ||grad f(D)||²/(2 lambda/H).
    bound = norm_g**2 * obj.h / (2*lam)
    fstate = optim.state[parameters[0]]
    report = {'family': family, 'lambda': lam, 'initial_objective': initial,
        'objective': float((data+penalty).detach()), 'data_loss': float(data.detach()),
        'penalty': float(penalty.detach()), 'function_evaluations': evaluations,
        'optimizer_iterations': fstate.get('n_iter'), 'optimizer_func_evals': fstate.get('func_evals'),
        'parameter_gradient_l2': math.sqrt(sum(float(x.grad.square().sum()) for x in parameters)),
        'parameter_gradient_max': max(float(x.grad.abs().max()) for x in parameters),
        'full_matrix_gradient_l2': norm_g,
        'full_objective_optimality_gap_upper_bound': bound,
        'full_solver_certified_to_1e-6': family=='full' and bound<=1e-6,
        'bound_interpretation': 'Exact-arithmetic strongly convex bound from measured float64 gradient; for rank8 it bounds gap to unconstrained optimum, not rank-constrained stationarity',
        'delta_scaled_norm': float(torch.linalg.vector_norm(delta)),
        'W_minus_P0_norm': float(torch.linalg.vector_norm(delta))*obj.tau,
        'seconds': time.monotonic()-started, 'trace': trace}
    assert report['objective'] <= initial+1e-10, 'optimizer failed to decrease fixed objective'
    w64 = obj.p + obj.tau * delta
    w32 = w64.numpy().astype('<f4')
    # Export keeps raw inner-product geometry; no row normalization or mapping change.
    exported_delta = (torch.from_numpy(w32.astype('float64'))-obj.p)/obj.tau
    with torch.no_grad():
        export_loss = float(obj.value(exported_delta, lam))
    report['export_objective'] = export_loss
    report['export_objective_abs_error'] = abs(export_loss-report['objective'])
    assert report['export_objective_abs_error'] < 1e-6, 'float32 folding changed objective materially'
    if family == 'rank8':
        basis = torch.linalg.qr(v.detach(), mode='reduced').Q
        projected = (full_g @ basis) @ basis.T
        report['full_gradient_outside_learned_subspace_ratio'] = float(torch.linalg.vector_norm(full_g-projected))/max(norm_g,1e-30)
        report['factor_rank'] = v.shape[1]
        if dest: np.savez(dest/'factors.npz', V=v.detach().numpy(), Z=z.detach().numpy())
    if dest:
        w32.tofile(dest/'W.f32'); np.save(dest/'D.f64.npy',delta.numpy())
        report['W'] = identity(dest/'W.f32')
        dump(dest/'training.json', report)
    return delta, report


def load_objective(dataset):
    inp = RUN/'inputs'/dataset
    prepared = read(inp/'prepared.json'); meta=read(inp/'fit/config.json')
    labels=RUN/'labels'/dataset
    complete=read(labels/'complete.json'); assert complete['status']=='COMPLETE'
    n,h,d=meta['num_queries'],prepared['H'],prepared['dim']
    assert n==20000
    options=np.fromfile(inp/'fit/options.i32',dtype='<i4').reshape(n,4,6)
    hits=np.fromfile(labels/'hits.u8',dtype='u1').reshape(n,4,6).astype('int16')
    assert hits.min()>=0 and hits.max()<=10
    left,right=np.triu_indices(6,1)
    difference=hits[:,:,left]-hits[:,:,right]
    magnitude=np.abs(difference).astype('float64')
    total=magnitude.sum(axis=(1,2))
    weight=magnitude/np.maximum(total[:,None,None],1)
    positive=difference>0; valid=difference!=0
    winner=np.where(positive,options[:,:,left],options[:,:,right])
    loser=np.where(positive,options[:,:,right],options[:,:,left])
    qi=np.broadcast_to(np.arange(n)[:,None,None],valid.shape)[valid].copy()
    assert np.allclose(weight.sum(axis=(1,2)),total>0)
    assert (winner[valid]!=loser[valid]).all()
    q=torch.from_numpy(np.fromfile(inp/'fit/queries.f32',dtype='<f4').reshape(n,d).astype('float64'))
    p=torch.from_numpy(np.fromfile(inp/'P0.f32',dtype='<f4').reshape(h,d).astype('float64'))
    obj=Objective(q,p,prepared['tau'],torch.from_numpy(qi),torch.from_numpy(winner[valid].astype('int64')),
                  torch.from_numpy(loser[valid].astype('int64')),torch.from_numpy(weight[valid]))
    stats={'fit_queries':n,'active_queries':int((total>0).sum()),'nonzero_pairs':int(valid.sum()),
        'zero_difference_pairs':int((~valid).sum()),'pair_weighting':'per-query normalized absolute joint-hit difference',
        'baseline_exact_fast3_recall':float(hits[:,0,0].mean()/10),
        'sampled_joint_oracle_recall':float(hits.max(axis=(1,2)).mean()/10),
        'oracle_scope':'fit-only free choice among sampled triple labels; not deployable or equal-cost',
        'tau':prepared['tau'], 'source_files':[identity(x) for x in [inp/'fit/options.i32',labels/'hits.u8',inp/'fit/queries.f32',inp/'P0.f32']]}
    return obj,stats


def self_test():
    torch.set_num_threads(1)
    q=torch.tensor([[1.,0.],[0.,1.],[1.,1.]],dtype=torch.float64)
    p=torch.zeros((3,2),dtype=torch.float64)
    obj=Objective(q,p,1.,torch.tensor([0,1,2]),torch.tensor([0,1,2]),torch.tensor([1,0,0]),torch.ones(3,dtype=torch.float64))
    x=torch.tensor([[.2,-.1],[.1,.3],[-.2,.1]],dtype=torch.float64)
    g=full_gradient(obj,x,.1);eps=1e-6
    for i in range(3):
        for j in range(2):
            plus=x.clone();minus=x.clone();plus[i,j]+=eps;minus[i,j]-=eps
            numerical=(float(obj.value(plus,.1))-float(obj.value(minus,.1)))/(2*eps)
            assert abs(numerical-float(g[i,j]))<1e-8
    settings={'max_iter':200,'max_eval':250,'history_size':20,'tolerance_grad':1e-10,'tolerance_change':1e-14,'line_search_fn':'strong_wolfe'}
    _,_,vh=torch.linalg.svd(full_gradient(obj,torch.zeros_like(x),.1),full_matrices=False)
    d,report=fit(obj,'full',.1,vh.T,settings)
    scores=q@d.T
    assert ((scores[obj.qi,obj.winner]-scores[obj.qi,obj.loser])>0).all()
    assert report['full_objective_optimality_gap_upper_bound']<1e-10
    dr,rr=fit(obj,'rank8',.1,vh.T,settings)
    assert abs(rr['objective']-report['objective'])<1e-8
    dump(RUN/'reviews/trainer_self_test.json',{'status':'PASS','checks':['independent central finite differences','known three preferences learned','strong convex gradient certificate','full-capacity factor optimum matches full matrix','float32 folded objective parity'],
        'full_gap_bound':report['full_objective_optimality_gap_upper_bound'],'factor_vs_full_objective_difference':abs(rr['objective']-report['objective'])})
    print('TRAINER_SELF_TEST_PASS',flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset');parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:return self_test()
    cfg=read(RUN/'config.locked.json');assert sha(RUN/'protocol.md')==cfg['protocol_sha256']
    torch.set_num_threads(cfg['train_threads']);torch.set_num_interop_threads(1)
    assert torch.version.cuda is None and not torch.cuda.is_available()
    torch.use_deterministic_algorithms(True)
    dest=RUN/'models'/args.dataset;assert not dest.exists();dest.mkdir()
    obj,stats=load_objective(args.dataset);dump(dest/'objective_data.json',stats)
    g=full_gradient(obj,torch.zeros((obj.h,obj.d),dtype=torch.float64),1.)
    _,singular,vh=torch.linalg.svd(g,full_matrices=False)
    v0=vh[:cfg['rank']].T.contiguous()
    for j in range(v0.shape[1]):
        if v0[v0[:,j].abs().argmax(),j]<0:v0[:,j]*=-1
    np.save(dest/'initial_gradient_singular_values.npy',singular.numpy())
    np.save(dest/'initial_V.f64.npy',v0.numpy())
    settings={k:v for k,v in cfg['optimizer'].items() if k!='name'}
    models=[]
    for family in ['full','rank8']:
        for lam in cfg['regularization']:
            folder=dest/f'{family}_lambda{lam:g}';folder.mkdir()
            _,report=fit(obj,family,lam,v0,settings,folder)
            models.append({'name':folder.name,'family':family,'lambda':lam,'W':str(folder/'W.f32'),
                           'W_sha256':sha(folder/'W.f32'),'training_report':str(folder/'training.json')})
    dump(dest/'complete.json',{'status':'ALL_CANDIDATES_TRAINED_BEFORE_CAL','models':models,
        'protocol_sha256':cfg['protocol_sha256'],'trainer_sha256':sha(__file__),
        'cal_used':False,'audit_used':False,'validation_used':False,'heldout_used':False})
    print('ALL_CANDIDATES_TRAINED',args.dataset,flush=True)

if __name__=='__main__':main()
