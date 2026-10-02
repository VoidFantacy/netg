"""Audit frozen E96 labels/model export; no ANN, optimization, or new GT."""
import ast
import hashlib
import json
import os
from pathlib import Path

os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

ROOT = Path('/data/netg/ACSG')
E96 = ROOT / 'entry_method_exploration/20260914_gate_new_ood_v1'
OUT = Path(__file__).resolve().parents[1]
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

# Extract only pure definitions, bypassing all old runner/preparation entrypoints.
tree = ast.parse((E96/'src/train_gate.py').read_text())
defs = [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))
        and n.name in ('Tower', 'release_samples')]
scope = dict(nn=nn, torch=torch, np=np)
exec(compile(ast.Module(body=defs, type_ignores=[]), 'frozen_e96_definitions', 'exec'), scope)
Tower, release_samples = scope['Tower'], scope['release_samples']

preflight = json.loads((E96/'reviews/preflight.json').read_text())
records = []
with torch.inference_mode():
    for frozen in preflight['datasets']:
        ds = frozen['dataset']
        inp = E96/'inputs'/ds
        modeldir = E96/'models'/ds/'gate_release10_v2'
        d = json.loads((modeldir/'config.json').read_text())['dim']
        assert sha(modeldir/'W.f32') == frozen['gate_W_sha256']
        assert sha(modeldir/'best.pt') == frozen['training']['checkpoint_sha256']
        node = torch.from_numpy(np.fromfile(inp/'gate.hubs.f32','f4').reshape(512,d))
        graph = torch.from_numpy(np.fromfile(inp/'gate.release10.graph2vec.f32','f4').reshape(512,d))
        q = torch.from_numpy(np.fromfile(inp/'gate_monitor.f32','f4').reshape(1024,d))
        hops = np.concatenate([np.fromfile(inp/'labels'/f'rows_{s}.hop.i32','i4').reshape(-1,512)
                               for s in range(0,11024,128)])
        returned = np.concatenate([np.fromfile(inp/'labels'/f'rows_{s}.ids.i32','i4').reshape(-1,512)
                                   for s in range(0,11024,128)])
        gt = np.concatenate([np.fromfile(inp/f'{name}.gt.i32','i4').reshape(-1,100)
                             for name in ['gate_train','gate_monitor']])
        assert np.array_equal(hops != 999, returned == gt[:,:1])
        pos, neg = release_samples(hops)
        good = np.array([10 <= len(n) <= 500 for n in neg])
        mon = hops[10000:]
        usable = good[10000:]
        target = mon == mon.min(axis=1,keepdims=True)
        pairs = np.fromfile(inp/'gate.triplets.i32','i4').reshape(-1,3)
        assert pairs[:,1:].min() >= 0 and pairs[:,1:].max() < 10000
        assert np.all(hops[pairs[:,1], pairs[:,0]] == hops[pairs[:,1]].min(axis=1))
        assert all(int(h) in neg[int(n)] for h,_,n in pairs)
        model = Tower(d).eval()
        model.load_state_dict(torch.load(modeldir/'best.pt', map_location='cpu', weights_only=True))
        predicted = F.normalize(model(node,graph),dim=1)
        saved = torch.from_numpy(np.fromfile(modeldir/'W.f32','f4').reshape(512,d))
        torch.testing.assert_close(predicted, saved, atol=4e-6,rtol=4e-5)
        multi = model(node[:8],graph[:8])
        single = torch.cat([model(node[i:i+1],graph[i:i+1]) for i in range(8)])
        torch.testing.assert_close(multi,single,atol=4e-6,rtol=4e-5)
        methods = {}
        for name,w in [('raw_hub_cosine',F.normalize(node,dim=1)), ('GATE_learned',saved)]:
            selected = (F.normalize(q,dim=1) @ w.T).argmax(dim=1).numpy()
            picked = mon[np.arange(1024),selected]
            methods[name] = dict(exact_min_hop_route_acc=float(target[np.arange(1024),selected][usable].mean()),
                                 selected_cached_single_entry_gt1_success_all1024=float((picked!=999).mean()),
                                 unique_selected_hubs=int(len(np.unique(selected))))
        observed = methods['GATE_learned']['exact_min_hop_route_acc']
        assert abs(observed-frozen['training']['best']['monitor_route_accuracy']) < 1e-7
        sizes = [len(json.loads((inp/'subgraphs_release10_v2'/f'{h}.json').read_text())['nodes']) for h in range(512)]
        hist = json.loads((modeldir/'history.json').read_text())
        best = max(hist,key=lambda r:r['monitor_route_accuracy'])
        assert best['epoch'] == frozen['training']['best']['epoch']
        records.append(dict(dataset=ds,monitor_usable=int(usable.sum()),triplets=len(pairs),
                            identical_positive_negative_query_triplets=int((pairs[:,1]==pairs[:,2]).sum()),
                            represented_hubs=int(len(np.unique(pairs[:,0]))),
                            first_loss=hist[0]['loss'],last_loss=hist[-1]['loss'],best_epoch=best['epoch'],
                            model_export_max_abs=float((predicted-saved).abs().max()),
                            batch_singleton_max_abs=float((multi-single).abs().max()),
                            subgraphs_at_1000_node_cap=int(sum(n==1000 for n in sizes)),
                            subgraph_nodes_min=min(sizes),subgraph_nodes_max=max(sizes),
                            cached_monitor_controls=methods))
        print(json.dumps(records[-1]),flush=True)
        del model, predicted, saved, node, graph, hops, returned, pairs

# The legacy fusion's default sequence-first setting mixes different hubs.
torch.manual_seed(42)
layer = nn.TransformerEncoderLayer(16,4,32,dropout=0).eval()
x = torch.randn(8,2,16)
with torch.inference_mode():
    delta = float((layer(x)[:1]-layer(x[:1])).abs().max())
assert delta > 1e-4
result = dict(status='PASS_CACHED_IMPLEMENTATION_CHECKS',new_training=0,new_ANN=0,new_graph_build=0,new_GT=0,new_QPS=0,
              definition='Route accuracy and cached L64 single-entry success are diagnostics, not Recall@1 of deployed top3 search.',
              source_sha256=sha(E96/'src/train_gate.py'),datasets=records,
              synthetic_legacy_cross_hub_attention_max_abs=delta)
(OUT/'results/cached_checks.json').write_text(json.dumps(result,indent=2)+'\n')
