"""Separate reconstruction of saved models, selected actions, and result totals."""
from common import *
import pickle
import sys
import torch
from threadpoolctl import threadpool_limits

def choose_reference(scores, hubs):
    answer = np.zeros((len(scores), 2), 'i4')
    for q in range(len(scores)):
        for k in range(2):
            # Sort real IDs as an explicit secondary key; default beats zero.
            order = np.lexsort((hubs, -scores[q, :, k]))
            h = order[0]
            if scores[q, h, k] > 0:
                answer[q, k] = h + 1
    return answer

def primary_reference(rep, state, rows, data, capability):
    bank = rep['bank'].astype('f8').copy()
    if not capability:
        bank[:, -64:] = 0
    q = rep['q'][rows].astype('f8')
    raw = unit(data['q'][rows].astype('f8'))
    cosine = np.stack([raw @ unit(data['hv'].astype('f8')).T,
                       raw @ unit(data['profiles'].astype('f8')).T], -1)
    w = {k:v.numpy().astype('f8') for k,v in state.items()}
    u = q @ w['query.weight'].T + w['query.bias']
    v = bank @ w['entry.weight'].T + w['entry.bias']
    hidden = np.maximum(u[:, None, :] + v[None, :, :] + u[:, None, :] * v[None, :, :], 0)
    return hidden @ w['output.weight'].T + cosine @ w['cosine.weight'].T + rep['prior'][None, :, :]

if __name__ == '__main__':
    os.sched_setaffinity(0, {15})
    torch.set_num_threads(1)
    start = time.monotonic()
    lock = read(RUN/'config.locked.json')
    result = read(RUN/'analysis/results.json')
    frozen = read(RUN/'reviews/pretraining_freeze.json')
    for item in frozen['files'] + [frozen['config'], frozen['protocol']]:
        assert identity(item['path']) == item
    inputs = read(RUN/'reviews/source_identity.json')['files']
    for item in inputs:
        assert identity(item['path']) == item
    records = []
    for ds in lock['datasets']:
        data = load_data(ds)
        totals = {name:np.zeros((4096,2)) for name in result['results'][ds]}
        for fold, roles in enumerate(lock['roles'][ds]):
            src = RUN/'models'/ds/f'fold_{fold}'
            out = RUN/'results'/ds/f'fold_{fold}'
            with np.load(src/'representation.npz') as saved_rep:
                rep = {key:saved_rep[key] for key in saved_rep.files}
            rows = np.asarray(roles['outer'])
            supp = np.asarray(roles['support'])
            u, dr, dt, tref = targets(data, supp)
            original = np.load(out/'labels.npz')
            assert np.array_equal(original['utility'],u[rows])
            assert np.array_equal(original['recall_delta'],dr[rows])
            assert np.array_equal(original['time_delta'],dt[rows])
            # Independently reconstruct every cluster response and shrinkage mean.
            response = np.concatenate([dr[:,1:],dt[:,1:]],-1)
            support_response = response[supp]
            support_cluster = rep['cluster'][supp]
            mean = support_response.sum(0)/len(supp)
            expected = []
            for h in range(len(data['hubs'])):
                expected.append(np.concatenate([(support_response[support_cluster==c,h].sum(0)+16*mean[h]) /
                    (int(np.sum(support_cluster==c))+16)-mean[h] for c in range(16)]))
            assert np.allclose(rep['raw_capability'],expected,atol=1e-12,rtol=1e-12)
            model_checks = {}
            pick = np.array([0,1,127,511,1023])
            for name in result['results'][ds]:
                saved = np.zeros((1024,len(data['hubs']),2), 'f4') if name=='GT10' else np.load(out/f'{name}.npy')
                act = choose_reference(saved, data['hubs'])
                aligned = np.load(RUN/'analysis'/ds/f'{name}.npz')
                assert np.array_equal(act, aligned['actions'][rows])
                for k in range(2):
                    actual = u[rows,act[:,k],k]
                    assert np.array_equal(actual.astype('f8'),aligned['utility'][rows,k])
                    assert np.array_equal(dr[rows,act[:,k],k].astype('f8'),aligned['recall_delta'][rows,k])
                    totals[name][rows,k] = actual
                if name in lock['primary']:
                    state = torch.load(src/name/'model.pt', map_location='cpu', weights_only=True)
                    estimate = primary_reference(rep,state,rows[pick],data,name.startswith('Cap'))
                    error = float(np.max(abs(estimate-saved[pick])))
                    assert error < 2e-4
                    assert np.array_equal(choose_reference(estimate,data['hubs']),act[pick])
                    history = read(src/name/'training.json')['history']
                    best = max(history,key=lambda v:v['monitor_utility'])
                    pm = primary_reference(rep,state,np.asarray(roles['monitor']),data,name.startswith('Cap'))
                    ma = choose_reference(pm,data['hubs'])
                    mon = np.asarray(roles['monitor'])
                    value = np.mean([u[mon,ma[:,k],k].mean() for k in range(2)])
                    assert abs(value-best['monitor_utility'])<1e-6
                    model_checks[name] = dict(independent_forward_max_error=error, best_epoch=best['epoch'],
                        fit_utility_at_selected=best['fit_utility'], monitor_utility=best['monitor_utility'])
                elif name in lock['strong']:
                    r = rows[pick]
                    raw = unit(data['q'][r].astype('f8'))
                    cos = np.stack([raw@unit(data['hv'].astype('f8')).T,raw@unit(data['profiles'].astype('f8')).T],-1).astype('f4')
                    matrix = np.concatenate([np.repeat(rep['q'][r],len(data['hubs']),0),
                        np.tile(rep['bank'],(len(r),1)),cos.reshape(-1,2)],1)
                    if name=='GBDT':
                        heads=[]
                        for k in range(2):
                            with (src/name/f'K{k}.pickle').open('rb') as f: model=pickle.load(f)
                            heads.append(model.predict(matrix).reshape(len(r),-1))
                        estimate=np.stack(heads,-1)
                    else:
                        sys.path.insert(0,str(RUN/'vendor'))
                        from tabm import TabM
                        model=TabM.make(n_num_features=matrix.shape[1],d_out=2,k=16,n_blocks=2,d_block=128,dropout=0.1)
                        model.load_state_dict(torch.load(src/name/'model.pt',map_location='cpu',weights_only=True))
                        model.eval()
                        with torch.no_grad(): estimate=model(torch.from_numpy(matrix)).mean(1).numpy().reshape(len(r),-1,2)
                    error=float(np.max(abs(estimate-saved[pick])))
                    assert error<2e-4
                    assert np.array_equal(choose_reference(estimate,data['hubs']),act[pick])
                    model_checks[name]=dict(reloaded_forward_max_error=error)
            records.append(dict(dataset=ds,fold=fold,all_saved_actions_and_payoffs_verified=True,
                capability_means_verified=True,models=model_checks))
        for name, value in totals.items():
            assert abs(value.mean()-result['results'][ds][name]['mean_utility'])<1e-9
    dump(RUN/'reviews/independent_audit.json',dict(status='PASS',source_files_verified=len(inputs),
        frozen_training_code_unchanged=True,records=records,seconds=time.monotonic()-start,
        independence='separate numerical implementation in the same session; not a separate human/agent review',
        no_new_search=True,no_new_training=True))
    print('INDEPENDENT NUMERICAL AUDIT PASS',flush=True)
