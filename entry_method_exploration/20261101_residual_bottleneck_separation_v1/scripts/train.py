from common import *
import gzip
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import sklearn

ds = sys.argv[1]
c = read(R / 'configs' / f'{ds}.labels.json')
label_dir = Path(c['output_dir']); info = read(label_dir / 'complete.json')
meta = np.frombuffer(gzip.open(label_dir / 'labels.i32.gz', 'rb').read(), '<i4').reshape(-1, 11)
xp = Path(c['scratch']) / 'features.f32'
X = np.memmap(xp, '<f4', mode='r', shape=(len(meta), 104))
assert len(meta) == info['rows'] and np.isfinite(X).all()
assert np.array_equal(meta[:,7], meta[:,5]-meta[:,6])
models = {}; comparisons = []; audits = []
started = time.perf_counter()

def choose(indices, predictions):
    selected = []
    query_ids=meta[indices,0]
    starts=np.r_[0,np.flatnonzero(np.diff(query_ids))+1]
    ends=np.r_[starts[1:],len(indices)]
    for start,end in zip(starts,ends):
        local=int(start+np.argmax(predictions[start:end]))
        selected.append((int(query_ids[start]), indices[local], float(predictions[local])))
    return selected

def tree_export(model):
    trees = []
    for stage in model._predictors:
        assert len(stage) == 1
        tree = stage[0].nodes
        assert not np.any(tree['is_categorical'])
        trees.append([dict(f=int(n['feature_idx']), t=float(n['num_threshold']),
                           l=int(n['left']), r=int(n['right']), v=float(n['value']),
                           leaf=bool(n['is_leaf'])) for n in tree])
    return dict(type='hgb', feature_count=104, bias=float(model._baseline_prediction[0,0]), trees=trees)

for K in [1,100]:
    take = np.flatnonzero(meta[:,1] == K)
    fit = take[meta[take,0] < 2048]; cal = take[meta[take,0] >= 2048]
    assert len(fit) and len(cal)
    y = meta[fit,7].astype(float)
    candidates = []
    for kind in ['ridge','hgb']:
        t = time.perf_counter()
        if kind == 'ridge':
            scaler = StandardScaler().fit(X[fit,:24])
            learner = Ridge(alpha=10).fit(scaler.transform(X[fit,:24]), y)
            coefficient = learner.coef_ / scaler.scale_
            exported = dict(type='ridge', feature_count=24,
                            bias=float(learner.intercept_-np.dot(coefficient,scaler.mean_)),
                            coef=coefficient.tolist())
            predictions = np.asarray(X[take,:24], float) @ coefficient + exported['bias']
        else:
            learner = HistGradientBoostingRegressor(max_iter=128, max_leaf_nodes=15,
                l2_regularization=10, learning_rate=.08, random_state=197,
                early_stopping=False).fit(np.asarray(X[fit]), y)
            predictions = learner.predict(np.asarray(X[take]))
            exported = tree_export(learner)
        selected = choose(take, predictions)
        cal_selected = [(q,i,p) for q,i,p in selected if q>=2048]
        fit_scores = [p for q,i,p in selected if q<2048]
        net = sum(int(meta[i,7]) for q,i,p in cal_selected)
        positive = sum(max(0,int(meta[i,7])) for q,i,p in cal_selected)
        thresholds = [float(np.quantile(fit_scores,1-rate)) for rate in [1,.75,.5,.25,.1,.05,.01]]
        feasible = []
        for threshold in thresholds:
            enabled = [(q,i,p) for q,i,p in cal_selected if p>=threshold]
            kept_positive = sum(max(0,int(meta[i,7])) for q,i,p in enabled)
            kept_net = sum(int(meta[i,7]) for q,i,p in enabled)
            if positive>0 and kept_positive>=.9*positive:
                feasible.append((len(enabled),-kept_net,threshold,kept_positive))
        if feasible:
            active,negative_net,threshold,kept_positive = min(feasible)
            exported.update(threshold=threshold, gate_all_off=False)
        else:
            active=0;negative_net=0;kept_positive=0
            exported.update(threshold=0., gate_all_off=True)
        row=dict(dataset=ds,K=K,model=kind,fit_seed_rows=len(fit),cal_seed_rows=len(cal),
                 fit_positive_rows=int((meta[fit,7]>0).sum()),cal_positive_rows=int((meta[cal,7]>0).sum()),
                 cal_selected_net_hits=net,cal_selected_positive_hits=positive,
                 cal_gate_enabled=active,cal_gate_net_hits=-negative_net,
                 cal_positive_kept=kept_positive,training_seconds=time.perf_counter()-t)
        comparisons.append(row);candidates.append((net,kind=='ridge',kind,exported,predictions))
        dump(R/'storage/models'/ds/f'{kind}.k{K}.json',exported)
        print(json.dumps(row),flush=True)
    net,cheap,kind,exported,predictions = max(candidates,key=lambda t:(t[0],t[1]))
    models[str(K)] = exported
    # Retain all selected-model numerical predictions for native inference parity.
    audit = np.column_stack([take.astype(float), predictions]).astype('<f8')
    with gzip.open(R/'storage/models'/ds/f'inference.k{K}.f64.gz','wb',compresslevel=1) as f:f.write(audit.tobytes())
    audits.append(dict(K=K,selected_model=kind,rows=len(take),cal_selection_net=net))
dump(R/'storage/models'/ds/'selected.json',dict(dataset=ds,K=models,features=104,
    training_GT_only=True,fit_queries=2048,cal_queries=1024,sklearn=sklearn.__version__,
    feature_sha256=sha(xp),label_metadata_sha256=sha(label_dir/'labels.i32.gz'),
    source_labels_info=info,selection=audits,seconds=time.perf_counter()-started))
csvwrite(R/'storage/models'/ds/'model_comparisons.csv',comparisons)
print('TRAINED',ds,flush=True)
