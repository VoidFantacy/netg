"""One frozen local-mean control; only entered after the response gate."""
from common import *

def intervals(values, folds):
    rng = np.random.default_rng(20260922)
    blocks = [np.flatnonzero(folds == f) for f in range(4)]
    draws = []
    for _ in range(50):
        idx = np.concatenate([b[rng.integers(len(b),size=(100,len(b)))] for b in blocks],axis=1)
        draws.append(values[idx].mean(1))
    return np.quantile(np.concatenate(draws),[.025,.975],axis=0).tolist()

def evaluate(ds,cfg,lock):
    data = np.load(RUN/'analysis'/f'{ds}.npz')
    raw = np.fromfile(cfg['native']['queries'],'<f4').reshape(4096,cfg['native']['dimension'])
    q = raw.astype('f8')
    q /= np.linalg.norm(q,axis=1,keepdims=True)
    methods = [m['name'] for m in cfg['native']['methods']]
    cols = [methods.index(a) for a in lock['actions']]
    target_hits = np.stack([data[f'K{K}_L{cfg["target"][str(K)][1]}'][:,cols] for K in [1,100]],axis=-1)
    low_hits = np.stack([data[f'K{K}_L128'][:,cols] for K in [1,100]],axis=-1)
    target = target_hits-target_hits[:,:1]
    low = low_hits-low_hits[:,:1]
    denominators = np.array([1.,100.])
    folds = np.empty(4096,'i4')
    for f,rows in enumerate(np.array_split(np.random.default_rng(lock['seed']).permutation(4096),4)):
        folds[rows] = f
    predictions = {name:np.zeros((4096,len(cols),2),'f8') for name in lock['information_methods']}
    neighbors = np.empty((4096,lock['info_neighbors']),'i4')
    fit_rows = {}
    for f in range(4):
        fit = np.flatnonzero(folds != f)
        outer = np.flatnonzero(folds == f)
        assert len(fit) == 3072 and int(np.sqrt(len(fit))) == lock['info_neighbors']
        sim = q[outer]@q[fit].T
        nearest = np.stack([np.lexsort((data['source_rows'][fit],-s))[:lock['info_neighbors']] for s in sim])
        nn = fit[nearest]
        assert np.all(folds[nn] != f)
        neighbors[outer] = nn
        shuffled = np.random.default_rng(lock['seed']+f).permutation(fit)
        predictions['TargetKNN'][outer] = target[nn].sum(1,dtype='i8')/(lock['info_neighbors']*denominators)
        predictions['LowKNN'][outer] = low[nn].sum(1,dtype='i8')/(lock['info_neighbors']*denominators)
        predictions['TargetFixed'][outer] = target[fit].sum(0,dtype='i8')/(len(fit)*denominators)
        predictions['ShuffleKNN'][outer] = target[shuffled[nearest]].sum(1,dtype='i8')/(lock['info_neighbors']*denominators)
        fit_rows[str(f)] = dict(fit=fit.tolist(),outer=outer.tolist(),shuffled_fit=shuffled.tolist())
    summaries = {}
    deltas = {}
    saved = dict(source_rows=data['source_rows'],folds=folds,neighbors=neighbors)
    for method,pred in predictions.items():
        actions = pred.argmax(1)
        assert np.all(pred[:,0] == 0)
        delta = target[np.arange(4096)[:,None],actions,np.arange(2)[None,:]]/denominators
        mean = delta.mean(1)
        deltas[method] = mean
        saved[method+'_scores'] = pred
        saved[method+'_actions'] = actions
        saved[method+'_delta'] = delta
        summaries[method] = dict(mean_gain_pp=float(100*mean.mean()),CI95_pp=intervals(100*mean,folds),
            K_mean_gain_pp=(100*delta.mean(0)).tolist(),switches=(actions != 0).sum(0).tolist(),
            fold_gain_pp=[float(100*mean[folds==f].mean()) for f in range(4)])
    contrasts = {}
    for control in ['LowKNN','TargetFixed','ShuffleKNN']:
        diff = 100*(deltas['TargetKNN']-deltas[control])
        contrasts[control] = dict(gain_pp=float(diff.mean()),CI95_pp=intervals(diff,folds))
    main = summaries['TargetKNN']
    gate = dict(positive_mean=main['mean_gain_pp']>0,positive_lower=main['CI95_pp'][0]>0,
        both_K_nonnegative=min(main['K_mean_gain_pp'])>=0,
        beats_fixed_lower=contrasts['TargetFixed']['CI95_pp'][0]>0,
        beats_shuffle_lower=contrasts['ShuffleKNN']['CI95_pp'][0]>0,
        beats_low_mean=contrasts['LowKNN']['gain_pp']>0)
    np.savez_compressed(RUN/'analysis'/f'{ds}.information.npz',**saved)
    dump(RUN/'analysis'/f'{ds}.information_roles.json',fit_rows)
    return dict(methods=summaries,contrasts=contrasts,gate=gate,pass_all=all(gate.values()))

if __name__ == '__main__':
    assert read(RUN/'analysis/response.json')['information_control_eligible'], 'Conditional control not authorized by its gate'
    assert not (RUN/'analysis/information.json').exists()
    lock = read(RUN/'config.locked.json')
    start = time.monotonic()
    dump(RUN/'reviews/information_source_frozen.json',dict(files=[identity(Path(__file__)),identity(RUN/'protocol.md'),identity(RUN/'config.locked.json')],created_unix=time.time()))
    results = {ds:evaluate(ds,cfg,lock) for ds,cfg in lock['datasets'].items()}
    passed = all(r['pass_all'] for r in results.values())
    dump(RUN/'analysis/information.json',dict(results=results,pass_all=passed,seconds=time.monotonic()-start,
        optimizer_steps=0,label_based_outer_folds=8,scope='exposed-development quality-only information control, not cheap deployment or QPS'))
    dump(RUN/'state.json',dict(status='INFORMATION_SIGNAL_REQUIRES_CHEAP_METHOD' if passed else 'STOP_TARGET_LOCAL_INFORMATION',
        completed=False,pending=['independent_audit','report','documentation']+(['derive_cheap_method_and_frozen_cost_protocol'] if passed else [])))
    print(json.dumps(results,indent=2),flush=True)
