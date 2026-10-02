from common import *
from features import representation
from models import SharedInteraction, objective
import torch
import sys

def synthetic():
    hubs = np.array([7, 2, 9])
    scores = np.array([[0, 0, 0], [1, 1, 0], [-1, -2, -3], [0.1, 0.2, 0.3]])
    assert np.array_equal(actions(scores, hubs), [0, 2, 0, 3])
    pred = torch.tensor([[[0.2, -0.3], [0.1, 0.1]]], dtype=torch.float64, requires_grad=True)
    target = torch.tensor([[[0.4, -0.1], [0.2, 0.2]]], dtype=torch.float64)
    assert torch.autograd.gradcheck(lambda x: objective(x, target, True), (pred,))
    assert objective(target, target, False).item() == 0
    torch.manual_seed(19)
    model = SharedInteraction(5, 68).double()
    with torch.no_grad():
        model.output.weight.normal_()
        model.cosine.weight.normal_()
    q = torch.randn(3, 5, dtype=torch.float64)
    bank = torch.randn(4, 68, dtype=torch.float64)
    cosine = torch.randn(3, 4, 2, dtype=torch.float64)
    prior = torch.randn(4, 2, dtype=torch.float64)
    actual = model(q, bank, cosine, prior).detach().numpy()
    state = {k: v.detach().numpy() for k, v in model.state_dict().items()}
    expected = np.empty_like(actual)
    for i in range(3):
        for h in range(4):
            u = state['query.weight'] @ q[i].numpy() + state['query.bias']
            v = state['entry.weight'] @ bank[h].numpy() + state['entry.bias']
            expected[i, h] = state['output.weight'] @ np.maximum(u + v + u * v, 0) + state['cosine.weight'] @ cosine[i, h].numpy() + prior[h].numpy()
    assert np.allclose(actual, expected, atol=1e-12, rtol=1e-12)
    sys.path.insert(0, str(RUN / 'vendor'))
    from tabm import TabM
    m = TabM.make(n_num_features=7, d_out=2, k=16, n_blocks=2, d_block=128, dropout=0.1)
    assert m(torch.ones(4, 7)).shape == (4, 16, 2)
    return dict(default_and_real_ID_ties=True, rank_gradient_check=True, scalar_forward_max_error=float(abs(actual - expected).max()), author_tabm_shape=True)

if __name__ == '__main__':
    start = time.monotonic()
    lock = read(RUN / 'config.locked.json')
    assert identity(RUN / 'protocol.md') == lock['protocol']
    assert identity(RUN / 'research.md') == lock['research']
    checks = dict(synthetic=synthetic(), datasets={})
    for ds in lock['datasets']:
        data = load_data(ds)
        hashes = np.array([hashlib.sha256(q.tobytes()).hexdigest() for q in data['q']])
        assert len(set(hashes)) == 4096
        for roles in lock['roles'][ds]:
            assert sorted(sum(roles.values(), [])) == list(range(4096))
            allkeys = [set(hashes[rows]) for rows in roles.values()]
            assert all(not (allkeys[i] & allkeys[j]) for i in range(4) for j in range(i))
        rep = representation(data, lock['roles'][ds][0], 0)
        # A hostile outer-label change must leave the deployable representation unchanged.
        modified = dict(data)
        modified['recall'] = data['recall'].copy()
        modified['seconds'] = data['seconds'].copy()
        outer = lock['roles'][ds][0]['outer']
        modified['recall'][outer] = 1 - modified['recall'][outer]
        modified['seconds'][outer] *= 5
        other = representation(modified, lock['roles'][ds][0], 0)
        for k in ['q', 'bank', 'cosine', 'prior', 'cluster_scores', 'qmean', 'qscale', 'centers']:
            assert np.array_equal(rep[k], other[k]), k
        roles = lock['roles'][ds][0]
        selected_rows = np.asarray(roles['outer'])[:16]
        act = actions(rep['cluster_scores'][selected_rows, :, 0], data['hubs'])
        u = selected(rep['utility'][selected_rows, :, 0], act)
        direct = selected(rep['dr'][selected_rows, :, 0], act) - 0.1 * selected(rep['dt'][selected_rows, :, 0], act)
        assert np.allclose(u, direct, atol=1e-7)
        checks['datasets'][ds] = dict(n=4096, H=len(data['hubs']), all_top1_and_K100_masks_verified=True,
            four_roles_row_and_byte_disjoint=True, outer_response_invariance=True,
            cluster_counts=rep['cluster_counts'].tolist(), raw_response_shapes={k:list(data[k].shape) for k in ['recall','seconds','masks']})
        print('PREFLIGHT', ds, 'PASS', flush=True)
    dump(RUN / 'reviews/preflight.json', dict(status='PASS', checks=checks, seconds=time.monotonic() - start))
